"""SQLAlchemy database models."""
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text, LargeBinary, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class User(Base):
    """User model for authentication."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_login = Column(DateTime(timezone=True), nullable=True)

    # RSA Key Pair (stored encrypted or in secure storage)
    public_key = Column(Text, nullable=True)
    private_key_encrypted = Column(Text, nullable=True)

    # Relationships
    files = relationship("File", back_populates="owner", cascade="all, delete-orphan")
    shared_with_me = relationship("FileShare", foreign_keys="FileShare.recipient_id", back_populates="recipient")
    audit_logs = relationship("AuditLog", back_populates="user")


class File(Base):
    """File model for encrypted file storage."""
    __tablename__ = "files"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_size = Column(Integer, nullable=False)
    mime_type = Column(String(100), nullable=True)

    # Encryption metadata
    encrypted_file_path = Column(String(500), nullable=False)
    file_hash = Column(String(64), nullable=False)  # SHA-256 of original file

    # AES key encrypted with owner's public key (hybrid encryption)
    encrypted_aes_key = Column(Text, nullable=False)
    aes_nonce = Column(String(255), nullable=False)  # Base64 encoded nonce

    # Digital signature (Phase 2)
    signature = Column(Text, nullable=True)

    # Ownership
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    owner = relationship("User", back_populates="files")
    shares = relationship("FileShare", back_populates="file", cascade="all, delete-orphan")


class FileShare(Base):
    """File sharing permissions model."""
    __tablename__ = "file_shares"

    id = Column(Integer, primary_key=True, index=True)
    file_id = Column(Integer, ForeignKey("files.id"), nullable=False)
    recipient_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # AES key encrypted with recipient's public key
    encrypted_aes_key_for_recipient = Column(Text, nullable=False)

    # Permissions
    can_download = Column(Boolean, default=True)
    can_view = Column(Boolean, default=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    file = relationship("File", back_populates="shares")
    recipient = relationship("User", foreign_keys=[recipient_id], back_populates="shared_with_me")


class AuditLog(Base):
    """Security audit log model."""
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    event_type = Column(String(50), nullable=False, index=True)
    event_description = Column(Text, nullable=False)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)
    success = Column(Boolean, default=True)
    details = Column(Text, nullable=True)  # JSON string with additional details
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationship
    user = relationship("User", back_populates="audit_logs")


class FailedAccessAttempt(Base):
    """Track failed access attempts for security monitoring."""
    __tablename__ = "failed_access_attempts"

    id = Column(Integer, primary_key=True, index=True)
    ip_address = Column(String(45), nullable=False, index=True)
    username_attempted = Column(String(50), nullable=True)
    resource = Column(String(255), nullable=True)
    attempt_count = Column(Integer, default=1)
    last_attempt = Column(DateTime(timezone=True), server_default=func.now())
    blocked_until = Column(DateTime(timezone=True), nullable=True)
