"""Integration tests — real OllamaClient backed by mock server via ASGI transport."""

import httpx
import pytest

from tests.mock_ollama_server import app as mock_ollama_app


@pytest.fixture
async def mock_ollama_client():
    """Create an OllamaClient whose httpx transport is the mock ASGI app."""
    from app.llm.ollama_client import OllamaClient

    transport = httpx.ASGITransport(app=mock_ollama_app)
    client = OllamaClient(base_url="http://test")
    client._client = httpx.AsyncClient(transport=transport, base_url="http://test")
    yield client
    await client.close()


class TestOllamaClientIntegration:
    """Integration tests hitting the mock Ollama server via real HTTP."""

    async def test_generate_returns_mock_output(self, mock_ollama_client):
        result = await mock_ollama_client.generate("Hello")
        assert result == "mock output"

    async def test_generate_stream_yields_tokens(self, mock_ollama_client):
        tokens = []
        async for token in mock_ollama_client.generate_stream("Hello"):
            tokens.append(token)
        assert len(tokens) > 0
        assert "mock output" in "".join(tokens)

    async def test_chat_raises_llm_connection_error(self, mock_ollama_client):
        from app.errors import LLMConnectionError

        with pytest.raises(LLMConnectionError):
            await mock_ollama_client.chat(
                messages=[{"role": "user", "content": "Hello"}],
                model="qwen3:8b-gpu",
            )

    async def test_list_models(self, mock_ollama_client):
        models = await mock_ollama_client.list_models()
        assert len(models) > 0
        assert models[0]["name"] == "qwen3:8b-gpu"


class TestWorkflowIntegration:
    """Integration test — CodingWorkflow backed by mock Ollama server."""

    async def test_coding_workflow_completes(self, mock_ollama_client):
        from app.workflows.coding import CodingWorkflow

        wf = CodingWorkflow()
        wf.llm = mock_ollama_client
        result = await wf.execute("Build a hello world app", {"language": "python"})
        assert result["status"] == "completed"
        assert "phases" in result
        assert "plan" in result["phases"]


class TestConsensusIntegration:
    """Integration test — ConsensusEngine backed by mock Ollama server."""

    async def test_consensus_run_completes(self, mock_ollama_client):
        from app.consensus.engine import ConsensusEngine

        engine = ConsensusEngine(llm_client=mock_ollama_client)
        session = await engine.run_consensus(
            task="Evaluate the impact of AI on software development",
            max_rounds=3,
        )
        assert session.status == "completed"
        assert session.final_synthesis == "mock output"
