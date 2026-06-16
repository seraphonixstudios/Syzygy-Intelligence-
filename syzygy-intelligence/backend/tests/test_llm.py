"""Tests for LLM factory and LiteLLM client uncovered branches."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestLLMFactory:
    def test_create_ollama_client(self):
        from app.llm import LLMFactory
        with patch("app.llm.ollama_client.settings") as ms:
            ms.ollama_base_url = "http://localhost:11434"
            ms.default_model = "qwen3"
            client = LLMFactory.create_client("ollama")
            from app.llm.ollama_client import OllamaClient
            assert isinstance(client, OllamaClient)

    def test_create_litellm_client(self):
        from app.llm import LLMFactory
        with patch("app.llm.litellm_client.settings") as ms:
            ms.fallback_model = "gpt-4o-mini"
            ms.litellm_enabled = True
            client = LLMFactory.create_client("litellm")
            from app.llm.litellm_client import LiteLLMClient
            assert isinstance(client, LiteLLMClient)

    def test_create_openai_compat_client(self):
        from app.llm import LLMFactory
        with patch("app.llm.openai_compat.settings") as ms:
            ms.openai_compat_base_url = "http://localhost:8000/v1"
            ms.openai_compat_api_key = "test-key"
            ms.openai_compat_default_model = "test-model"
            client = LLMFactory.create_client("openai_compat")
            from app.llm.openai_compat import OpenAICompatClient
            assert isinstance(client, OpenAICompatClient)

    def test_unknown_provider_raises(self):
        from app.llm import LLMFactory
        with pytest.raises(ValueError, match="Unknown provider"):
            LLMFactory.create_client("nonexistent")


class TestLiteLlmClientStream:
    @pytest.fixture
    def client(self):
        with patch("app.llm.litellm_client.settings") as ms:
            ms.fallback_model = "gpt-4o-mini"
            ms.litellm_enabled = True
            from app.llm.litellm_client import LiteLLMClient
            yield LiteLLMClient()

    @pytest.mark.asyncio
    async def test_generate_stream_disabled(self, client):
        client._enabled = False
        gen = client.generate_stream("prompt")
        items = []
        async for item in gen:
            items.append(item)
        assert items == []

    @pytest.mark.asyncio
    async def test_generate_stream_error(self, client):
        with patch("litellm.acompletion", new=AsyncMock(side_effect=Exception("stream failed"))):
            gen = client.generate_stream("prompt")
            items = []
            async for item in gen:
                items.append(item)
            assert items == []

    @pytest.mark.asyncio
    async def test_generate_stream_success(self, client):
        class MockChunk:
            def __init__(self, content):
                self.choices = [MagicMock()]
                self.choices[0].delta.content = content

        class MockAsyncIterable:
            def __init__(self, items):
                self._items = items

            def __aiter__(self):
                return self

            async def __anext__(self):
                if not self._items:
                    raise StopAsyncIteration
                return self._items.pop(0)

        mock_response = MockAsyncIterable([MockChunk("Hello"), MockChunk(" World")])
        with patch("litellm.acompletion", new=AsyncMock(return_value=mock_response)):
            gen = client.generate_stream("prompt")
            tokens = []
            async for token in gen:
                tokens.append(token)
            assert tokens == ["Hello", " World"]

    @pytest.mark.asyncio
    async def test_generate_with_system_prompt(self, client):
        class MockChunk:
            def __init__(self, content):
                self.choices = [MagicMock()]
                self.choices[0].delta.content = content

        class MockAsyncIterable:
            def __init__(self, items):
                self._items = items
            def __aiter__(self):
                return self
            async def __anext__(self):
                if not self._items:
                    raise StopAsyncIteration
                return self._items.pop(0)

        mock_response = MockAsyncIterable([MockChunk("Reply")])
        with patch("litellm.acompletion", new=AsyncMock(return_value=mock_response)):
            gen = client.generate_stream("prompt", system="Be helpful")
            tokens = []
            async for token in gen:
                tokens.append(token)
            assert tokens == ["Reply"]

    @pytest.mark.asyncio
    async def test_list_models(self, client):
        models = await client.list_models()
        assert models == [{"name": "gpt-4o-mini", "provider": "litellm"}]
