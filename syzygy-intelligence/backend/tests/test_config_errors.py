"""Unit tests for Syzygy Configuration and Error Handling."""

from unittest.mock import patch

import pytest
from app.config import SyzygyConfig
from app.errors import (
    AgentNotFoundError,
    ConsensusError,
    LLMConnectionError,
    SessionNotFoundError,
    SyzygyError,
    ToolExecutionError,
    ValidationError,
)


class TestSyzygyConfig:
    def test_default_values(self):
        config = SyzygyConfig(_env_file=None)
        # Ensure env vars don't pollute
        assert config.env in ("development", "production", "testing")
        assert config.max_consensus_rounds == 6
        assert config.convergence_threshold == 0.85

    def test_default_model(self):
        config = SyzygyConfig()
        assert config.default_model

    def test_database_url(self):
        config = SyzygyConfig()
        url = config.database_url
        assert url.startswith("postgresql+asyncpg://")


class TestSyzygyErrors:
    def test_base_error(self):
        err = SyzygyError("Test error", code="TEST", status_code=400)
        assert err.message == "Test error"
        assert err.code == "TEST"
        assert err.status_code == 400

    def test_agent_not_found(self):
        err = AgentNotFoundError("agent_123")
        assert "agent_123" in str(err)
        assert err.code == "AGENT_NOT_FOUND"
        assert err.status_code == 404
        assert err.details == {"agent_id": "agent_123"}

    def test_session_not_found(self):
        err = SessionNotFoundError("session_456")
        assert err.code == "SESSION_NOT_FOUND"
        assert err.status_code == 404

    def test_consensus_error(self):
        err = ConsensusError("Consensus failed", {"round": 3})
        assert err.code == "CONSENSUS_ERROR"
        assert err.details == {"round": 3}

    def test_llm_connection_error(self):
        err = LLMConnectionError("qwen3.5", "timeout")
        assert "qwen3.5" in str(err)
        assert err.code == "LLM_CONNECTION_ERROR"
        assert err.status_code == 503

    def test_tool_execution_error(self):
        err = ToolExecutionError("browser", "navigation failed")
        assert err.code == "TOOL_EXECUTION_ERROR"

    def test_validation_error(self):
        err = ValidationError("Invalid input", {"field": "name"})
        assert err.code == "VALIDATION_ERROR"
        assert err.status_code in (422, 422)

    def test_error_inheritance(self):
        assert issubclass(AgentNotFoundError, SyzygyError)
        assert issubclass(ConsensusError, SyzygyError)
        assert issubclass(LLMConnectionError, SyzygyError)
        assert issubclass(ValidationError, SyzygyError)

    def test_error_with_details_none(self):
        err = SyzygyError("Simple error")
        assert err.details == {}


