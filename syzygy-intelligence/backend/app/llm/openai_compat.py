"""OpenAI-compatible API client — works with OpenAI, Anthropic, Groq, Together AI, OpenCode, etc."""

from __future__ import annotations

from typing import Any

import httpx

from app.config import settings
from app.errors import LLMConnectionError
from app.logging_setup import logger


class OpenAICompatClient:
    """Client for any OpenAI-compatible API endpoint.

    Supports any provider that exposes an OpenAI-compatible /v1/chat/completions
    endpoint — including OpenAI, Anthropic, Groq, Together AI, OpenCode, local
    inference servers, and more.
    """

    def __init__(
        self,
        base_url: str = "",
        api_key: str = "",
        default_model: str = "",
        timeout: float = 120.0,
    ):
        self.base_url = (base_url or settings.openai_compat_base_url).rstrip("/")
        self.api_key = api_key or settings.openai_compat_api_key
        self.default_model = default_model or settings.openai_compat_default_model
        self.timeout = timeout
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=self.timeout)
        return self._client

    async def generate(
        self,
        prompt: str,
        system: str = "",
        model: str = "",
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> str:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        return await self.chat(
            messages=messages,
            model=model or self.default_model,
            temperature=temperature,
            max_tokens=max_tokens,
        )

    async def chat(
        self,
        messages: list[dict[str, str]],
        model: str = "",
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> str:
        client = await self._get_client()
        try:
            resp = await client.post(
                f"{self.base_url}/v1/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}"} if self.api_key else {},
                json={
                    "model": model or self.default_model,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                },
            )
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"]
        except httpx.HTTPStatusError as e:
            raise LLMConnectionError(
                model or self.default_model,
                f"HTTP {e.response.status_code}: {e.response.text[:200]}",
            )
        except Exception as e:
            raise LLMConnectionError(model or self.default_model, str(e))

    async def generate_stream(
        self,
        prompt: str,
        system: str = "",
        model: str = "",
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ):
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        client = await self._get_client()
        try:
            async with client.stream(
                "POST",
                f"{self.base_url}/v1/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}"} if self.api_key else {},
                json={
                    "model": model or self.default_model,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                    "stream": True,
                },
            ) as resp:
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    if line.startswith("data: "):
                        chunk = line[6:].strip()
                        if chunk and chunk != "[DONE]":
                            import json
                            try:
                                data = json.loads(chunk)
                                delta = data["choices"][0].get("delta", {})
                                if content := delta.get("content"):
                                    yield content
                            except (json.JSONDecodeError, KeyError, IndexError):
                                continue
        except Exception as e:
            logger.error("OpenAI-compat stream error", error=str(e))
            raise LLMConnectionError(model or self.default_model, str(e))

    async def list_models(self) -> list[dict[str, Any]]:
        client = await self._get_client()
        try:
            resp = await client.get(
                f"{self.base_url}/v1/models",
                headers={"Authorization": f"Bearer {self.api_key}"} if self.api_key else {},
            )
            resp.raise_for_status()
            data = resp.json()
            return [
                {"name": m["id"], "provider": "openai_compat"}
                for m in data.get("data", [])
            ]
        except Exception as e:
            logger.warning("Failed to list models from OpenAI-compat provider", error=str(e))
            return []
