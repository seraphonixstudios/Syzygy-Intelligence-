"""Content creation pipeline — research → outline → draft → edit → polish with LLM.

The edit phase reports real diff statistics (computed, not asserted), and the
result is labeled degraded if any phase came back empty.
"""

from __future__ import annotations

import difflib
from dataclasses import dataclass, field
from typing import Any

from app.llm.model_manager import ModelManager
from app.logging_setup import logger


def _diff_stats(before: str, after: str) -> dict[str, Any]:
    """Compute real line-level diff statistics between two texts."""
    before_lines = (before or "").splitlines()
    after_lines = (after or "").splitlines()
    diff = list(difflib.unified_diff(before_lines, after_lines, lineterm=""))
    added = sum(1 for line in diff if line.startswith("+") and not line.startswith("+++"))
    removed = sum(1 for line in diff if line.startswith("-") and not line.startswith("---"))
    hunks = sum(1 for line in diff if line.startswith("@@"))
    return {
        "added_lines": added,
        "removed_lines": removed,
        "hunks": hunks,
        "diff": "\n".join(diff)[:2000],
    }


@dataclass
class ContentWorkflow:
    """Full content creation pipeline with polarity/archetype balance using LLM."""

    name: str = "content"
    description: str = "Content creation: research → outline → draft → edit → polish"
    required_capabilities: list[str] = field(
        default_factory=lambda: ["writing", "editing", "storytelling"]
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
                text = await self.llm.generate(prompt, role="creative", temperature=temperature, think=False)
            except Exception as exc:
                logger.warning("ContentWorkflow LLM call failed", error=str(exc))
                return ""
            text = (text or "").strip()
            if text:
                head = text[:40].lower()
                if not (head.startswith("[") and "error" in head):
                    return text
        return ""

    async def research(self, topic: str) -> dict[str, Any]:
        prompt = (
            f"Research the following topic thoroughly:\n\n{topic}\n\n"
            f"Provide:\n"
            f"1. Key facts and data points\n"
            f"2. Different perspectives on the topic\n"
            f"3. Notable experts or sources\n"
            f"4. Current state of understanding\n"
            f"5. Gaps or controversies"
        )
        research = await self._generate(prompt, temperature=0.4)
        return {"topic": topic, "research": research}

    async def outline(self, topic: str, research: dict[str, Any], polarity: str = "balanced") -> dict[str, Any]:
        prompt = (
            f"Topic: {topic}\n\n"
            f"Research findings:\n{research.get('research', '')[:2000]}\n\n"
            f"Create a detailed content outline with:\n"
            f"1. Compelling title/headline\n"
            f"2. Introduction hook\n"
            f"3. Main sections with key points\n"
            f"4. Balance of analytical depth ({polarity} perspective)\n"
            f"5. Conclusion with call to action"
        )
        outline = await self._generate(prompt, temperature=0.4)
        return {"topic": topic, "outline": outline, "polarity": polarity}

    async def draft(self, outline: dict[str, Any], polarity: str = "balanced") -> dict[str, Any]:
        prompt = (
            f"Write a complete content draft based on this outline:\n\n"
            f"{outline.get('outline', '')[:3000]}\n\n"
            f"Style: Professional yet engaging. "
            f"{'Balance analytical rigor with accessibility.' if polarity == 'balanced' else ''}"
            f"{'Emphasize structure and evidence.' if polarity == 'masculine' else ''}"
            f"{'Emphasize narrative and connection.' if polarity == 'feminine' else ''}\n\n"
            f"Write at least 500 words."
        )
        draft = await self._generate(prompt, temperature=0.5)
        return {"draft": draft, "word_count": len(draft.split())}

    async def edit(self, draft: dict[str, Any], feedback: str = "") -> dict[str, Any]:
        original = draft.get("draft", "")
        prompt = (
            f"Edit the following content for clarity, flow, and impact:\n\n"
            f"{original[:4000]}\n\n"
            f"Focus on:\n"
            f"1. Sentence structure and flow\n"
            f"2. Clarity of arguments\n"
            f"3. Engagement and readability\n"
            f"4. Grammar and style\n"
            f"{f'Additional feedback: {feedback}' if feedback else ''}\n\n"
            f"Return the complete edited version."
        )
        edited = await self._generate(prompt, temperature=0.3)
        stats = _diff_stats(original, edited)
        changes = (
            f"{stats['added_lines']} additions, {stats['removed_lines']} deletions "
            f"across {stats['hunks']} hunk(s)"
        )
        return {
            "edited": edited,
            "changes": changes,
            "diff": stats["diff"],
            "word_count": len(edited.split()),
        }

    async def polish(self, edited: dict[str, Any]) -> dict[str, Any]:
        prompt = (
            f"Do a final polish pass on this content:\n\n"
            f"{edited.get('edited', '')[:4000]}\n\n"
            f"Check:\n"
            f"1. Opening hook strength\n"
            f"2. Closing impact\n"
            f"3. Transitions between sections\n"
            f"4. Consistency of voice\n"
            f"5. No redundancy\n\n"
            f"Return the final polished version."
        )
        polished = await self._generate(prompt, temperature=0.3)
        return {"polished": polished, "word_count": len(polished.split())}

    async def execute(self, task: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
        ctx = context or {}
        polarity = ctx.get("polarity", "balanced")

        logger.info("Content workflow started", task=task[:100], polarity=polarity)

        r = await self.research(task)
        o = await self.outline(task, r, polarity)
        d = await self.draft(o, polarity)
        e = await self.edit(d, ctx.get("feedback", ""))
        p = await self.polish(e)

        degraded = not all([r.get("research"), o.get("outline"), d.get("draft"), e.get("edited"), p.get("polished")])
        if degraded:
            logger.warning("ContentWorkflow completed with empty phases", task=task[:100])
        result = {
            "topic": task,
            "polarity": polarity,
            "research": r,
            "outline": o,
            "draft": d,
            "edited": e,
            "final": p,
            "degraded": degraded,
            "status": "completed",
        }
        logger.info("Content workflow completed", word_count=p.get("word_count", 0))
        return result


CONTENT_WORKFLOW = ContentWorkflow()
