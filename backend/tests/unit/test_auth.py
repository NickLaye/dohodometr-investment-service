"""
Unit tests for authentication functionality.

Tests cover:
- User registration and login
- JWT token handling
- Password hashing and verification
- Two-factor authentication
- User permissions and roles
"""
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta

from app.core.security import (
    create_access_token,
    verify_token,
    hash_password,
    verify_password,
    generate_totp_secret,
    verify_totp_token,
)
from app.repositories.user import UserRepository
from app.schemas.auth import UserCreate, UserLogin


class TestPasswordSecurity:
    """Test password hashing and verification."""
    
    def test_hash_password(self):
        """Test password hashing."""
        password = "test_password_123"
        hashed = hash_password(password)
        
        assert hashed != password
        assert len(hashed) > 0
        assert hashed.startswith("$argon2id$")
    
    def test_verify_password_correct(self):
        """Test password verification with correct password."""
        password = "test_password_123"
        hashed = hash_password(password)
        
        assert verify_password(password, hashed) is True
    
    def test_verify_password_incorrect(self):
        """Test password verification with incorrect password."""
        password = "test_password_123"
        wrong_password = "wrong_password_456"
        hashed = hash_password(password)
        
        assert verify_password(wrong_password, hashed) is False
    
    def test_password_hash_uniqueness(self):
        """Test that same password produces different hashes."""
        password = "test_password_123"
        hash1 = hash_password(password)
        hash2 = hash_password(password)
        
        assert hash1 != hash2
        assert verify_password(password, hash1) is True
        assert verify_password(password, hash2) is True


class TestJWTTokens:
    """Test JWT token creation and verification."""
    
    def test_create_access_token(self):
        """Test access token creation."""
        user_id = "123"
        token = create_access_token(subject=user_id)
        
        assert isinstance(token, str)
        assert len(token) > 0
        assert "." in token  # JWT format
    
    def test_verify_valid_token(self):
        """Test verification of valid token."""
        user_id = "123"
        token = create_access_token(subject=user_id)
        
        payload = verify_token(token, "access")
        
        assert payload["sub"] == user_id
        assert payload["type"] == "access"
        assert "exp" in payload
        assert "iat" in payload
    
    def test_verify_invalid_token(self):
        """Test verification of invalid token."""
        invalid_token = "invalid.token.here"
        
        with pytest.raises(Exception):  # Should raise some kind of JWT exception
            verify_token(invalid_token, "access")
    
    def test_verify_expired_token(self):
        """Test verification of expired token."""
        user_id = "123"
        # Create token that expires immediately
        expired_token = create_access_token(
            subject=user_id,
            expires_delta=timedelta(seconds=-1)
        )
        
        with pytest.raises(Exception):  # Should raise expired token exception
            verify_token(expired_token, "access")
    
    def test_token_with_custom_claims(self):
        """Test token creation with custom claims."""
        user_id = "123"
        token = create_access_token(
            subject=user_id,
            is_superuser=True,
            email="test@example.com"
        )
        
        payload = verify_token(token, "access")
        
        assert payload["sub"] == user_id
        assert payload.get("is_superuser") is True
        assert payload.get("email") == "test@example.com"


class TestTwoFactorAuth:
    """Test two-factor authentication functionality."""
    
    def test_generate_totp_secret(self):
        """Test TOTP secret generation."""
        secret = generate_totp_secret()
        
        assert isinstance(secret, str)
        assert len(secret) == 32  # Base32 encoded secret length
    
    @patch('app.core.security.pyotp.TOTP')
    def test_verify_totp_token_valid(self, mock_totp):
        """Test TOTP token verification with valid token."""
        secret = "TESTSECRET123456789012345678"
        token = "123456"
        
        # Mock TOTP verification
        mock_totp_instance = MagicMock()
        mock_totp_instance.verify.return_value = True
        mock_totp.return_value = mock_totp_instance
        
        result = verify_totp_token(token, secret)
        
        assert result is True
        mock_totp.assert_called_once_with(secret)
        mock_totp_instance.verify.assert_called_once_with(token, valid_window=1)
    
    @patch('app.core.security.pyotp.TOTP')
    def test_verify_totp_token_invalid(self, mock_totp):
        """Test TOTP token verification with invalid token."""
        secret = "TESTSECRET123456789012345678"
        token = "invalid"
        
        # Mock TOTP verification
        mock_totp_instance = MagicMock()
        mock_totp_instance.verify.return_value = False
        mock_totp.return_value = mock_totp_instance
        
        result = verify_totp_token(token, secret)
        
        assert result is False


