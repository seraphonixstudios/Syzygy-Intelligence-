"""Tests for the Ollama LLM client."""
from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from app.errors import LLMConnectionError
from app.llm.ollama_client import OllamaClient


@pytest.fixture
def mock_httpx_client():
    client = MagicMock(spec=httpx.AsyncClient)
    return client


class TestInit:
    def test_defaults_from_settings(self):
        with patch("app.llm.ollama_client.settings") as s:
            s.ollama_base_url = "http://default:11434"
            s.default_model = "default-model"
            c = OllamaClient()
            assert c.base_url == "http://default:11434"
            assert c.default_model == "default-model"

    def test_custom_values(self):
        c = OllamaClient(base_url="http://custom:11434/", default_model="custom-model")
        assert c.base_url == "http://custom:11434"
        assert c.default_model == "custom-model"

    def test_strips_trailing_slash(self):
        c = OllamaClient(base_url="http://host:11434/")
        assert c.base_url == "http://host:11434"


class TestGetClient:
    @pytest.mark.asyncio
    async def test_lazy_creation(self):
        c = OllamaClient(base_url="http://test:11434", default_model="m")
        client = await c._get_client()
        assert client is not None
        assert c._client is client

    @pytest.mark.asyncio
    async def test_returns_cached(self):
        c = OllamaClient(base_url="http://test:11434", default_model="m")
        first = await c._get_client()
        second = await c._get_client()
        assert first is second


class TestGenerate:
    @pytest.mark.asyncio
    async def test_generates_text(self, mock_httpx_client):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b'{"response": "Hello world"}'
        mock_httpx_client.post = AsyncMock(return_value=mock_response)

        c = OllamaClient(base_url="http://test:11434", default_model="m")
        c._client = mock_httpx_client
        result = await c.generate("Say hello")
        assert result == "Hello world"

    @pytest.mark.asyncio
    async def test_uses_custom_model(self, mock_httpx_client):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b'{"response": "ok"}'
        mock_httpx_client.post = AsyncMock(return_value=mock_response)

        c = OllamaClient(base_url="http://test:11434", default_model="default")
        c._client = mock_httpx_client
        await c.generate("test", model="custom")
        call_kwargs = mock_httpx_client.post.call_args[1]
        assert call_kwargs["json"]["model"] == "custom"

    @pytest.mark.asyncio
    async def test_includes_options(self, mock_httpx_client):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b'{"response": "ok"}'
        mock_httpx_client.post = AsyncMock(return_value=mock_response)

        c = OllamaClient(base_url="http://test:11434", default_model="m")
        c._client = mock_httpx_client
        await c.generate("test", temperature=0.5, max_tokens=1024)
        opts = mock_httpx_client.post.call_args[1]["json"]["options"]
        assert opts["temperature"] == 0.5
        assert opts["num_predict"] == 1024

    @pytest.mark.asyncio
    async def test_system_prompt_included(self, mock_httpx_client):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b'{"response": "ok"}'
        mock_httpx_client.post = AsyncMock(return_value=mock_response)

        c = OllamaClient(base_url="http://test:11434", default_model="m")
        c._client = mock_httpx_client
        await c.generate("test", system="Be helpful")
        payload = mock_httpx_client.post.call_args[1]["json"]
        assert payload["system"] == "Be helpful"

    @pytest.mark.asyncio
    async def test_handles_stream_flag(self, mock_httpx_client):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.aiter_lines.return_value = async_gen(
            ['{"response":"A","done":false}', '{"response":"B","done":true}']
        )
        mock_httpx_client.post = AsyncMock(return_value=mock_response)

        c = OllamaClient(base_url="http://test:11434", default_model="m")
        c._client = mock_httpx_client
        result = await c.generate("test", stream=True)
        assert result == "AB"

    @pytest.mark.asyncio
    async def test_raises_on_http_4xx(self, mock_httpx_client):
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.text = "Not Found"
        exc = httpx.HTTPStatusError("404", request=MagicMock(), response=mock_response)
        mock_httpx_client.post = AsyncMock(side_effect=exc)

        c = OllamaClient(base_url="http://test:11434", default_model="m")
        c._client = mock_httpx_client
        with pytest.raises(LLMConnectionError):
            await c.generate("test")

    @pytest.mark.asyncio
    async def test_raises_on_connection_error(self, mock_httpx_client):
        mock_httpx_client.post = AsyncMock(
            side_effect=httpx.RequestError("connection refused", request=MagicMock())
        )

        c = OllamaClient(base_url="http://test:11434", default_model="m")
        c._client = mock_httpx_client
        with pytest.raises(LLMConnectionError):
            await c.generate("test")


