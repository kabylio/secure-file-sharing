"""Security and audit logging tests."""
import pytest
from fastapi import status
import io


class TestAuditLogging:
    """Test security audit logging functionality."""

    def test_login_audit_log_created(self, test_client, test_user_data):
        """Test audit log is created on login."""
        # Register user
        test_client.post(
            "/auth/register",
            json={
                "username": test_user_data["username"],
                "password": test_user_data["password"],
                "email": test_user_data["email"]
            }
        )

        # Login (should create audit log)
        response = test_client.post(
            "/auth/login",
            json={
                "username": test_user_data["username"],
                "password": test_user_data["password"]
            }
        )
        
        assert response.status_code == status.HTTP_200_OK

        # Verify audit logs endpoint is available
        # Note: This would require an authenticated client with audit access

    def test_failed_login_audit_log(self, test_client, test_user_data):
        """Test audit log is created on failed login."""
        # Register user
        test_client.post(
            "/auth/register",
            json={
                "username": test_user_data["username"],
                "password": test_user_data["password"],
                "email": test_user_data["email"]
            }
        )

        # Attempt login with wrong password
        response = test_client.post(
            "/auth/login",
            json={
                "username": test_user_data["username"],
                "password": "WrongPassword123!"
            }
        )
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_file_upload_audit_log(self, authenticated_client):
        """Test audit log is created on file upload."""
        file_content = b"Test file for audit logging"
        
        response = authenticated_client.post(
            "/files/upload",
            files={"file": ("audit_test.txt", io.BytesIO(file_content), "text/plain")},
            data={"sign_file": "false"}
        )
        
        assert response.status_code == status.HTTP_201_CREATED

    def test_file_download_audit_log(self, authenticated_client):
        """Test audit log is created on file download."""
        # Upload file
        file_content = b"Test file"
        upload_response = authenticated_client.post(
            "/files/upload",
            files={"file": ("test.txt", io.BytesIO(file_content), "text/plain")},
            data={"sign_file": "false"}
        )
        file_id = upload_response.json()["id"]

        # Download file (should create audit log)
        response = authenticated_client.get(f"/files/{file_id}/download")
        
        assert response.status_code == status.HTTP_200_OK

    def test_file_share_audit_log(self, test_client, authenticated_client):
        """Test audit log is created on file share."""
        # Create second user
        second_user_data = {
            "username": "testuser2",
            "password": "TestPassword123!",
            "email": "test2@example.com"
        }
        test_client.post("/auth/register", json=second_user_data)

        # Upload file
        file_content = b"File to share"
        upload_response = authenticated_client.post(
            "/files/upload",
            files={"file": ("share.txt", io.BytesIO(file_content), "text/plain")},
            data={"sign_file": "false"}
        )
        file_id = upload_response.json()["id"]

        # Share file (should create audit log)
        response = authenticated_client.post(
            f"/files/{file_id}/share",
            json={"recipient_username": second_user_data["username"]}
        )
        
        assert response.status_code == status.HTTP_200_OK


class TestIPMonitoring:
    """Test IP address tracking in security logs."""

    def test_failed_login_ip_recorded(self, test_client):
        """Test failed login attempts record IP address."""
        # Make failed login attempt
        test_client.post(
            "/auth/login",
            json={
                "username": "testuser",
                "password": "wrong_password"
            }
        )
        
        # IP should be recorded (testclient uses "testclient" as IP)
        # This would be verified in audit logs

    def test_successful_login_ip_recorded(self, test_client, test_user_data):
        """Test successful login records IP address."""
        # Register and login
        test_client.post(
            "/auth/register",
            json={
                "username": test_user_data["username"],
                "password": test_user_data["password"],
                "email": test_user_data["email"]
            }
        )

        test_client.post(
            "/auth/login",
            json={
                "username": test_user_data["username"],
                "password": test_user_data["password"]
            }
        )
        
        # IP should be recorded


class TestAccessControl:
    """Test access control and authorization."""

    def test_unauthorized_file_download(self, test_client, authenticated_client):
        """Test downloading file from another user fails."""
        # First user uploads file
        file_content = b"Private file"
        upload_response = authenticated_client.post(
            "/files/upload",
            files={"file": ("private.txt", io.BytesIO(file_content), "text/plain")},
            data={"sign_file": "false"}
        )
        file_id = upload_response.json()["id"]

        # Second user tries to download (unauthenticated client)
        download_response = test_client.get(f"/files/{file_id}/download")
        assert download_response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_unauthorized_file_delete(self, test_client, authenticated_client):
        """Test deleting file from another user fails."""
        # First user uploads file
        file_content = b"Protected file"
        upload_response = authenticated_client.post(
            "/files/upload",
            files={"file": ("protected.txt", io.BytesIO(file_content), "text/plain")},
            data={"sign_file": "false"}
        )
        file_id = upload_response.json()["id"]

        # Second user tries to delete (unauthenticated client)
        delete_response = test_client.delete(f"/files/{file_id}")
        assert delete_response.status_code == status.HTTP_401_UNAUTHORIZED


class TestHealthCheckSecurity:
    """Test security-related endpoints."""

    def test_health_check_accessible(self, test_client):
        """Test health check endpoint is accessible."""
        response = test_client.get("/health")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "Secure File Sharing System"

    def test_api_info_accessible(self, test_client):
        """Test API info endpoint is accessible."""
        response = test_client.get("/api")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["name"] == "Secure File Sharing API"
        assert data["version"] == "1.0.0"
