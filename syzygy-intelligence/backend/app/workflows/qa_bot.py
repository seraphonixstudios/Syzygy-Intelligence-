"""Q&A Bot workflow — knowledge-base ingestion, retrieval, and answer generation."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.llm.ollama_client import OllamaClient
from app.logging_setup import logger


@dataclass
class QABotWorkflow:
    """Knowledge-base Q&A with document ingestion, retrieval, and answer synthesis."""

    name: str = "qa_bot"
    description: str = "Knowledge-base Q&A — ingest docs, retrieve context, generate answers"
    required_capabilities: list[str] = field(
        default_factory=lambda: ["document_qa", "retrieval", "information_synthesis"]
    )
    llm: OllamaClient | None = None
    knowledge_base: dict[str, str] = field(default_factory=dict)

    def __post_init__(self):
        if self.llm is None:
            self.llm = OllamaClient()

    async def ingest_document(self, doc_id: str, content: str) -> dict[str, Any]:
        self.knowledge_base[doc_id] = content
        prompt = (
            f"Summarize the following document (id: {doc_id}) for indexing:\n\n{content[:3000]}\n\n"
            f"Provide:\n"
            f"1. Document summary (2-3 sentences)\n"
            f"2. 5-10 keywords/topics\n"
            f"3. Key entities mentioned\n"
            f"4. Document type classification"
        )
        summary = await self.llm.generate(prompt, temperature=0.3)
        return {"doc_id": doc_id, "summary": summary, "ingested": True}

    async def retrieve_context(self, query: str) -> dict[str, Any]:
        if not self.knowledge_base:
            return {"context": [], "sources": [], "note": "No documents ingested. Using LLM knowledge only."}

        doc_list = "\n\n".join(
            f"Document: {doc_id}\n{content[:1500]}"
            for doc_id, content in self.knowledge_base.items()
        )
        prompt = (
            f"Given the following knowledge base documents:\n\n{doc_list}\n\n"
            f"Query: {query}\n\n"
            f"Identify which documents are relevant and extract the specific passages "
            f"that answer or relate to the query. Return passages with source document IDs."
        )
        context = await self.llm.generate(prompt, temperature=0.3)
        sources = list(self.knowledge_base.keys())
        return {"context": context, "sources": sources, "note": "Retrieved from knowledge base"}

    async def generate_answer(self, query: str, context: dict) -> str:
        context_text = context.get("context", "No specific context available for this query.")
        sources = context.get("sources", [])

        prompt = (
            f"Question: {query}\n\n"
            f"Context:\n{context_text}\n\n"
            f"Sources: {', '.join(sources) if sources else 'General knowledge'}\n\n"
            f"Provide a comprehensive answer that:\n"
            f"1. Directly answers the question\n"
            f"2. Cites specific sources where applicable\n"
            f"3. Notes confidence level\n"
            f"4. Suggests follow-up questions if relevant"
        )
        return await self.llm.generate(prompt, temperature=0.3)

    async def generate_follow_ups(self, query: str, answer: str) -> list[str]:
        prompt = (
            f"Based on the following Q&A pair:\n\n"
            f"Question: {query}\n\n"
            f"Answer:\n{answer[:1500]}\n\n"
            f"Generate 3-5 suggested follow-up questions that would deepen understanding "
            f"or explore related topics. Return as a numbered list."
        )
        suggestions = await self.llm.generate(prompt, temperature=0.4)
        lines = [l.strip() for l in suggestions.split("\n") if l.strip()]
        return [l for l in lines if any(c.isdigit() for c in l[:3])] or [
            "What are the limitations?",
            "How does this compare to alternatives?",
            "What are the next steps?",
        ]

    async def execute(self, task: str, context: dict[str, Any] = None) -> dict[str, Any]:
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
            "suggested_follow_ups": follow_ups,
            "status": "completed",
        }
        logger.info("Q&A Bot workflow completed")
        return result


QA_BOT_WORKFLOW = QABotWorkflow()
