"""Dynamic polarity-aware team formation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.agents.polarity import compute_polarity_balance, is_balanced
from app.agents.registry import agent_registry


@dataclass
class TeamFormation:
    """Dynamically forms polarity-balanced agent teams."""

    async def form_team(
        self,
        task: str = "",
        num_agents: int = 5,
        polarity_balance: float = 0.6,
        required_archetypes: list[str] | None = None,
    ) -> dict[str, Any]:
        """Form a polarity-balanced team for a given task."""
        agents = agent_registry.create_polarity_balanced_team(
            task_description=task,
            num_agents=num_agents,
        )

        # Optionally filter by required archetypes
        if required_archetypes:
            agents = [a for a in agents if a.archetype_key in required_archetypes]

        polarities = [a.polarity for a in agents]
        balance = compute_polarity_balance(polarities)

        return {
            "agents": [a.to_dict() for a in agents],
            "polarity_balance": balance,
            "balanced": is_balanced(balance, polarity_balance),
            "num_agents": len(agents),
        }

    async def suggest_team_for_task(self, task: str) -> dict[str, Any]:
        """Analyze task and suggest optimal team composition."""
        task_lower = task.lower()

        # Keyword-based heuristic
        needs_analysis = any(w in task_lower for w in ["analyze", "research", "investigate", "study"])
        needs_creation = any(w in task_lower for w in ["create", "write", "design", "build", "generate"])
        needs_code = any(
            w in task_lower
            for w in [
                "code", "program", "develop", "implement", "debug",
                "build", "web", "api", "app", "software", "script",
            ]
        )
        needs_critique = any(w in task_lower for w in ["critique", "review", "evaluate", "assess"])
        needs_synthesis = any(
            w in task_lower
            for w in ["synthesize", "integrate", "unify", "combine"]
        )

        archetypes = []
        if needs_analysis:
            archetypes.extend(["sage", "sage"])
        if needs_creation:
            archetypes.extend(["creator", "great_mother"])
        if needs_code:
            archetypes.extend(["magician", "hero"])
        if needs_critique:
            archetypes.extend(["trickster", "sage"])
        if needs_synthesis:
            archetypes.extend(["self", "hermes"])

        # Ensure default balance
        if not archetypes:
            archetypes = ["sage", "great_mother", "self", "hero", "creator"]

        # Deduplicate while preserving order
        seen = set()
        unique_archetypes = []
        for a in archetypes:
            if a not in seen:
                seen.add(a)
                unique_archetypes.append(a)

        return {
            "task_type": "mixed",
            "recommended_archetypes": unique_archetypes,
            "num_agents": len(unique_archetypes),
        }
