"""Interview Coach workflow — role-specific questions, practice-answer evaluation, scoring feedback.

Scores come from a structured rubric parse: dimensions bounded 1-10 with the
average as overall; unparseable verdicts are labeled. Empty answers are
reported honestly instead of skipping silently.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any

from app.llm.model_manager import ModelManager
from app.logging_setup import logger
from app.text_utils import truncate

_DIMENSIONS = ["correctness", "completeness", "structure", "depth", "communication"]


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


def _safe_float(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _normalize_eval(raw: dict[str, Any]) -> dict[str, Any]:
    dims = {
        dim: (max(0.0, min(10.0, value)) if (value := _safe_float(raw.get(dim))) is not None else None)
        for dim in _DIMENSIONS
    }
    measured = [value for value in dims.values() if value is not None]
    overall = round(sum(measured) / len(measured), 2) if measured else None
    return {
        **dims,
        "overall": overall,
        "strengths": str(raw.get("strengths", ""))[:500],
        "weaknesses": str(raw.get("weaknesses", ""))[:500],
        "improvements": str(raw.get("improvements", ""))[:500],
    }


@dataclass
class InterviewCoachWorkflow:
    """Grounded interview coaching: structured rubric parsing, honest provenance."""

    name: str = "interview_coach"
    description: str = "Role-specific interview questions, practice answer evaluation, and scoring feedback"
    required_capabilities: list[str] = field(
        default_factory=lambda: ["question_generation", "answer_evaluation", "feedback_scoring"]
    )
    llm: ModelManager | None = None

    def __post_init__(self) -> None:
        if self.llm is None:
            self.llm: ModelManager = ModelManager()

    async def _generate(self, prompt: str, temperature: float = 0.3) -> str:
        """Call the LLM (no chain-of-thought). Returns "" when unreachable/failed."""
        assert self.llm is not None
        for _ in (1, 2):
            try:
                text = await self.llm.generate(prompt, role="sage", temperature=temperature, think=False)
            except Exception as exc:
                logger.warning("InterviewCoachWorkflow LLM call failed", error=str(exc))
                return ""
            text = (text or "").strip()
            if text:
                head = text[:40].lower()
                if not (head.startswith("[") and "error" in head):
                    return text
        return ""

    async def generate_questions(self, role: str, difficulty: str, count: int) -> dict[str, Any]:
        prompt = (
            f"Generate {count} {difficulty}-level interview questions for a {role} position.\n\n"
            f"For each question provide:\n"
            f"1. The question text and category (technical / behavioral / system-design / situational)\n"
            f"2. What a good answer covers\n"
            f"3. Ideal answer key points\n\n"
            f"Cover a range of topics relevant to {role}."
        )
        result = await self._generate(prompt, temperature=0.4)
        return {"questions": result, "role": role, "difficulty": difficulty, "count": count}

    async def evaluate_answer(self, question: str, answer: str, role: str) -> dict[str, Any]:
        prompt = (
            f"Evaluate the following interview answer for a {role} position:\n\n"
            f"Question: {question}\n\n"
            f"Candidate Answer: {truncate(answer, 4000)}\n\n"
            f"Return ONLY a JSON object with each of these dimensions as 1-10 numbers, "
            f'plus "strengths", "weaknesses", and "improvements" strings:\n'
            f"correctness, completeness, structure, depth, communication"
        )
        raw = await self._generate(prompt, temperature=0.3)
        parsed = _parse_json_obj(raw)
        if parsed is None:
            return {
                "question": question,
                "evaluation": {
                    "overall": None,
                    "notes": raw[:500],
                    "structured": False,
                },
            }
        normalized = _normalize_eval(parsed)
        return {"question": question, "evaluation": {"structured": True, **normalized}}

    async def generate_feedback(self, evaluations: list[dict[str, Any]]) -> str:
        combined = "\n\n".join(
            f"Q: {e.get('question', '')}\nEvaluation: {e.get('evaluation', '')}"
            for e in evaluations
        )
        prompt = (
            f"Based on the following interview answer evaluations, generate comprehensive feedback:\n\n"
            f"{combined}\n\n"
            f"Provide:\n"
            f"1. Overall performance summary\n"
            f"2. Key strengths (top 3)\n"
            f"3. Areas for improvement (top 3)\n"
            f"4. Recommended preparation resources\n"
            f"5. Estimated readiness level (Strong / Good / Needs Work / Weak)"
        )
        return await self._generate(prompt, temperature=0.3)

    async def execute(self, task: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
        ctx = context or {}
        role = ctx.get("role", task)
        difficulty = ctx.get("difficulty", "medium")
        count = ctx.get("question_count", 5)
        answers = ctx.get("answers", [])

        logger.info("Interview Coach workflow started", role=role, difficulty=difficulty)
        questions = await self.generate_questions(role, difficulty, count)

        evaluations = []
        notes = ""
        if answers:
            for item in answers:
                q = item.get("question", "")
                a = item.get("answer", "")
                if q and a:
                    ev = await self.evaluate_answer(q, a, role)
                    evaluations.append(ev)
        else:
            notes = "no practice answers provided — generated questions only"

        feedback = None
        if evaluations:
            feedback = await self.generate_feedback(evaluations)

        result = {
            "task": task,
            "role": role,
            "difficulty": difficulty,
            "questions": questions,
            "evaluations": evaluations,
            "notes": notes,
            "evaluations_present": len(evaluations),
            "structured_evals": sum(1 for e in evaluations if e["evaluation"].get("structured")),
            "feedback": feedback,
            "status": "completed",
        }
        logger.info("Interview Coach workflow completed", evaluations=len(evaluations))
        return result


INTERVIEW_COACH_WORKFLOW = InterviewCoachWorkflow()
