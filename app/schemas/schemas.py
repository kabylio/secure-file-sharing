"""Pydantic schemas for request/response validation."""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime


# ═══════════════════════════════════════════════════════════════
# USER SCHEMAS
# ═══════════════════════════════════════════════════════════════

class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr

class UserCreate(UserBase):
    password: str = Field(..., min_length=8, max_length=100)

class UserLogin(BaseModel):
    username: str
    password: str

class UserResponse(UserBase):
    id: int
    is_active: bool
    created_at: datetime
    last_login: Optional[datetime] = None

    class Config:
        from_attributes = True

class UserProfile(UserResponse):
    public_key: Optional[str] = None


# ═══════════════════════════════════════════════════════════════
# FILE SCHEMAS
# ═══════════════════════════════════════════════════════════════

class FileUploadResponse(BaseModel):
    id: int
    filename: str
    original_filename: str
    file_size: int
    file_hash: str
    created_at: datetime

    class Config:
        from_attributes = True

class FileListItem(BaseModel):
    id: int
    original_filename: str
    file_size: int
    mime_type: Optional[str]
    created_at: datetime
    owner_id: int
    owner_username: str

    class Config:
        from_attributes = True

class FileDetail(FileListItem):
    file_hash: str
    signature: Optional[str] = None

    class Config:
        from_attributes = True


# ═══════════════════════════════════════════════════════════════
# FILE SHARE SCHEMAS
# ═══════════════════════════════════════════════════════════════

class FileShareCreate(BaseModel):
    recipient_username: str = Field(..., min_length=3, max_length=50)
    can_download: bool = True
    can_view: bool = True

class FileShareResponse(BaseModel):
    id: int
    file_id: int
    recipient_id: int
    recipient_username: str
    can_download: bool
    can_view: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ═══════════════════════════════════════════════════════════════
# AUDIT LOG SCHEMAS
# ═══════════════════════════════════════════════════════════════

class AuditLogResponse(BaseModel):
    id: int
    event_type: str
    event_description: str
    ip_address: Optional[str]
    success: bool
    created_at: datetime
    username: Optional[str] = None

    class Config:
        from_attributes = True


# ═══════════════════════════════════════════════════════════════
# AUTH SCHEMAS
# ═══════════════════════════════════════════════════════════════

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class TokenData(BaseModel):
    username: Optional[str] = None
    user_id: Optional[int] = None


# ═══════════════════════════════════════════════════════════════
# DASHBOARD SCHEMAS
# ═══════════════════════════════════════════════════════════════

class DashboardStats(BaseModel):
    total_files: int
    total_shared_with_me: int
    total_shared_by_me: int
    recent_uploads: List[FileListItem]
    recent_audit_logs: List[AuditLogResponse]
