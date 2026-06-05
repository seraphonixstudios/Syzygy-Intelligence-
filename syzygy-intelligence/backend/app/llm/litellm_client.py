"""LiteLLM client for optional API fallback to OpenAI/Anthropic/etc."""

from __future__ import annotations

from typing import Any, Optional

from app.config import settings


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

        try:
            from litellm import acompletion

            messages = []
            if system:
                messages.append({"role": "system", "content": system})
            messages.append({"role": "user", "content": prompt})

            response = await acompletion(
                model=model or self.fallback_model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            return response.choices[0].message.content or ""

        except Exception as e:
            return f"[LiteLLM error: {e}]"

    async def chat(
        self,
        messages: list[dict[str, str]],
        model: str = "",
        temperature: float = 0.7,
    ) -> str:
        if not self._enabled:
            return "[LiteLLM disabled]"

        try:
            from litellm import acompletion
            response = await acompletion(
                model=model or self.fallback_model,
                messages=messages,
                temperature=temperature,
            )
            return response.choices[0].message.content or ""
        except Exception as e:
            return f"[LiteLLM error: {e}]"
