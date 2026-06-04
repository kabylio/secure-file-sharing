"""Secure File Sharing System - Main FastAPI Application."""
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from contextlib import asynccontextmanager
from pathlib import Path
from datetime import datetime, timezone
import os
import logging

from app.core.database import engine, Base
from app.core.config import get_settings
from app.routers import auth, files, audit

settings = get_settings()
BASE_DIR = Path(__file__).resolve().parent.parent

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup: Create database tables
    Base.metadata.create_all(bind=engine)

    # Ensure upload directory exists
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    os.makedirs(settings.KEYS_DIR, exist_ok=True)

    logger.info("Secure File Sharing System started successfully!")
    logger.info(f"Database: {settings.DATABASE_URL}")
    logger.info(f"Upload directory: {os.path.abspath(settings.UPLOAD_DIR)}")

    yield

    # Shutdown
    logger.info("Secure File Sharing System shutting down...")


# Create FastAPI app
app = FastAPI(
    title="Secure File Sharing System",
    description="""
    A production-grade secure file sharing system demonstrating:
    - AES-256-GCM symmetric encryption
    - RSA-2048 asymmetric encryption (hybrid encryption)
    - Digital signatures for authenticity & integrity
    - bcrypt password hashing
    - JWT authentication
    - Comprehensive audit logging
    - Rate limiting and IP blocking
    """,
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# Security headers middleware
@app.middleware("http")
async def security_headers(request: Request, call_next):
    """Add security headers to all responses."""
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "style-src 'self' 'unsafe-inline' https://cdnjs.cloudflare.com; "
        "font-src 'self' https://cdnjs.cloudflare.com; "
        "script-src 'self'; "
        "img-src 'self' data:"
    )
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
    return response

