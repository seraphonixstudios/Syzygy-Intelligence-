"""RAG document storage and retrieval via ChromaDB with Ollama embeddings."""

import uuid
from datetime import UTC, datetime
from typing import Any

import chromadb

from app.config import settings
from app.logging_setup import logger
from app.rag.embeddings import embed
from app.rag.ingester import chunk_text, parse_document

# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _collection():
    """Return (creating if needed) the RAG document collection."""
    client = chromadb.PersistentClient(path=settings.chroma_path)
    return client.get_or_create_collection(
        name="syzygy_documents",
        metadata={"hnsw:space": "cosine"},
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

async def ingest_document(
    file_path: str,
    metadata: dict[str, Any] | None = None,
) -> int:
    """Parse, chunk, embed and store a document file.

    Returns the number of chunks stored.
    """
    logger.info("Ingesting document", file_path=file_path)
    text = parse_document(file_path)
    source = metadata.get("source", file_path) if metadata else file_path
    return await ingest_text(text, source=str(source), metadata=metadata)


async def ingest_text(
    text: str,
    source: str = "",
    metadata: dict[str, Any] | None = None,
) -> int:
    """Chunk, embed and store raw text.

    Returns the number of chunks stored.
    """
    logger.info("Ingesting text", source=source or "anonymous", text_len=len(text))

    chunks = chunk_text(text)
    if not chunks:
        logger.warning("No chunks produced", source=source)
        return 0

    embeddings = await embed(chunks)
    collection = _collection()

    ids: list[str] = []
    metadatas: list[dict[str, Any]] = []
    now = datetime.now(UTC).isoformat()
    base_meta = {**(metadata or {})}

    for i, chunk in enumerate(chunks):
        chunk_id = str(uuid.uuid4())
        ids.append(chunk_id)
        metadatas.append({
            "source": source,
            "chunk_index": i,
            "total_chunks": len(chunks),
            "char_count": len(chunk),
            "ingested_at": now,
            **base_meta,
        })

    collection.add(
        documents=chunks,
        embeddings=embeddings,
        ids=ids,
        metadatas=metadatas,
    )

    logger.info("Document ingested", source=source or "anonymous", chunks=len(chunks))
    return len(chunks)


async def query(
    query: str,
    top_k: int = 5,
    min_score: float = 0.3,
) -> list[dict[str, Any]]:
    """Semantic search over ingested document chunks.

    Returns results sorted by descending relevance score.
    """
    logger.info("RAG query", query=query, top_k=top_k, min_score=min_score)

    query_embedding = await embed([query])
    collection = _collection()

    results = collection.query(
        query_embeddings=query_embedding,
        n_results=min(top_k, 50),
    )

    hits: list[dict[str, Any]] = []
    if results and results.get("ids"):
        for i, doc_id in enumerate(results["ids"][0]):
            distance = results["distances"][0][i] if results.get("distances") else 0.0
            score = 1.0 - distance  # cosine distance → similarity

            if score < min_score:
                continue

            hits.append({
                "id": doc_id,
                "content": results["documents"][0][i] if results.get("documents") else "",
                "metadata": results["metadatas"][0][i] if results.get("metadatas") else {},
                "score": round(score, 4),
            })

    hits.sort(key=lambda x: x["score"], reverse=True)
    return hits[:top_k]


async def list_documents() -> list[dict[str, Any]]:
    """Return every unique document source with its chunk count and total chars."""
    collection = _collection()
    all_data = collection.get()

    source_map: dict[str, dict[str, Any]] = {}
    for meta in all_data.get("metadatas") or []:
        src = meta.get("source", "unknown")
        entry = source_map.setdefault(src, {
            "source": src,
            "chunk_count": 0,
            "total_chars": 0,
            "ingested_at": "",
        })
        entry["chunk_count"] += 1
        entry["total_chars"] += meta.get("char_count", 0)
        ingested = meta.get("ingested_at", "")
        if ingested and (not entry["ingested_at"] or ingested < entry["ingested_at"]):
            entry["ingested_at"] = ingested

    return list(source_map.values())


async def delete_document(source: str) -> bool:
    """Delete every chunk whose ``source`` metadata matches *source*.

    Returns ``True`` if any chunks were removed.
    """
    logger.info("Deleting document", source=source)
    collection = _collection()

    all_data = collection.get(where={"source": source})
    ids = all_data.get("ids") or []
    if not ids:
        logger.warning("Document not found for deletion", source=source)
        return False

    collection.delete(ids=ids)
    logger.info("Document deleted", source=source, chunks=len(ids))
    return True
