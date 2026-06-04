"""File encryption and storage service."""
import os
import base64
import shutil
from pathlib import Path
from typing import Optional, Tuple
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import (
    generate_aes_key,
    encrypt_file_aes,
    decrypt_file_aes,
    encrypt_aes_key_with_rsa,
    decrypt_aes_key_with_rsa,
    compute_file_hash,
    sign_data,
    verify_signature
)
from app.models.models import File as FileModel, FileShare, User
from app.services.audit_service import log_file_upload, log_file_download, log_failed_access

settings = get_settings()


def ensure_upload_dir():
    """Ensure upload directory exists."""
    Path(settings.UPLOAD_DIR).mkdir(parents=True, exist_ok=True)


def store_encrypted_file(
    db: Session,
    file_data: bytes,
    original_filename: str,
    mime_type: Optional[str],
    owner: User,
    ip_address: str = None,
    should_sign: bool = False
) -> FileModel:
    """
    Encrypt and store a file using hybrid encryption.

    Process:
    1. Compute file hash (integrity)
    2. Generate random AES-256 key
    3. Encrypt file with AES-GCM
    4. Encrypt AES key with owner's public key (RSA)
    5. Optionally sign the file hash
    6. Store encrypted file and metadata
    """
    ensure_upload_dir()

    # Step 1: Compute file hash for integrity verification
    file_hash = compute_file_hash(file_data)

    # Step 2: Generate AES-256 key
    aes_key = generate_aes_key()

    # Step 3: Encrypt file with AES-GCM
    ciphertext, nonce, _ = encrypt_file_aes(file_data, aes_key)

    # Step 4: Encrypt AES key with owner's public key
    encrypted_aes_key = encrypt_aes_key_with_rsa(
        aes_key,
        owner.public_key.encode() if owner.public_key else b""
    )

    # Step 5: Optionally sign the file hash (digital signature)
    signature = None
    if should_sign and owner.private_key_encrypted:
        # In production, decrypt the private key first (using user's password)
        # For demo, we sign with a derived key approach
        signature = base64.b64encode(sign_data(
            file_hash.encode(),
            owner.private_key_encrypted.encode()  # Simplified for demo
        )).decode()

    # Step 6: Store encrypted file
    safe_name = (original_filename or "upload").replace(" ", "_").replace("/", "_").replace("\\", "_")
    safe_filename = f"{file_hash}_{safe_name}"
    encrypted_path = os.path.join(settings.UPLOAD_DIR, safe_filename + ".enc")

    with open(encrypted_path, "wb") as f:
        f.write(ciphertext)

    # Create database record
    db_file = FileModel(
        filename=safe_filename,
        original_filename=original_filename,
        file_size=len(file_data),
        mime_type=mime_type,
        encrypted_file_path=encrypted_path,
        file_hash=file_hash,
        encrypted_aes_key=base64.b64encode(encrypted_aes_key).decode(),
        aes_nonce=base64.b64encode(nonce).decode(),
        signature=signature,
        owner_id=owner.id
    )

    db.add(db_file)
    db.commit()
    db.refresh(db_file)

    # Log the upload
    log_file_upload(
        db=db,
        user_id=owner.id,
        filename=original_filename,
        file_hash=file_hash,
        ip_address=ip_address,
        success=True
    )

    return db_file


def retrieve_and_decrypt_file(
    db: Session,
    file_id: int,
    user: User,
    ip_address: str = None
) -> Tuple[bytes, str]:
    """
    Retrieve and decrypt a file for an authorized user.

    Process:
    1. Verify user has access (owner or shared with)
    2. Get encrypted AES key (decrypted with user's private key)
    3. Decrypt file with AES-GCM
    4. Verify file hash (integrity check)
    5. Log download
    """
    db_file = db.query(FileModel).filter(FileModel.id == file_id).first()

    if not db_file:
        log_failed_access(
            db=db,
            ip_address=ip_address,
            resource=f"file:{file_id}",
            username_attempted=user.username,
            reason="File not found"
        )
        raise ValueError("File not found")

    # Verify ownership or sharing permission
    is_owner = db_file.owner_id == user.id
    share = db.query(FileShare).filter(
        FileShare.file_id == file_id,
        FileShare.recipient_id == user.id
    ).first()

    if not is_owner and not share:
        log_failed_access(
            db=db,
            ip_address=ip_address,
            resource=f"file:{file_id}",
            username_attempted=user.username,
            reason="Unauthorized access - not owner or shared recipient"
        )
        raise PermissionError("You do not have access to this file")

    if not is_owner and share and not share.can_download:
        log_failed_access(
            db=db,
            ip_address=ip_address,
            resource=f"file:{file_id}",
            username_attempted=user.username,
            reason="Download not permitted for shared recipient"
        )
        raise PermissionError("You do not have download permission for this file")

    # Determine which encrypted AES key to use
    if is_owner:
        encrypted_aes_key = base64.b64decode(db_file.encrypted_aes_key)
    else:
        encrypted_aes_key = base64.b64decode(share.encrypted_aes_key_for_recipient)

    # Decrypt AES key with user's private key
    # In production, decrypt the private key with user's password first
    private_key = user.private_key_encrypted.encode() if user.private_key_encrypted else b""

    try:
        aes_key = decrypt_aes_key_with_rsa(encrypted_aes_key, private_key)
    except Exception as e:
        log_failed_access(
            db=db,
            ip_address=ip_address,
            resource=f"file:{file_id}",
            username_attempted=user.username,
            reason=f"Decryption failed: {str(e)}"
        )
        raise ValueError("Failed to decrypt file key")

    # Read encrypted file
    with open(db_file.encrypted_file_path, "rb") as f:
        ciphertext = f.read()

    # Decrypt file
    nonce = base64.b64decode(db_file.aes_nonce)
    try:
        decrypted_data = decrypt_file_aes(ciphertext, aes_key, nonce)
    except Exception as e:
        log_failed_access(
            db=db,
            ip_address=ip_address,
            resource=f"file:{file_id}",
            username_attempted=user.username,
            reason=f"File decryption failed: {str(e)}"
        )
        raise ValueError("Failed to decrypt file - possible tampering")

    # Verify integrity
    computed_hash = compute_file_hash(decrypted_data)
    if computed_hash != db_file.file_hash:
        log_failed_access(
            db=db,
            ip_address=ip_address,
            resource=f"file:{file_id}",
            username_attempted=user.username,
            reason="Integrity check failed - file may have been tampered with"
        )
        raise ValueError("File integrity check failed - possible tampering detected")

    # Log successful download
    log_file_download(
        db=db,
        user_id=user.id,
        file_id=file_id,
        filename=db_file.original_filename,
        ip_address=ip_address,
        success=True
    )

    return decrypted_data, db_file.original_filename


