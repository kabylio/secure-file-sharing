# Secure File Sharing System

A production-grade secure file sharing application built with **Python + FastAPI**, demonstrating real-world cybersecurity engineering skills.

## What This Project Demonstrates

| Skill | Implementation |
|-------|---------------|
| **Cryptography** | AES-256-GCM symmetric encryption, RSA-2048 hybrid encryption, Digital Signatures |
| **Authentication** | JWT tokens, bcrypt password hashing, OAuth2 flow |
| **Authorization** | Role-based access control, file ownership verification |
| **Secure Programming** | Input validation, SQL injection prevention, XSS protection, CSRF mitigation |
| **File Handling** | Secure upload/download with integrity verification |
| **Networking** | RESTful API with security headers, CORS configuration |
| **Audit Logging** | Comprehensive security event tracking with IP monitoring |
| **Rate Limiting** | IP-based blocking after failed attempts |

## Architecture

```
Secure File Sharing System
├── app/
│   ├── core/           # Configuration, security utilities, database
│   │   ├── config.py   # App settings & environment variables
│   │   ├── security.py # Cryptographic operations (AES, RSA, JWT, bcrypt)
│   │   └── database.py # SQLAlchemy engine & session management
│   ├── models/         # SQLAlchemy database models
│   │   └── models.py   # User, File, FileShare, AuditLog, FailedAccessAttempt
│   ├── schemas/        # Pydantic request/response validation
│   │   └── schemas.py  # Data transfer objects
│   ├── services/       # Business logic layer
│   │   ├── audit_service.py   # Security event logging
│   │   └── file_service.py    # Encryption/decryption operations
│   ├── routers/        # API endpoints
│   │   ├── auth.py     # Registration, login, JWT management
│   │   ├── files.py    # Upload, download, share, verify
│   │   └── audit.py    # Security logs & monitoring
│   └── main.py         # FastAPI application entry point
├── static/             # Frontend assets
│   ├── css/style.css   # Dark theme UI
│   └── js/app.js       # Single-page application logic
├── templates/
│   └── index.html      # Main application template
├── uploads/            # Encrypted file storage
├── keys/               # Key storage directory
└── requirements.txt    # Python dependencies
```

## Encryption Flow

### Upload (Encrypt)
1. Compute SHA-256 hash of original file (integrity)
2. Generate random 256-bit AES key
3. Encrypt file with AES-256-GCM
4. Encrypt AES key with owner's RSA-2048 public key (hybrid encryption)
5. Store encrypted file + metadata

### Download (Decrypt)
1. Verify user has access (owner or shared recipient)
2. Decrypt AES key with user's RSA-2048 private key
3. Decrypt file with AES-256-GCM
4. Verify SHA-256 hash matches (detect tampering)
5. Stream decrypted file to user

### Share (Re-encrypt)
1. Owner decrypts AES key with their private key
2. Re-encrypts AES key with recipient's public key
3. Recipient can now decrypt using their own private key

## Security Features

- **AES-256-GCM**: Authenticated encryption with associated data
- **RSA-2048**: Asymmetric encryption for key exchange
- **Hybrid Encryption**: Combines speed of symmetric + security of asymmetric
- **Digital Signatures**: RSA-PSS with SHA-256 for non-repudiation
- **bcrypt**: Adaptive password hashing (work factor 12+)
- **JWT**: Stateless authentication with expiration
- **Security Headers**: HSTS, CSP, X-Frame-Options, X-Content-Type-Options
- **Audit Logging**: All security events tracked with IP and timestamp
- **Rate Limiting**: IP blocking after 5 failed attempts (15 min)
- **Input Validation**: Pydantic schemas prevent injection attacks
- **SQL Injection Prevention**: SQLAlchemy ORM with parameterized queries

## Quick Start

### 1. Install Dependencies
```bash
cd secure_file_sharing
pip install -r requirements.txt
```

### 2. Run the Application
```bash
python -m app.main
```

Or with uvicorn directly:
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 3. Access the Application
- Web UI: http://localhost:8000
- API Docs: http://localhost:8000/api/docs
- Health Check: http://localhost:8000/health

### 4. Create an Account
1. Open the web UI
2. Click "Register" tab
3. Enter username, email, and password (min 8 chars)
4. RSA-2048 key pair is auto-generated
5. Login and start sharing files securely!

## API Endpoints

### Authentication
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/auth/register` | Create account with auto-generated RSA keys |
| POST | `/auth/login` | Authenticate and receive JWT token |
| GET | `/auth/me` | Get current user profile |
| POST | `/auth/logout` | Invalidate session (client-side) |

### Files
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/files/upload` | Upload and encrypt file |
| GET | `/files/my-files` | List owned files |
| GET | `/files/shared-with-me` | List shared files |
| GET | `/files/{id}/download` | Download and decrypt file |
| GET | `/files/{id}` | Get file details |
| POST | `/files/{id}/share` | Share file with user |
| GET | `/files/{id}/verify` | Verify digital signature |
| DELETE | `/files/{id}` | Delete file |

### Audit
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/audit/logs` | View security logs |
| GET | `/audit/logs/my` | View personal logs |
| GET | `/audit/failed-attempts` | View failed access attempts (admin) |
| GET | `/audit/stats` | Get security statistics |

## Technologies Used

- **Backend**: Python 3.11+, FastAPI, SQLAlchemy, Alembic
- **Cryptography**: cryptography (pyca), python-jose, passlib
- **Database**: SQLite (development), PostgreSQL (production)
- **Frontend**: Vanilla JavaScript, CSS3, Font Awesome
- **Security**: bcrypt, JWT, AES-GCM, RSA-OAEP, RSA-PSS

## Production Considerations

1. **Database**: Switch to PostgreSQL for concurrent access
2. **HTTPS**: Configure SSL certificates
3. **Key Storage**: Encrypt private keys with user passwords (use PBKDF2)
4. **File Storage**: Use S3/MinIO with server-side encryption
5. **Rate Limiting**: Implement Redis-based distributed rate limiting
6. **Background Tasks**: Use Celery for heavy encryption operations
7. **Monitoring**: Integrate with SIEM for real-time threat detection

## Why Recruiters Like This Project

Unlike typical beginner portfolios showing password generators or port scanners, this project demonstrates:

- **Real Security Engineering**: Production-grade encryption, not toy examples
- **Full-Stack Development**: Backend API + Frontend + Database
- **Cryptographic Knowledge**: Understanding of hybrid encryption, PKI, signatures
- **Security Mindset**: Audit logging, rate limiting, input validation, secure headers
- **Professional Code Structure**: Clean architecture with separation of concerns
- **Industry Standards**: Uses the same libraries and patterns as real security products

## License

MIT License - Free for educational and commercial use.
