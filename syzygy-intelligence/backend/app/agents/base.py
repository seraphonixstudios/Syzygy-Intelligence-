"""Base agent class for Syzygy Intelligence.

Every agent has:
- Polarity (Masculine/Feminine/Unified)
- Primary Jungian Archetype + Shadow Archetype
- Persona layer for external presentation
- Configurable LLM model binding
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any

from app.agents.archetypes import (
    Archetype,
    ShadowArchetype,
    get_archetype,
    get_shadow,
)
from app.agents.personas import Persona, get_persona
from app.agents.polarity import POLARITY_CONFIGS, PolarityType


@dataclass
class SyzygyAgent:
    """A complete Syzygy agent with polarity, archetype, shadow, and persona."""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    archetype_key: str = "sage"
    shadow_active: bool = False
    model: str = ""
    custom_system_prompt: str = ""
    custom_persona: Persona | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    # Derived / cached
    _archetype: Archetype | None = None
    _shadow: ShadowArchetype | None = None
    _persona: Persona | None = None

    def __post_init__(self):
        if not self.name:
            self.name = self.archetype_key.title()
        self._archetype = get_archetype(self.archetype_key)
        self._shadow = get_shadow(self.archetype_key)
        self._persona = self.custom_persona or get_persona(self.archetype_key)

    @property
    def archetype(self) -> Archetype | None:
        return self._archetype

    @property
    def shadow(self) -> ShadowArchetype | None:
        return self._shadow if self.shadow_active else None

    @property
    def persona(self) -> Persona | None:
        return self._persona

    @property
    def polarity(self) -> PolarityType:
        if self._archetype:
            return PolarityType(self._archetype.polarity.value)
        return PolarityType.UNIFIED

    @property
    def polarity_config(self):
        return POLARITY_CONFIGS.get(self.polarity)

    @property
    def glyph(self) -> str:
        return self.polarity_config.glyph if self.polarity_config else "☿"

    def build_system_prompt(self) -> str:
        """Build the full system prompt embedding archetype, persona, and optional shadow."""
        parts = []

        # Core archetype instruction
        if self._archetype:
            parts.append(self._archetype.system_prompt_fragment)

        # Persona layer
        if self._persona:
            parts.append(self._persona.to_system_prompt_fragment())

        # Shadow activation
        if self.shadow_active and self._shadow:
            parts.append(
                f"\n[Shadow Active - {self._shadow.name}]: {self._shadow.activation_prompt}"
            )

        # Custom overrides
        if self.custom_system_prompt:
            parts.append(self.custom_system_prompt)

        return "\n\n".join(parts)

    def activate_shadow(self) -> None:
        self.shadow_active = True

    def deactivate_shadow(self) -> None:
        self.shadow_active = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "archetype": self.archetype_key,
            "polarity": self.polarity.value,
            "glyph": self.glyph,
            "shadow_active": self.shadow_active,
            "persona": self._persona.name if self._persona else None,
            "model": self.model,
        }

    @classmethod
    def create(
        cls,
        archetype_key: str,
        name: str = "",
        model: str = "",
        shadow_active: bool = False,
        **kwargs,
    ) -> SyzygyAgent:
        return cls(
            name=name or archetype_key.title(),
            archetype_key=archetype_key,
            model=model,
            shadow_active=shadow_active,
            **kwargs,
        )


__all__ = ["SyzygyAgent"]
