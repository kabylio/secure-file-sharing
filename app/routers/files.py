"""File management router - handles upload, download, sharing, and verification."""
from fastapi import APIRouter, Depends, HTTPException, status, Request, UploadFile, File as FastAPIFile, Form
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List
import io

from app.core.database import get_db
from app.models.models import User, File as FileModel
from app.schemas.schemas import (
    FileUploadResponse,
    FileListItem,
    FileDetail,
    FileShareCreate,
    FileShareResponse
)
from app.routers.auth import get_current_active_user
from app.services.file_service import (
    store_encrypted_file,
    retrieve_and_decrypt_file,
    share_file,
    verify_file_signature,
    delete_file
)
from app.services.audit_service import log_failed_access

router = APIRouter(prefix="/files", tags=["Files"])


@router.post("/upload", response_model=FileUploadResponse)
async def upload_file(
    request: Request,
    file: UploadFile = FastAPIFile(...),
    sign: bool = Form(False),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Upload and encrypt a file."""
    # Read file content
    file_data = await file.read()

    # Check file size (100MB limit)
    max_size = 100 * 1024 * 1024
    if len(file_data) > max_size:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File too large. Maximum size is 100MB."
        )

    try:
        db_file = store_encrypted_file(
            db=db,
            file_data=file_data,
            original_filename=file.filename or "upload",
            mime_type=file.content_type,
            owner=current_user,
            ip_address=request.client.host,
            should_sign=sign
        )
        return db_file
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to encrypt and store file: {str(e)}"
        )


@router.get("/my-files", response_model=List[FileListItem])
async def list_my_files(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """List files owned by current user with pagination."""
    query = db.query(FileModel).filter(FileModel.owner_id == current_user.id).order_by(FileModel.created_at.desc())
    
    total = query.count()
    files = query.offset(skip).limit(limit).all()

    result = []
    for f in files:
        result.append(FileListItem(
            id=f.id,
            original_filename=f.original_filename,
            file_size=f.file_size,
            mime_type=f.mime_type,
            created_at=f.created_at,
            owner_id=f.owner_id,
            owner_username=current_user.username
        ))
    return result


@router.get("/shared-with-me", response_model=List[FileListItem])
async def list_shared_files(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """List files shared with current user with pagination."""
    from app.models.models import FileShare

    shares = db.query(FileShare).filter(
        FileShare.recipient_id == current_user.id
    ).order_by(FileShare.created_at.desc()).offset(skip).limit(limit).all()

    result = []
    for share in shares:
        f = share.file
        owner = db.query(User).filter(User.id == f.owner_id).first()
        result.append(FileListItem(
            id=f.id,
            original_filename=f.original_filename,
            file_size=f.file_size,
            mime_type=f.mime_type,
            created_at=f.created_at,
            owner_id=f.owner_id,
            owner_username=owner.username if owner else "Unknown"
        ))
    return result


@router.get("/{file_id}/download")
async def download_file(
    request: Request,
    file_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Download and decrypt a file."""
    try:
        decrypted_data, original_filename = retrieve_and_decrypt_file(
            db=db,
            file_id=file_id,
            user=current_user,
            ip_address=request.client.host
        )

        return StreamingResponse(
            io.BytesIO(decrypted_data),
            media_type="application/octet-stream",
            headers={
                "Content-Disposition": f'attachment; filename="{original_filename}"',
                "X-Content-Type-Options": "nosniff",
                "X-Frame-Options": "DENY"
            }
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to decrypt file: {str(e)}"
        )


@router.get("/{file_id}", response_model=FileDetail)
async def get_file_details(
    file_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get detailed information about a file."""
    db_file = db.query(FileModel).filter(FileModel.id == file_id).first()

    if not db_file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )

    # Check access
    is_owner = db_file.owner_id == current_user.id
    from app.models.models import FileShare
    share = db.query(FileShare).filter(
        FileShare.file_id == file_id,
        FileShare.recipient_id == current_user.id
    ).first()

    if not is_owner and not share:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this file"
        )

    if not is_owner and share and not share.can_view:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have view permission for this file"
        )

    owner = db.query(User).filter(User.id == db_file.owner_id).first()

    return FileDetail(
        id=db_file.id,
        original_filename=db_file.original_filename,
        file_size=db_file.file_size,
        mime_type=db_file.mime_type,
        created_at=db_file.created_at,
        owner_id=db_file.owner_id,
        owner_username=owner.username if owner else "Unknown",
        file_hash=db_file.file_hash,
        signature=db_file.signature
    )


@router.post("/{file_id}/share", response_model=FileShareResponse)
async def share_file_endpoint(
    request: Request,
    file_id: int,
    share_data: FileShareCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Share a file with another user."""
    # Find recipient
    recipient = db.query(User).filter(User.username == share_data.recipient_username).first()

    if not recipient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recipient user not found"
        )

    if recipient.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot share file with yourself"
        )

    try:
        share = share_file(
            db=db,
            file_id=file_id,
            owner=current_user,
            recipient=recipient,
            can_download=share_data.can_download,
            can_view=share_data.can_view,
            ip_address=request.client.host
        )

        return FileShareResponse(
            id=share.id,
            file_id=share.file_id,
            recipient_id=share.recipient_id,
            recipient_username=recipient.username,
            can_download=share.can_download,
            can_view=share.can_view,
            created_at=share.created_at
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/{file_id}/verify")
async def verify_signature_endpoint(
    file_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Verify the digital signature of a file."""
    result = verify_file_signature(db, file_id, current_user)
    return result


@router.delete("/{file_id}")
async def delete_file_endpoint(
    file_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Delete a file (owner only)."""
    success = delete_file(db, file_id, current_user)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found or you are not the owner"
        )

    return {"message": "File deleted successfully"}