def share_file(
    db: Session,
    file_id: int,
    owner: User,
    recipient: User,
    can_download: bool = True,
    can_view: bool = True,
    ip_address: str = None
) -> FileShare:
    """
    Share a file with another user using hybrid encryption.

    Process:
    1. Verify owner has the file
    2. Decrypt AES key with owner's private key
    3. Re-encrypt AES key with recipient's public key
    4. Create share record
    """
    db_file = db.query(FileModel).filter(
        FileModel.id == file_id,
        FileModel.owner_id == owner.id
    ).first()

    if not db_file:
        raise ValueError("File not found or you are not the owner")

    # Decrypt AES key with owner's private key
    encrypted_aes_key = base64.b64decode(db_file.encrypted_aes_key)
    owner_private_key = owner.private_key_encrypted.encode() if owner.private_key_encrypted else b""

    try:
        aes_key = decrypt_aes_key_with_rsa(encrypted_aes_key, owner_private_key)
    except Exception:
        raise ValueError("Failed to decrypt file key for sharing")

    # Re-encrypt AES key with recipient's public key
    recipient_public_key = recipient.public_key.encode() if recipient.public_key else b""
    encrypted_aes_key_for_recipient = encrypt_aes_key_with_rsa(aes_key, recipient_public_key)

    # Check if share already exists
    existing_share = db.query(FileShare).filter(
        FileShare.file_id == file_id,
        FileShare.recipient_id == recipient.id
    ).first()

    if existing_share:
        existing_share.encrypted_aes_key_for_recipient = base64.b64encode(encrypted_aes_key_for_recipient).decode()
        existing_share.can_download = can_download
        existing_share.can_view = can_view
        db.commit()
        db.refresh(existing_share)
        share = existing_share
    else:
        share = FileShare(
            file_id=file_id,
            recipient_id=recipient.id,
            encrypted_aes_key_for_recipient=base64.b64encode(encrypted_aes_key_for_recipient).decode(),
            can_download=can_download,
            can_view=can_view
        )
        db.add(share)
        db.commit()
        db.refresh(share)

    # Log the share
    from app.services.audit_service import log_file_share
    log_file_share(
        db=db,
        user_id=owner.id,
        file_id=file_id,
        recipient_username=recipient.username,
        ip_address=ip_address,
        success=True
    )

    return share


def verify_file_signature(
    db: Session,
    file_id: int,
    user: User
) -> dict:
    """Verify the digital signature of a file."""
    db_file = db.query(FileModel).filter(FileModel.id == file_id).first()

    if not db_file or not db_file.signature:
        return {"verified": False, "message": "No signature available"}

    owner = db.query(User).filter(User.id == db_file.owner_id).first()
    if not owner or not owner.public_key:
        return {"verified": False, "message": "Owner public key not available"}

    try:
        is_valid = verify_signature(
            db_file.file_hash.encode(),
            base64.b64decode(db_file.signature),
            owner.public_key.encode()
        )
        return {
            "verified": is_valid,
            "message": "Signature valid - file authenticity and integrity confirmed" if is_valid else "Signature invalid - file may have been tampered with",
            "signer": owner.username,
            "file_hash": db_file.file_hash
        }
    except Exception as e:
        return {"verified": False, "message": f"Verification error: {str(e)}"}


def delete_file(db: Session, file_id: int, user: User) -> bool:
    """Delete a file and its encrypted storage."""
    db_file = db.query(FileModel).filter(
        FileModel.id == file_id,
        FileModel.owner_id == user.id
    ).first()

    if not db_file:
        return False

    # Delete encrypted file from disk
    if os.path.exists(db_file.encrypted_file_path):
        os.remove(db_file.encrypted_file_path)

    # Delete from database (cascade will handle shares)
    db.delete(db_file)
    db.commit()
    return True
    db.commit()

    return True