class TestGenerateStream:
    @pytest.mark.asyncio
    async def test_streams_tokens(self):
        lines = [
            '{"response":"Hello","done":false}',
            '{"response":" World","done":false}',
            '{"response":"","done":true}',
        ]

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.aiter_lines.return_value = async_gen(lines)

        mock_httpx = MagicMock()
        mock_httpx.__aenter__.return_value = mock_response
        mock_httpx.__aexit__ = AsyncMock()

        mock_client = MagicMock(spec=httpx.AsyncClient)
        mock_client.stream.return_value = mock_httpx

        c = OllamaClient(base_url="http://test:11434", default_model="m")
        c._client = mock_client

        tokens = []
        async for token in c.generate_stream("test"):
            tokens.append(token)
        assert tokens == ["Hello", " World"]

    @pytest.mark.asyncio
    async def test_skips_empty_lines(self):
        lines = [
            '',
            '{"response":"Hi","done":false}',
            '',
            '{"response":"","done":true}',
        ]

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.aiter_lines.return_value = async_gen(lines)

        mock_httpx = MagicMock()
        mock_httpx.__aenter__.return_value = mock_response
        mock_httpx.__aexit__ = AsyncMock()

        mock_client = MagicMock(spec=httpx.AsyncClient)
        mock_client.stream.return_value = mock_httpx

        c = OllamaClient(base_url="http://test:11434", default_model="m")
        c._client = mock_client

        tokens = []
        async for token in c.generate_stream("test"):
            tokens.append(token)
        assert tokens == ["Hi"]

    @pytest.mark.asyncio
    async def test_raises_on_http_error(self):
        mock_response = MagicMock()
        mock_response.status_code = 400
        exc = httpx.HTTPStatusError("400", request=MagicMock(), response=mock_response)

        mock_httpx = MagicMock()
        mock_httpx.__aenter__.side_effect = exc

        mock_client = MagicMock(spec=httpx.AsyncClient)
        mock_client.stream.return_value = mock_httpx

        c = OllamaClient(base_url="http://test:11434", default_model="m")
        c._client = mock_client

        with pytest.raises(LLMConnectionError):
            async for _ in c.generate_stream("test"):
                pass

    @pytest.mark.asyncio
    async def test_raises_on_connection_error(self):
        mock_httpx = MagicMock()
        mock_httpx.__aenter__.side_effect = httpx.RequestError("fail", request=MagicMock())

        mock_client = MagicMock(spec=httpx.AsyncClient)
        mock_client.stream.return_value = mock_httpx

        c = OllamaClient(base_url="http://test:11434", default_model="m")
        c._client = mock_client

        with pytest.raises(LLMConnectionError):
            async for _ in c.generate_stream("test"):
                pass


class TestChat:
    @pytest.mark.asyncio
    async def test_chat_returns_content(self, mock_httpx_client):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b'{"message": {"content": "Chat response"}}'
        mock_httpx_client.post = AsyncMock(return_value=mock_response)

        c = OllamaClient(base_url="http://test:11434", default_model="m")
        c._client = mock_httpx_client
        result = await c.chat([{"role": "user", "content": "Hi"}])
        assert result == "Chat response"

    @pytest.mark.asyncio
    async def test_includes_messages(self, mock_httpx_client):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b'{"message": {"content": "ok"}}'
        mock_httpx_client.post = AsyncMock(return_value=mock_response)

        c = OllamaClient(base_url="http://test:11434", default_model="m")
        c._client = mock_httpx_client
        msgs = [{"role": "system", "content": "Be nice"}, {"role": "user", "content": "Hi"}]
        await c.chat(msgs)
        payload = mock_httpx_client.post.call_args[1]["json"]
        assert payload["messages"] == msgs

    @pytest.mark.asyncio
    async def test_raises_on_error(self, mock_httpx_client):
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Server Error"
        exc = httpx.HTTPStatusError("500", request=MagicMock(), response=mock_response)
        mock_httpx_client.post = AsyncMock(side_effect=exc)

        c = OllamaClient(base_url="http://test:11434", default_model="m")
        c._client = mock_httpx_client
        with pytest.raises(LLMConnectionError):
            await c.chat([{"role": "user", "content": "Hi"}])


