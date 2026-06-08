"""RAG context injection — query relevant docs and build context strings for chat."""

from app.logging_setup import logger
from app.rag.retriever import query


CONTEXT_TEMPLATE = """You have access to the following knowledge base documents. Use them to ground your response:
{chunks}"""


async def build_rag_context(
    message: str,
    top_k: int = 3,
    min_score: float = 0.35,
) -> str:
    """Query the RAG knowledge base for chunks relevant to *message*.

    Returns a formatted system-context string, or an empty string if no
    relevant documents are found.
    """
    try:
        results = await query(message, top_k=top_k, min_score=min_score)
    except Exception as exc:
        logger.warning("RAG query failed during context injection", error=str(exc))
        return ""

    if not results:
        logger.info("No relevant RAG documents found for context injection")
        return ""

    lines: list[str] = []
    for i, r in enumerate(results, 1):
        src = r.get("metadata", {}).get("source", "unknown")
        lines.append(f"[{i}] (source: {src}, relevance: {r['score']:.0%})")
        lines.append(r.get("content", ""))
        lines.append("")

    chunks = "\n".join(lines)
    logger.info("RAG context injected", chunks=len(results), message_len=len(message))
    return CONTEXT_TEMPLATE.format(chunks=chunks)
