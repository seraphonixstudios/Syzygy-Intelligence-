"""Unit tests for Syzygy Configuration and Error Handling."""

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
