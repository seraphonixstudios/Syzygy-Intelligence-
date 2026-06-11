"""Phase implementations for the Syzygy Consensus Engine.

These provide phase-specific prompt templates; the actual orchestration 
and LLM calls happen in the ConsensusEngine.
"""

from __future__ import annotations

from app.agents.base import SyzygyAgent


class ProposalPhase:
    """Phase 1: Independent proposals tagged by polarity + archetype."""

    @staticmethod
    def build_prompt(task: str, agent: SyzygyAgent, context: str = "") -> str:
        return (
            f"As a {agent.archetype.name} agent ({agent.polarity.value} polarity), "
            f"propose your approach to the following task:\n\n{task}\n\n"
            f"{context}\n\n"
            f"Frame your proposal through the lens of your archetype's strengths: "
            f"{', '.join(agent.archetype.strengths)}."
        )


class CritiquePhase:
    """Phase 2: Cross-polarity critique with shadow activation."""

    @staticmethod
    def build_prompt(
        task: str,
        agent: SyzygyAgent,
        target_proposals: dict[str, str],
        shadow_instruction: str = "",
    ) -> str:
        targets_text = "\n\n".join(
            f"[{aid}]: {prop[:800]}"
            for aid, prop in target_proposals.items()
        )

        shadow_prompt = ""
        if shadow_instruction:
            shadow_prompt = (
                f"\n\nYour shadow ({shadow_instruction}) is active. "
                f"Allow this critical perspective to inform your analysis "
                f"without dominating it completely."
            )

        return (
            f"Review the following proposals for the task:\n\n{task}\n\n"
            f"Proposals to critique:\n{targets_text}\n"
            f"{shadow_prompt}\n\n"
            f"Provide constructive cross-polarity critique. Identify:\n"
            f"1. Blind spots and unexamined assumptions\n"
            f"2. Opportunities for integration\n"
            f"3. What each proposal misses from the opposite polarity perspective"
        )


class RefinementPhase:
    """Phase 3: Agents revise proposals incorporating feedback."""

    @staticmethod
    def build_prompt(
        task: str,
        agent: SyzygyAgent,
        own_proposal: str,
        critiques: dict[str, str],
    ) -> str:
        critiques_text = "\n\n".join(
            f"Critique from {cid}: {c[:600]}"
            for cid, c in critiques.items()
        )

        return (
            f"Your original proposal:\n{own_proposal[:1000]}\n\n"
            f"Critiques received:\n{critiques_text}\n\n"
            f"Revise your proposal, incorporating the valid feedback "
            f"while maintaining your archetypal perspective as {agent.archetype.name}. "
            f"Explain what you changed and why. "
            f"The goal is to integrate complementary perspectives "
            f"without losing your distinctive voice."
        )


class EvaluationPhase:
    """Phase 4: Handles evaluation prompts — actual scoring is in ConsensusScorer."""

    @staticmethod
    def build_evaluation_prompt(
        task: str,
        content: str,
        agent: SyzygyAgent,
    ) -> str:
        return (
            f"Task: {task}\n\n"
            f"Agent: {agent.name} ({agent.archetype.name}, {agent.polarity.value})\n"
            f"Content to evaluate:\n{content[:1500]}"
        )