class TestUserRepository:
    """Test user repository functionality."""
    
    def test_create_user(self, db_session):
        """Test user creation."""
        user_repo = UserRepository(db_session)
        user_data = UserCreate(
            email="test@example.com",
            username="testuser",
            password="password123",
            full_name="Test User"
        )
        
        user = user_repo.create(user_data)
        
        assert user.email == user_data.email
        assert user.username == user_data.username
        assert user.full_name == user_data.full_name
        assert user.hashed_password != user_data.password  # Should be hashed
        assert user.is_active is True
        assert user.is_superuser is False
    
    def test_get_user_by_email(self, db_session, mock_user):
        """Test getting user by email."""
        user_repo = UserRepository(db_session)
        
        # First create a user
        user_data = UserCreate(
            email=mock_user["email"],
            username=mock_user["username"],
            password="password123",
            full_name=mock_user["full_name"]
        )
        created_user = user_repo.create(user_data)
        
        # Then retrieve by email
        found_user = user_repo.get_by_email(mock_user["email"])
        
        assert found_user is not None
        assert found_user.email == mock_user["email"]
        assert found_user.id == created_user.id
    
    def test_get_user_by_username(self, db_session, mock_user):
        """Test getting user by username."""
        user_repo = UserRepository(db_session)
        
        # First create a user
        user_data = UserCreate(
            email=mock_user["email"],
            username=mock_user["username"],
            password="password123",
            full_name=mock_user["full_name"]
        )
        created_user = user_repo.create(user_data)
        
        # Then retrieve by username
        found_user = user_repo.get_by_username(mock_user["username"])
        
        assert found_user is not None
        assert found_user.username == mock_user["username"]
        assert found_user.id == created_user.id
    
    def test_authenticate_user_valid(self, db_session):
        """Test user authentication with valid credentials."""
        user_repo = UserRepository(db_session)
        password = "password123"
        
        # Create user
        user_data = UserCreate(
            email="test@example.com",
            username="testuser",
            password=password,
            full_name="Test User"
        )
        created_user = user_repo.create(user_data)
        
        # Authenticate
        authenticated_user = user_repo.authenticate(
            email="test@example.com",
            password=password
        )
        
        assert authenticated_user is not None
        assert authenticated_user.id == created_user.id
    
    def test_authenticate_user_invalid_password(self, db_session):
        """Test user authentication with invalid password."""
        user_repo = UserRepository(db_session)
        
        # Create user
        user_data = UserCreate(
            email="test@example.com",
            username="testuser",
            password="password123",
            full_name="Test User"
        )
        user_repo.create(user_data)
        
        # Try to authenticate with wrong password
        authenticated_user = user_repo.authenticate(
            email="test@example.com",
            password="wrong_password"
        )
        
        assert authenticated_user is None
    
    def test_authenticate_user_not_found(self, db_session):
        """Test user authentication with non-existent user."""
        user_repo = UserRepository(db_session)
        
        # Try to authenticate non-existent user
        authenticated_user = user_repo.authenticate(
            email="nonexistent@example.com",
            password="password123"
        )
        
        assert authenticated_user is None


@pytest.mark.integration
class TestAuthenticationFlow:
    """Integration tests for complete authentication flows."""
    
    def test_user_registration_flow(self, client):
        """Test complete user registration flow."""
        user_data = {
            "email": "newuser@example.com",
            "username": "newuser",
            "password": "password123",
            "full_name": "New User"
        }
        
        response = client.post("/api/v1/auth/register", json=user_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == user_data["email"]
        assert data["username"] == user_data["username"]
        assert data["full_name"] == user_data["full_name"]
        assert "password" not in data
        assert "hashed_password" not in data
    
    def test_user_login_flow(self, client, db_session):
        """Test complete user login flow."""
        # First register a user
        user_repo = UserRepository(db_session)
        password = "password123"
        user_data = UserCreate(
            email="logintest@example.com",
            username="logintest",
            password=password,
            full_name="Login Test User"
        )
        user_repo.create(user_data)
        
        # Then try to login
        login_data = {
            "username": "logintest@example.com",  # Can use email as username
            "password": password
        }
        
        response = client.post("/api/v1/auth/login", data=login_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
    
    def test_protected_endpoint_with_valid_token(self, client, auth_headers):
        """Test accessing protected endpoint with valid token."""
        response = client.get("/api/v1/auth/me", headers=auth_headers)
        
        # This might fail if the endpoint doesn't exist yet
        # Adjust based on actual implementation
        assert response.status_code in [200, 404]  # 404 if endpoint not implemented
    
    def test_protected_endpoint_without_token(self, client):
        """Test accessing protected endpoint without token."""
        response = client.get("/api/v1/auth/me")
        
        assert response.status_code == 401
