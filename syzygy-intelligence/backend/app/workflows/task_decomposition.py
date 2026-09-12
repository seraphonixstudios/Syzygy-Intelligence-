"""Task decomposition — breaks complex tasks into subtasks with LLM-powered analysis.

Grounded version: the LLM is prompted to return strict JSON matching a known schema.
If the output cannot be parsed, the workflow records ``structured:false`` and falls
back to a minimal deterministic set of subtasks.  All LLM calls go through the
shared ``_generate`` helper (error‑prefix guard, sentence‑boundary truncation).
"""

from __future__ import annotations

import json
import re
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from app.llm.model_manager import ModelManager
from app.logging_setup import logger
from app.text_utils import truncate

_SCHEMA = {
    "type": "object",
    "properties": {
        "subtasks": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "description": {"type": "string"},
                    "dependencies": {
                        "type": "array",
                        "items": {"type": "string"},
                        "default": [],
                    },
                    "agent_archetype": {
                        "type": "string",
                        "enum": [
                            "sage",
                            "hero",
                            "ruler",
                            "magician",
                            "explorer",
                            "great_mother",
                            "lover",
                            "innocent",
                            "creator",
                            "anima",
                            "self",
                            "hermes",
                            "trickster",
                        ],
                    },
                    "polarity": {"type": "string", "enum": ["masculine", "feminine", "unified"]},
                    "priority": {"type": "integer", "minimum": 1, "maximum": 5},
                },
                "required": ["id", "description", "agent_archetype", "polarity", "priority"],
            },
        }
    },
    "required": ["subtasks"],
}


def _safe_json_loads(text: str) -> dict[str, Any] | None:
    """Try to parse ``text`` as JSON; return ``None`` on any failure."""
    if not text:
        return None
    try:
        return json.loads(text.strip())
    except (json.JSONDecodeError, ValueError):
        return None


def _extract_json_object(text: str) -> str | None:
    """Find the innermost ``{...}`` block and return it; return ``None`` if absent."""
    if not text:
        return None
    # Strip out fenced code blocks first
    cleaned = re.sub(r"```(?:json)?\n.*?```", "", text, flags=re.DOTALL)
    start = cleaned.find("{")
    if start == -1:
        return None
    # Find matching closing brace by counting depth (outside strings)
    depth = 0
    in_string = False
    escape = False
    for i in range(start, len(cleaned)):
        ch = cleaned[i]
        if escape:
            escape = False
            continue
        if ch == "\\" and in_string:
            escape = True
            continue
        if ch == '"':
            in_string = not in_string
            continue
        if not in_string:
            if ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    return cleaned[start : i + 1]
    return None


def _schema_valid(data: dict[str, Any]) -> bool:
    """Validate that *data* conforms to the expected subtask schema."""
    if not isinstance(data, dict) or "subtasks" not in data:
        return False
    for item in data["subtasks"]:
        required = {"id", "description", "agent_archetype", "polarity", "priority"}
        if not required.issubset(item.keys()):
            return False
        if not isinstance(item["id"], str):
            return False
        if not isinstance(item["description"], str):
            return False
        allowed_archetypes = {
            "sage", "hero", "ruler", "magician", "explorer",
            "great_mother", "lover", "innocent", "creator",
            "anima", "self", "hermes", "trickster",
        }
        if item["agent_archetype"] not in allowed_archetypes:
            return False
        if item["polarity"] not in ("masculine", "feminine", "unified"):
            return False
        if not isinstance(item["priority"], int) or not (1 <= item["priority"] <= 5):
            return False
    return True


@dataclass
class Subtask:
    id: str = ""
    description: str = ""
    dependencies: list[str] = field(default_factory=list)
    agent_archetype: str = "sage"
    polarity: str = "unified"
    priority: int = 0
    result: str = ""


