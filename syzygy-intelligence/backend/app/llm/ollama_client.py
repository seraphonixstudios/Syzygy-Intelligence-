"""Ollama LLM client for local model inference."""

from __future__ import annotations

from typing import Any, Optional

import httpx

from app.config import settings


class OllamaClient:
    """Async client for Ollama API."""

    def __init__(self, base_url: str = "", default_model: str = ""):
        self.base_url = (base_url or settings.ollama_base_url).rstrip("/")
        self.default_model = default_model or settings.default_model
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(base_url=self.base_url, timeout=120.0)
        return self._client

    async def generate(
        self,
        prompt: str,
        system: str = "",
        model: str = "",
        temperature: float = 0.7,
        max_tokens: int = 2048,
        stream: bool = False,
    ) -> str:
        """Generate text using Ollama's generate endpoint."""
        client = await self._get_client()
        model = model or self.default_model

        payload = {
            "model": model,
            "prompt": prompt,
            "system": system,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
            "stream": stream,
        }

        try:
            response = await client.post("/api/generate", json=payload)
            response.raise_for_status()

            if stream:
                return await self._handle_stream(response)

            data = response.json()
            return data.get("response", "")

        except httpx.HTTPStatusError as e:
            return f"[Ollama error {e.response.status_code}: {e.response.text[:200]}]"
        except httpx.RequestError as e:
            return f"[Ollama connection error: {e}]"

    async def chat(
        self,
        messages: list[dict[str, str]],
        model: str = "",
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> str:
        """Chat completion via Ollama."""
        client = await self._get_client()
        model = model or self.default_model

        payload = {
            "model": model,
            "messages": messages,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        }

        try:
            response = await client.post("/api/chat", json=payload)
            response.raise_for_status()
            data = response.json()
            return data.get("message", {}).get("content", "")
        except httpx.HTTPStatusError as e:
            return f"[Ollama error {e.response.status_code}]"
        except httpx.RequestError as e:
            return f"[Ollama connection error: {e}]"

    async def list_models(self) -> list[dict[str, Any]]:
        """List available models from Ollama."""
        client = await self._get_client()
        try:
            response = await client.get("/api/tags")
            response.raise_for_status()
            return response.json().get("models", [])
        except Exception:
            return []

    async def _handle_stream(self, response: httpx.Response) -> str:
        full_response = ""
        async for line in response.aiter_lines():
            if line:
                import json
                try:
                    data = json.loads(line)
                    full_response += data.get("response", "")
                    if data.get("done"):
                        break
                except json.JSONDecodeError:
                    continue
        return full_response

    async def close(self):
        if self._client:
            await self._client.aclose()
            self._client = None
