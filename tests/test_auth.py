"""Authentication endpoint tests."""
import pytest
from fastapi import status


class TestUserRegistration:
    """Test user registration functionality."""

    def test_register_valid_user(self, test_client, test_user_data):
        """Test successful user registration."""
        response = test_client.post(
            "/auth/register",
            json={
                "username": test_user_data["username"],
                "password": test_user_data["password"],
                "email": test_user_data["email"]
            }
        )
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["username"] == test_user_data["username"]
        assert data["email"] == test_user_data["email"]

    def test_register_duplicate_username(self, test_client, test_user_data):
        """Test registration fails with duplicate username."""
        # Register first user
        test_client.post(
            "/auth/register",
            json={
                "username": test_user_data["username"],
                "password": test_user_data["password"],
                "email": test_user_data["email"]
            }
        )

        # Try to register with same username
        response = test_client.post(
            "/auth/register",
            json={
                "username": test_user_data["username"],
                "password": "DifferentPassword123!",
                "email": "different@example.com"
            }
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_register_weak_password(self, test_client):
        """Test registration fails with weak password."""
        response = test_client.post(
            "/auth/register",
            json={
                "username": "testuser",
                "password": "weak",  # Too short
                "email": "test@example.com"
            }
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST


class TestUserLogin:
    """Test user login functionality."""

    def test_login_valid_credentials(self, test_client, test_user_data):
        """Test successful login with valid credentials."""
        # Register user first
        test_client.post(
            "/auth/register",
            json={
                "username": test_user_data["username"],
                "password": test_user_data["password"],
                "email": test_user_data["email"]
            }
        )

        # Login
        response = test_client.post(
            "/auth/login",
            json={
                "username": test_user_data["username"],
                "password": test_user_data["password"]
            }
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_login_invalid_password(self, test_client, test_user_data):
        """Test login fails with incorrect password."""
        # Register user
        test_client.post(
            "/auth/register",
            json={
                "username": test_user_data["username"],
                "password": test_user_data["password"],
                "email": test_user_data["email"]
            }
        )

        # Try login with wrong password
        response = test_client.post(
            "/auth/login",
            json={
                "username": test_user_data["username"],
                "password": "WrongPassword123!"
            }
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_login_nonexistent_user(self, test_client):
        """Test login fails for non-existent user."""
        response = test_client.post(
            "/auth/login",
            json={
                "username": "nonexistent",
                "password": "Password123!"
            }
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestRateLimiting:
    """Test rate limiting and IP blocking functionality."""

    def test_rate_limiting_blocks_after_failed_attempts(self, test_client):
        """Test IP gets blocked after 5 failed login attempts."""
        username = "testuser"
        password = "CorrectPassword123!"

        # Make 5 failed attempts
        for _ in range(5):
            response = test_client.post(
                "/auth/login",
                json={
                    "username": username,
                    "password": "WrongPassword!"
                }
            )
            assert response.status_code == status.HTTP_401_UNAUTHORIZED

        # 6th attempt should be blocked
        response = test_client.post(
            "/auth/login",
            json={
                "username": username,
                "password": password
            }
        )
        assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS


class TestCurrentUser:
    """Test current user endpoint."""

    def test_get_current_user_authenticated(self, authenticated_client, test_user_data):
        """Test retrieving current user info when authenticated."""
        response = authenticated_client.get("/auth/me")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["username"] == test_user_data["username"]
        assert data["email"] == test_user_data["email"]

    def test_get_current_user_unauthenticated(self, test_client):
        """Test retrieving current user fails without authentication."""
        response = test_client.get("/auth/me")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