class TestGenerateMulti:
    @pytest.mark.asyncio
    async def test_queries_multiple_models(self):
        c = OllamaClient(base_url="http://test:11434", default_model="default")
        c.generate = AsyncMock(side_effect=lambda **kw: f"result-{kw['model']}")
        results = await c.generate_multi("test", models=["a", "b"])
        assert results == {"a": "result-a", "b": "result-b"}

    @pytest.mark.asyncio
    async def test_handles_model_error(self):
        c = OllamaClient(base_url="http://test:11434", default_model="default")
        c.generate = AsyncMock(side_effect=[LLMConnectionError("m1", "fail"), "ok"])
        results = await c.generate_multi("test", models=["m1", "m2"])
        assert "[Error:" in results["m1"]
        assert results["m2"] == "ok"


class TestListModels:
    @pytest.mark.asyncio
    async def test_lists_models(self, mock_httpx_client):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"models": [{"name": "qwen3"}]}
        mock_httpx_client.get = AsyncMock(return_value=mock_response)

        c = OllamaClient(base_url="http://test:11434", default_model="m")
        c._client = mock_httpx_client
        models = await c.list_models()
        assert len(models) == 1
        assert models[0]["name"] == "qwen3"

    @pytest.mark.asyncio
    async def test_returns_empty_on_error(self, mock_httpx_client):
        mock_httpx_client.get = AsyncMock(side_effect=RuntimeError("fail"))

        c = OllamaClient(base_url="http://test:11434", default_model="m")
        c._client = mock_httpx_client
        models = await c.list_models()
        assert models == []


class TestParseJson:
    def test_parses_valid(self):
        c = OllamaClient(base_url="http://test:11434", default_model="m")
        resp = MagicMock()
        resp.content = b'{"key": "value"}'
        assert c._parse_json(resp) == {"key": "value"}

    def test_parses_trailing_data(self):
        c = OllamaClient(base_url="http://test:11434", default_model="m")
        resp = MagicMock()
        resp.content = b'{"key": "value"}\ntrailing data'
        assert c._parse_json(resp) == {"key": "value"}

    def test_finds_first_brace_json(self):
        c = OllamaClient(base_url="http://test:11434", default_model="m")
        resp = MagicMock()
        resp.content = b'prefix\n{"a": 1}\nsuffix'
        assert c._parse_json(resp) == {"a": 1}

    def test_finds_complete_top_level_json(self):
        c = OllamaClient(base_url="http://test:11434", default_model="m")
        resp = MagicMock()
        resp.content = b'text {"nested": {"inner": 1}} more'
        assert c._parse_json(resp) == {"nested": {"inner": 1}}

    def test_raises_on_no_json(self):
        c = OllamaClient(base_url="http://test:11434", default_model="m")
        resp = MagicMock()
        resp.content = b"plain text no braces"
        with pytest.raises(json.JSONDecodeError):
            c._parse_json(resp)


class TestClose:
    @pytest.mark.asyncio
    async def test_closes_client(self):
        c = OllamaClient(base_url="http://test:11434", default_model="m")
        mock = AsyncMock()
        c._client = mock
        await c.close()
        mock.aclose.assert_awaited_once()
        assert c._client is None

    @pytest.mark.asyncio
    async def test_noop_when_no_client(self):
        c = OllamaClient(base_url="http://test:11434", default_model="m")
        await c.close()


# ── helper ──

async def async_gen(items):
    for item in items:
        yield item
