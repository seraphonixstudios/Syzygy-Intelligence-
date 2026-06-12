"""Vector memory store using Chroma with real sentence-embedding for semantic search."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from app.config import settings
from app.logging_setup import logger


class VectorMemory:
    """Chroma-based vector memory with real embedding generation for semantic retrieval."""

    def __init__(self) -> None:
        self._collection: Any = None
        self._embedding_function: Any = None
        self._initialized = False

    async def _ensure_init(self) -> None:
        if not self._initialized:
            try:
                import chromadb
                from chromadb.utils import embedding_functions

                client = chromadb.PersistentClient(path=settings.chroma_path)

                self._embedding_function = embedding_functions.DefaultEmbeddingFunction()

                self._collection = client.get_or_create_collection(
                    name="syzygy_memories",
                    metadata={"hnsw:space": "cosine"},
                    embedding_function=self._embedding_function,
                )

                self._initialized = True
                logger.info("Vector memory initialized with Chroma + default embeddings")
            except ImportError as e:
                logger.warning(f"Chroma import failed: {e}. Vector memory disabled.")
                self._initialized = True
            except Exception as e:
                logger.warning(f"Chroma init failed (will retry): {e}")
                self._initialized = True

    async def store(
        self,
        content: str,
        agent_id: str = "",
        session_id: str = "",
        polarity: str = "",
        tags: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        """Store memory with embedding for semantic search."""
        await self._ensure_init()
        memory_id = str(uuid.uuid4())

        if self._collection:
            try:
                self._collection.add(
                    documents=[content],
                    ids=[memory_id],
                    metadatas=[{
                        "agent_id": agent_id or "",
                        "session_id": session_id or "",
                        "polarity": polarity or "unknown",
                        "tags": ",".join(tags or []),
                        "created_at": datetime.now(UTC).isoformat(),
                        **(metadata or {}),
                    }],
                )
            except Exception as e:
                logger.error(f"Chroma store failed: {e}", memory_id=memory_id)

        return memory_id

    async def search(
        self,
        query: str,
        agent_id: str = "",
        polarity: str = "",
        limit: int = 10,
        min_score: float = 0.0,
    ) -> list[dict[str, Any]]:
        """Semantic search using vector similarity. Returns results sorted by relevance."""
        await self._ensure_init()
        results: list[dict[str, Any]] = []

        if self._collection:
            try:
                where = {}
                if agent_id:
                    where["agent_id"] = agent_id
                if polarity:
                    where["polarity"] = polarity

                query_results = self._collection.query(
                    query_texts=[query],
                    n_results=min(limit, 50),
                    where=where or None,
                )

                if query_results and query_results.get("ids"):
                    for i, doc_id in enumerate(query_results["ids"][0]):
                        distance = query_results["distances"][0][i] if query_results.get("distances") else 0
                        score = 1.0 - distance  # cosine distance -> similarity

                        if score < min_score:
                            continue

                        results.append({
                            "id": doc_id,
                            "content": query_results["documents"][0][i] if query_results.get("documents") else "",
                            "metadata": query_results["metadatas"][0][i] if query_results.get("metadatas") else {},
                            "memory_type": "vector",
                            "importance": score,
                            "score": round(score, 4),
                        })

                    results.sort(key=lambda x: x["score"], reverse=True)

            except Exception as e:
                logger.error(f"Chroma search failed: {e}")

        return results[:limit]

    async def delete(self, memory_id: str) -> bool:
        """Delete a memory from the vector store."""
        await self._ensure_init()
        if self._collection:
            try:
                self._collection.delete(ids=[memory_id])
                return True
            except Exception as e:
                logger.error(f"Chroma delete failed: {e}")
        return False

    async def count(self) -> int:
        """Count total vectors in the collection."""
        await self._ensure_init()
        if self._collection:
            try:
                return self._collection.count()  # type: ignore[no-any-return]
            except Exception as e:
                logger.warning("Vector store count failed", error=str(e))
        return 0
