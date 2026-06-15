"""Tests for LLMProvider protocol."""

from __future__ import annotations

from unittest.mock import AsyncMock


class TestLLMProviderProtocol:
    def test_ollama_client_is_provider(self):
        from app.llm.ollama_client import OllamaClient
        from app.llm.protocol import LLMProvider
        c = OllamaClient(base_url="http://test:11434", default_model="m")
        assert isinstance(c, LLMProvider)

    def test_openai_compat_client_is_provider(self):
        from app.llm.openai_compat import OpenAICompatClient
        from app.llm.protocol import LLMProvider
        c = OpenAICompatClient(base_url="http://test", api_key="key", default_model="m")
        assert isinstance(c, LLMProvider)

    def test_custom_class_is_provider(self):
        from app.llm.protocol import LLMProvider

        class GoodProvider:
            async def generate(self, prompt, system="", model="", temperature=0.7, max_tokens=2048):
                return "ok"
            async def chat(self, messages, model="", temperature=0.7, max_tokens=2048):
                return "ok"
            async def generate_stream(self, prompt, system="", model="", temperature=0.7, max_tokens=2048):
                yield "ok"
            async def list_models(self):
                return [{"name": "m"}]

        assert isinstance(GoodProvider(), LLMProvider)

    def test_partial_class_is_not_provider(self):
        from app.llm.protocol import LLMProvider

        class BadProvider:
            async def generate(self, prompt, **kwargs):
                return "ok"

        assert not isinstance(BadProvider(), LLMProvider)

    def test_empty_class_is_not_provider(self):
        from app.llm.protocol import LLMProvider

        class Empty:
            pass

        assert not isinstance(Empty(), LLMProvider)
