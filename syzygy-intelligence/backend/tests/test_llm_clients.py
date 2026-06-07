"""Tests for OllamaClient and LiteLLMClient."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch


class TestOllamaClient:
    @pytest.fixture
    def client(self):
        with patch("app.llm.ollama_client.settings") as ms:
            ms.ollama_base_url = "http://localhost:11434"
            ms.default_model = "qwen3:8b-gpu"
            from app.llm.ollama_client import OllamaClient
            yield OllamaClient()

    @pytest.mark.asyncio
    async def test_init_defaults(self, client):
        assert "11434" in client.base_url
        assert client.default_model == "qwen3:8b-gpu"
        assert client._client is None

    @pytest.mark.asyncio
    async def test_custom_init(self):
        from app.llm.ollama_client import OllamaClient
        c = OllamaClient(base_url="http://custom:11434", default_model="test")
        assert "custom" in c.base_url
        assert c.default_model == "test"

    @pytest.mark.asyncio
    async def test_generate_success(self, client):
        mock_resp = MagicMock()
        mock_resp.content = b'{"response":"Hello!"}'
        mock_resp.json = MagicMock(return_value={"response": "Hello!"})
        mock_resp.raise_for_status = MagicMock()
        mock_http = AsyncMock()
        mock_http.post = AsyncMock(return_value=mock_resp)
        client._client = mock_http

        result = await client.generate("hi")
        assert result == "Hello!"

    @pytest.mark.asyncio
    async def test_generate_with_system(self, client):
        mock_resp = MagicMock()
        mock_resp.content = b'{"response":"OK"}'
        mock_resp.json = MagicMock(return_value={"response": "OK"})
        mock_resp.raise_for_status = MagicMock()
        mock_http = AsyncMock()
        mock_http.post = AsyncMock(return_value=mock_resp)
        client._client = mock_http

        await client.generate("hi", system="You are a robot")
        call = mock_http.post.call_args
        assert call[1]["json"]["system"] == "You are a robot"

    @pytest.mark.asyncio
    async def test_generate_http_error(self, client):
        import httpx
        from app.errors import LLMConnectionError
        mock_resp = MagicMock(spec=httpx.Response)
        mock_resp.raise_for_status = MagicMock(
            side_effect=httpx.HTTPStatusError("HTTP 500", request=MagicMock(), response=mock_resp)
        )
        mock_resp.status_code = 500
        mock_resp.text = "Internal Server Error"
        mock_http = AsyncMock()
        mock_http.post = AsyncMock(return_value=mock_resp)
        client._client = mock_http

        with pytest.raises(LLMConnectionError) as exc:
            await client.generate("hi")
        assert "500" in str(exc.value)

    @pytest.mark.asyncio
    async def test_generate_connection_error(self, client):
        import httpx
        from app.errors import LLMConnectionError
        mock_http = AsyncMock()
        mock_http.post = AsyncMock(side_effect=httpx.RequestError("Connection refused"))
        client._client = mock_http

        with pytest.raises(LLMConnectionError):
            await client.generate("hi")

    @pytest.mark.asyncio
    async def test_chat_success(self, client):
        mock_resp = MagicMock()
        mock_resp.content = b'{"message":{"content":"Hi back"}}'
        mock_resp.json = MagicMock(return_value={"message": {"content": "Hi back"}})
        mock_resp.raise_for_status = MagicMock()
        mock_http = AsyncMock()
        mock_http.post = AsyncMock(return_value=mock_resp)
        client._client = mock_http

        result = await client.chat([{"role": "user", "content": "hello"}])
        assert result == "Hi back"

    @pytest.mark.asyncio
    async def test_list_models_success(self, client):
        mock_resp = MagicMock()
        mock_resp.json = MagicMock(return_value={"models": [{"name": "qwen"}]})
        mock_resp.raise_for_status = MagicMock()
        mock_http = AsyncMock()
        mock_http.get = AsyncMock(return_value=mock_resp)
        client._client = mock_http

        models = await client.list_models()
        assert len(models) == 1
        assert models[0]["name"] == "qwen"

    @pytest.mark.asyncio
    async def test_list_models_error(self, client):
        mock_http = AsyncMock()
        mock_http.get = AsyncMock(side_effect=Exception("fail"))
        client._client = mock_http

        assert await client.list_models() == []

    @pytest.mark.asyncio
    async def test_close(self, client):
        mock_http = AsyncMock()
        client._client = mock_http
        await client.close()
        mock_http.aclose.assert_awaited_once()
        assert client._client is None

    @pytest.mark.asyncio
    async def test_close_no_client(self, client):
        await client.close()
        assert client._client is None


class TestLiteLLMClient:
    @pytest.fixture
    def client(self):
        with patch("app.llm.litellm_client.settings") as ms:
            ms.fallback_model = "gpt-4o-mini"
            ms.litellm_enabled = True
            from app.llm.litellm_client import LiteLLMClient
            yield LiteLLMClient()

    def test_init_defaults(self, client):
        assert client.fallback_model == "gpt-4o-mini"
        assert client._enabled is True

    def test_init_disabled(self):
        with patch("app.llm.litellm_client.settings") as ms:
            ms.fallback_model = "gpt-4"
            ms.litellm_enabled = False
            from app.llm.litellm_client import LiteLLMClient
            c = LiteLLMClient()
            assert c._enabled is False

    @pytest.mark.asyncio
    async def test_generate_disabled(self, client):
        client._enabled = False
        result = await client.generate("prompt")
        assert "disabled" in result

    @pytest.mark.asyncio
    async def test_chat_disabled(self, client):
        client._enabled = False
        result = await client.chat([{"role": "user", "content": "hi"}])
        assert "disabled" in result

    @pytest.mark.asyncio
    async def test_generate_success(self, client):
        pytest.importorskip("litellm")
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Hello!"
        with patch("litellm.acompletion", new=AsyncMock(return_value=mock_response)):
            result = await client.generate("prompt", system="be helpful")
            assert result == "Hello!"

    @pytest.mark.asyncio
    async def test_chat_success(self, client):
        pytest.importorskip("litellm")
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Chat reply"
        with patch("litellm.acompletion", new=AsyncMock(return_value=mock_response)):
            result = await client.chat([{"role": "user", "content": "hi"}])
            assert result == "Chat reply"

    @pytest.mark.asyncio
    async def test_generate_error(self, client):
        pytest.importorskip("litellm")
        with patch("litellm.acompletion", new=AsyncMock(side_effect=Exception("API error"))):
            result = await client.generate("prompt")
            assert "error" in result.lower()

    @pytest.mark.asyncio
    async def test_generate_empty_content(self, client):
        pytest.importorskip("litellm")
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = None
        with patch("litellm.acompletion", new=AsyncMock(return_value=mock_response)):
            result = await client.generate("prompt")
            assert result == ""
