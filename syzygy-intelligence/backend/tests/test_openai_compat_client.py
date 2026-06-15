"""Tests for OpenAICompatClient — the HTTP client, not the API route."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.errors import LLMConnectionError


@pytest.fixture
def client():
    from app.llm.openai_compat import OpenAICompatClient
    with (
        patch("app.llm.openai_compat.settings") as ms,
    ):
        ms.openai_compat_base_url = "http://test:8000"
        ms.openai_compat_api_key = "test-key"
        ms.openai_compat_default_model = "gpt-4"
        yield OpenAICompatClient()


class TestInit:
    def test_uses_settings_defaults(self):
        from app.llm.openai_compat import OpenAICompatClient
        with patch("app.llm.openai_compat.settings") as ms:
            ms.openai_compat_base_url = "http://default:8000"
            ms.openai_compat_api_key = "default-key"
            ms.openai_compat_default_model = "default-model"
            c = OpenAICompatClient()
            assert c.base_url == "http://default:8000"
            assert c.api_key == "default-key"
            assert c.default_model == "default-model"

    def test_overrides_settings(self):
        from app.llm.openai_compat import OpenAICompatClient
        c = OpenAICompatClient(base_url="http://custom", api_key="custom-key", default_model="custom-model")
        assert c.base_url == "http://custom"
        assert c.api_key == "custom-key"
        assert c.default_model == "custom-model"

    def test_strips_trailing_slash(self):
        from app.llm.openai_compat import OpenAICompatClient
        with patch("app.llm.openai_compat.settings") as ms:
            ms.openai_compat_base_url = "http://test:8000/"
            c = OpenAICompatClient()
            assert c.base_url == "http://test:8000"

    def test_default_timeout(self):
        from app.llm.openai_compat import OpenAICompatClient
        with patch("app.llm.openai_compat.settings") as ms:
            ms.openai_compat_base_url = "http://test:8000"
            ms.openai_compat_api_key = ""
            ms.openai_compat_default_model = ""
            c = OpenAICompatClient()
            assert c.timeout == 120.0


class TestGetClient:
    @pytest.mark.asyncio
    async def test_creates_client_on_first_call(self, client):
        c = await client._get_client()
        assert c is not None
        assert client._client is c

    @pytest.mark.asyncio
    async def test_reuses_client(self, client):
        c1 = await client._get_client()
        c2 = await client._get_client()
        assert c1 is c2


class TestGenerate:
    @pytest.mark.asyncio
    async def test_generate_calls_chat(self, client):
        client.chat = AsyncMock(return_value="response text")
        result = await client.generate(prompt="Hello", system="Be helpful")
        client.chat.assert_awaited_once()
        kwargs = client.chat.call_args[1]
        assert kwargs["messages"] == [{"role": "system", "content": "Be helpful"}, {"role": "user", "content": "Hello"}]
        assert result == "response text"

    @pytest.mark.asyncio
    async def test_generate_without_system(self, client):
        client.chat = AsyncMock(return_value="response")
        result = await client.generate(prompt="Hello")
        kwargs = client.chat.call_args[1]
        assert kwargs["messages"] == [{"role": "user", "content": "Hello"}]
        assert result == "response"

    @pytest.mark.asyncio
    async def test_generate_passes_model(self, client):
        client.chat = AsyncMock(return_value="response")
        await client.generate(prompt="Hi", model="gpt-4-turbo")
        _, kwargs = client.chat.call_args
        assert kwargs["model"] == "gpt-4-turbo"


class TestChat:
    @pytest.mark.asyncio
    async def test_returns_content(self, client):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "choices": [{"message": {"content": "Hello from AI"}}]
        }
        client._client = AsyncMock()
        client._client.post = AsyncMock(return_value=mock_resp)

        result = await client.chat(messages=[{"role": "user", "content": "Hi"}])
        assert result == "Hello from AI"

    @pytest.mark.asyncio
    async def test_sends_correct_request(self, client):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"choices": [{"message": {"content": "ok"}}]}
        client._client = AsyncMock()
        client._client.post = AsyncMock(return_value=mock_resp)

        await client.chat(
            messages=[{"role": "user", "content": "Hi"}],
            model="gpt-4",
            temperature=0.5,
            max_tokens=100,
        )
        client._client.post.assert_awaited_once()
        url = client._client.post.call_args[0][0]
        json_data = client._client.post.call_args[1]["json"]
        assert "v1/chat/completions" in url
        assert json_data["model"] == "gpt-4"
        assert json_data["temperature"] == 0.5
        assert json_data["max_tokens"] == 100

    @pytest.mark.asyncio
    async def test_sends_auth_header(self, client):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"choices": [{"message": {"content": "ok"}}]}
        client._client = AsyncMock()
        client._client.post = AsyncMock(return_value=mock_resp)

        await client.chat(messages=[{"role": "user", "content": "Hi"}])
        headers = client._client.post.call_args[1]["headers"]
        assert headers["Authorization"] == "Bearer test-key"

    @pytest.mark.asyncio
    async def test_skips_auth_header_when_no_key(self, client):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"choices": [{"message": {"content": "ok"}}]}
        client._client = AsyncMock()
        client._client.post = AsyncMock(return_value=mock_resp)
        client.api_key = ""

        await client.chat(messages=[{"role": "user", "content": "Hi"}])
        headers = client._client.post.call_args[1]["headers"]
        assert headers == {}

    @pytest.mark.asyncio
    async def test_uses_default_model(self, client):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"choices": [{"message": {"content": "ok"}}]}
        client._client = AsyncMock()
        client._client.post = AsyncMock(return_value=mock_resp)

        await client.chat(messages=[{"role": "user", "content": "Hi"}], model="")
        json_data = client._client.post.call_args[1]["json"]
        assert json_data["model"] == "gpt-4"

    @pytest.mark.asyncio
    async def test_raises_on_http_error(self, client):
        mock_resp = MagicMock()
        mock_resp.status_code = 401
        mock_resp.text = "Unauthorized"
        mock_resp.raise_for_status.side_effect = Exception("401 Unauthorized: Unauthorized")
        client._client = AsyncMock()
        client._client.post = AsyncMock(return_value=mock_resp)

        with pytest.raises(LLMConnectionError) as exc:
            await client.chat(messages=[{"role": "user", "content": "Hi"}])
        assert "401" in str(exc.value)

    @pytest.mark.asyncio
    async def test_raises_on_network_error(self, client):
        client._client = AsyncMock()
        client._client.post = AsyncMock(side_effect=ConnectionError("DNS failure"))

        with pytest.raises(LLMConnectionError) as exc:
            await client.chat(messages=[{"role": "user", "content": "Hi"}])


class TestGenerateStream:
    def _mock_stream_client(self, client, lines):
        async def mock_aiter_lines():
            for line in lines:
                yield line

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.aiter_lines = mock_aiter_lines

        mock_cm = MagicMock()
        mock_cm.__aenter__ = AsyncMock(return_value=mock_resp)
        mock_cm.__aexit__ = AsyncMock()

        client._client = MagicMock()
        client._client.stream = MagicMock(return_value=mock_cm)
        return client

    @pytest.mark.asyncio
    async def test_yields_content_chunks(self, client):
        self._mock_stream_client(client, [
            'data: {"choices": [{"delta": {"content": "Hello"}}]}',
            'data: {"choices": [{"delta": {"content": " World"}}]}',
            "data: [DONE]",
        ])
        result = []
        async for chunk in client.generate_stream(prompt="Hi"):
            result.append(chunk)
        assert result == ["Hello", " World"]

    @pytest.mark.asyncio
    async def test_skips_non_data_lines(self, client):
        self._mock_stream_client(client, [
            ": keep-alive",
            'data: {"choices": [{"delta": {"content": "Hi"}}]}',
            "data: [DONE]",
        ])
        result = []
        async for chunk in client.generate_stream(prompt="Hi"):
            result.append(chunk)
        assert result == ["Hi"]

    @pytest.mark.asyncio
    async def test_handles_malformed_json(self, client):
        self._mock_stream_client(client, [
            "data: not-json",
            'data: {"choices": [{"delta": {"content": "ok"}}]}',
            "data: [DONE]",
        ])
        result = []
        async for chunk in client.generate_stream(prompt="Hi"):
            result.append(chunk)
        assert result == ["ok"]

    @pytest.mark.asyncio
    async def test_skips_chunks_without_content_delta(self, client):
        self._mock_stream_client(client, [
            'data: {"choices": [{"delta": {}}]}',
            'data: {"choices": [{"delta": {"content": "Hi"}}]}',
            "data: [DONE]",
        ])
        result = []
        async for chunk in client.generate_stream(prompt="Hi"):
            result.append(chunk)
        assert result == ["Hi"]

    @pytest.mark.asyncio
    async def test_raises_on_stream_error(self, client):
        client._client = AsyncMock()
        client._client.stream.side_effect = ConnectionError("Stream failed")

        with pytest.raises(LLMConnectionError):
            async for _ in client.generate_stream(prompt="Hi"):
                pass

    @pytest.mark.asyncio
    async def test_includes_system_in_messages(self, client):
        self._mock_stream_client(client, [
            'data: {"choices": [{"delta": {"content": "ok"}}]}',
            "data: [DONE]",
        ])
        async for _ in client.generate_stream(prompt="Hi", system="Be concise"):
            pass
        json_data = client._client.stream.call_args[1]["json"]
        messages = json_data["messages"]
        assert messages[0] == {"role": "system", "content": "Be concise"}
        assert messages[1] == {"role": "user", "content": "Hi"}


class TestListModels:
    @pytest.mark.asyncio
    async def test_returns_models(self, client):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "data": [
                {"id": "gpt-4", "object": "model"},
                {"id": "gpt-3.5-turbo", "object": "model"},
            ]
        }
        client._client = AsyncMock()
        client._client.get = AsyncMock(return_value=mock_resp)

        models = await client.list_models()
        assert len(models) == 2
        assert models[0]["name"] == "gpt-4"
        assert models[0]["provider"] == "openai_compat"

    @pytest.mark.asyncio
    async def test_returns_empty_on_error(self, client):
        client._client = AsyncMock()
        client._client.get = AsyncMock(side_effect=ConnectionError("fail"))

        models = await client.list_models()
        assert models == []

    @pytest.mark.asyncio
    async def test_returns_empty_on_empty_data(self, client):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"data": []}
        client._client = AsyncMock()
        client._client.get = AsyncMock(return_value=mock_resp)

        models = await client.list_models()
        assert models == []
