"""LLM Abstraction Layer — pluggable providers with Ollama default and OpenAI-compatible support."""

from __future__ import annotations

from typing import Any

from app.llm.litellm_client import LiteLLMClient
from app.llm.model_manager import ModelManager
from app.llm.ollama_client import OllamaClient
from app.llm.openai_compat import OpenAICompatClient
from app.llm.protocol import LLMProvider


class LLMFactory:
    """Factory for creating LLM clients."""

    @staticmethod
    def create_client(provider: str = "ollama", **kwargs: Any) -> Any:
        if provider == "ollama":
            return OllamaClient(**kwargs)
        elif provider == "litellm":
            return LiteLLMClient(**kwargs)
        elif provider == "openai_compat":
            return OpenAICompatClient(**kwargs)
        raise ValueError(f"Unknown provider: {provider}")


__all__ = [
    "OllamaClient",
    "LiteLLMClient",
    "OpenAICompatClient",
    "ModelManager",
    "LLMFactory",
    "LLMProvider",
]
