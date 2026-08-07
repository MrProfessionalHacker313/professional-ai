"""
Professional AI - Comprehensive Test Suite
Tests all critical functionality with proper error handling and edge cases.
"""

import pytest
import uuid
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.main import app
from app.database import Base, get_db
from app.config import Settings
from app.models.user import User
from app.services.auth_service import AuthService
from app.middleware.security import InputSanitizer, PasswordValidator
from fastapi import HTTPException


# Test database
TEST_DATABASE_URL = "postgresql+asyncpg://proai:proai_password@localhost:5432/professional_ai_test"
test_engine = None
test_session_factory = None


@pytest.fixture
def client():
    """Test client fixture."""
    return TestClient(app)


class TestSecurity:
    """Security middleware and validation tests."""

    def test_input_sanitizer_removes_script_tags(self):
        """Test that script tags are removed."""
        dirty = "<script>alert('xss')</script><p>Hello</p>"
        clean = InputSanitizer.sanitize_text(dirty)
        assert "<script>" not in clean
        assert "Hello" in clean

    def test_input_sanitizer_removes_event_handlers(self):
        """Test that event handlers are removed."""
        dirty = '<div onclick="alert(1)">Click me</div>'
        clean = InputSanitizer.sanitize_text(dirty)
        assert "onclick" not in clean
        assert "Click me" in clean

    def test_input_sanitizer_empty_input(self):
        """Test empty input handling."""
        assert InputSanitizer.sanitize_text("") == ""
        assert InputSanitizer.sanitize_text(None) is None

    def test_code_sanitizer_blocks_dangerous_patterns(self):
        """Test that dangerous code patterns are blocked."""
        dangerous_codes = [
            "import os; os.system('rm -rf /')",
            "subprocess.run(['ls'])",
        ]
        for code in dangerous_codes:
            with pytest.raises(HTTPException, match="Dangerous code pattern"):
                InputSanitizer.sanitize_code_input(code)

    def test_password_validator_strong_password(self):
        """Test password strength validation."""
        PasswordValidator.validate("SecurePass123!@#")

        with pytest.raises(HTTPException, match="at least 12 characters"):
            PasswordValidator.validate("Short1!")

        with pytest.raises(HTTPException, match="uppercase"):
            PasswordValidator.validate("securepass123!")


class TestAuthentication:
    """Authentication service tests."""

    def test_password_hashing(self):
        """Test password hashing and verification."""
        password = "TestPassword123!"
        hashed = AuthService.hash_password(password)
        assert hashed != password
        assert AuthService.verify_password(password, hashed)
        assert not AuthService.verify_password("WrongPassword", hashed)

    def test_create_access_token(self):
        """Test JWT access token creation."""
        token = AuthService.create_access_token("user-123", "test@example.com", False)
        assert isinstance(token, str)
        assert len(token) > 0

        payload = AuthService.decode_token(token)
        assert payload["sub"] == "user-123"
        assert payload["email"] == "test@example.com"
        assert payload["type"] == "access"

    def test_create_refresh_token(self):
        """Test JWT refresh token creation."""
        token = AuthService.create_refresh_token("user-123")
        payload = AuthService.decode_token(token)
        assert payload["sub"] == "user-123"
        assert payload["type"] == "refresh"

    def test_invalid_token_raises_error(self):
        """Test that invalid tokens raise HTTPException."""
        with pytest.raises(HTTPException) as exc_info:
            AuthService.decode_token("invalid-token")
        assert exc_info.value.status_code == 401

    def test_totp_generation(self):
        """Test TOTP secret generation."""
        secret = AuthService.generate_totp_secret()
        assert len(secret) > 0

        uri = AuthService.get_totp_uri(secret, "test@example.com")
        assert "test%40example.com" in uri or "test@example.com" in uri
        assert "Professional" in uri


class TestAPI:
    """API endpoint tests."""

    def test_health_check(self, client):
        """Test health check endpoint."""
        response = client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data

    def test_root_endpoint(self, client):
        """Test root endpoint."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Professional AI"

    def test_chat_endpoint_requires_auth(self, client):
        """Test that chat endpoint requires authentication."""
        response = client.post(
            "/api/chat/send",
            json={"prompt": "Hello", "mode": "chat"}
        )
        assert response.status_code in (401, 403)


class TestDatabase:
    """Database tests."""

    def test_database_engine_created(self):
        """Test database engine exists."""
        from app.database import _get_engine
        engine = _get_engine()
        assert engine is not None

    def test_user_model_columns(self):
        """Test User model has expected columns."""
        from sqlalchemy import inspect
        mapper = inspect(User)
        column_names = [c.key for c in mapper.columns]
        assert "id" in column_names
        assert "email" in column_names
        assert "password_hash" in column_names


class TestAI:
    """AI service tests."""

    def test_ai_service_initialization(self):
        """Test AI service initializes correctly."""
        from app.services.ai_service import ai_service
        assert ai_service is not None
        assert isinstance(ai_service.providers, list)

    def test_advanced_features_service_initialization(self):
        """Test advanced features service initializes correctly."""
        from app.services.advanced_features_service import advanced_features_service
        assert advanced_features_service is not None
        assert hasattr(advanced_features_service, 'available_models')


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
