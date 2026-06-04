"""Cryptographic operations and security utilities."""
import os
import base64
import hashlib
import secrets
from typing import Tuple, Optional
from pathlib import Path

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding as asym_padding
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
from passlib.context import CryptContext
from jose import jwt, JWTError
from datetime import datetime, timedelta, timezone

from app.core.config import get_settings

settings = get_settings()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ═══════════════════════════════════════════════════════════════
# PASSWORD HASHING
# ═══════════════════════════════════════════════════════════════

def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


# ═══════════════════════════════════════════════════════════════
# JWT TOKENS
# ═══════════════════════════════════════════════════════════════

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)

    now = datetime.now(timezone.utc)
    to_encode.update({
        "exp": int(expire.timestamp()),
        "iat": int(now.timestamp()),
        "type": "access"
    })
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt

def decode_access_token(token: str) -> Optional[dict]:
    """Decode and validate a JWT access token."""
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        if payload.get("type") != "access":
            return None
        return payload
    except JWTError:
        return None


# ═══════════════════════════════════════════════════════════════
# SYMMETRIC ENCRYPTION (AES-256-GCM)
# ═══════════════════════════════════════════════════════════════

def generate_aes_key() -> bytes:
    """Generate a random 256-bit AES key."""
    return AESGCM.generate_key(bit_length=256)

def encrypt_file_aes(file_data: bytes, key: bytes) -> Tuple[bytes, bytes, bytes]:
    """
    Encrypt file data using AES-256-GCM.
    Returns: (ciphertext, nonce, tag)
    """
    aesgcm = AESGCM(key)
    nonce = os.urandom(12)  # 96-bit nonce for GCM
    ciphertext = aesgcm.encrypt(nonce, file_data, None)
    return ciphertext, nonce, b""  # tag is appended to ciphertext in AESGCM

def decrypt_file_aes(ciphertext: bytes, key: bytes, nonce: bytes) -> bytes:
    """
    Decrypt file data using AES-256-GCM.
    """
    aesgcm = AESGCM(key)
    return aesgcm.decrypt(nonce, ciphertext, None)


# ═══════════════════════════════════════════════════════════════
# ASYMMETRIC ENCRYPTION (RSA-2048)
# ═══════════════════════════════════════════════════════════════

def generate_rsa_keypair() -> Tuple[bytes, bytes]:
    """
    Generate an RSA key pair.
    Returns: (private_key_pem, public_key_pem)
    """
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=settings.RSA_KEY_SIZE,
        backend=default_backend()
    )

    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )

    public_key = private_key.public_key()
    public_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )

    return private_pem, public_pem

def encrypt_aes_key_with_rsa(aes_key: bytes, public_key_pem: bytes) -> bytes:
    """Encrypt an AES key using RSA public key."""
    public_key = serialization.load_pem_public_key(public_key_pem, backend=default_backend())
    encrypted_key = public_key.encrypt(
        aes_key,
        asym_padding.OAEP(
            mgf=asym_padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )
    return encrypted_key

def decrypt_aes_key_with_rsa(encrypted_key: bytes, private_key_pem: bytes) -> bytes:
    """Decrypt an AES key using RSA private key."""
    private_key = serialization.load_pem_private_key(
        private_key_pem,
        password=None,
        backend=default_backend()
    )
    aes_key = private_key.decrypt(
        encrypted_key,
        asym_padding.OAEP(
            mgf=asym_padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )
    return aes_key


# ═══════════════════════════════════════════════════════════════
# DIGITAL SIGNATURES
# ═══════════════════════════════════════════════════════════════

def sign_data(data: bytes, private_key_pem: bytes) -> bytes:
    """Sign data using RSA private key."""
    private_key = serialization.load_pem_private_key(
        private_key_pem,
        password=None,
        backend=default_backend()
    )
    signature = private_key.sign(
        data,
        asym_padding.PSS(
            mgf=asym_padding.MGF1(hashes.SHA256()),
            salt_length=asym_padding.PSS.MAX_LENGTH
        ),
        hashes.SHA256()
    )
    return signature

def verify_signature(data: bytes, signature: bytes, public_key_pem: bytes) -> bool:
    """Verify a digital signature using RSA public key."""
    try:
        public_key = serialization.load_pem_public_key(public_key_pem, backend=default_backend())
        public_key.verify(
            signature,
            data,
            asym_padding.PSS(
                mgf=asym_padding.MGF1(hashes.SHA256()),
                salt_length=asym_padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        return True
    except Exception:
        return False


# ═══════════════════════════════════════════════════════════════
# FILE HASHING (INTEGRITY)
# ═══════════════════════════════════════════════════════════════

def compute_file_hash(file_data: bytes) -> str:
    """Compute SHA-256 hash of file data."""
    return hashlib.sha256(file_data).hexdigest()


# ═══════════════════════════════════════════════════════════════
# SECURE RANDOM GENERATION
# ═══════════════════════════════════════════════════════════════

def generate_secure_token(length: int = 32) -> str:
    """Generate a cryptographically secure random token."""
    return secrets.token_urlsafe(length)


def generate_salt() -> bytes:
    """Generate a random salt for key derivation."""
    return os.urandom(32)
