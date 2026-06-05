"""Agent Registry — factory for creating and managing Syzygy agents."""

from __future__ import annotations

from typing import Any, Optional

from app.agents.base import SyzygyAgent
from app.agents.archetypes import ARCHETYPE_REGISTRY, get_archetypes_by_polarity
from app.agents.polarity import PolarityType
from app.agents.personas import PERSONA_REGISTRY

# Default models for each archetype (can be overridden)
DEFAULT_AGENT_MODELS: dict[str, str] = {
    "hero": "qwen3.5:8b",
    "sage": "deepseek-r1:7b",
    "ruler": "qwen3.5:8b",
    "magician": "qwen-coder:7b",
    "explorer": "qwen3.5:8b",
    "great_mother": "dolphin-llama3:8b",
    "lover": "dolphin-llama3:8b",
    "innocent": "dolphin-llama3:8b",
    "creator": "qwen-coder:7b",
    "anima": "deepseek-r1:7b",
    "self": "qwen3.5:8b",
    "hermes": "qwen3.5:8b",
    "trickster": "qwen3.5:8b",
}


class AgentRegistry:
    """Central registry for all Syzygy agents."""

    def __init__(self):
        self._agents: dict[str, SyzygyAgent] = {}

    def register(self, agent: SyzygyAgent) -> str:
        self._agents[agent.id] = agent
        return agent.id

    def get(self, agent_id: str) -> Optional[SyzygyAgent]:
        return self._agents.get(agent_id)

    def remove(self, agent_id: str) -> bool:
        if agent_id in self._agents:
            del self._agents[agent_id]
            return True
        return False

    def list(self, polarity: Optional[PolarityType] = None) -> list[SyzygyAgent]:
        if polarity:
            return [a for a in self._agents.values() if a.polarity == polarity]
        return list(self._agents.values())

    def clear(self):
        self._agents.clear()

    def create_agent(
        self,
        archetype_key: str,
        name: str = "",
        model: str = "",
        shadow_active: bool = False,
        **kwargs,
    ) -> SyzygyAgent:
        """Create and register a new agent."""
        if archetype_key not in ARCHETYPE_REGISTRY:
            raise ValueError(f"Unknown archetype: {archetype_key}. Available: {list(ARCHETYPE_REGISTRY.keys())}")

        agent = SyzygyAgent.create(
            archetype_key=archetype_key,
            name=name or archetype_key.title(),
            model=model or DEFAULT_AGENT_MODELS.get(archetype_key, "qwen3.5:8b"),
            shadow_active=shadow_active,
            **kwargs,
        )
        self.register(agent)
        return agent

    def create_default_team(self) -> list[SyzygyAgent]:
        """Create a balanced default team with masculine, feminine, and unified agents."""
        team = []

        # Masculine agents
        team.append(self.create_agent("sage", name="Sage"))
        team.append(self.create_agent("hero", name="Heracles"))
        team.append(self.create_agent("magician", name="Merlin"))

        # Feminine agents
        team.append(self.create_agent("great_mother", name="Nurtura"))
        team.append(self.create_agent("lover", name="Aphrodite"))
        team.append(self.create_agent("creator", name="Astra"))

        # Unified agents
        team.append(self.create_agent("self", name="Rebis"))
        team.append(self.create_agent("trickster", name="Loki"))

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


# Global singleton
agent_registry = AgentRegistry()
