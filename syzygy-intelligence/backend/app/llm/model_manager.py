"""Model manager — handles model routing, multi-model queries, fallback, and configuration."""

from __future__ import annotations

from typing import Any

from app.config import settings
from app.errors import LLMConnectionError
from app.llm.litellm_client import LiteLLMClient
from app.llm.ollama_client import OllamaClient
from app.logging_setup import logger


class ModelManager:
    """Manages model selection, multi-model routing, and fallback between providers."""

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
        "vision": "vision_model",
        "image": "vision_model",
        "analyze": "critic_model",
        "reason": "critic_model",
        "code": "coding_model",
        "programming": "coding_model",
        "write": "creative_model",
        "creative": "creative_model",
        "synthesize": "synthesis_model",
        "summarize": "synthesis_model",
        "fast": "fast_model",
        "quick": "fast_model",
    }

    def __init__(self):
        self.ollama = OllamaClient()
        self.litellm = LiteLLMClient()
        self._model_cache: dict[str, Any] = {}

    def get_model_for_role(self, role: str = "default") -> str:
        """Get the configured model for a specific role."""
        config_key = self.MODEL_ROLES.get(role, "default_model")
        return getattr(settings, config_key, settings.default_model)

    def get_model_for_task(self, task: str) -> str:
        """Route to best model based on task description keywords."""
        task_lower = task.lower()
        for keyword, role in self.TASK_MODEL_MAP.items():
            if keyword in task_lower:
                return self.get_model_for_role(role)
        return self.get_model_for_role("default")

    def get_models_for_task(self, task: str) -> list[str]:
        """Return all candidate models that match a task, not just the best one."""
        task_lower = task.lower()
        matched = set()
        for keyword, role in self.TASK_MODEL_MAP.items():
            if keyword in task_lower:
                matched.add(self.get_model_for_role(role))
        if not matched:
            matched.add(self.get_model_for_role("default"))
        return list(matched)

    def get_all_model_names(self) -> list[str]:
        """Return the unique set of configured model names."""
        seen = set()
        models = []
        for field in self.MODEL_ROLES.values():
            m = getattr(settings, field, None)
            if m and m not in seen:
                seen.add(m)
                models.append(m)
        return models

    async def generate(
        self,
        prompt: str,
        system: str = "",
        role: str = "default",
        temperature: float = 0.7,
        max_tokens: int = 2048,
        task_hint: str = "",
    ) -> str:
        """Generate text using best available model for the role."""
        if task_hint:
            model = self.get_model_for_task(task_hint)
        else:
            model = self.get_model_for_role(role)

        try:
            result = await self.ollama.generate(
                prompt=prompt,
                system=system,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            return result
        except LLMConnectionError:
            if settings.litellm_enabled:
                logger.warning("Ollama failed, falling back to LiteLLM", model=model)
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
        """Query multiple models in parallel and return results keyed by model name."""
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

    async def list_available_models(self) -> list[dict[str, Any]]:
        """List all available models from Ollama."""
        return await self.ollama.list_models()

    async def is_model_available(self, model: str) -> bool:
        """Check if a specific model is available."""
        models = await self.list_available_models()
        return any(m.get("name") == model for m in models)