class TestSyzygyConfigEdgeCases:
    def test_validate_positive_float_raises(self):
        with pytest.raises(ValueError, match="Rate limit must be positive"):
            SyzygyConfig(rate_limit_per_second=0, _env_file=None)

    def test_validate_positive_int_raises(self):
        with pytest.raises(ValueError, match="Burst size must be positive"):
            SyzygyConfig(rate_limit_burst=0, _env_file=None)

    def test_database_url_parsing_error_raises(self):
        import os
        from unittest.mock import patch
        with patch.dict(os.environ, {"DATABASE_URL": "invalid://"}):
            with pytest.raises(ValueError, match="Invalid DATABASE_URL"):
                SyzygyConfig(_env_file=None)

    def test_production_secrets_not_configured_raises(self):
        with pytest.raises(ValueError, match="Production configuration validation failed"):
            SyzygyConfig(env="production", _env_file=None)

    def test_production_cors_logs_warning(self):
        from unittest.mock import MagicMock, patch
        mock_logger = MagicMock()
        with patch("app.config._get_logger", return_value=mock_logger):
            SyzygyConfig(
                env="production",
                _env_file=None,
                secret_key="a-real-secret-key-that-is-long-enough-here",
                db_password="a-real-db-password",
                neo4j_password="a-real-neo4j-password",
                cors_origins="http://localhost:3000",
            )
            mock_logger.warning.assert_any_call(
                "CORS origins contain localhost in production",
                detail="Set SYZYGY_CORS_ORIGINS to your actual domain(s)",
            )

    def test_production_email_warning(self):
        from unittest.mock import MagicMock, patch
        mock_logger = MagicMock()
        with patch("app.config._get_logger", return_value=mock_logger):
            SyzygyConfig(
                env="production",
                _env_file=None,
                secret_key="a-real-secret-key-that-is-long-enough-here",
                db_password="a-real-db-password",
                neo4j_password="a-real-neo4j-password",
            )
            mock_logger.warning.assert_any_call(
                "Email provider is 'console' in production",
                detail=(
                    "Email tokens will be exposed in API responses. "
                    "Configure SendGrid or AWS SES instead."
                ),
            )

    def test_allowed_origins_empty_production_raises(self):
        config = SyzygyConfig(
            env="production",
            _env_file=None,
            cors_origins="",
            secret_key="a-real-secret-key-that-is-long-enough-here",
            db_password="a-real-db-password",
            neo4j_password="a-real-neo4j-password",
        )
        with pytest.raises(ValueError, match="SYZYGY_CORS_ORIGINS must be set"):
            _ = config.allowed_origins

    def test_allowed_origins_empty_development_uses_defaults(self):
        from unittest.mock import MagicMock, patch
        mock_logger = MagicMock()
        with patch("app.config._get_logger", return_value=mock_logger):
            config = SyzygyConfig(env="development", _env_file=None, cors_origins="")
            assert config.allowed_origins == ["http://localhost:3000", "http://localhost:8000"]
            mock_logger.info.assert_called_once()

    def test_database_url_sync_sqlite(self):
        config = SyzygyConfig(env="development", _env_file=None)
        url = config.database_url_sync
        assert url.startswith("sqlite:///")

    def test_database_url_sync_postgresql(self):
        config = SyzygyConfig(env="production", _env_file=None,
                              secret_key="real", db_password="real", neo4j_password="real")
        url = config.database_url_sync
        assert url.startswith("postgresql://")

    def test_oauth_redirect_localhost_warning(self):
        from unittest.mock import MagicMock, patch
        mock_logger = MagicMock()
        with patch("app.config._get_logger", return_value=mock_logger):
            SyzygyConfig(
                env="production",
                _env_file=None,
                secret_key="a-real-secret-key-that-is-long-enough-here",
                db_password="a-real-db-password",
                neo4j_password="a-real-neo4j-password",
                cors_origins="https://example.com",
                oauth_redirect_url="http://localhost:8001/api/auth/oauth",
            )
            mock_logger.warning.assert_any_call(
                "OAuth redirect URL contains localhost in production",
                detail="OAuth providers will not recognize redirect",
            )


class TestGetLoggerFallback:
    def test_get_logger_import_error(self):
        """_get_logger falls back to logging.getLogger when ImportError occurs."""
        import importlib
        import app.config
        with patch.dict("sys.modules", {"app.logging_setup": None}):
            logger_fn = app.config._get_logger()
            assert logger_fn.name == "syzygy.config"


class TestDatabaseUrlParsing:
    def test_parse_database_url_success(self):
        from app.config import DatabaseConfig
        result = DatabaseConfig.parse_database_url(
            "postgresql+asyncpg://user:pass@myhost:5432/mydb"
        )
        assert result["db_user"] == "user"
        assert result["db_password"] == "pass"
        assert result["db_host"] == "myhost"
        assert result["db_port"] == 5432
        assert result["db_name"] == "mydb"

    def test_parse_database_url_default_port(self):
        from app.config import DatabaseConfig
        result = DatabaseConfig.parse_database_url(
            "postgresql+asyncpg://user:pass@host/db"
        )
        assert result["db_port"] == 5432

    def test_config_init_with_database_url(self):
        """Setting DATABASE_URL triggers parse and log."""
        import os
        from unittest.mock import MagicMock, patch
        with patch.dict(os.environ, {"DATABASE_URL": "postgresql+asyncpg://u:p@h:5555/testdb"}):
            mock_logger = MagicMock()
            with patch("app.config._get_logger", return_value=mock_logger):
                config = SyzygyConfig(_env_file=None)
                assert config.db_host == "h"
                assert config.db_port == 5555
                assert config.db_name == "testdb"
