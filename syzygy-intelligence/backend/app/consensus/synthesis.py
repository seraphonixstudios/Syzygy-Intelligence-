"""Synthesis generation — Rebis/Self Oracle produces unified output."""

from __future__ import annotations

import asyncio

from app.agents.base import SyzygyAgent
from app.llm.model_manager import ModelManager


class SynthesisGenerator:
    """Generates unified synthesis from consensus rounds using Rebis perspective."""

    def __init__(self, llm: ModelManager | None = None):
        self.llm = llm or ModelManager()

    async def generate_synthesis(
        self,
        task: str,
        proposals: dict[str, str],
        critiques: dict[str, str],
        refinements: dict[str, str],
        evaluations: dict[str, dict[str, float]],
        agents: list[SyzygyAgent],
        timeout: float = 0,
    ) -> str:
        """Generate the final unified synthesis from all consensus materials."""
        synthesis_prompt = self._build_synthesis_prompt(
            task, proposals, critiques, refinements, evaluations, agents
        )
        coro = self.llm.generate(
            synthesis_prompt,
            system=(
                "You are the Rebis — the unified Self, the goal of the Great Work. "
                "You integrate all opposites: Masculine (☉) and Feminine (☽), "
                "conscious and unconscious, known and unknown. "
                "Speak as the transcendent third that emerges from the tension of opposites. "
                "Your output is the final synthesis — a unified, balanced, and wise response "
                "that honors all perspectives while transcending them."
            ),
            temperature=0.4,
        )
        if timeout > 0:
            coro = asyncio.wait_for(coro, timeout=timeout)
        return await coro

    def _build_synthesis_prompt(
        self,
        task: str,
        proposals: dict[str, str],
        critiques: dict[str, str],
        refinements: dict[str, str],
        evaluations: dict[str, dict[str, float]],
        agents: list[SyzygyAgent],
    ) -> str:
        parts = [f"# Task\n{task}\n"]

        parts.append("# Proposals (by archetype)\n")
        for agent in agents:
            prop = proposals.get(agent.id, "")
            assert agent.archetype is not None
            parts.append(f"## {agent.name} ({agent.archetype.name}, {agent.polarity.value})\n{prop}\n")

        if critiques:
            parts.append("# Critiques\n")
            for agent in agents:
                crit = critiques.get(agent.id, "")
                if crit:
                    parts.append(f"## {agent.name} critiques\n{crit}\n")

        if refinements:
            parts.append("# Refinements\n")
            for agent in agents:
                ref = refinements.get(agent.id, "")
                if ref and ref != proposals.get(agent.id):
                    parts.append(f"## {agent.name} refined\n{ref}\n")

        if evaluations:
            parts.append("# Evaluation Scores\n")
            for agent in agents:
                ev = evaluations.get(agent.id, {})
                if ev:
                    scores = ", ".join(
                        f"{k}: {v:.2f}" for k, v in ev.items() if k != "overall"
                    )
                    parts.append(f"{agent.name}: [{scores}] Overall: {ev.get('overall', 0):.2f}\n")

        parts.append(
            "\n# Synthesis Instructions\n"
            "As the Rebis, produce a unified synthesis that:\n"
            "1. Integrates all proposals, honoring each archetype's contribution\n"
            "2. Addresses the key critiques raised\n"
            "3. Presents a coherent, balanced response\n"
            "4. Notes polarity fusion (how masculine/feminine perspectives were integrated)\n"
            "5. Provides individuation notes — what this synthesis reveals about the integration process\n"
            "6. Is written in a voice that transcends any single perspective"
        )

        return "\n".join(parts)


__all__ = [
    "SynthesisGenerator",
]