@dataclass
class TaskDecompositionWorkflow:
    """Grounded task decomposition: JSON schema, provenance flags, honest fallbacks."""

    name: str = "task_decomposition"
    description: str = "Break complex tasks into manageable subtasks with dependency analysis"
    required_capabilities: list[str] = field(
        default_factory=lambda: ["analysis", "planning"]
    )
    llm: ModelManager | None = None

    def __post_init__(self) -> None:
        if self.llm is None:
            self.llm: ModelManager = ModelManager()

    async def _generate(self, prompt: str, temperature: float = 0.3) -> str:
        """Call the LLM (no chain-of-thought). Returns ``""`` when unreachable/failed."""
        assert self.llm is not None
        for _ in (1, 2):
            try:
                text = await self.llm.generate(prompt, role="sage", temperature=temperature, think=False)
            except Exception as exc:
                logger.warning("TaskDecompositionWorkflow LLM call failed", error=str(exc))
                return ""
            text = (text or "").strip()
            head = text[:40].lower()
            if not (head.startswith("[") and "error" in head):
                return text
        return ""

    async def decompose(self, task: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
        ctx = context or {}
        prompt = (
            f"Decompose the following complex task into manageable subtasks. "
            f"Return STRICT JSON with a single top-level key \"subtasks\" whose value is an "
            f"array of objects. Each object must have the keys: id (string), description "
            f"(one sentence), dependencies (array of subtask IDs, may be empty), "
            f"agent_archetype (choose from: sage, hero, ruler, magician, explorer, "
            f"great_mother, lover, innocent, creator, anima, self, hermes, trickster), "
            f"polarity (masculine, feminine, or unified), priority (1-5, 5=highest).\n\n"
            f"Task: {task}"
        )
        raw = await self._generate(prompt, temperature=0.3)

        # Attempt to extract a JSON object from the LLM output
        json_str = _extract_json_object(raw) or raw
        parsed = _safe_json_loads(json_str)

        structured = parsed is not None and _schema_valid(parsed)
        if structured and isinstance(parsed.get("subtasks"), list):
            subtasks = self._dicts_to_subtasks(parsed["subtasks"])
        else:
            subtasks = self._fallback_subtasks(task)
            structured = False

        logger.info(
            "Task decomposed",
            task=task[:80],
            subtask_count=len(subtasks),
            structured=structured,
        )
        return {
            "task": task,
            "subtasks": subtasks,
            "structured": structured,
            "fallback_used": not structured,
        }

    @staticmethod
    def _schema_valid(data: dict[str, Any]) -> bool:
        """Very light validation: required keys present and correct types."""
        if not isinstance(data, dict) or "subtasks" not in data:
            return False
        for item in data["subtasks"]:
            required = {"id", "description", "agent_archetype", "polarity", "priority"}
            if not required.issubset(item.keys()):
                return False
            if not isinstance(item["id"], str):
                return False
            if not isinstance(item["description"], str):
                return False
            if item["agent_archetype"] not in {
                "sage",
                "hero",
                "ruler",
                "magician",
                "explorer",
                "great_mother",
                "lover",
                "innocent",
                "creator",
                "anima",
                "self",
                "hermes",
                "trickster",
            }:
                return False
            if item["polarity"] not in ("masculine", "feminine", "unified"):
                return False
            if not isinstance(item["priority"], int) or not (1 <= item["priority"] <= 5):
                return False
        return True

    @staticmethod
    def _dicts_to_subtasks(dicts: list[dict[str, Any]]) -> list[Subtask]:
        out: list[Subtask] = []
        for d in dicts:
            out.append(
                Subtask(
                    id=str(d.get("id", "")),
                    description=str(d.get("description", "")),
                    dependencies=[str(x) for x in d.get("dependencies", [])],
                    agent_archetype=str(d.get("agent_archetype", "sage")),
                    polarity=str(d.get("polarity", "unified")),
                    priority=int(d.get("priority", 0)),
                )
            )
        return out

    @staticmethod
    def _fallback_subtasks(task: str) -> list[Subtask]:
        return [
            Subtask(
                id="analysis_1",
                description=f"Analyze requirements for: {task[:100]}",
                agent_archetype="sage",
                polarity="masculine",
                priority=1,
            ),
            Subtask(
                id="research_1",
                description="Gather relevant information",
                dependencies=["analysis_1"],
                agent_archetype="sage",
                polarity="masculine",
                priority=2,
            ),
            Subtask(
                id="creative_1",
                description="Generate approaches and solutions",
                dependencies=["research_1"],
                agent_archetype="creator",
                polarity="feminine",
                priority=3,
            ),
            Subtask(
                id="development_1",
                description="Execute the primary work",
                dependencies=["creative_1"],
                agent_archetype="hero",
                polarity="masculine",
                priority=4,
            ),
            Subtask(
                id="review_1",
                description="Review and refine the output",
                dependencies=["development_1"],
                agent_archetype="trickster",
                polarity="unified",
                priority=4,
            ),
            Subtask(
                id="synthesis_1",
                description="Synthesize final output with balanced perspective",
                dependencies=[
                    "analysis_1",
                    "research_1",
                    "creative_1",
                    "development_1",
                    "review_1",
                ],
                agent_archetype="self",
                polarity="unified",
                priority=5,
            ),
        ]

    async def execute(
        self,
        task: str,
        context: dict[str, Any] | None = None,
        on_subtask_complete: Callable[..., Any] | None = None,
    ) -> dict[str, Any]:
        ctx = context or {}
        result = await self.decompose(task, ctx)

        # Run optional subtask completion callbacks if desired
        subtasks = result.get("subtasks", [])
        completed: set[str] = set()
        for i, subtask in enumerate(subtasks):
            deps_met = all(d in completed for d in subtask.dependencies)
            if deps_met:
                subtask.status = "in_progress"
                prompt = (
                    f"Task: {subtask.description}\n"
                    f"Main project: {task[:200]}\n"
                    f"Agent archetype: {subtask.agent_archetype}\n"
                    f"Polarity: {subtask.polarity}\n\n"
                    f"Provide a brief output for this subtask."
                )
                result_sub = await self._generate(prompt, temperature=0.3)
                subtask.result = result_sub
                subtask.status = "completed"
                completed.add(subtask.id)
                if on_subtask_complete:
                    try:
                        await on_subtask_complete(subtask)
                    except Exception as exc:
                        logger.warning("on_subtask_complete callback failed", error=str(exc))

        return {
            "task": task,
            "subtasks": subtasks,
            "structured": result.get("structured", False),
            "fallback_used": result.get("fallback_used", True),
            "status": "completed",
        }


TASK_DECOMPOSITION_WORKFLOW = TaskDecompositionWorkflow()