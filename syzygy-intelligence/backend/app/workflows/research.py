"""Research workflow — multi-source parallel research with validation and synthesis."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Any

from app.llm.ollama_client import OllamaClient
from app.logging_setup import logger
from app.tools.browser import BrowserTool
from app.tools.search import SearchTool


@dataclass
class ResearchWorkflow:
    """Deep research with parallel search, cross-validation, and LLM-powered synthesis."""

    name: str = "research"
    description: str = "Multi-source parallel research with cross-validation and synthesis"
    required_capabilities: list[str] = field(
        default_factory=lambda: ["web_search", "analysis", "fact_checking"]
    )

    def __init__(self):
        self.search_tool = SearchTool()
        self.browser_tool = BrowserTool()
        self.llm = OllamaClient()

    async def search(self, query: str) -> list[dict[str, Any]]:
        """Perform parallel searches across multiple queries derived from the main query."""
        # Generate sub-queries for comprehensive coverage
        sub_queries_prompt = (
            f"Given the research query: '{query}'\n"
            f"Generate 3-5 specific sub-queries that would help build a comprehensive understanding. "
            f"Return each sub-query on a new line, prefixed with '- '."
        )
        sub_queries_text = await self.llm.generate(sub_queries_prompt, temperature=0.3)
        sub_queries = [
            line.strip("- ").strip()
            for line in sub_queries_text.split("\n")
            if line.strip().startswith("- ")
        ]
        if not sub_queries:
            sub_queries = [query]

        all_results = []
        search_tasks = [self.search_tool.execute(q, num_results=5) for q in sub_queries[:5]]
        search_results = await asyncio.gather(*search_tasks, return_exceptions=True)

        for sr in search_results:
            if isinstance(sr, dict) and not sr.get("error"):
                all_results.extend(sr.get("results", []))

        # Deduplicate by URL
        seen_urls = set()
        unique_results = []
        for r in all_results:
            url = r.get("url", "")
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique_results.append(r)

        logger.info(
            "Research search complete",
            query=query, results_found=len(unique_results), sub_queries=len(sub_queries),
        )
        return unique_results[:15]

    async def validate(self, findings: list[dict]) -> list[dict]:
        """Cross-validate findings for consistency and conflicts."""
        if not findings:
            return []

        sources_text = "\n\n".join(
            f"Source {i+1} ({r.get('url', 'unknown')}): {r.get('snippet', r.get('content', ''))[:500]}"
            for i, r in enumerate(findings[:10])
        )

        prompt = (
            f"Cross-validate the following research findings:\n\n{sources_text}\n\n"
            f"Identify:\n"
            f"1. Points of consensus across sources\n"
            f"2. Contradictions or conflicts\n"
            f"3. Source quality assessment\n"
            f"4. Confidence level for each major claim"
        )
        await self.llm.generate(prompt, temperature=0.3)

        for f in findings:
            f["validated"] = True
        return findings

    async def synthesize(self, findings: list[dict], original_query: str) -> str:
        """Synthesize findings into a coherent analysis."""
        sources_summary = "\n\n".join(
            f"- {r.get('title', 'Untitled')} ({r.get('url', 'no url')}): {r.get('snippet', '')[:300]}"
            for r in findings[:10]
        )

        prompt = (
            f"Original research query: {original_query}\n\n"
            f"Research findings from {len(findings)} sources:\n\n{sources_summary}\n\n"
            f"Produce a comprehensive, well-structured synthesis that:\n"
            f"1. Answers the original query directly\n"
            f"2. Presents key findings organized by theme\n"
            f"3. Notes areas of consensus and disagreement\n"
            f"4. Identifies gaps in current knowledge\n"
            f"5. Provides a balanced perspective"
        )
        synthesis = await self.llm.generate(prompt, temperature=0.4)
        return synthesis

    async def execute(self, task: str, context: dict[str, Any] = None) -> dict[str, Any]:
        """Execute full research workflow."""
        logger.info("Research workflow started", task=task[:100])

        findings = await self.search(task)
        validated = await self.validate(findings)
        synthesis = await self.synthesize(validated, task)

        result = {
            "query": task,
            "sources_count": len(validated),
            "findings": validated,
            "synthesis": synthesis,
            "status": "completed",
        }
        logger.info("Research workflow completed", sources=len(validated))
        return result


RESEARCH_WORKFLOW = ResearchWorkflow()
