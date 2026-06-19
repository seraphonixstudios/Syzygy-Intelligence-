"""Model manager — handles model routing, multi-model queries, provider selection, and fallback."""

from __future__ import annotations

from typing import Any

from app.config import settings
from app.errors import LLMConnectionError
from app.llm.litellm_client import LiteLLMClient
from app.llm.ollama_client import OllamaClient
from app.llm.openai_compat import OpenAICompatClient
from app.llm.protocol import LLMProvider
from app.logging_setup import logger


class ModelManager:
    """Manages model selection, multi-model routing, and fallback between providers.

    Supports pluggable providers via the LLMProvider protocol.
    New providers can be registered by adding them to the _providers dict.
    """

    MODEL_ROLES = {
        "default": "default_model",
        "critic": "critic_model",
        "synthesis": "synthesis_model",
        "coding": "coding_model",
        "creative": "creative_model",
        "vision": "vision_model",
        "gpu": "gpu_model",
        "fast": "fast_model",
    }

    TASK_MODEL_MAP: dict[str, str] = {
        "vision": "vision",
        "image": "vision",
        "analyze": "critic",
        "reason": "critic",
        "code": "coding",
        "programming": "coding",
        "write": "creative",
        "creative": "creative",
        "synthesize": "synthesis",
        "summarize": "synthesis",
        "fast": "fast",
        "quick": "fast",
    }

    def __init__(self) -> None:
        self.ollama = OllamaClient()
        self.litellm = LiteLLMClient()
        self.openai_compat = OpenAICompatClient() if settings.openai_compat_enabled else None
        self._providers: dict[str, LLMProvider] = {
            "ollama": self.ollama,
            "litellm": self.litellm,
        }
        if self.openai_compat:
            self._providers["openai_compat"] = self.openai_compat
        self._default_provider = settings.default_llm_provider
        self._model_cache: dict[str, Any] = {}

    def get_provider(self, name: str | None = None) -> LLMProvider:
        """Get an LLM provider by name, falling back to the default."""
        key = name or self._default_provider
        provider = self._providers.get(key)
        if not provider:
            logger.warning("Unknown LLM provider, falling back to ollama", requested=key)
            return self._providers["ollama"]
        return provider

    def get_model_for_role(self, role: str = "default") -> str:
        config_key = self.MODEL_ROLES.get(role, "default_model")
        return getattr(settings, config_key, settings.default_model)

    def get_model_for_task(self, task: str) -> str:
        task_lower = task.lower()
        for keyword, role in self.TASK_MODEL_MAP.items():
            if keyword in task_lower:
                return self.get_model_for_role(role)
        return self.get_model_for_role("default")

    def get_models_for_task(self, task: str) -> list[str]:
        task_lower = task.lower()
        matched = set()
        for keyword, role in self.TASK_MODEL_MAP.items():
            if keyword in task_lower:
                matched.add(self.get_model_for_role(role))
        if not matched:
            matched.add(self.get_model_for_role("default"))
        return list(matched)

    def get_all_model_names(self) -> list[str]:
        seen = set()
        models = []
        for field in self.MODEL_ROLES.values():
            m = getattr(settings, field, None)
            if m and m not in seen:
                seen.add(m)
                models.append(m)
        return models

    def get_all_providers(self) -> dict[str, LLMProvider]:
        return dict(self._providers)

    async def generate(
        self,
        prompt: str,
        system: str = "",
        model: str = "",
        role: str = "default",
        temperature: float = 0.7,
        max_tokens: int = 2048,
        task_hint: str = "",
        provider: str | None = None,
    ) -> str:
        if not model:
            if task_hint:
                model = self.get_model_for_task(task_hint)
            else:
                model = self.get_model_for_role(role)

        llm = self.get_provider(provider)
        try:
            return await llm.generate(
                prompt=prompt,
                system=system,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
            )
        except LLMConnectionError:
            if provider is None and settings.litellm_enabled:
                logger.warning("Primary provider failed, falling back to LiteLLM", model=model)
                return await self.litellm.generate(
                    prompt=prompt,
                    system=system,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
            raise

    async def generate_multi_model(
        self,
        prompt: str,
        models: list[str],
        system: str = "",
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> dict[str, str]:
        logger.info(
            "Multi-model query",
            models=models,
            prompt_len=len(prompt),
        )
        return await self.ollama.generate_multi(
            prompt=prompt,
            models=models,
            system=system,
            temperature=temperature,
            max_tokens=max_tokens,
        )

    async def chat(
        self,
        messages: list[dict[str, str]],
        model: str = "",
        role: str = "default",
        temperature: float = 0.7,
        max_tokens: int = 2048,
        provider: str | None = None,
    ) -> str:
        resolved = model or self.get_model_for_role(role)
        llm = self.get_provider(provider)
        return await llm.chat(
            messages=messages,
            model=resolved,
            temperature=temperature,
            max_tokens=max_tokens,
        )

    async def generate_stream(
        self,
        prompt: str,
        system: str = "",
        role: str = "default",
        temperature: float = 0.7,
        max_tokens: int = 2048,
        provider: str | None = None,
    ):
        model = self.get_model_for_role(role)
        llm = self.get_provider(provider)
        async for chunk in llm.generate_stream(
            prompt=prompt,
            system=system,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
        ):
            yield chunk

    async def list_available_models(self) -> list[dict[str, Any]]:
        all_models = []
        for name, provider in self._providers.items():
            try:
                models = await provider.list_models()
                for m in models:
                    m["provider"] = name
                all_models.extend(models)
            except Exception as e:
                logger.warning("Failed to list models from provider", provider=name, error=str(e))
        return all_models

    async def is_model_available(self, model: str) -> bool:
        models = await self.list_available_models()
        return any(m.get("name") == model for m in models)
