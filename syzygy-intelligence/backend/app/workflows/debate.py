"""Debate workflow — structured multi-agent debate with polarity-aware positions and LLM.

Every listed round actually runs (including cross-examination), the completed
count is measured (not asserted), and each opening is judged for stance and
quality. Anything the judge cannot parse is reported as unknown, never invented.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any

from app.llm.model_manager import ModelManager
from app.logging_setup import logger
from app.text_utils import truncate

_STANCES = ("supports", "opposes", "neutral", "unknown")


def _parse_json_obj(text: str) -> dict[str, Any] | None:
    """Leniently extract a JSON object from LLM output."""
    if not text:
        return None
    fenced = re.search(r"```(?:json)?\n(.*?)```", text, re.DOTALL)
    candidate = fenced.group(1).strip() if fenced else text.strip()
    start, end = candidate.find("{"), candidate.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return None
    try:
        parsed = json.loads(candidate[start : end + 1])
    except (json.JSONDecodeError, ValueError):
        return None
    return parsed if isinstance(parsed, dict) else None


def _normalize_judgment(raw: dict[str, Any]) -> dict[str, Any]:
    try:
        score = float(raw.get("score", 0.0))
    except (TypeError, ValueError):
        score = 0.0
    score = max(0.0, min(10.0, score))
    stance = str(raw.get("stance", "unknown")).lower()
    if stance not in _STANCES:
        stance = "unknown"
    return {"score": round(score, 1), "stance": stance, "notes": str(raw.get("notes", ""))[:500]}


@dataclass
class DebateWorkflow:
    """Structured multi-agent debate with polarity-aware positions."""

    ROUNDS = ["opening", "rebuttal", "cross_examination", "closing", "synthesis"]

    name: str = "debate"
    description: str = "Multi-agent structured debate with polarity-aware positions"
    required_capabilities: list[str] = field(
        default_factory=lambda: ["argumentation", "critique", "synthesis"]
    )
    llm: ModelManager | None = None

    def __post_init__(self) -> None:
        if self.llm is None:
            self.llm: ModelManager = ModelManager()

    async def _generate(self, prompt: str, temperature: float = 0.4) -> str:
        """Call the LLM (no chain-of-thought). Returns "" when unreachable/failed."""
        assert self.llm is not None
        for _ in (1, 2):
            try:
                text = await self.llm.generate(prompt, role="critic", temperature=temperature, think=False)
            except Exception as exc:
                logger.warning("DebateWorkflow LLM call failed", error=str(exc))
                return ""
            text = (text or "").strip()
            if text:
                head = text[:40].lower()
                if not (head.startswith("[") and "error" in head):
                    return text
        return ""

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
        return await self._generate(prompt, temperature=0.5)

    async def rebuttal(self, topic: str, position: str, opponent_opening: str) -> str:
        prompt = (
            f"Topic: {topic}\nYour position: {position}\n\n"
            f"Opponent's opening statement:\n{truncate(opponent_opening, 8000)}\n\n"
            f"Write a sharp rebuttal (2 paragraphs) that:\n"
            f"1. Identifies weaknesses in the opponent's argument\n"
            f"2. Provides counter-evidence or counter-examples\n"
            f"3. Reinforces your own position\n"
            f"4. Is respectful but firm"
        )
        return await self._generate(prompt, temperature=0.5)

    async def cross_examine(self, topic: str, position: str, opponent_args: str) -> str:
        prompt = (
            f"Topic: {topic}\nYour position: {position}\n\n"
            f"Opponent's arguments:\n{truncate(opponent_args, 8000)}\n\n"
            f"Ask 3-5 penetrating questions that expose assumptions, "
            f"logical gaps, or unaddressed implications in the opponent's position."
        )
        return await self._generate(prompt, temperature=0.5)

    async def closing(self, topic: str, position: str, debate_summary: str) -> str:
        prompt = (
            f"Topic: {topic}\nYour position: {position}\n\n"
            f"Debate summary:\n{truncate(debate_summary, 8000)}\n\n"
            f"Write a compelling closing statement (2 paragraphs) that:\n"
            f"1. Summarizes your strongest points\n"
            f"2. Addresses the key exchange\n"
            f"3. Leaves a lasting impression\n"
            f"4. Calls for resolution or action"
        )
        return await self._generate(prompt, temperature=0.5)

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
        return await self._generate(prompt, temperature=0.3)

    async def judge_statement(self, topic: str, position: str, text: str) -> dict[str, Any]:
        """Judge one statement: quality score + whether it actually holds its position."""
        if not text.strip():
            return {"score": None, "stance": "unknown", "notes": "Nothing to judge."}
        prompt = (
            f"Topic: {topic}\nAssigned position: {position}\n\n"
            f"Statement to judge:\n{truncate(text, 8000)}\n\n"
            f"You are an impartial debate judge. Return ONLY a JSON object "
            f'{{"score": 0-10 argument quality, "stance": "supports"|"opposes"|"neutral" '
            f"(stance of the statement TOWARD the assigned position), "
            f'"notes": "one-sentence justification"}}.'
        )
        raw_text = await self._generate(prompt, temperature=0.2)
        parsed = _parse_json_obj(raw_text)
        if parsed is None:
            return {"score": None, "stance": "unknown", "notes": raw_text[:500]}
        return _normalize_judgment(parsed)

    def _normalize_positions(self, positions: dict[str, Any]) -> dict[str, dict[str, str]]:
        normalized: dict[str, dict[str, str]] = {}
        for side, config in positions.items():
            if not isinstance(config, dict):
                config = {}
            normalized[side] = {
                "archetype": str(config.get("archetype", side)),
                "position": str(config.get("position", side)),
            }
        return normalized or {
            "pro": {"archetype": "hero", "position": "In favor"},
            "con": {"archetype": "sage", "position": "Opposed"},
        }

    async def execute(self, task: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
        ctx = context or {}
        positions = self._normalize_positions(ctx.get("positions", {
            "pro": {"archetype": "hero", "position": "In favor"},
            "con": {"archetype": "sage", "position": "Opposed"},
            "neutral": {"archetype": "self", "position": "Balanced perspective"},
        }))

        logger.info("Debate workflow started", task=task[:100], positions=list(positions.keys()))

        rounds_run: list[str] = []

        openings = {}
        for side, config in positions.items():
            openings[side] = await self.opening_statement(task, config["position"], config["archetype"])
        if all(openings.values()):
            rounds_run.append("opening")

        rebuttals = {}
        for side, config in positions.items():
            opponent = [s for s in positions if s != side]
            opp_text = "\n\n".join(openings[o] for o in opponent)
            rebuttals[side] = await self.rebuttal(task, config["position"], opp_text)
        if all(rebuttals.values()):
            rounds_run.append("rebuttal")

        cross_examinations = {}
        for side, config in positions.items():
            opponent = [s for s in positions if s != side]
            opp_text = "\n\n".join(openings[o] for o in opponent)
            if rebuttals.get(side):
                opp_text += "\n\n" + str(rebuttals[side])
            cross_examinations[side] = await self.cross_examine(task, config["position"], opp_text)
        if all(cross_examinations.values()):
            rounds_run.append("cross_examination")

        closings = {}
        debate_summary = "\n\n".join(
            list(openings.values()) + list(rebuttals.values()) + list(cross_examinations.values())
        )
        for side, config in positions.items():
            closings[side] = await self.closing(task, config["position"], debate_summary)
        if all(closings.values()):
            rounds_run.append("closing")

        judging = {}
        for side, config in positions.items():
            judging[side] = await self.judge_statement(task, config["position"], openings.get(side, ""))

        all_args = list(openings.values()) + list(rebuttals.values()) + list(cross_examinations.values())
        all_args += list(closings.values())
        synthesis = await self.synthesize(task, all_args)
        if synthesis:
            rounds_run.append("synthesis")

        degraded = len(rounds_run) < len(self.ROUNDS)
        if degraded:
            logger.warning("DebateWorkflow completed with missing rounds", rounds=rounds_run)

        result = {
            "topic": task,
            "rounds_run": rounds_run,
            "rounds_completed": len(rounds_run),
            "openings": openings,
            "rebuttals": rebuttals,
            "cross_examinations": cross_examinations,
            "closings": closings,
            "judging": judging,
            "synthesis": synthesis,
            "degraded": degraded,
            "status": "completed",
        }
        logger.info("Debate workflow completed", positions=len(positions), rounds=rounds_run)
        return result


DEBATE_WORKFLOW = DebateWorkflow()
