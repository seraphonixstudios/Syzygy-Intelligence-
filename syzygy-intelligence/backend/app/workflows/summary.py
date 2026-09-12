"""Summary workflow — multi-document summarization with key insight extraction.

Compression is measured, not claimed: results carry input/output word counts
and the ratio between them. Documents are numbered so extracted points stay
traceable to their source document. Empty input is reported, not padded.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.llm.model_manager import ModelManager
from app.logging_setup import logger


def _word_count(text: str) -> int:
    return len((text or "").split())


def _numbered(documents: list[str]) -> str:
    from app.text_utils import truncate

    return "\n\n".join(
        f"--- Document {i + 1} ---\n{truncate(doc, 12000)}" for i, doc in enumerate(documents)
    )


@dataclass
class SummaryWorkflow:
    """Multi-document summarization with key insight extraction and synthesis."""

    name: str = "summary"
    description: str = "Multi-document summarization with key insight extraction and synthesis"
    required_capabilities: list[str] = field(
        default_factory=lambda: ["summarization", "information_extraction", "synthesis"]
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
                text = await self.llm.generate(prompt, role="synthesis", temperature=temperature, think=False)
            except Exception as exc:
                logger.warning("SummaryWorkflow LLM call failed", error=str(exc))
                return ""
            text = (text or "").strip()
            if text:
                head = text[:40].lower()
                if not (head.startswith("[") and "error" in head):
                    return text
        return ""

    async def extract_key_points(self, documents: list[str]) -> dict[str, Any]:
        combined = _numbered(documents)
        prompt = (
            f"Extract key points from the following documents:\n\n{combined}\n\n"
            f"For each document (cite its number), extract:\n"
            f"1. Main thesis or purpose\n"
            f"2. 3-5 key supporting points\n"
            f"3. Notable data, statistics, or quotes\n"
            f"4. Author's stance or bias (if detectable)"
        )
        points = await self._generate(prompt, temperature=0.3)
        return {"key_points": points, "document_count": len(documents)}

    async def identify_themes(self, documents: list[str]) -> dict[str, Any]:
        combined = _numbered(documents)
        prompt = (
            f"Analyze the following documents for cross-cutting themes:\n\n{combined}\n\n"
            f"Identify:\n"
            f"1. Recurring themes across documents\n"
            f"2. Points of consensus or agreement\n"
            f"3. Contradictions or disagreements\n"
            f"4. Unique perspectives not found elsewhere\n"
            f"5. Temporal trends (if dates are available)"
        )
        themes = await self._generate(prompt, temperature=0.3)
        return {"themes": themes}

    async def generate_insights(self, key_points: dict[str, Any], themes: dict[str, Any]) -> str:
        prompt = (
            f"Based on the extracted key points and themes, generate actionable insights:\n\n"
            f"Key Points:\n{key_points.get('key_points', 'N/A')[:2000]}\n\n"
            f"Themes:\n{themes.get('themes', 'N/A')[:2000]}\n\n"
            f"Provide:\n"
            f"1. Top 5 most important insights\n"
            f"2. Implications and recommended actions\n"
            f"3. Knowledge gaps that need further research\n"
            f"4. Confidence assessment for each insight"
        )
        return await self._generate(prompt, temperature=0.3)

    async def create_summary(self, task: str, key_points: dict[str, Any], themes: dict[str, Any], insights: str) -> str:
        prompt = (
            f"Create a concise executive summary addressing: {task}\n\n"
            f"Key Points:\n{key_points.get('key_points', 'N/A')[:1500]}\n\n"
            f"Cross-cutting Themes:\n{themes.get('themes', 'N/A')[:1500]}\n\n"
            f"Key Insights:\n{insights[:1500]}\n\n"
            f"Write a well-structured summary with:\n"
            f"1. Overview and context\n"
            f"2. Main findings organized by theme\n"
            f"3. Critical insights and takeaways\n"
            f"4. Conclusion and next steps\n\n"
            f"Keep it strictly shorter than the source material above."
        )
        return await self._generate(prompt, temperature=0.4)

    async def execute(self, task: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
        ctx = context or {}
        documents = [doc for doc in ctx.get("documents", [task]) if doc and doc.strip()]

        logger.info("Summary workflow started", documents=len(documents))
        if not documents:
            return {
                "task": task,
                "document_count": 0,
                "summary": "",
                "note": "No documents provided — nothing to summarize.",
                "status": "completed",
            }
        key_points = await self.extract_key_points(documents)
        themes = await self.identify_themes(documents)
        insights = await self.generate_insights(key_points, themes)
        summary = await self.create_summary(task, key_points, themes, insights)

        input_words = sum(_word_count(doc) for doc in documents)
        summary_words = _word_count(summary)
        if summary and input_words and summary_words >= input_words:
            # One condense retry — a summary longer than its sources is a failed summary.
            shorter = await self._generate(
                f"Condense the following summary to under {input_words} words "
                f"without losing key facts:\n\n{summary[:3000]}",
                temperature=0.3,
            )
            if shorter and _word_count(shorter) < summary_words:
                summary = shorter
                summary_words = _word_count(summary)
        compression = round(summary_words / input_words, 3) if input_words else 0.0

        result = {
            "task": task,
            "document_count": len(documents),
            "input_words": input_words,
            "summary_words": summary_words,
            "compression_ratio": compression,
            "key_points": key_points,
            "themes": themes,
            "insights": insights,
            "summary": summary,
            "status": "completed",
        }
        logger.info("Summary workflow completed", compression=compression)
        return result


SUMMARY_WORKFLOW = SummaryWorkflow()
