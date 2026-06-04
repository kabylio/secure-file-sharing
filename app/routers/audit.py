"""Audit logs router - handles security event viewing and monitoring."""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.models.models import User, AuditLog, FailedAccessAttempt
from app.schemas.schemas import AuditLogResponse
from app.routers.auth import get_current_active_user
from app.services.audit_service import get_recent_audit_logs

router = APIRouter(prefix="/audit", tags=["Audit Logs"])


@router.get("/logs", response_model=List[AuditLogResponse])
async def get_audit_logs(
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get recent audit logs (users see their own, admins see all)."""
    if current_user.is_admin:
        logs = db.query(AuditLog).order_by(AuditLog.created_at.desc()).limit(limit).all()
    else:
        logs = db.query(AuditLog).filter(
            AuditLog.user_id == current_user.id
        ).order_by(AuditLog.created_at.desc()).limit(limit).all()

    result = []
    for log in logs:
        username = None
        if log.user_id:
            user = db.query(User).filter(User.id == log.user_id).first()
            username = user.username if user else None

        result.append(AuditLogResponse(
            id=log.id,
            event_type=log.event_type,
            event_description=log.event_description,
            ip_address=log.ip_address,
            success=log.success,
            created_at=log.created_at,
            username=username
        ))

    return result


@router.get("/logs/my")
async def get_my_audit_logs(
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get current user's audit logs."""
    logs = db.query(AuditLog).filter(
        AuditLog.user_id == current_user.id
    ).order_by(AuditLog.created_at.desc()).limit(limit).all()

    result = []
    for log in logs:
        result.append(AuditLogResponse(
            id=log.id,
            event_type=log.event_type,
            event_description=log.event_description,
            ip_address=log.ip_address,
            success=log.success,
            created_at=log.created_at,
            username=current_user.username
        ))

    return result


@router.get("/failed-attempts")
async def get_failed_attempts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get failed access attempts (admin only)."""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )

    attempts = db.query(FailedAccessAttempt).order_by(
        FailedAccessAttempt.last_attempt.desc()
    ).all()

    return [
        {
            "id": a.id,
            "ip_address": a.ip_address,
            "username_attempted": a.username_attempted,
            "resource": a.resource,
            "attempt_count": a.attempt_count,
            "last_attempt": a.last_attempt,
            "blocked_until": a.blocked_until
        }
        for a in attempts
    ]


@router.get("/stats")
async def get_audit_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get audit statistics."""
    if current_user.is_admin:
        total_events = db.query(AuditLog).count()
        failed_logins = db.query(AuditLog).filter(
            AuditLog.event_type == "LOGIN_ATTEMPT",
            AuditLog.success == False
        ).count()
        successful_logins = db.query(AuditLog).filter(
            AuditLog.event_type == "LOGIN_ATTEMPT",
            AuditLog.success == True
        ).count()
        total_uploads = db.query(AuditLog).filter(
            AuditLog.event_type == "FILE_UPLOAD"
        ).count()
        total_downloads = db.query(AuditLog).filter(
            AuditLog.event_type == "FILE_DOWNLOAD"
        ).count()
    else:
        total_events = db.query(AuditLog).filter(AuditLog.user_id == current_user.id).count()
        failed_logins = db.query(AuditLog).filter(
            AuditLog.user_id == current_user.id,
            AuditLog.event_type == "LOGIN_ATTEMPT",
            AuditLog.success == False
        ).count()
        successful_logins = db.query(AuditLog).filter(
            AuditLog.user_id == current_user.id,
            AuditLog.event_type == "LOGIN_ATTEMPT",
            AuditLog.success == True
        ).count()
        total_uploads = db.query(AuditLog).filter(
            AuditLog.user_id == current_user.id,
            AuditLog.event_type == "FILE_UPLOAD"
        ).count()
        total_downloads = db.query(AuditLog).filter(
            AuditLog.user_id == current_user.id,
            AuditLog.event_type == "FILE_DOWNLOAD"
        ).count()

    return {
        "total_events": total_events,
        "failed_logins": failed_logins,
        "successful_logins": successful_logins,
        "total_uploads": total_uploads,
        "total_downloads": total_downloads,
        "security_score": "Good" if failed_logins < 3 else "Review Required"
    }
