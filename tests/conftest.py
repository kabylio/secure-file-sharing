"""Pytest configuration and shared fixtures for test suite."""
import pytest
import os
import tempfile
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from fastapi.testclient import TestClient

from app.main import app
from app.core.database import Base, get_db
from app.core.config import Settings, get_settings
from app.core.security import (
    hash_password,
    generate_rsa_key_pair,
    encrypt_aes_key,
    decrypt_aes_key
)
from app.models.models import User


@pytest.fixture(scope="session")
def test_settings():
    """Create test environment settings."""
    temp_dir = tempfile.mkdtemp()
    settings = Settings(
        DATABASE_URL="sqlite:///:memory:",
        UPLOAD_DIR=temp_dir,
        KEYS_DIR=temp_dir,
        JWT_ALGORITHM="HS256",
        JWT_SECRET_KEY="test-secret-key-do-not-use-in-production",
        JWT_EXPIRATION_HOURS=24
    )
    return settings


@pytest.fixture(scope="session")
def test_db_engine(test_settings):
    """Create test database engine."""
    engine = create_engine(
        test_settings.DATABASE_URL,
        connect_args={"check_same_thread": False}
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def test_db_session(test_db_engine):
    """Create a test database session."""
    connection = test_db_engine.connect()
    transaction = connection.begin()
    session = sessionmaker(autocommit=False, autoflush=False, bind=connection)()

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def test_client(test_db_session, test_settings):
    """Create FastAPI test client."""
    def override_get_db():
        yield test_db_session

    def override_get_settings():
        return test_settings

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_settings] = override_get_settings

    client = TestClient(app)
    yield client

    app.dependency_overrides.clear()


@pytest.fixture
def test_user_data():
    """Provide sample user credentials."""
    return {
        "username": "testuser",
        "password": "TestPassword123!",
        "email": "test@example.com"
    }


@pytest.fixture
def test_user_with_keys(test_db_session, test_user_data):
    """Create a test user with RSA key pair."""
    public_key, private_key = generate_rsa_key_pair()
    password_hash = hash_password(test_user_data["password"])

    user = User(
        username=test_user_data["username"],
        email=test_user_data["email"],
        password_hash=password_hash,
        public_key=public_key,
        private_key=private_key
    )
    test_db_session.add(user)
    test_db_session.commit()
    test_db_session.refresh(user)

    return user


@pytest.fixture
def test_token(test_client, test_user_data):
    """Generate JWT token for test user."""
    # Register user
    test_client.post(
        "/auth/register",
        json={
            "username": test_user_data["username"],
            "password": test_user_data["password"],
            "email": test_user_data["email"]
        }
    )

    # Login to get token
    response = test_client.post(
        "/auth/login",
        json={
            "username": test_user_data["username"],
            "password": test_user_data["password"]
        }
    )
    return response.json()["access_token"]


@pytest.fixture
def authenticated_client(test_client, test_token):
    """Test client with authorization header."""
    test_client.headers.update({"Authorization": f"Bearer {test_token}"})
    return test_client


@pytest.fixture
def sample_file():
    """Provide sample file content."""
    return b"This is a sample file for testing encryption and decryption."
