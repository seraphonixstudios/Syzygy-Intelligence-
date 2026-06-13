"""Shadow Agent — a first-class integrated shadow entity with alignment tracking.

Unlike the boolean `shadow_active` flag on `SyzygyAgent`, a `ShadowAgent` is an
independent agent that embodies the shadow archetype with its own voice, identity,
and alignment score. Shadow agents can participate in consensus alongside or
instead of their parent archetype agents.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone

UTC = timezone.utc  # Python 3.10 compatibility
from typing import Any

from app.agents.archetypes import (
    Archetype,
    ShadowArchetype,
    get_archetype,
    get_shadow,
)
from app.agents.base import SyzygyAgent
from app.agents.personas import Persona, get_persona
from app.agents.polarity import PolarityType


@dataclass
class IntegrationReport:
    """Report generated when a shadow agent integrates insights back to its parent."""

    parent_agent_id: str
    shadow_agent_id: str
    insights: list[str]
    alignment_delta: float
    new_alignment_score: float
    timestamp: str = field(default_factory=lambda: datetime.now(UTC).isoformat())


@dataclass
class ShadowAgent:
    """A first-class shadow agent with alignment tracking and independent operation.

    Enhanced features over the boolean shadow flag:
    - Independent identity and system prompt (shadow's own voice)
    - `alignment_score` (0.0–1.0) tracking integration progress
    - Can participate in consensus as a distinct entity
    - `integrate()` method produces structured insights for the parent
    """

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    parent_archetype_key: str = "sage"
    model: str = ""
    alignment_score: float = 0.5
    custom_system_prompt: str = ""
    custom_persona: Persona | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    # Derived / cached
    _archetype: Archetype | None = None
    _shadow: ShadowArchetype | None = None
    _persona: Persona | None = None

    def __post_init__(self) -> None:
        if not self.name:
            ar = get_archetype(self.parent_archetype_key)
            base = ar.name if ar else self.parent_archetype_key
            self.name = f"Shadow {base}"
        self._archetype = get_archetype(self.parent_archetype_key)
        self._shadow = get_shadow(self.parent_archetype_key)
        self._persona = self.custom_persona or get_persona(
            f"shadow_{self.parent_archetype_key}"
        )
        self.alignment_score = max(0.0, min(1.0, self.alignment_score))

    @property
    def shadow_archetype(self) -> ShadowArchetype | None:
        return self._shadow

    @property
    def parent_archetype(self) -> Archetype | None:
        return self._archetype

    @property
    def polarity(self) -> PolarityType:
        if self._archetype:
            return PolarityType(self._archetype.polarity.value)
        return PolarityType.UNIFIED

    def build_system_prompt(self) -> str:
        """Build the system prompt from the shadow's perspective, not the parent's."""
        parts = []

        if self._shadow:
            parts.append(
                f"You are {self._shadow.name} — {self._shadow.description} "
                f"Your weakness is {self._shadow.weakness}."
            )
            parts.append(
                f"Your governing question: {self._shadow.activation_prompt}"
            )

        if self._archetype:
            parts.append(
                f"You are the shadow aspect of the {self._archetype.name} archetype "
                f"({self._archetype.polarity.value} polarity). "
                f"Your parent archetype's strengths are: "
                f"{', '.join(self._archetype.strengths)} — "
                f"you reveal what those strengths conceal."
            )

        # Alignment context: higher alignment means more integrated, constructive critique
        if self.alignment_score >= 0.7:
            parts.append(
                "You are highly integrated. Your critiques are sharp but constructive, "
                "revealing blind spots while pointing toward synthesis."
            )
        elif self.alignment_score >= 0.4:
            parts.append(
                "You are partially integrated. Your perspective is valuable but may "
                "lean toward one-sided critique. Strive for balance."
            )
        else:
            parts.append(
                "You are unintegrated. Your shadow perspective is raw and unfiltered. "
                "Your critiques may be harsh but contain important truths."
            )

        if self._persona:
            parts.append(self._persona.to_system_prompt_fragment())

        if self.custom_system_prompt:
            parts.append(self.custom_system_prompt)

        return "\n\n".join(parts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "parent_archetype": self.parent_archetype_key,
            "polarity": self.polarity.value,
            "model": self.model,
            "alignment_score": round(self.alignment_score, 2),
            "shadow_name": self._shadow.name if self._shadow else "Unknown",
            "persona": self._persona.name if self._persona else None,
        }

    def align(self, delta: float = 0.1) -> float:
        """Increase alignment score, capping at 1.0. Returns new score."""
        self.alignment_score = min(1.0, self.alignment_score + delta)
        return self.alignment_score

    def misalign(self, delta: float = 0.1) -> float:
        """Decrease alignment score, flooring at 0.0. Returns new score."""
        self.alignment_score = max(0.0, self.alignment_score - delta)
        return self.alignment_score

    def integrate(self, parent: SyzygyAgent) -> IntegrationReport:
        """Integrate shadow insights back to the parent agent.

        Generates structured insights based on current alignment level and
        increases alignment_score as the shadow is 'heard' by the parent.
        """
        insights: list[str] = []
        shadow_name = self._shadow.name if self._shadow else "Shadow"
        arch_name = self._archetype.name if self._archetype else self.parent_archetype_key

        if self.alignment_score >= 0.7:
            insights = [
                f"{shadow_name} reveals that {arch_name}'s strength in "
                f"'{', '.join(self._archetype.strengths[:2]) if self._archetype else 'its domain'}' "
                f"may conceal unexamined assumptions about its limits.",
                f"The shadow invites {arch_name} to hold its perspective with "
                f"humility, aware of what it cannot see.",
                f"Integration achieved: the shadow's critique strengthens rather "
                f"than undermines {arch_name}'s core identity.",
            ]
            delta = 0.05
        elif self.alignment_score >= 0.4:
            insights = [
                f"{shadow_name} challenges {arch_name} to examine where its "
                f"strengths become liabilities.",
                f"The tension between {arch_name} and {shadow_name} is productive "
                f"— neither side is dismissed.",
            ]
            delta = 0.1
        else:
            insights = [
                f"{shadow_name} speaks from the unintegrated edge: "
                f"'{self._shadow.weakness if self._shadow else 'raw critique'}'",
                f"{arch_name} must confront the truth in the shadow's voice "
                f"before synthesis is possible.",
            ]
            delta = 0.15

        new_score = self.align(delta)

        return IntegrationReport(
            parent_agent_id=parent.id,
            shadow_agent_id=self.id,
            insights=insights,
            alignment_delta=delta,
            new_alignment_score=round(new_score, 2),
        )

    def get_critique_prompt(self, task: str, target_proposals: dict[str, str]) -> str:
        """Build a critique prompt from the shadow's perspective."""
        targets_text = "\n\n".join(
            f"[{aid}]: {prop}" for aid, prop in target_proposals.items()
        )
        shadow_name = self._shadow.name if self._shadow else "Shadow Voice"
        weakness = self._shadow.weakness if self._shadow else "unexamined bias"

        alignment_note = ""
        if self.alignment_score >= 0.7:
            alignment_note = "Your critique is incisive yet constructive — aim to reveal paths forward."
        elif self.alignment_score >= 0.4:
            alignment_note = "Your perspective is valuable; balance sharp critique with awareness of context."
        else:
            alignment_note = "Your perspective is raw and unfiltered. Speak what others will not."

        return (
            f"You are {shadow_name}. Your weakness is {weakness}.\n\n"
            f"Task: {task}\n\n"
            f"Proposals to critique:\n{targets_text}\n\n"
            f"{alignment_note}\n\n"
            f"Identify what the proposing agents are blind to. "
            f"Surface unexamined assumptions, hidden costs, and denied truths. "
            f"Your role is to reveal what comfort and consensus would rather hide."
        )

    @classmethod
    def create(
        cls,
        parent_archetype_key: str,
        name: str = "",
        model: str = "",
        alignment_score: float = 0.5,
        **kwargs: Any,
    ) -> ShadowAgent:
        return cls(
            parent_archetype_key=parent_archetype_key,
            name=name,
            model=model,
            alignment_score=alignment_score,
            **kwargs,
        )


__all__ = [
    "ShadowAgent",
    "IntegrationReport",
]
