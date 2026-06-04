"""Audit logging service for security event tracking."""
from sqlalchemy.orm import Session
from app.models.models import AuditLog, FailedAccessAttempt
from datetime import datetime, timedelta, timezone


def log_security_event(
    db: Session,
    event_type: str,
    event_description: str,
    user_id: int = None,
    ip_address: str = None,
    user_agent: str = None,
    success: bool = True,
    details: str = None
) -> AuditLog:
    """Log a security event to the audit log."""
    audit_log = AuditLog(
        user_id=user_id,
        event_type=event_type,
        event_description=event_description,
        ip_address=ip_address,
        user_agent=user_agent,
        success=success,
        details=details
    )
    db.add(audit_log)
    db.commit()
    db.refresh(audit_log)
    return audit_log


def log_login_attempt(
    db: Session,
    username: str,
    ip_address: str,
    success: bool,
    user_id: int = None,
    user_agent: str = None
) -> AuditLog:
    """Log a login attempt."""
    status = "successful" if success else "failed"
    return log_security_event(
        db=db,
        event_type="LOGIN_ATTEMPT",
        event_description=f"Login attempt for user '{username}' was {status}",
        user_id=user_id,
        ip_address=ip_address,
        user_agent=user_agent,
        success=success,
        details=f"username={username}, success={success}"
    )


def log_file_upload(
    db: Session,
    user_id: int,
    filename: str,
    file_hash: str,
    ip_address: str = None,
    success: bool = True
) -> AuditLog:
    """Log a file upload event."""
    return log_security_event(
        db=db,
        event_type="FILE_UPLOAD",
        event_description=f"File '{filename}' uploaded (hash: {file_hash[:16]}...)",
        user_id=user_id,
        ip_address=ip_address,
        success=success,
        details=f"filename={filename}, hash={file_hash}"
    )


def log_file_download(
    db: Session,
    user_id: int,
    file_id: int,
    filename: str,
    ip_address: str = None,
    success: bool = True
) -> AuditLog:
    """Log a file download event."""
    return log_security_event(
        db=db,
        event_type="FILE_DOWNLOAD",
        event_description=f"File '{filename}' (ID: {file_id}) downloaded",
        user_id=user_id,
        ip_address=ip_address,
        success=success,
        details=f"file_id={file_id}, filename={filename}"
    )


def log_file_share(
    db: Session,
    user_id: int,
    file_id: int,
    recipient_username: str,
    ip_address: str = None,
    success: bool = True
) -> AuditLog:
    """Log a file sharing event."""
    return log_security_event(
        db=db,
        event_type="FILE_SHARE",
        event_description=f"File (ID: {file_id}) shared with '{recipient_username}'",
        user_id=user_id,
        ip_address=ip_address,
        success=success,
        details=f"file_id={file_id}, recipient={recipient_username}"
    )


def log_failed_access(
    db: Session,
    ip_address: str,
    resource: str,
    username_attempted: str = None,
    reason: str = None
) -> AuditLog:
    """Log a failed access attempt."""
    return log_security_event(
        db=db,
        event_type="FAILED_ACCESS",
        event_description=f"Failed access to '{resource}': {reason or 'Unauthorized'}",
        ip_address=ip_address,
        success=False,
        details=f"resource={resource}, username={username_attempted}, reason={reason}"
    )


def record_failed_attempt(
    db: Session,
    ip_address: str,
    username: str = None,
    resource: str = None
) -> FailedAccessAttempt:
    """Record a failed access attempt for rate limiting."""
    existing = db.query(FailedAccessAttempt).filter(
        FailedAccessAttempt.ip_address == ip_address
    ).first()

    if existing:
        existing.attempt_count += 1
        existing.last_attempt = datetime.now(timezone.utc)
        existing.username_attempted = username or existing.username_attempted
        existing.resource = resource or existing.resource

        # Block after 5 failed attempts for 15 minutes
        if existing.attempt_count >= 5:
            existing.blocked_until = datetime.now(timezone.utc) + timedelta(minutes=15)
    else:
        existing = FailedAccessAttempt(
            ip_address=ip_address,
            username_attempted=username,
            resource=resource,
            attempt_count=1
        )
        db.add(existing)

    db.commit()
    db.refresh(existing)
    return existing


def is_ip_blocked(db: Session, ip_address: str) -> bool:
    """Check if an IP address is currently blocked."""
    attempt = db.query(FailedAccessAttempt).filter(
        FailedAccessAttempt.ip_address == ip_address
    ).first()

    if not attempt or not attempt.blocked_until:
        return False

    return datetime.now(timezone.utc) < attempt.blocked_until


def clear_failed_attempts(db: Session, ip_address: str):
    """Clear failed attempts after successful login."""
    db.query(FailedAccessAttempt).filter(
        FailedAccessAttempt.ip_address == ip_address
    ).delete()
    db.commit()


def get_recent_audit_logs(db: Session, limit: int = 50) -> list:
    """Get recent audit logs."""
    return db.query(AuditLog).order_by(AuditLog.created_at.desc()).limit(limit).all()
