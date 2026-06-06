"""Model manager — handles model routing, fallback, and configuration."""

from __future__ import annotations

from typing import Any, Optional

from app.config import settings
from app.llm.ollama_client import OllamaClient
from app.llm.litellm_client import LiteLLMClient


class ModelManager:
    """Manages model selection, routing, and fallback between providers."""

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

        # Try Ollama first
        result = await self.ollama.generate(
            prompt=prompt,
            system=system,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        # Fallback to LiteLLM if Ollama fails
        if result.startswith("[Ollama error") and settings.litellm_enabled:
            result = await self.litellm.generate(
                prompt=prompt,
                system=system,
                temperature=temperature,
                max_tokens=max_tokens,
            )

        return result

    async def list_available_models(self) -> list[dict[str, Any]]:
        """List all available models from Ollama."""
        return await self.ollama.list_models()

    async def is_model_available(self, model: str) -> bool:
        """Check if a specific model is available."""
        models = await self.list_available_models()
        return any(m.get("name") == model for m in models)