# Global exception handler for improved error handling
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle unexpected errors with proper logging and response."""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "Internal server error",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "path": str(request.url)
        }
    )

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8000"],  # Configure for production
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(files.router)
app.include_router(audit.router)

# Static files and templates
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


@app.get("/")
async def root(request: Request):
    """Root endpoint - serves the main application page."""
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "Secure File Sharing System",
        "version": "1.0.0",
        "features": [
            "AES-256-GCM Encryption",
            "RSA-2048 Hybrid Encryption",
            "Digital Signatures",
            "bcrypt Password Hashing",
            "JWT Authentication",
            "Audit Logging",
            "Rate Limiting"
        ]
    }


@app.get("/api")
async def api_info():
    """API information endpoint."""
    return {
        "name": "Secure File Sharing API",
        "version": "1.0.0",
        "endpoints": {
            "auth": {
                "register": "POST /auth/register",
                "login": "POST /auth/login",
                "me": "GET /auth/me",
                "logout": "POST /auth/logout"
            },
            "files": {
                "upload": "POST /files/upload",
                "my_files": "GET /files/my-files",
                "shared_with_me": "GET /files/shared-with-me",
                "download": "GET /files/{file_id}/download",
                "details": "GET /files/{file_id}",
                "share": "POST /files/{file_id}/share",
                "verify": "GET /files/{file_id}/verify",
                "delete": "DELETE /files/{file_id}"
            },
            "audit": {
                "logs": "GET /audit/logs",
                "my_logs": "GET /audit/logs/my",
                "failed_attempts": "GET /audit/failed-attempts",
                "stats": "GET /audit/stats"
            }
        }
    }


@app.get("/api/documentation")
async def api_documentation():
    """Comprehensive API documentation with endpoint details."""
    return {
        "name": "Secure File Sharing API",
        "version": "1.0.0",
        "description": "A production-grade secure file sharing system with end-to-end encryption",
        "baseUrl": "http://localhost:8000",
        "authentication": {
            "type": "Bearer Token (JWT)",
            "location": "Authorization header",
            "format": "Authorization: Bearer <token>",
            "expires": "24 hours"
        },
        "endpoints": {
            "authentication": [
                {
                    "path": "/auth/register",
                    "method": "POST",
                    "description": "Register a new user account",
                    "required_auth": False,
                    "request_body": {
                        "username": "string",
                        "email": "string",
                        "password": "string (min 8 chars)"
                    },
                    "response": {
                        "id": "integer",
                        "username": "string",
                        "email": "string",
                        "created_at": "ISO 8601 datetime"
                    },
                    "status_codes": {"201": "Created", "400": "Bad Request"}
                },
                {
                    "path": "/auth/login",
                    "method": "POST",
                    "description": "Login and receive JWT token",
                    "required_auth": False,
                    "request_body": {
                        "username": "string",
                        "password": "string"
                    },
                    "response": {
                        "access_token": "string (JWT)",
                        "token_type": "bearer",
                        "user": {"id": "integer", "username": "string"}
                    },
                    "status_codes": {"200": "OK", "401": "Unauthorized", "429": "Too Many Requests"}
                },
                {
                    "path": "/auth/me",
                    "method": "GET",
                    "description": "Get current authenticated user info",
                    "required_auth": True,
                    "response": {
                        "id": "integer",
                        "username": "string",
                        "email": "string",
                        "created_at": "ISO 8601 datetime"
                    },
                    "status_codes": {"200": "OK", "401": "Unauthorized"}
                }
            ],
            "file_operations": [
                {
                    "path": "/files/upload",
                    "method": "POST",
                    "description": "Upload and encrypt a file",
                    "required_auth": True,
                    "request": {
                        "file": "binary file content",
                        "sign_file": "boolean (optional, for digital signatures)"
                    },
                    "response": {
                        "id": "string (UUID)",
                        "original_filename": "string",
                        "file_size": "integer",
                        "file_hash": "SHA-256 hex",
                        "mime_type": "string",
                        "file_signature": "RSA-PSS signature (if signed)",
                        "created_at": "ISO 8601 datetime"
                    },
                    "status_codes": {"201": "Created", "400": "Bad Request", "401": "Unauthorized"}
                },
                {
                    "path": "/files/my",
                    "method": "GET",
                    "description": "List user's own files with pagination",
                    "required_auth": True,
                    "query_params": {
                        "skip": "integer (default: 0)",
                        "limit": "integer (default: 50)"
                    },
                    "response": {
                        "items": [{"id": "string", "original_filename": "string", "file_size": "integer"}],
                        "total": "integer",
                        "skip": "integer",
                        "limit": "integer",
                        "has_more": "boolean"
                    },
                    "status_codes": {"200": "OK", "401": "Unauthorized"}
                },
                {
                    "path": "/files/shared",
                    "method": "GET",
                    "description": "List files shared with user",
                    "required_auth": True,
                    "query_params": {
                        "skip": "integer (default: 0)",
                        "limit": "integer (default: 50)"
                    },
                    "response": {
                        "items": [{"id": "string", "original_filename": "string", "owner_username": "string"}],
                        "total": "integer",
                        "has_more": "boolean"
                    },
                    "status_codes": {"200": "OK", "401": "Unauthorized"}
                },
                {
                    "path": "/files/{file_id}/download",
                    "method": "GET",
                    "description": "Download and decrypt a file",
                    "required_auth": True,
                    "response": "binary file content",
                    "status_codes": {"200": "OK", "403": "Forbidden", "404": "Not Found"}
                },
                {
                    "path": "/files/{file_id}",
                    "method": "GET",
                    "description": "Get file metadata and details",
                    "required_auth": True,
                    "response": {
                        "id": "string",
                        "original_filename": "string",
                        "file_size": "integer",
                        "file_hash": "SHA-256 hex",
                        "owner_id": "integer",
                        "owner_username": "string",
                        "created_at": "ISO 8601 datetime",
                        "mime_type": "string"
                    },
                    "status_codes": {"200": "OK", "403": "Forbidden", "404": "Not Found"}
                },
                {
                    "path": "/files/{file_id}/share",
                    "method": "POST",
                    "description": "Share file with another user",
                    "required_auth": True,
                    "request_body": {
                        "recipient_username": "string",
                        "can_download": "boolean (optional, default: true)"
                    },
                    "status_codes": {"200": "OK", "404": "Not Found", "403": "Forbidden"}
                },
                {
                    "path": "/files/{file_id}",
                    "method": "DELETE",
                    "description": "Delete a file permanently",
                    "required_auth": True,
                    "status_codes": {"200": "OK", "404": "Not Found", "403": "Forbidden"}
                }
            ],
            "audit_logging": [
                {
                    "path": "/audit/logs",
                    "method": "GET",
                    "description": "Get security audit logs",
                    "required_auth": True,
                    "query_params": {
                        "limit": "integer (default: 100)",
                        "event_type": "string (optional): LOGIN_ATTEMPT, FILE_UPLOAD, etc"
                    },
                    "response": {
                        "items": [
                            {
                                "id": "integer",
                                "user_id": "integer",
                                "event_type": "string",
                                "ip_address": "string",
                                "success": "boolean",
                                "timestamp": "ISO 8601 datetime"
                            }
                        ]
                    },
                    "status_codes": {"200": "OK", "401": "Unauthorized"}
                }
            ]
        },
        "security_features": {
            "encryption": [
                "AES-256-GCM (symmetric) for file content",
                "RSA-2048 (asymmetric) for key exchange",
                "Hybrid encryption combining both for optimal security/performance"
            ],
            "authentication": [
                "JWT tokens with 24-hour expiration",
                "bcrypt with cost factor 12+ for password hashing",
                "Secure token storage in browser localStorage"
            ],
            "integrity": [
                "SHA-256 file hashing for tamper detection",
                "RSA-PSS digital signatures (optional per file)"
            ],
            "rate_limiting": [
                "5 failed login attempts trigger IP block",
                "IP blocks last 15 minutes",
                "Automatic blocking with detailed audit logging"
            ],
            "http_security": [
                "HSTS for HTTPS enforcement",
                "Content Security Policy (CSP)",
                "X-Frame-Options: DENY",
                "X-Content-Type-Options: nosniff"
            ]
        },
        "error_responses": {
            "400": "Bad Request - Invalid input or validation error",
            "401": "Unauthorized - Missing or invalid authentication token",
            "403": "Forbidden - User lacks permission for this resource",
            "404": "Not Found - Resource does not exist",
            "429": "Too Many Requests - Rate limit exceeded (IP blocked)",
            "500": "Internal Server Error - Server-side error occurred"
        },
        "rate_limits": {
            "login_attempts": "5 attempts per 15 minutes per IP",
            "file_upload": "No limit (subject to storage quota)",
            "api_requests": "No global limit (per-operation limits apply)"
        }
    }


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle unhandled exceptions securely."""
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An internal server error occurred"}
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        ssl_keyfile=None,  # Configure for production
        ssl_certfile=None
    )
