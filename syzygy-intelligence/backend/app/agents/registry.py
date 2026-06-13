"""Agent Registry — factory for creating and managing Syzygy agents and shadow agents."""

from __future__ import annotations

from typing import Any

from app.agents.archetypes import ARCHETYPE_REGISTRY
from app.agents.base import SyzygyAgent
from app.agents.polarity import PolarityType
from app.agents.shadow import ShadowAgent

# Default models for each archetype (can be overridden)
DEFAULT_AGENT_MODELS: dict[str, str] = {
    "hero": "qwen3:8b-gpu",
    "sage": "qwen3:8b-gpu",
    "ruler": "qwen3:8b-gpu",
    "magician": "qwen3:8b-gpu",
    "explorer": "qwen3:8b-gpu",
    "great_mother": "qwen3:8b-gpu",
    "lover": "qwen3:8b-gpu",
    "innocent": "qwen3:8b-gpu",
    "creator": "qwen3:8b-gpu",
    "anima": "qwen3:8b-gpu",
    "self": "qwen3:8b-gpu",
    "hermes": "qwen3:8b-gpu",
    "trickster": "qwen3:8b-gpu",
}


class AgentRegistry:
    """Central registry for all Syzygy agents and shadow agents."""

    def __init__(self) -> None:
        self._agents: dict[str, SyzygyAgent] = {}
        self._shadow_agents: dict[str, ShadowAgent] = {}

    # ── Primary agents ──────────────────────────────────────

    def register(self, agent: SyzygyAgent) -> str:
        self._agents[agent.id] = agent
        return agent.id

    def get(self, agent_id: str) -> SyzygyAgent | None:
        return self._agents.get(agent_id)

    def remove(self, agent_id: str) -> bool:
        if agent_id in self._agents:
            del self._agents[agent_id]
            return True
        return False

    def list_agents(self, polarity: PolarityType | None = None) -> list[SyzygyAgent]:
        if polarity:
            return [a for a in self._agents.values() if a.polarity == polarity]
        return list(self._agents.values())

    def clear(self) -> None:
        self._agents.clear()

    def create_agent(
        self,
        archetype_key: str,
        name: str = "",
        model: str = "",
        shadow_active: bool = False,
        **kwargs: Any,
    ) -> SyzygyAgent:
        """Create and register a new agent."""
        if archetype_key not in ARCHETYPE_REGISTRY:
            raise ValueError(f"Unknown archetype: {archetype_key}. Available: {list(ARCHETYPE_REGISTRY.keys())}")

        agent = SyzygyAgent.create(
            archetype_key=archetype_key,
            name=name or archetype_key.title(),
            model=model or DEFAULT_AGENT_MODELS.get(archetype_key, "qwen3:8b-gpu"),
            shadow_active=shadow_active,
            **kwargs,
        )
        self.register(agent)
        return agent

    # ── Shadow agents ───────────────────────────────────────

    def register_shadow(self, agent: ShadowAgent) -> str:
        self._shadow_agents[agent.id] = agent
        return agent.id

    def get_shadow(self, shadow_id: str) -> ShadowAgent | None:
        return self._shadow_agents.get(shadow_id)

    def remove_shadow(self, shadow_id: str) -> bool:
        if shadow_id in self._shadow_agents:
            del self._shadow_agents[shadow_id]
            return True
        return False

    def list_shadow_agents(
        self, parent_archetype_key: str | None = None
    ) -> list[ShadowAgent]:
        if parent_archetype_key:
            return [
                a
                for a in self._shadow_agents.values()
                if a.parent_archetype_key == parent_archetype_key
            ]
        return list(self._shadow_agents.values())

    def create_shadow_agent(
        self,
        parent_archetype_key: str,
        name: str = "",
        model: str = "",
        alignment_score: float = 0.5,
        **kwargs: Any,
    ) -> ShadowAgent:
        """Create and register a new shadow agent."""
        if parent_archetype_key not in ARCHETYPE_REGISTRY:
            raise ValueError(
                f"Unknown archetype: {parent_archetype_key}. "
                f"Available: {list(ARCHETYPE_REGISTRY.keys())}"
            )
        agent = ShadowAgent.create(
            parent_archetype_key=parent_archetype_key,
            name=name,
            model=model or DEFAULT_AGENT_MODELS.get(parent_archetype_key, "qwen3:8b-gpu"),
            alignment_score=alignment_score,
            **kwargs,
        )
        self.register_shadow(agent)
        return agent

    def clear_shadows(self) -> None:
        self._shadow_agents.clear()

    # ── Team composition ────────────────────────────────────

    def create_default_team(self) -> list[SyzygyAgent]:
        """Create a balanced default team with masculine, feminine, and unified agents."""
        team = []

        # Masculine agents
        team.append(self.create_agent("sage", name="Sage"))
        team.append(self.create_agent("hero", name="Heracles"))

        # Feminine agents
        team.append(self.create_agent("great_mother", name="Nurtura"))
        team.append(self.create_agent("lover", name="Aphrodite"))

        # Unified agent
        team.append(self.create_agent("self", name="Rebis"))

        return team

    def create_polarity_balanced_team(
        self,
        task_description: str = "",
        num_agents: int = 5,
    ) -> list[SyzygyAgent]:
        """Dynamically form a polarity-balanced team based on task context."""
        masc_keys = ["sage", "hero", "ruler", "magician", "explorer"]
        fem_keys = ["great_mother", "lover", "innocent", "creator", "anima"]
        unified_keys = ["self", "hermes", "trickster"]

        masc_count = max(1, num_agents // 3)
        fem_count = max(1, num_agents // 3)
        unified_count = num_agents - masc_count - fem_count

        team = []
        for i in range(masc_count):
            key = masc_keys[i % len(masc_keys)]
            team.append(self.create_agent(key))
        for i in range(fem_count):
            key = fem_keys[i % len(fem_keys)]
            team.append(self.create_agent(key))
        for i in range(unified_count):
            key = unified_keys[i % len(unified_keys)]
            team.append(self.create_agent(key))

        return team

    def create_shadow_balanced_team(
        self, num_shadows: int = 3
    ) -> list[ShadowAgent]:
        """Create a polarity-balanced team of shadow agents."""
        keys = ["sage", "great_mother", "trickster"]
        team = []
        for i in range(num_shadows):
            key = keys[i % len(keys)]
            alignment = max(0.3, min(0.8, 0.5 + (i * 0.1)))
            team.append(self.create_shadow_agent(key, alignment_score=alignment))
        return team


# Global singleton
agent_registry = AgentRegistry()
