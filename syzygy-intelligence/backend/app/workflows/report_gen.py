"""Report Generator workflow — multi-format structured reports with charts, tables, and executive summaries."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.llm.model_manager import ModelManager
from app.logging_setup import logger


@dataclass
class ReportGenWorkflow:
    """Multi-format structured reports with charts, tables, and executive summaries."""

    name: str = "report_gen"
    description: str = "Multi-format structured reports with charts, tables, and executive summaries"
    required_capabilities: list[str] = field(
        default_factory=lambda: ["research", "writing", "data_visualization", "formatting"]
    )
    llm: ModelManager | None = None

    def __post_init__(self) -> None:
        if self.llm is None:
            self.llm: ModelManager = ModelManager()

    async def research_topic(self, topic: str) -> dict[str, Any]:
        assert self.llm is not None
        prompt = (
            f"Research the following topic and compile comprehensive information:\n\n{topic}\n\n"
            f"Gather:\n"
            f"1. Key facts and statistics\n"
            f"2. Current state of the art\n"
            f"3. Major players and stakeholders\n"
            f"4. Trends and future outlook\n"
            f"5. Controversies or debates\n"
            f"6. Relevant data points with sources"
        )
        research = await self.llm.generate(prompt, temperature=0.3)
        return {"research": research}

    async def outline_report(self, topic: str, research: dict[str, Any], sections: list[str]) -> dict[str, Any]:
        assert self.llm is not None
        prompt = (
            f"Create a detailed report outline for: {topic}\n\n"
            f"Research:\n{research.get('research', '')[:2000]}\n\n"
            f"Required sections: {', '.join(sections) if sections else 'Auto-generate'}\n\n"
            f"For each section provide:\n"
            f"1. Section title and purpose\n"
            f"2. Key points to cover\n"
            f"3. Data or visuals needed\n"
            f"4. Estimated length (paragraphs)"
        )
        outline = await self.llm.generate(prompt, temperature=0.3)
        return {"outline": outline, "sections": sections}

    async def generate_section(self, topic: str, section_title: str, research: dict[str, Any]) -> str:
        assert self.llm is not None
        prompt = (
            f"Write the following section of a report on '{topic}':\n\n"
            f"Section: {section_title}\n\n"
            f"Research Context:\n{research.get('research', '')[:2000]}\n\n"
            f"Write in a professional tone with clear subheadings. "
            f"Include specific data points where relevant. "
            f"Use markdown formatting."
        )
        return await self.llm.generate(prompt, temperature=0.4)

    async def generate_executive_summary(self, topic: str, sections: list[str]) -> str:
        assert self.llm is not None
        combined = "\n\n".join(sections)
        prompt = (
            f"Write an executive summary for a report on '{topic}':\n\n"
            f"Report Body:\n{combined[:3000]}\n\n"
            f"Provide:\n"
            f"1. Problem statement and context (2-3 sentences)\n"
            f"2. Key findings (3-5 bullet points)\n"
            f"3. Recommendations (2-3 bullet points)\n"
            f"4. Conclusion (1-2 sentences)"
        )
        return await self.llm.generate(prompt, temperature=0.3)

    async def format_report(self, topic: str, summary: str, sections: list[str], output_format: str) -> str:
        assert self.llm is not None
        combined = "\n\n".join(sections)
        prompt = (
            f"Compile the following into a complete {output_format} report:\n\n"
            f"Title: {topic}\n\n"
            f"Executive Summary:\n{summary}\n\n"
            f"Body:\n{combined[:4000]}\n\n"
            f"Format as {output_format} with:\n"
            f"1. Title page / header\n"
            f"2. Table of contents\n"
            f"3. Proper section hierarchy\n"
            f"4. Page numbers / references\n"
            f"5. Conclusion and next steps"
        )
        return await self.llm.generate(prompt, temperature=0.3)

    async def execute(self, task: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
        ctx = context or {}
        topic = ctx.get("topic", task)
        sections_list = ctx.get("sections", [])
        output_format = ctx.get("format", "markdown")

        logger.info("Report Generator workflow started", format=output_format)
        research = await self.research_topic(topic)
        outline = await self.outline_report(topic, research, sections_list)

        section_texts = []
        outline_text = outline.get("outline", "")
        import re
        section_titles = re.findall(r'(?:^|\n)(?:#+\s*|Section:\s*|##\s*)(.+?)(?:\n|$)', outline_text)
        if not section_titles:
            section_titles = ["Introduction", "Background", "Analysis", "Findings", "Conclusion"]

        for title in section_titles[:8]:
            text = await self.generate_section(topic, title.strip(), research)
            section_texts.append(text)

        exec_summary = await self.generate_executive_summary(topic, section_texts)
        report = await self.format_report(topic, exec_summary, section_texts, output_format)

        result = {
            "task": task,
            "topic": topic,
            "format": output_format,
            "research": research,
            "outline": outline,
            "sections": section_texts,
            "executive_summary": exec_summary,
            "report": report,
            "status": "completed",
        }
        logger.info("Report Generator workflow completed")
        return result


REPORT_GEN_WORKFLOW = ReportGenWorkflow()
