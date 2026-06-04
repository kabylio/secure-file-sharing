"""Cryptographic operations tests."""
import pytest
from app.core.security import (
    hash_password,
    verify_password,
    generate_rsa_key_pair,
    encrypt_aes_key,
    decrypt_aes_key,
    generate_aes_key,
    encrypt_file,
    decrypt_file,
    generate_file_hash,
    sign_file,
    verify_signature
)


class TestPasswordHashing:
    """Test bcrypt password hashing."""

    def test_hash_password(self):
        """Test password hashing produces hash different from plaintext."""
        password = "TestPassword123!"
        hashed = hash_password(password)

        assert hashed != password
        assert len(hashed) > 20  # bcrypt hashes are 60+ chars

    def test_verify_correct_password(self):
        """Test password verification succeeds with correct password."""
        password = "TestPassword123!"
        hashed = hash_password(password)

        assert verify_password(password, hashed)

    def test_verify_incorrect_password(self):
        """Test password verification fails with incorrect password."""
        password = "TestPassword123!"
        hashed = hash_password(password)

        assert not verify_password("WrongPassword123!", hashed)

    def test_hash_randomness(self):
        """Test same password produces different hashes (salt randomization)."""
        password = "TestPassword123!"
        hash1 = hash_password(password)
        hash2 = hash_password(password)

        assert hash1 != hash2


class TestRSAEncryption:
    """Test RSA key pair generation and encryption."""

    def test_generate_rsa_key_pair(self):
        """Test RSA key pair generation."""
        public_key, private_key = generate_rsa_key_pair()

        assert public_key is not None
        assert private_key is not None
        assert len(public_key) > 100
        assert len(private_key) > 500

    def test_rsa_key_pair_uniqueness(self):
        """Test multiple key pairs are unique."""
        public_key1, private_key1 = generate_rsa_key_pair()
        public_key2, private_key2 = generate_rsa_key_pair()

        assert public_key1 != public_key2
        assert private_key1 != private_key2


class TestAESEncryption:
    """Test AES encryption and decryption."""

    def test_generate_aes_key(self):
        """Test AES key generation."""
        key = generate_aes_key()

        assert key is not None
        assert len(key) == 32  # 256 bits = 32 bytes

    def test_encrypt_decrypt_aes_key(self):
        """Test AES key encryption and decryption with RSA."""
        # Generate RSA keys
        public_key, private_key = generate_rsa_key_pair()

        # Generate AES key
        aes_key = generate_aes_key()

        # Encrypt AES key with public key
        encrypted_aes_key = encrypt_aes_key(aes_key, public_key)

        # Decrypt AES key with private key
        decrypted_aes_key = decrypt_aes_key(encrypted_aes_key, private_key)

        assert decrypted_aes_key == aes_key

    def test_encrypted_aes_key_differs_from_original(self):
        """Test encrypted AES key is different from plaintext."""
        public_key, _ = generate_rsa_key_pair()
        aes_key = generate_aes_key()
        encrypted_aes_key = encrypt_aes_key(aes_key, public_key)

        assert encrypted_aes_key != aes_key


class TestFileEncryption:
    """Test file encryption and decryption."""

    def test_encrypt_decrypt_file(self, sample_file):
        """Test file encryption and decryption produces original content."""
        # Generate AES key
        aes_key = generate_aes_key()

        # Encrypt file
        encrypted_content, iv = encrypt_file(sample_file, aes_key)

        # Decrypt file
        decrypted_content = decrypt_file(encrypted_content, aes_key, iv)

        assert decrypted_content == sample_file

    def test_encryption_randomness(self, sample_file):
        """Test same file encrypts differently each time (IV randomization)."""
        aes_key = generate_aes_key()

        # Encrypt same file twice
        encrypted1, iv1 = encrypt_file(sample_file, aes_key)
        encrypted2, iv2 = encrypt_file(sample_file, aes_key)

        # Different IVs and encrypted content
        assert encrypted1 != encrypted2
        assert iv1 != iv2

    def test_wrong_key_fails_decryption(self, sample_file):
        """Test decryption fails with wrong key."""
        aes_key1 = generate_aes_key()
        aes_key2 = generate_aes_key()

        encrypted_content, iv = encrypt_file(sample_file, aes_key1)

        # Should raise exception with wrong key
        with pytest.raises(Exception):
            decrypt_file(encrypted_content, aes_key2, iv)


class TestFileHashing:
    """Test SHA-256 file hashing."""

    def test_generate_file_hash(self, sample_file):
        """Test SHA-256 hash generation."""
        hash_value = generate_file_hash(sample_file)

        assert hash_value is not None
        assert len(hash_value) == 64  # SHA-256 hex = 64 chars

    def test_hash_deterministic(self, sample_file):
        """Test same file produces same hash."""
        hash1 = generate_file_hash(sample_file)
        hash2 = generate_file_hash(sample_file)

        assert hash1 == hash2

    def test_different_content_different_hash(self, sample_file):
        """Test different content produces different hash."""
        hash1 = generate_file_hash(sample_file)
        hash2 = generate_file_hash(sample_file + b"extra")

        assert hash1 != hash2


class TestDigitalSignatures:
    """Test RSA digital signatures."""

    def test_sign_and_verify_file(self, sample_file):
        """Test file signing and verification."""
        # Generate RSA keys
        public_key, private_key = generate_rsa_key_pair()

        # Sign file
        signature = sign_file(sample_file, private_key)

        # Verify signature
        assert verify_signature(sample_file, signature, public_key)

    def test_tampered_file_fails_verification(self, sample_file):
        """Test verification fails if file is tampered."""
        # Generate RSA keys
        public_key, private_key = generate_rsa_key_pair()

        # Sign file
        signature = sign_file(sample_file, private_key)

        # Tamper with file
        tampered_file = sample_file + b"tampered"

        # Verification should fail
        assert not verify_signature(tampered_file, signature, public_key)

    def test_signature_randomness(self, sample_file):
        """Test same file produces different signatures (randomized PSS)."""
        _, private_key = generate_rsa_key_pair()

        # Sign same file twice
        signature1 = sign_file(sample_file, private_key)
        signature2 = sign_file(sample_file, private_key)

        # Signatures should be different (PSS is randomized)
        assert signature1 != signature2
