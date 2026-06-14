"""LiteLLM client for optional API fallback to OpenAI/Anthropic/etc."""

from __future__ import annotations

from typing import Any

from app.config import settings
from app.logging_setup import logger


class LiteLLMClient:
    """Client using LiteLLM for multi-provider API access."""

    def __init__(self, fallback_model: str = ""):
        self.fallback_model = fallback_model or settings.fallback_model
        self._enabled = settings.litellm_enabled

    async def generate(
        self,
        prompt: str,
        system: str = "",
        model: str = "",
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> str:
        if not self._enabled:
            return "[LiteLLM disabled. Enable with SYZYGY_LITELLM_ENABLED=true]"

        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        return await self.chat(
            messages=messages,
            model=model or self.fallback_model,
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
        if not self._enabled:
            return "[LiteLLM disabled]"

        try:
            from litellm import acompletion
            response = await acompletion(
                model=model or self.fallback_model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            return response.choices[0].message.content or ""
        except Exception as e:
            return f"[LiteLLM error: {e}]"

    async def generate_stream(
        self,
        prompt: str,
        system: str = "",
        model: str = "",
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ):
        if not self._enabled:
            return

        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        try:
            from litellm import acompletion
            response = await acompletion(
                model=model or self.fallback_model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True,
            )
            async for chunk in response:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        except Exception as e:
            logger.error("LiteLLM stream error", error=str(e))

    async def list_models(self) -> list[dict[str, Any]]:
        return [{"name": self.fallback_model, "provider": "litellm"}]
