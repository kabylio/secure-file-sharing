"""Application configuration and settings."""
from pydantic_settings import BaseSettings
from functools import lru_cache
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # App
    APP_NAME: str = "SecureFileShare"
    DEBUG: bool = False
    SECRET_KEY: str = "your-super-secret-key-change-in-production-256bits"

    # Database
    DATABASE_URL: str = f"sqlite:///{(BASE_DIR / 'secure_file_sharing.db').as_posix()}"

    # JWT
    JWT_SECRET_KEY: str = "your-jwt-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # File Storage
    UPLOAD_DIR: str = str(BASE_DIR / "uploads")
    MAX_FILE_SIZE: int = 100 * 1024 * 1024  # 100MB

    # Encryption
    AES_KEY_SIZE: int = 32  # 256 bits
    RSA_KEY_SIZE: int = 2048

    # Key Storage
    KEYS_DIR: str = str(BASE_DIR / "keys")

    class Config:
        env_file = ".env"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
