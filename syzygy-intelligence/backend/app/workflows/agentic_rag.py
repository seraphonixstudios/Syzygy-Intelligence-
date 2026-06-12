"""Agentic RAG workflow — query decomposition, multi-hop retrieval, source-grounded synthesis."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.llm.ollama_client import OllamaClient
from app.logging_setup import logger


@dataclass
class AgenticRagWorkflow:
    """Advanced RAG with query decomposition, multi-hop retrieval, and source-grounded synthesis."""

    name: str = "agentic_rag"
    description: str = "Query decomposition, multi-hop retrieval, source-grounded synthesis beyond simple Q&A"
    required_capabilities: list[str] = field(
        default_factory=lambda: ["query_planning", "retrieval", "synthesis", "source_tracking"]
    )
    llm: OllamaClient | None = None

    def __post_init__(self) -> None:
        if self.llm is None:
            self.llm = OllamaClient()

    async def decompose_query(self, query: str) -> dict[str, Any]:
        assert self.llm is not None
        prompt = (
            f"Decompose the following complex query into simpler sub-queries:\n\n{query}\n\n"
            f"For each sub-query provide:\n"
            f"1. The sub-query text\n"
            f"2. What information it targets\n"
            f"3. Dependencies on other sub-queries (if any)\n"
            f"4. Priority order for execution\n\n"
            f"Return sub-queries that can be answered independently where possible."
        )
        decomposed = await self.llm.generate(prompt, temperature=0.3)
        return {"sub_queries": decomposed, "original_query": query}

    async def retrieve_context(self, sub_query: str, knowledge_base: str) -> dict[str, Any]:
        assert self.llm is not None
        prompt = (
            f"Search the following knowledge base for information relevant to:\n{sub_query}\n\n"
            f"Knowledge Base:\n{knowledge_base[:5000]}\n\n"
            f"Extract:\n"
            f"1. Relevant passages (verbatim quotes)\n"
            f"2. Source references\n"
            f"3. Relevance score (1-10)\n"
            f"4. Confidence in the information\n"
            f"5. Related concepts to explore further"
        )
        retrieved = await self.llm.generate(prompt, temperature=0.2)
        return {"sub_query": sub_query, "retrieved": retrieved}

    async def multi_hop_synthesize(
        self, query: str, sub_query_results: list[dict[str, Any]], context: list[dict[str, Any]]
    ) -> str:
        assert self.llm is not None
        combined = "\n\n".join(
            f"Sub-query: {r.get('sub_query', '')}\nResults: {r.get('retrieved', '')}"
            for r in sub_query_results
        )
        extra = "\n\n".join(f"Context: {c}" for c in context[:3])
        prompt = (
            f"Synthesize an answer to the original query by connecting information across sources:\n\n"
            f"Original Query: {query}\n\n"
            f"Sub-query Results:\n{combined[:3000]}\n\n"
            f"Additional Context:\n{extra[:1500]}\n\n"
            f"Provide:\n"
            f"1. Direct answer to the original query\n"
            f"2. Supporting evidence with source citations\n"
            f"3. Confidence level for each claim\n"
            f"4. Acknowledged gaps or uncertainties\n"
            f"5. Follow-up queries that would strengthen the answer"
        )
        return await self.llm.generate(prompt, temperature=0.3)

    async def validate_answer(self, query: str, answer: str, sources: list[str]) -> str:
        assert self.llm is not None
        src_text = "\n".join(f"- {s[:200]}" for s in sources[:5])
        prompt = (
            f"Fact-check the following answer against its sources:\n\n"
            f"Query: {query}\n\n"
            f"Answer: {answer[:2000]}\n\n"
            f"Sources:\n{src_text}\n\n"
            f"Check:\n"
            f"1. Are all claims supported by sources?\n"
            f"2. Are there hallucinations or unsupported statements?\n"
            f"3. Are sources correctly cited?\n"
            f"4. Is there contradictory information?\n"
            f"5. Overall accuracy score (1-10)"
        )
        return await self.llm.generate(prompt, temperature=0.2)

    async def execute(self, task: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
        ctx = context or {}
        query = ctx.get("query", task)
        knowledge_base = ctx.get("knowledge_base", "")
        additional_context = ctx.get("additional_context", [])

        logger.info("Agentic RAG workflow started", query=query[:80])
        decomposed = await self.decompose_query(query)

        sub_query_results = []
        sub_queries_text = decomposed.get("sub_queries", "")
        if knowledge_base:
            import re
            sub_qs = re.findall(r'(?:\d+[.)]\s*)(.+?)(?:\n|$)', sub_queries_text)
            for sq in sub_qs[:5]:
                if sq.strip():
                    result = await self.retrieve_context(sq.strip(), knowledge_base)
                    sub_query_results.append(result)

        answer = await self.multi_hop_synthesize(query, sub_query_results, additional_context)
        sources = [r.get("retrieved", "") for r in sub_query_results]
        validation = await self.validate_answer(query, answer, sources)

        result = {
            "task": task,
            "original_query": query,
            "decomposed_query": decomposed,
            "retrieval_results": sub_query_results,
            "synthesized_answer": answer,
            "validation": validation,
            "status": "completed",
        }
        logger.info("Agentic RAG workflow completed")
        return result


AGENTIC_RAG_WORKFLOW = AgenticRagWorkflow()
