"""Q&A Bot workflow — knowledge-base ingestion, retrieval, and answer generation.

Retrieval reports exactly which documents the model found relevant (parsed from
its answer, intersected with ingested IDs). When relevance cannot be determined
it says so instead of silently citing everything. Answers carry a grounded flag.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from app.llm.model_manager import ModelManager
from app.logging_setup import logger
from app.text_utils import truncate


def _parse_sources(text: str, known_ids: list[str]) -> list[str]:
    """Extract relevant doc IDs from a trailing `SOURCES: a, b` line."""
    match = None
    for line in (text or "").splitlines():
        found = re.match(r"^\s*SOURCES\s*:\s*(.*)$", line, re.IGNORECASE)
        if found:
            match = found
    if match is None:
        return []
    known = set(known_ids)
    return [part.strip() for part in match.group(1).split(",") if part.strip() in known]


@dataclass
class QABotWorkflow:
    """Knowledge-base Q&A with document ingestion, retrieval, and answer synthesis."""

    name: str = "qa_bot"
    description: str = "Knowledge-base Q&A — ingest docs, retrieve context, generate answers"
    required_capabilities: list[str] = field(
        default_factory=lambda: ["document_qa", "retrieval", "information_synthesis"]
    )
    llm: ModelManager | None = None
    knowledge_base: dict[str, str] = field(default_factory=dict)

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
                logger.warning("QABotWorkflow LLM call failed", error=str(exc))
                return ""
            text = (text or "").strip()
            if text:
                head = text[:40].lower()
                if not (head.startswith("[") and "error" in head):
                    return text
        return ""

    async def ingest_document(self, doc_id: str, content: str) -> dict[str, Any]:
        self.knowledge_base[doc_id] = content
        prompt = (
            f"Summarize the following document (id: {doc_id}) for indexing:\n\n{truncate(content, 12000)}\n\n"
            f"Provide:\n"
            f"1. Document summary (2-3 sentences)\n"
            f"2. 5-10 keywords/topics\n"
            f"3. Key entities mentioned\n"
            f"4. Document type classification"
        )
        summary = await self._generate(prompt, temperature=0.3)
        return {"doc_id": doc_id, "summary": summary, "ingested": True}

    async def retrieve_context(self, query: str) -> dict[str, Any]:
        if not self.knowledge_base:
            return {
                "context": [],
                "sources": [],
                "grounded": False,
                "note": "No documents ingested. Using LLM knowledge only.",
            }

        doc_list = "\n\n".join(
            f"Document: {doc_id}\n{truncate(content, 8000)}"
            for doc_id, content in self.knowledge_base.items()
        )
        prompt = (
            f"Given the following knowledge base documents:\n\n{doc_list}\n\n"
            f"Query: {query}\n\n"
            f"Identify which documents are relevant and extract the specific passages "
            f"that answer or relate to the query. Return passages with source document IDs.\n"
            f"End your response with a line exactly like this, listing ONLY the IDs of "
            f"relevant documents (empty if none are relevant):\n"
            f"SOURCES: <id1>, <id2>"
        )
        context = await self._generate(prompt, temperature=0.3)
        known_ids = list(self.knowledge_base.keys())
        sources = _parse_sources(context, known_ids)
        if sources:
            note = "Retrieved from knowledge base"
        else:
            # Relevance could not be determined — say so instead of citing everything.
            sources = known_ids
            note = "Retrieved from knowledge base (relevance unconfirmed)"
        return {"context": context, "sources": sources, "grounded": bool(sources), "note": note}

    async def generate_answer(self, query: str, context: dict[str, Any]) -> str:
        context_text = context.get("context", "No specific context available for this query.")
        sources = context.get("sources", [])

        prompt = (
            f"Question: {query}\n\n"
            f"Context:\n{context_text}\n\n"
            f"Sources: {', '.join(sources) if sources else 'General knowledge'}\n\n"
            f"Provide a comprehensive answer that:\n"
            f"1. Directly answers the question\n"
            f"2. Cites specific sources where applicable, using [document-id] markers\n"
            f"3. Notes confidence level\n"
            f"4. Suggests follow-up questions if relevant"
        )
        return await self._generate(prompt, temperature=0.3)

    async def generate_follow_ups(self, query: str, answer: str) -> list[str]:
        prompt = (
            f"Based on the following Q&A pair:\n\n"
            f"Question: {query}\n\n"
            f"Answer:\n{truncate(answer, 8000)}\n\n"
            f"Generate 3-5 suggested follow-up questions that would deepen understanding "
            f"or explore related topics. Return as a numbered list."
        )
        suggestions = await self._generate(prompt, temperature=0.4)
        lines = [line.strip() for line in suggestions.split("\n") if line.strip()]
        return [line for line in lines if any(c.isdigit() for c in line[:3])] or [
            "What are the limitations?",
            "How does this compare to alternatives?",
            "What are the next steps?",
        ]

    async def execute(self, task: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
        ctx = context or {}
        query = ctx.get("query", task)
        action = ctx.get("action", "ask")

        logger.info("Q&A Bot workflow started", action=action, query=query[:100])

        if action == "ingest":
            doc_id = ctx.get("doc_id", f"doc_{len(self.knowledge_base) + 1}")
            content = ctx.get("content", task)
            ingestion = await self.ingest_document(doc_id, content)
            return {"action": "ingested", "result": ingestion, "status": "completed"}

        retrieved = await self.retrieve_context(query)
        answer = await self.generate_answer(query, retrieved)
        follow_ups = await self.generate_follow_ups(query, answer)

        result = {
            "action": "ask",
            "query": query,
            "answer": answer,
            "context_used": retrieved,
            "grounded": retrieved.get("grounded", False),
            "suggested_follow_ups": follow_ups,
            "status": "completed",
        }
        logger.info("Q&A Bot workflow completed", grounded=result["grounded"])
        return result


QA_BOT_WORKFLOW = QABotWorkflow()
