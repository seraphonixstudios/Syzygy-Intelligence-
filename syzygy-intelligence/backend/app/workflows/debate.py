"""Debate workflow — structured multi-agent debate with polarity-aware positions and LLM."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

from app.llm.ollama_client import OllamaClient
from app.logging_setup import logger


@dataclass
class DebateWorkflow:
    """Structured multi-agent debate with polarity-aware positions."""

    ROUNDS = ["opening", "rebuttal", "cross_examination", "closing", "synthesis"]

    name: str = "debate"
    description: str = "Multi-agent structured debate with polarity-aware positions"
    required_capabilities: list[str] = field(
        default_factory=lambda: ["argumentation", "critique", "synthesis"]
    )
    llm: Optional[OllamaClient] = None

    def __post_init__(self):
        if self.llm is None:
            self.llm = OllamaClient()

    async def opening_statement(self, topic: str, position: str, archetype: str) -> str:
        prompt = (
            f"Topic for debate: {topic}\n\n"
            f"Your position: {position}\nYour archetype: {archetype}\n\n"
            f"Write a compelling opening statement (2-3 paragraphs) that:\n"
            f"1. Clearly states your position\n"
            f"2. Presents your strongest arguments\n"
            f"3. Frames the issue through your archetypal lens\n"
            f"4. Anticipates counter-arguments"
        )
        return await self.llm.generate(prompt, temperature=0.5)

    async def rebuttal(self, topic: str, position: str, opponent_opening: str) -> str:
        prompt = (
            f"Topic: {topic}\nYour position: {position}\n\n"
            f"Opponent's opening statement:\n{opponent_opening[:1500]}\n\n"
            f"Write a sharp rebuttal (2 paragraphs) that:\n"
            f"1. Identifies weaknesses in the opponent's argument\n"
            f"2. Provides counter-evidence or counter-examples\n"
            f"3. Reinforces your own position\n"
            f"4. Is respectful but firm"
        )
        return await self.llm.generate(prompt, temperature=0.5)

    async def cross_examine(self, topic: str, position: str, opponent_args: str) -> str:
        prompt = (
            f"Topic: {topic}\nYour position: {position}\n\n"
            f"Opponent's arguments:\n{opponent_args[:1500]}\n\n"
            f"Ask 3-5 penetrating questions that expose assumptions, "
            f"logical gaps, or unaddressed implications in the opponent's position."
        )
        return await self.llm.generate(prompt, temperature=0.5)

    async def closing(self, topic: str, position: str, debate_summary: str) -> str:
        prompt = (
            f"Topic: {topic}\nYour position: {position}\n\n"
            f"Debate summary:\n{debate_summary[:1500]}\n\n"
            f"Write a compelling closing statement (2 paragraphs) that:\n"
            f"1. Summarizes your strongest points\n"
            f"2. Addresses the key exchange\n"
            f"3. Leaves a lasting impression\n"
            f"4. Calls for resolution or action"
        )
        return await self.llm.generate(prompt, temperature=0.5)

    async def synthesize(self, topic: str, all_arguments: list[str]) -> str:
        args_text = "\n\n---\n\n".join(all_arguments)
        prompt = (
            f"Topic: {topic}\n\nAll debate arguments:\n{args_text[:3000]}\n\n"
            f"As a neutral synthesis oracle, produce a balanced resolution that:\n"
            f"1. Acknowledges the strongest points from each position\n"
            f"2. Identifies common ground\n"
            f"3. Presents a nuanced, integrated conclusion\n"
            f"4. Notes remaining areas of disagreement"
        )
        return await self.llm.generate(prompt, temperature=0.3)

    async def execute(self, task: str, context: dict[str, Any] = None) -> dict[str, Any]:
        ctx = context or {}
        positions = ctx.get("positions", {
            "pro": {"archetype": "hero", "position": "In favor"},
            "con": {"archetype": "sage", "position": "Opposed"},
            "neutral": {"archetype": "self", "position": "Balanced perspective"},
        })

        logger.info(f"Debate workflow started", task=task[:100], positions=list(positions.keys()))

        openings = {}
        for side, config in positions.items():
            openings[side] = await self.opening_statement(task, config["position"], config["archetype"])

        rebuttals = {}
        for side, config in positions.items():
            opponent = [s for s in positions if s != side]
            opp_text = "\n\n".join(openings[o] for o in opponent)
            rebuttals[side] = await self.rebuttal(task, config["position"], opp_text)

        closings = {}
        debate_summary = "\n\n".join(list(openings.values()) + list(rebuttals.values()))
        for side, config in positions.items():
            closings[side] = await self.closing(task, config["position"], debate_summary)

        all_args = list(openings.values()) + list(rebuttals.values()) + list(closings.values())
        synthesis = await self.synthesize(task, all_args)

        result = {
            "topic": task,
            "rounds_completed": len(self.ROUNDS),
            "openings": openings,
            "rebuttals": rebuttals,
            "closings": closings,
            "synthesis": synthesis,
            "status": "completed",
        }
        logger.info(f"Debate workflow completed", positions=len(positions))
        return result


DEBATE_WORKFLOW = DebateWorkflow()
