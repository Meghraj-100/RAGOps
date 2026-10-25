"""Security regression test suite — verifies preventive controls and bug fixes."""

import pytest
from unittest.mock import patch, MagicMock
from app.core.config import Settings
from app.core.security import verify_api_key
from fastapi.security import HTTPAuthorizationCredentials
from fastapi import HTTPException


class TestProductionSecurityFailClosed:
    """Verifies that the application fails closed when misconfigured in production."""

    def test_production_rejects_empty_api_key(self):
        settings = Settings(
            environment="production",
            api_key="",
            database_url="postgresql+asyncpg://produser:strongsecretpassword@db:5432/ragdb",
            groq_api_key="gsk_actual_valid_production_key_12345",
        )
        with pytest.raises(ValueError, match="API_KEY"):
            settings.validate_production_security()

    def test_production_rejects_weak_or_default_api_key(self):
        settings = Settings(
            environment="production",
            api_key="dev-api-key",
            database_url="postgresql+asyncpg://produser:strongsecretpassword@db:5432/ragdb",
            groq_api_key="gsk_actual_valid_production_key_12345",
        )
        with pytest.raises(ValueError, match="API_KEY"):
            settings.validate_production_security()

    def test_production_rejects_default_database_password(self):
        settings = Settings(
            environment="production",
            api_key="a-very-strong-production-api-key-9999",
            database_url="postgresql+asyncpg://raguser:ragpass@db:5432/ragdb",
            groq_api_key="gsk_actual_valid_production_key_12345",
        )
        with pytest.raises(ValueError, match="Default database password 'ragpass' is prohibited"):
            settings.validate_production_security()

    def test_production_rejects_missing_groq_api_key(self):
        settings = Settings(
            environment="production",
            api_key="a-very-strong-production-api-key-9999",
            database_url="postgresql+asyncpg://produser:strongsecretpassword@db:5432/ragdb",
            database_url_sync="postgresql://produser:strongsecretpassword@db:5432/ragdb",
            groq_api_key="",
        )
        with pytest.raises(ValueError, match="GROQ_API_KEY must be configured"):
            settings.validate_production_security()

    def test_valid_production_config_passes(self):
        settings = Settings(
            environment="production",
            api_key="a-very-strong-production-api-key-9999",
            database_url="postgresql+asyncpg://produser:strongsecretpassword@db:5432/ragdb",
            database_url_sync="postgresql://produser:strongsecretpassword@db:5432/ragdb",
            groq_api_key="gsk_actual_valid_production_key_12345",
        )
        # Should not raise
        settings.validate_production_security()


class TestChunkingBoundsAndDos:
    """Verifies input bounds and DoS prevention in text chunking."""

    def test_chunking_rejects_overlap_equal_to_size(self):
        from app.services.ingestion import chunk_text
        with pytest.raises(ValueError, match="strictly less than chunk_size"):
            chunk_text("Hello world", chunk_size=100, overlap=100)

    def test_chunking_rejects_overlap_greater_than_size(self):
        from app.services.ingestion import chunk_text
        with pytest.raises(ValueError, match="strictly less than chunk_size"):
            chunk_text("Hello world", chunk_size=100, overlap=150)

    def test_chunking_rejects_negative_overlap(self):
        from app.services.ingestion import chunk_text
        with pytest.raises(ValueError, match="non-negative"):
            chunk_text("Hello world", chunk_size=100, overlap=-5)

    def test_chunking_rejects_zero_or_negative_chunk_size(self):
        from app.services.ingestion import chunk_text
        with pytest.raises(ValueError, match="greater than 0"):
            chunk_text("Hello world", chunk_size=0, overlap=0)
        with pytest.raises(ValueError, match="greater than 0"):
            chunk_text("Hello world", chunk_size=-10, overlap=0)

    def test_config_model_validator_rejects_invalid_overlap(self):
        with pytest.raises(ValueError, match="chunk_overlap must be strictly less than chunk_size"):
            Settings(chunk_size=100, chunk_overlap=100)


class TestPathTraversalPrevention:
    """Verifies that dataset loader prevents directory traversal and path leakage."""

    def test_load_eval_dataset_rejects_dot_dot_traversal(self):
        from app.evaluation.engine import load_eval_dataset
        with pytest.raises(ValueError, match="Invalid dataset name"):
            load_eval_dataset("../../etc/passwd")

    def test_load_eval_dataset_rejects_special_characters(self):
        from app.evaluation.engine import load_eval_dataset
        with pytest.raises(ValueError, match="Invalid dataset name"):
            load_eval_dataset("default;rm -rf /")

    def test_load_eval_dataset_does_not_leak_absolute_path_on_not_found(self):
        from app.evaluation.engine import load_eval_dataset
        with pytest.raises(FileNotFoundError) as exc_info:
            load_eval_dataset("nonexistent_dataset_name")
        error_msg = str(exc_info.value)
        assert "nonexistent_dataset_name" in error_msg
        assert "\\" not in error_msg
        assert "/" not in error_msg


class TestApiKeyVerificationLogic:
    """Verifies timing-safe API key verification."""

    def test_verify_api_key_when_configured(self):
        with patch("app.core.security.get_settings") as mock_get_settings:
            mock_settings = MagicMock()
            mock_settings.api_key = "secret-token-123"
            mock_settings.environment = "production"
            mock_get_settings.return_value = mock_settings

            # Correct header key
            assert verify_api_key(x_api_key="secret-token-123", bearer=None) is True

            # Correct bearer key
            bearer = HTTPAuthorizationCredentials(scheme="Bearer", credentials="secret-token-123")
            assert verify_api_key(x_api_key=None, bearer=bearer) is True

            # Missing key raises 401
            with pytest.raises(HTTPException) as exc:
                verify_api_key(x_api_key=None, bearer=None)
            assert exc.value.status_code == 401

            # Incorrect key raises 401
            with pytest.raises(HTTPException) as exc:
                verify_api_key(x_api_key="wrong-token", bearer=None)
            assert exc.value.status_code == 401

    def test_verify_api_key_when_not_configured(self):
        with patch("app.core.security.get_settings") as mock_get_settings:
            mock_settings = MagicMock()
            mock_settings.api_key = ""
            mock_get_settings.return_value = mock_settings

            assert verify_api_key(x_api_key=None, bearer=None) is True
