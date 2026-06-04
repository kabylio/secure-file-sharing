"""File operations tests."""
import pytest
from fastapi import status
import io


class TestFileUpload:
    """Test file upload functionality."""

    def test_upload_file_success(self, authenticated_client):
        """Test successful file upload."""
        file_content = b"Test file content for uploading"
        
        response = authenticated_client.post(
            "/files/upload",
            files={"file": ("test.txt", io.BytesIO(file_content), "text/plain")},
            data={"sign_file": "false"}
        )
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["original_filename"] == "test.txt"
        assert data["file_size"] == len(file_content)
        assert "file_hash" in data
        assert "created_at" in data

    def test_upload_file_unauthenticated(self, test_client):
        """Test file upload fails without authentication."""
        file_content = b"Test file content"
        
        response = test_client.post(
            "/files/upload",
            files={"file": ("test.txt", io.BytesIO(file_content), "text/plain")},
            data={"sign_file": "false"}
        )
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_upload_with_digital_signature(self, authenticated_client):
        """Test file upload with digital signature."""
        file_content = b"Test file to be signed"
        
        response = authenticated_client.post(
            "/files/upload",
            files={"file": ("signed.txt", io.BytesIO(file_content), "text/plain")},
            data={"sign_file": "true"}
        )
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert "file_signature" in data
        assert data["file_signature"] is not None


class TestFileDownload:
    """Test file download functionality."""

    def test_download_own_file(self, authenticated_client):
        """Test downloading own uploaded file."""
        # Upload file first
        file_content = b"Download test content"
        upload_response = authenticated_client.post(
            "/files/upload",
            files={"file": ("test.txt", io.BytesIO(file_content), "text/plain")},
            data={"sign_file": "false"}
        )
        file_id = upload_response.json()["id"]

        # Download file
        download_response = authenticated_client.get(f"/files/{file_id}/download")
        
        assert download_response.status_code == status.HTTP_200_OK
        assert download_response.content == file_content

    def test_download_nonexistent_file(self, authenticated_client):
        """Test downloading non-existent file."""
        response = authenticated_client.get("/files/nonexistent-id/download")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_download_unauthenticated(self, test_client):
        """Test file download fails without authentication."""
        response = test_client.get("/files/some-id/download")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestFileSharing:
    """Test file sharing functionality."""

    def test_share_file_with_user(self, test_client, authenticated_client, test_user_data):
        """Test sharing file with another user."""
        # Create second user
        second_user_data = {
            "username": "testuser2",
            "password": "TestPassword123!",
            "email": "test2@example.com"
        }
        test_client.post(
            "/auth/register",
            json=second_user_data
        )

        # Upload file with first user
        file_content = b"File to share"
        upload_response = authenticated_client.post(
            "/files/upload",
            files={"file": ("share.txt", io.BytesIO(file_content), "text/plain")},
            data={"sign_file": "false"}
        )
        file_id = upload_response.json()["id"]

        # Share file
        share_response = authenticated_client.post(
            f"/files/{file_id}/share",
            json={"recipient_username": second_user_data["username"]}
        )
        
        assert share_response.status_code == status.HTTP_200_OK

    def test_share_nonexistent_file(self, authenticated_client):
        """Test sharing non-existent file."""
        response = authenticated_client.post(
            "/files/nonexistent-id/share",
            json={"recipient_username": "someuser"}
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_share_with_invalid_recipient(self, authenticated_client):
        """Test sharing with non-existent user."""
        # Upload file
        file_content = b"Test file"
        upload_response = authenticated_client.post(
            "/files/upload",
            files={"file": ("test.txt", io.BytesIO(file_content), "text/plain")},
            data={"sign_file": "false"}
        )
        file_id = upload_response.json()["id"]

        # Try to share with non-existent user
        share_response = authenticated_client.post(
            f"/files/{file_id}/share",
            json={"recipient_username": "nonexistent"}
        )
        assert share_response.status_code == status.HTTP_404_NOT_FOUND


class TestListFiles:
    """Test file listing functionality."""

    def test_list_my_files(self, authenticated_client):
        """Test listing user's own files."""
        # Upload some files
        for i in range(3):
            file_content = f"File {i}".encode()
            authenticated_client.post(
                "/files/upload",
                files={"file": (f"file{i}.txt", io.BytesIO(file_content), "text/plain")},
                data={"sign_file": "false"}
            )

        # List files
        response = authenticated_client.get("/files/my")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["items"]) == 3
        assert data["total"] == 3

    def test_list_my_files_pagination(self, authenticated_client):
        """Test file listing with pagination."""
        # Upload multiple files
        for i in range(10):
            file_content = f"File {i}".encode()
            authenticated_client.post(
                "/files/upload",
                files={"file": (f"file{i}.txt", io.BytesIO(file_content), "text/plain")},
                data={"sign_file": "false"}
            )

        # Get first page (default limit=50)
        response = authenticated_client.get("/files/my?skip=0&limit=5")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["items"]) == 5
        assert data["total"] == 10
        assert data["has_more"] is True

    def test_list_shared_files_empty(self, authenticated_client):
        """Test listing shared files when none are shared."""
        response = authenticated_client.get("/files/shared")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["items"]) == 0
        assert data["total"] == 0


class TestFileDelete:
    """Test file deletion functionality."""

    def test_delete_own_file(self, authenticated_client):
        """Test deleting own file."""
        # Upload file
        file_content = b"File to delete"
        upload_response = authenticated_client.post(
            "/files/upload",
            files={"file": ("delete.txt", io.BytesIO(file_content), "text/plain")},
            data={"sign_file": "false"}
        )
        file_id = upload_response.json()["id"]

        # Delete file
        delete_response = authenticated_client.delete(f"/files/{file_id}")
        
        assert delete_response.status_code == status.HTTP_200_OK

        # Verify file is deleted
        list_response = authenticated_client.get("/files/my")
        data = list_response.json()
        assert data["total"] == 0

    def test_delete_nonexistent_file(self, authenticated_client):
        """Test deleting non-existent file."""
        response = authenticated_client.delete("/files/nonexistent-id")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_without_permission(self, test_client, authenticated_client):
        """Test deleting file uploaded by another user fails."""
        # Create second user
        second_user_data = {
            "username": "testuser2",
            "password": "TestPassword123!",
            "email": "test2@example.com"
        }
        test_client.post("/auth/register", json=second_user_data)

        # First user uploads file
        file_content = b"Another user's file"
        upload_response = authenticated_client.post(
            "/files/upload",
            files={"file": ("protected.txt", io.BytesIO(file_content), "text/plain")},
            data={"sign_file": "false"}
        )
        file_id = upload_response.json()["id"]

        # Second user tries to delete
        second_user_login = test_client.post(
            "/auth/login",
            json={
                "username": second_user_data["username"],
                "password": second_user_data["password"]
            }
        )
        second_token = second_user_login.json()["access_token"]
        test_client.headers.update({"Authorization": f"Bearer {second_token}"})

        delete_response = test_client.delete(f"/files/{file_id}")
        assert delete_response.status_code == status.HTTP_403_FORBIDDEN
