"""LLM Abstraction Layer — Ollama-first with LiteLLM fallback."""

from __future__ import annotations

from typing import Any, Optional

from app.llm.litellm_client import LiteLLMClient
from app.llm.model_manager import ModelManager
from app.llm.ollama_client import OllamaClient


class LLMFactory:
    """Factory for creating LLM clients."""

    @staticmethod
    def create_client(provider: str = "ollama", **kwargs) -> Any:
        if provider == "ollama":
            return OllamaClient(**kwargs)
        elif provider == "litellm":
            return LiteLLMClient(**kwargs)
        raise ValueError(f"Unknown provider: {provider}")


__all__ = [
    "OllamaClient",
    "LiteLLMClient",
    "ModelManager",
    "LLMFactory",
]
