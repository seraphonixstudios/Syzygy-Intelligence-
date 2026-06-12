"""Tests for OpenAI-compatible /v1/chat/completions endpoint."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.openai_compat import router as oai_router
from app.consensus.engine import ConsensusRound, ConsensusSession

# Minimal test app with only the openai_compat router
test_app = FastAPI(debug=False)
test_app.include_router(oai_router)


def _fake_session(task="Test task"):
    r1 = ConsensusRound(round_number=1)
    r1.proposals = {"a1": "Proposal A"}
    r1.critiques = {"a1": "Critique A"}
    r1.refinements = {"a1": "Refined A"}
    r1.scores = {"a1": 0.85}
    r1.convergence_score = 0.92
    r1.polarity_balance = 0.55
    r1.completed = True
    return ConsensusSession(
        task=task,
        agents=[],
        rounds=[r1],
        current_round=1,
        status="completed",
        final_synthesis="This is the final synthesized response.",
        polarity_fusion_report={
            "masculine_forces": ["Force A"],
            "feminine_forces": ["Force B"],
            "unified_perspective": ["Unified C"],
            "polarity_balance_scores": [0.55],
            "rounds_completed": 1,
            "individuation_notes": "Test individuation notes.",
        },
    )


@pytest.fixture(autouse=True)
def _patch_modules():
    """Mock ConsensusEngine and OllamaClient on openai_compat module."""
    with (
        patch("app.api.openai_compat.ConsensusEngine") as mock_engine_cls,
        patch("app.api.openai_compat.OllamaClient") as mock_llm_cls,
    ):
        mock_engine = MagicMock()
        mock_engine.run_consensus = AsyncMock()
        mock_engine_cls.return_value = mock_engine

        mock_llm = MagicMock()
        mock_llm.chat = AsyncMock()
        mock_llm_cls.return_value = mock_llm

        yield {
            "engine_cls": mock_engine_cls,
            "engine": mock_engine,
            "llm_cls": mock_llm_cls,
            "llm": mock_llm,
        }


# ===================================================================
# POST /v1/chat/completions — Syzygy model
# ===================================================================


class TestSyzygyModel:
    """Tests for the syzygy consensus model path."""

    def test_uses_consensus_engine(self, _patch_modules):
        mocks = _patch_modules
        mocks["engine"].run_consensus.return_value = _fake_session()

        resp = TestClient(test_app).post("/v1/chat/completions", json={
            "model": "syzygy",
            "messages": [{"role": "user", "content": "Test query"}],
        })
        assert resp.status_code == 200
        mocks["engine"].run_consensus.assert_called_once()

    def test_returns_openai_format(self, _patch_modules):
        mocks = _patch_modules
        mocks["engine"].run_consensus.return_value = _fake_session()

        resp = TestClient(test_app).post("/v1/chat/completions", json={
            "model": "syzygy",
            "messages": [{"role": "user", "content": "Hello"}],
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["object"] == "chat.completion"
        assert data["model"] == "syzygy"
        assert len(data["choices"]) == 1
        assert data["choices"][0]["finish_reason"] == "stop"
        assert data["choices"][0]["message"]["role"] == "assistant"
        assert "id" in data
        assert "usage" in data
        assert "prompt_tokens" in data["usage"]
        assert "completion_tokens" in data["usage"]
        assert "total_tokens" in data["usage"]

    def test_includes_synthesis_content(self, _patch_modules):
        mocks = _patch_modules
        mocks["engine"].run_consensus.return_value = _fake_session()

        resp = TestClient(test_app).post("/v1/chat/completions", json={
            "model": "syzygy",
            "messages": [{"role": "user", "content": "Test"}],
        })
        content = resp.json()["choices"][0]["message"]["content"]
        assert "This is the final synthesized response." in content
        assert "Syzygy Polarity Fusion Report" in content
        assert "Test individuation notes." in content

    def test_passes_max_rounds(self, _patch_modules):
        mocks = _patch_modules
        mocks["engine"].run_consensus.return_value = _fake_session()

        TestClient(test_app).post("/v1/chat/completions", json={
            "model": "syzygy",
            "messages": [{"role": "user", "content": "Test"}],
            "syzygy_consensus_rounds": 5,
        })
        _, kwargs = mocks["engine"].run_consensus.call_args
        assert kwargs["max_rounds"] == 5

    def test_default_max_rounds(self, _patch_modules):
        mocks = _patch_modules
        mocks["engine"].run_consensus.return_value = _fake_session()

        TestClient(test_app).post("/v1/chat/completions", json={
            "model": "syzygy-consensus",
            "messages": [{"role": "user", "content": "Test"}],
        })
        _, kwargs = mocks["engine"].run_consensus.call_args
        assert kwargs["max_rounds"] == 4

    def test_syzygy_variant_models(self, _patch_modules):
        mocks = _patch_modules
        mocks["engine"].run_consensus.return_value = _fake_session()

        for model in ["syzygy-consensus", "syzygy-3b", "SyzyGy-pro"]:
            resp = TestClient(test_app).post("/v1/chat/completions", json={
                "model": model,
                "messages": [{"role": "user", "content": "Test"}],
            })
            assert resp.status_code == 200, f"Failed for model={model}"
        assert mocks["engine"].run_consensus.call_count == 3

    def test_passes_task_from_user_message(self, _patch_modules):
        mocks = _patch_modules
        mocks["engine"].run_consensus.return_value = _fake_session()

        TestClient(test_app).post("/v1/chat/completions", json={
            "model": "syzygy",
            "messages": [{"role": "user", "content": "Research quantum computing"}],
        })
        _, kwargs = mocks["engine"].run_consensus.call_args
        assert kwargs["task"] == "Research quantum computing"


# ===================================================================
# POST /v1/chat/completions — Non-syzygy (direct LLM) model
# ===================================================================


class TestNonSyzygyModel:
    """Tests for the direct LLM model path."""

    def test_uses_ollama_client(self, _patch_modules):
        mocks = _patch_modules
        mocks["llm"].chat.return_value = "Direct LLM response"

        resp = TestClient(test_app).post("/v1/chat/completions", json={
            "model": "qwen3:8b-gpu",
            "messages": [{"role": "user", "content": "Hello"}],
        })
        assert resp.status_code == 200
        mocks["llm"].chat.assert_called_once()

    def test_passes_messages_and_model(self, _patch_modules):
        mocks = _patch_modules
        mocks["llm"].chat.return_value = "Response"

        TestClient(test_app).post("/v1/chat/completions", json={
            "model": "dolphin-llama3:8b-gpu",
            "messages": [
                {"role": "system", "content": "You are helpful"},
                {"role": "user", "content": "Hi"},
            ],
        })
        _, kwargs = mocks["llm"].chat.call_args
        assert kwargs["model"] == "dolphin-llama3:8b-gpu"
        assert len(kwargs["messages"]) == 2
        assert kwargs["messages"][0]["role"] == "system"

    def test_passes_temperature(self, _patch_modules):
        mocks = _patch_modules
        mocks["llm"].chat.return_value = "Response"

        TestClient(test_app).post("/v1/chat/completions", json={
            "model": "qwen3:8b-gpu",
            "messages": [{"role": "user", "content": "Hi"}],
            "temperature": 0.3,
        })
        _, kwargs = mocks["llm"].chat.call_args
        assert kwargs["temperature"] == 0.3

    def test_returns_direct_content(self, _patch_modules):
        mocks = _patch_modules
        mocks["llm"].chat.return_value = "Direct LLM response"

        resp = TestClient(test_app).post("/v1/chat/completions", json={
            "model": "qwen3:8b-gpu",
            "messages": [{"role": "user", "content": "Hello"}],
        })
        content = resp.json()["choices"][0]["message"]["content"]
        assert content == "Direct LLM response"

    def test_no_fusion_report_for_non_syzygy(self, _patch_modules):
        mocks = _patch_modules
        mocks["llm"].chat.return_value = "Plain response"

        resp = TestClient(test_app).post("/v1/chat/completions", json={
            "model": "qwen3:8b-gpu",
            "messages": [{"role": "user", "content": "Hello"}],
        })
        content = resp.json()["choices"][0]["message"]["content"]
        assert "Syzygy Polarity Fusion Report" not in content

    def test_returns_openai_format_non_syzygy(self, _patch_modules):
        mocks = _patch_modules
        mocks["llm"].chat.return_value = "Response"

        resp = TestClient(test_app).post("/v1/chat/completions", json={
            "model": "llama3",
            "messages": [{"role": "user", "content": "Hi"}],
        })
        data = resp.json()
        assert data["object"] == "chat.completion"
        assert data["model"] == "llama3"
        assert len(data["choices"]) == 1
        assert data["choices"][0]["message"]["role"] == "assistant"


# ===================================================================
# POST /v1/chat/completions — Error handling
# ===================================================================


class TestErrorHandling:
    """Tests for error cases in the chat completions endpoint."""

    def test_empty_message_returns_400(self, _patch_modules):
        resp = TestClient(test_app).post("/v1/chat/completions", json={
            "model": "syzygy",
            "messages": [{"role": "system", "content": "System message"}],
        })
        assert resp.status_code == 400

    def test_empty_messages_list_returns_400(self, _patch_modules):
        resp = TestClient(test_app).post("/v1/chat/completions", json={
            "model": "syzygy",
            "messages": [],
        })
        assert resp.status_code == 400

    def test_consensus_timeout_returns_504(self, _patch_modules):
        mocks = _patch_modules
        mocks["engine"].run_consensus.side_effect = TimeoutError("Consensus timed out")

        resp = TestClient(test_app).post("/v1/chat/completions", json={
            "model": "syzygy",
            "messages": [{"role": "user", "content": "Test"}],
        })
        assert resp.status_code == 504
        assert resp.json()["detail"]["code"] == "CONSENSUS_TIMEOUT"

    def test_consensus_generic_error_returns_500(self, _patch_modules):
        mocks = _patch_modules
        mocks["engine"].run_consensus.side_effect = RuntimeError("Unexpected consensus error")

        resp = TestClient(test_app).post("/v1/chat/completions", json={
            "model": "syzygy",
            "messages": [{"role": "user", "content": "Test"}],
        })
        assert resp.status_code == 500
        assert resp.json()["detail"]["code"] == "CONSENSUS_ERROR"

    def test_ollama_connection_error_returns_503(self, _patch_modules):
        mocks = _patch_modules
        from app.errors import LLMConnectionError
        mocks["llm"].chat.side_effect = LLMConnectionError(
            model="qwen3:8b-gpu", original_error="Ollama not running"
        )

        resp = TestClient(test_app).post("/v1/chat/completions", json={
            "model": "qwen3:8b-gpu",
            "messages": [{"role": "user", "content": "Hello"}],
        })
        assert resp.status_code == 503
        assert resp.json()["detail"]["code"] == "LLM_CONNECTION_ERROR"

    def test_generic_llm_exception_returns_500(self, _patch_modules):
        mocks = _patch_modules
        mocks["llm"].chat.side_effect = RuntimeError("Unexpected error")

        resp = TestClient(test_app).post("/v1/chat/completions", json={
            "model": "qwen3:8b-gpu",
            "messages": [{"role": "user", "content": "Hello"}],
        })
        assert resp.status_code == 500
        assert resp.json()["detail"]["code"] == "LLM_ERROR"


# ===================================================================
# POST /v1/chat/completions — Request validation
# ===================================================================


class TestRequestValidation:
    """Tests for request validation and edge cases."""

    def test_multiple_messages_extracts_last_user(self, _patch_modules):
        mocks = _patch_modules
        mocks["engine"].run_consensus.return_value = _fake_session()

        TestClient(test_app).post("/v1/chat/completions", json={
            "model": "syzygy",
            "messages": [
                {"role": "system", "content": "You are an assistant"},
                {"role": "user", "content": "First query"},
                {"role": "assistant", "content": "First response"},
                {"role": "user", "content": "Second query"},
            ],
        })
        _, kwargs = mocks["engine"].run_consensus.call_args
        assert kwargs["task"] == "Second query"

    def test_missing_model_uses_default(self, _patch_modules):
        mocks = _patch_modules
        mocks["engine"].run_consensus.return_value = _fake_session()

        resp = TestClient(test_app).post("/v1/chat/completions", json={
            "messages": [{"role": "user", "content": "Hello"}],
        })
        assert resp.status_code == 200
        # Default model is "syzygy-consensus" so consensus engine is used
        mocks["engine"].run_consensus.assert_called_once()

    def test_rejects_missing_messages(self, _patch_modules):
        resp = TestClient(test_app).post("/v1/chat/completions", json={
            "model": "syzygy",
        })
        assert resp.status_code == 422

    def test_accepts_additional_fields(self, _patch_modules):
        mocks = _patch_modules
        mocks["engine"].run_consensus.return_value = _fake_session()

        resp = TestClient(test_app).post("/v1/chat/completions", json={
            "model": "syzygy",
            "messages": [{"role": "user", "content": "Test"}],
            "temperature": 0.5,
            "max_tokens": 1024,
            "stream": False,
        })
        assert resp.status_code == 200

    def test_empty_content_returns_400(self, _patch_modules):
        resp = TestClient(test_app).post("/v1/chat/completions", json={
            "model": "syzygy",
            "messages": [{"role": "user", "content": ""}],
        })
        assert resp.status_code == 400
