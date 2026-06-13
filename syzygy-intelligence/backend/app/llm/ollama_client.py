"""Ollama LLM client for local model inference — with structured logging and proper exceptions."""

from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncGenerator
from typing import Any

import httpx

from app.config import settings
from app.errors import LLMConnectionError
from app.logging_setup import logger


class OllamaClient:
    """Async client for Ollama API with structured error handling."""

    def __init__(self, base_url: str = "", default_model: str = ""):
        self.base_url = (base_url or settings.ollama_base_url).rstrip("/")
        self.default_model = default_model or settings.default_model
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=300.0,
            )
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
                "num_ctx": 2048,
            },
            "stream": stream,
        }

        logger.info(
            "Ollama generate call",
            model=model,
            prompt_len=len(prompt),
            temperature=temperature,
        )

        try:
            response = await client.post("/api/generate", json=payload)
            response.raise_for_status()

            if stream:
                return await self._handle_stream(response)

            data = self._parse_json(response)
            result = data.get("response", "")
            logger.info(
                "Ollama generate success",
                model=model,
                response_len=len(result),
            )
            return result  # type: ignore[no-any-return]

        except httpx.HTTPStatusError as e:
            status = e.response.status_code
            body = e.response.text[:300]
            logger.error(
                "Ollama HTTP error",
                model=model,
                status=status,
                body=body,
            )
            raise LLMConnectionError(
                model=model,
                original_error=f"HTTP {status}: {body}",
            )
        except httpx.RequestError as e:
            logger.error(
                "Ollama connection error",
                model=model,
                error=str(e),
            )
            raise LLMConnectionError(
                model=model,
                original_error=str(e),
            )

    async def generate_stream(
        self,
        prompt: str,
        system: str = "",
        model: str = "",
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> AsyncGenerator[str, None]:
        """Stream tokens from Ollama's generate endpoint."""
        client = await self._get_client()
        model = model or self.default_model
        payload = {
            "model": model,
            "prompt": prompt,
            "system": system,
            "stream": True,
            "options": {"temperature": temperature, "num_predict": max_tokens, "num_ctx": 2048},
        }
        logger.info("Ollama generate stream start", model=model)
        try:
            async with client.stream("POST", "/api/generate", json=payload) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if line:
                        try:
                            data = json.loads(line)
                            token = data.get("response", "")
                            if token:
                                yield token
                            if data.get("done"):
                                break
                        except json.JSONDecodeError:
                            continue
            logger.info("Ollama generate stream complete", model=model)
        except httpx.HTTPStatusError as e:
            logger.error("Ollama stream HTTP error", model=model, status=e.response.status_code)
            raise LLMConnectionError(model=model, original_error=f"HTTP {e.response.status_code}")
        except httpx.RequestError as e:
            logger.error("Ollama stream connection error", model=model, error=str(e))
            raise LLMConnectionError(model=model, original_error=str(e))

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
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
                "num_ctx": 2048,
            },
        }

        logger.info(
            "Ollama chat call",
            model=model,
            messages=len(messages),
            temperature=temperature,
        )

        try:
            response = await client.post("/api/chat", json=payload)
            response.raise_for_status()
            data = self._parse_json(response)
            result = data.get("message", {}).get("content", "")
            logger.info(
                "Ollama chat success",
                model=model,
                response_len=len(result),
            )
            return result  # type: ignore[no-any-return]
        except httpx.HTTPStatusError as e:
            status = e.response.status_code
            body = e.response.text[:300]
            logger.error(
                "Ollama HTTP error",
                model=model,
                status=status,
                body=body,
            )
            raise LLMConnectionError(
                model=model,
                original_error=f"HTTP {status}: {body}",
            )
        except httpx.RequestError as e:
            logger.error(
                "Ollama connection error",
                model=model,
                error=str(e),
            )
            raise LLMConnectionError(
                model=model,
                original_error=str(e),
            )

    async def generate_multi(
        self,
        prompt: str,
        models: list[str],
        system: str = "",
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> dict[str, str]:
        """Query multiple models in parallel and return results keyed by model name."""

        async def _query(model: str) -> tuple[str, str]:
            try:
                result = await self.generate(
                    prompt=prompt,
                    system=system,
                    model=model,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
                return model, result
            except LLMConnectionError as e:
                return model, f"[Error: {e.message}]"

        results = await asyncio.gather(*[_query(m) for m in models])
        return dict(results)

    async def list_models(self) -> list[dict[str, Any]]:
        """List available models from Ollama."""
        client = await self._get_client()
        try:
            response = await client.get("/api/tags")
            response.raise_for_status()
            models = response.json().get("models", [])
            logger.info("Ollama models listed", count=len(models))
            return models  # type: ignore
        except Exception as e:
            logger.error("Failed to list Ollama models", error=str(e))
            return []

    def _parse_json(self, response: httpx.Response) -> dict[str, Any]:
        """Parse JSON response, handling trailing data gracefully."""
        raw = response.content.decode("utf-8", errors="replace").strip()
        try:
            return json.loads(raw)  # type: ignore
        except json.JSONDecodeError:
            first_brace = raw.find("{")
            last_brace = raw.rfind("}")
            if first_brace >= 0 and last_brace > first_brace:
                candidate = raw[first_brace:last_brace + 1]
                try:
                    return json.loads(candidate)  # type: ignore
                except json.JSONDecodeError:
                    # Last resort: try to find a complete top-level JSON object
                    depth = 0
                    start = -1
                    for i, ch in enumerate(raw):
                        if ch == "{":
                            if start < 0:
                                start = i
                            depth += 1
                        elif ch == "}":
                            depth -= 1
                            if depth == 0 and start >= 0:
                                return json.loads(raw[start:i + 1])  # type: ignore
                    raise
            raise

    async def _handle_stream(self, response: httpx.Response) -> str:
        full_response = ""
        async for line in response.aiter_lines():
            if line:
                try:
                    data = json.loads(line)
                    full_response += data.get("response", "")
                    if data.get("done"):
                        break
                except json.JSONDecodeError:
                    continue
        return full_response

    async def close(self) -> None:
        if self._client:
            await self._client.aclose()
            self._client = None
