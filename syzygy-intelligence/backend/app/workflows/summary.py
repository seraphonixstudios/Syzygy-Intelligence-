"""Summary workflow — multi-document summarization with key insight extraction."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.llm.ollama_client import OllamaClient
from app.logging_setup import logger


@dataclass
class SummaryWorkflow:
    """Multi-document summarization with key insight extraction and synthesis."""

    name: str = "summary"
    description: str = "Multi-document summarization with key insight extraction and synthesis"
    required_capabilities: list[str] = field(
        default_factory=lambda: ["summarization", "information_extraction", "synthesis"]
    )
    llm: OllamaClient | None = None

    def __post_init__(self) -> None:
        if self.llm is None:
            self.llm = OllamaClient()

    async def extract_key_points(self, documents: list[str]) -> dict[str, Any]:
        assert self.llm is not None
        combined = "\n\n---DOCUMENT SEPARATOR---\n\n".join(
            doc[:2000] for doc in documents
        )
        prompt = (
            f"Extract key points from the following documents:\n\n{combined}\n\n"
            f"For each document, extract:\n"
            f"1. Main thesis or purpose\n"
            f"2. 3-5 key supporting points\n"
            f"3. Notable data, statistics, or quotes\n"
            f"4. Author's stance or bias (if detectable)"
        )
        points = await self.llm.generate(prompt, temperature=0.3)
        return {"key_points": points, "document_count": len(documents)}

    async def identify_themes(self, documents: list[str]) -> dict[str, Any]:
        assert self.llm is not None
        combined = "\n\n---DOCUMENT SEPARATOR---\n\n".join(
            doc[:2000] for doc in documents
        )
        prompt = (
            f"Analyze the following documents for cross-cutting themes:\n\n{combined}\n\n"
            f"Identify:\n"
            f"1. Recurring themes across documents\n"
            f"2. Points of consensus or agreement\n"
            f"3. Contradictions or disagreements\n"
            f"4. Unique perspectives not found elsewhere\n"
            f"5. Temporal trends (if dates are available)"
        )
        themes = await self.llm.generate(prompt, temperature=0.3)
        return {"themes": themes}

    async def generate_insights(self, key_points: dict[str, Any], themes: dict[str, Any]) -> str:
        assert self.llm is not None
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
        return await self.llm.generate(prompt, temperature=0.3)

    async def create_summary(self, task: str, key_points: dict[str, Any], themes: dict[str, Any], insights: str) -> str:
        assert self.llm is not None
        prompt = (
            f"Create a concise executive summary addressing: {task}\n\n"
            f"Key Points:\n{key_points.get('key_points', 'N/A')[:1500]}\n\n"
            f"Cross-cutting Themes:\n{themes.get('themes', 'N/A')[:1500]}\n\n"
            f"Key Insights:\n{insights[:1500]}\n\n"
            f"Write a well-structured summary with:\n"
            f"1. Overview and context\n"
            f"2. Main findings organized by theme\n"
            f"3. Critical insights and takeaways\n"
            f"4. Conclusion and next steps"
        )
        return await self.llm.generate(prompt, temperature=0.4)

    async def execute(self, task: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
        ctx = context or {}
        documents = ctx.get("documents", [task])

        logger.info("Summary workflow started", documents=len(documents))
        key_points = await self.extract_key_points(documents)
        themes = await self.identify_themes(documents)
        insights = await self.generate_insights(key_points, themes)
        summary = await self.create_summary(task, key_points, themes, insights)

        result = {
            "task": task,
            "document_count": len(documents),
            "key_points": key_points,
            "themes": themes,
            "insights": insights,
            "summary": summary,
            "status": "completed",
        }
        logger.info("Summary workflow completed")
        return result


SUMMARY_WORKFLOW = SummaryWorkflow()
