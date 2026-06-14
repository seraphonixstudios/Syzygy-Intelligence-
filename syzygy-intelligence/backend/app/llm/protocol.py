"""LLM Provider protocol — abstract interface for all LLM backends."""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class LLMProvider(Protocol):
    """Interface that all LLM providers must implement."""

    async def generate(
        self,
        prompt: str,
        system: str = "",
        model: str = "",
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> str:
        ...

    async def chat(
        self,
        messages: list[dict[str, str]],
        model: str = "",
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> str:
        ...

    async def generate_stream(
        self,
        prompt: str,
        system: str = "",
        model: str = "",
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ):
        ...

    async def list_models(self) -> list[dict[str, Any]]:
        ...
