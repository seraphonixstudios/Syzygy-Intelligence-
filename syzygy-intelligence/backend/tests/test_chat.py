"""Tests for chat API routes — consensus mode, direct LLM, multi-model, streaming."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.auth import require_user
from app.api.routes.chat import router as chat_router
from app.consensus.engine import ConsensusRound, ConsensusSession
from app.db.session import get_db

# Minimal test app with only the chat router
test_app = FastAPI()
test_app.include_router(chat_router, prefix="/api/chat")


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
            "masculine_forces": [],
            "feminine_forces": [],
            "unified_perspective": [],
            "polarity_balance_scores": [0.55],
            "rounds_completed": 1,
            "individuation_notes": "Test individuation notes.",
        },
    )


@pytest.fixture(autouse=True)
def _override_auth_and_db():
    async def _mock_user():
        return MagicMock()

    async def _mock_db():
        return AsyncMock()

    test_app.dependency_overrides[require_user] = _mock_user
    test_app.dependency_overrides[get_db] = _mock_db
    yield
    test_app.dependency_overrides.clear()


@pytest.fixture(autouse=True)
def _patch_modules():
    """Mock module-level llm, model_manager, and engine on chat route module."""
    with (
        patch("app.api.routes.chat.engine") as mock_engine,
        patch("app.api.routes.chat.llm") as mock_llm,
        patch("app.api.routes.chat.model_manager") as mock_mm,
    ):
        mock_engine.run_consensus = AsyncMock()
        mock_llm.chat = AsyncMock()
        mock_llm.generate_stream = AsyncMock()
        mock_llm.default_model = "qwen3:8b-gpu"
        mock_mm.get_all_model_names = MagicMock()
        mock_mm.generate_multi_model = AsyncMock()
        mock_mm.list_available_models = AsyncMock()
        mock_mm.get_model_for_role = MagicMock()

        # MODEL_ROLES is a dict mapping role names to config keys
        mock_mm.MODEL_ROLES = {
            "default": "default_model",
            "coding": "coding_model",
            "creative": "creative_model",
        }
        yield


# ===================================================================
# POST /api/chat/completions — Consensus mode
# ===================================================================

class TestChatCompletionsConsensus:
    """Tests for consensus mode via POST /api/chat/completions."""

    def test_model_syzygy_uses_consensus(self, _patch_modules):
        from app.api.routes.chat import engine
        engine.run_consensus.return_value = _fake_session()

        resp = TestClient(test_app).post("/api/chat/completions", json={
            "message": "Test query",
            "model": "syzygy",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["response"] == "This is the final synthesized response."
        assert "session_id" in data
        assert data["rounds"] == 1
        assert "fusion_report" in data

    def test_use_consensus_flag(self, _patch_modules):
        from app.api.routes.chat import engine
        engine.run_consensus.return_value = _fake_session()

        resp = TestClient(test_app).post("/api/chat/completions", json={
            "message": "Test query",
            "model": "some-model",
            "use_consensus": True,
        })
        assert resp.status_code == 200
        assert resp.json()["response"] == "This is the final synthesized response."

    def test_consensus_with_rag(self, _patch_modules):
        from app.api.routes.chat import engine
        engine.run_consensus.return_value = _fake_session()

        with patch("app.api.routes.chat.build_rag_context", new_callable=AsyncMock) as mock_rag:
            mock_rag.return_value = "RAG context data"

            resp = TestClient(test_app).post("/api/chat/completions", json={
                "message": "Test query",
                "model": "syzygy",
                "use_rag": True,
            })
            assert resp.status_code == 200
            assert resp.json()["rag_context_used"] is True

    def test_consensus_timeout_returns_504(self, _patch_modules):
        from app.api.routes.chat import engine
        engine.run_consensus = AsyncMock(side_effect=TimeoutError())

        resp = TestClient(test_app).post("/api/chat/completions", json={
            "message": "Test query",
            "model": "syzygy",
        })
        assert resp.status_code == 504
        assert resp.json()["detail"]["code"] == "CONSENSUS_TIMEOUT"

    def test_consensus_rounds_param(self, _patch_modules):
        from app.api.routes.chat import engine
        engine.run_consensus.return_value = _fake_session()

        TestClient(test_app).post("/api/chat/completions", json={
            "message": "Test query",
            "model": "syzygy",
            "consensus_rounds": 5,
        })
        _, kwargs = engine.run_consensus.call_args
        assert kwargs["max_rounds"] == 5


# ===================================================================
# POST /api/chat/completions — Direct LLM mode
# ===================================================================

class TestChatCompletionsDirect:
    """Tests for direct LLM mode via POST /api/chat/completions."""

    def test_direct_llm_response(self, _patch_modules):
        from app.api.routes.chat import llm
        llm.chat.return_value = "Direct LLM response"

        resp = TestClient(test_app).post("/api/chat/completions", json={
            "message": "Hello",
            "model": "qwen3:8b-gpu",
        })
        assert resp.status_code == 200
        assert resp.json()["response"] == "Direct LLM response"
        assert resp.json()["rag_context_used"] is False

    def test_direct_llm_with_rag(self, _patch_modules):
        from app.api.routes.chat import llm
        llm.chat.return_value = "RAG-enhanced response"

        with patch("app.api.routes.chat.build_rag_context", new_callable=AsyncMock) as mock_rag:
            mock_rag.return_value = "RAG data"

            resp = TestClient(test_app).post("/api/chat/completions", json={
                "message": "Query",
                "model": "qwen3:8b-gpu",
                "use_rag": True,
            })
            assert resp.status_code == 200
            assert resp.json()["rag_context_used"] is True

    def test_llm_connection_error_returns_503(self, _patch_modules):
        from app.api.routes.chat import llm
        from app.errors import LLMConnectionError
        llm.chat.side_effect = LLMConnectionError(model="qwen3:8b-gpu", original_error="Ollama not running")

        resp = TestClient(test_app).post("/api/chat/completions", json={
            "message": "Hello",
            "model": "qwen3:8b-gpu",
        })
        assert resp.status_code == 503
        assert resp.json()["detail"]["code"] == "LLM_CONNECTION_ERROR"

    def test_invalid_message_returns_422(self, _patch_modules):
        resp = TestClient(test_app).post("/api/chat/completions", json={
            "message": "",
            "model": "qwen3:8b-gpu",
        })
        assert resp.status_code == 422

    def test_no_auth_optional(self, _patch_modules):
        test_app.dependency_overrides[require_user] = lambda: None

        from app.api.routes.chat import llm
        llm.chat.return_value = "Response"

        resp = TestClient(test_app).post("/api/chat/completions", json={
            "message": "Hello",
        })
        assert resp.status_code == 200


# ===================================================================
# POST /api/chat/multi-model
# ===================================================================

class TestChatMultiModel:
    """Tests for POST /api/chat/multi-model."""

    def test_multi_model_with_custom_models(self, _patch_modules):
        from app.api.routes.chat import model_manager
        model_manager.generate_multi_model.return_value = [
            {"model": "qwen3:8b-gpu", "response": "A"},
            {"model": "dolphin-llama3:8b-gpu", "response": "B"},
        ]

        resp = TestClient(test_app).post("/api/chat/multi-model", json={
            "message": "Test",
            "models": ["qwen3:8b-gpu", "dolphin-llama3:8b-gpu"],
        })
        assert resp.status_code == 200
        assert len(resp.json()["responses"]) == 2

    def test_multi_model_empty_models_uses_all(self, _patch_modules):
        from app.api.routes.chat import model_manager
        model_manager.get_all_model_names.return_value = ["qwen3:8b-gpu", "dolphin-llama3:8b-gpu"]
        model_manager.generate_multi_model.return_value = [
            {"model": "qwen3:8b-gpu", "response": "A"},
            {"model": "dolphin-llama3:8b-gpu", "response": "B"},
        ]

        resp = TestClient(test_app).post("/api/chat/multi-model", json={"message": "Test"})
        assert resp.status_code == 200
        assert len(resp.json()["responses"]) == 2


# ===================================================================
# GET /api/chat/models
# ===================================================================

class TestChatModels:
    """Tests for GET /api/chat/models."""

    def test_returns_configured_and_available(self, _patch_modules):
        from app.api.routes.chat import model_manager
        model_manager.get_model_for_role.side_effect = lambda r: f"model-{r}"
        model_manager.list_available_models.return_value = [
            {"name": "qwen3:8b-gpu"},
        ]
        model_manager.get_all_model_names.return_value = ["qwen3:8b-gpu", "dolphin-llama3:8b-gpu"]

        resp = TestClient(test_app).get("/api/chat/models")
        assert resp.status_code == 200
        data = resp.json()
        assert data["configured"]["default"] == "model-default"
        assert data["configured"]["coding"] == "model-coding"
        assert "qwen3:8b-gpu" in data["available"]
        assert len(data["all_models"]) == 2


# ===================================================================
# POST /api/chat/stream
# ===================================================================

class TestChatStream:
    """Tests for POST /api/chat/stream (SSE streaming)."""

    def test_stream_yields_tokens(self, _patch_modules):
        from app.api.routes.chat import llm
        async def mock_stream(*args, **kwargs):
            for token in ["Hello", " ", "World"]:
                yield token
        llm.generate_stream = mock_stream

        resp = TestClient(test_app).post("/api/chat/stream", json={
            "message": "Hi",
            "model": "qwen3:8b-gpu",
        })
        assert resp.status_code == 200
        text = resp.text
        assert '"token": "Hello"' in text
        assert '"token": " "' in text
        assert '"token": "World"' in text
        assert '"done": true' in text

    def test_stream_with_rag(self, _patch_modules):
        from app.api.routes.chat import llm
        async def mock_stream(*args, **kwargs):
            yield "Output"
        llm.generate_stream = mock_stream

        with patch("app.api.routes.chat.build_rag_context", new_callable=AsyncMock) as mock_rag:
            mock_rag.return_value = "RAG"

            resp = TestClient(test_app).post("/api/chat/stream", json={
                "message": "Hi",
                "model": "qwen3:8b-gpu",
                "use_rag": True,
            })
            assert resp.status_code == 200
            assert '"rag_context": true' in resp.text

    def test_stream_error_yields_error_event(self, _patch_modules):
        from app.api.routes.chat import llm
        from app.errors import LLMConnectionError
        async def mock_stream(*args, **kwargs):
            """Async generator that raises on first iteration."""
            if False:
                yield
            raise LLMConnectionError(model="qwen3:8b-gpu", original_error="Connection failed")
        llm.generate_stream = mock_stream

        resp = TestClient(test_app).post("/api/chat/stream", json={
            "message": "Hi",
            "model": "qwen3:8b-gpu",
        })
        assert resp.status_code == 200
        assert "Connection failed" in resp.text

    def test_stream_generic_exception_is_handled(self, _patch_modules):
        from app.api.routes.chat import llm
        async def mock_stream(*args, **kwargs):
            if False:
                yield
            raise RuntimeError("Unexpected")
        llm.generate_stream = mock_stream

        resp = TestClient(test_app).post("/api/chat/stream", json={
            "message": "Hi",
            "model": "qwen3:8b-gpu",
        })
        assert resp.status_code == 200
        assert "Unexpected" in resp.text
