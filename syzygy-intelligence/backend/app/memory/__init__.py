"""Syzygy Memory System — multi-layer persistent memory.

Architecture:
- Short-term memory: Episodic, session-scoped, with decay
- Long-term memory: Vector store (Chroma) with semantic retrieval
- Graph memory: Neo4j knowledge graph for relationships
- Polity-tagged: Memory associated with specific polarities
- Archetype-tagged: Memory associated with archetypes
- Team memory: Shared cross-agent memory store
"""

from __future__ import annotations

from typing import Any

from app.logging_setup import logger
from app.memory.base import Memory  # noqa: F401
from app.memory.graph_memory import GraphMemory
from app.memory.long_term import LongTermMemory
from app.memory.short_term import ShortTermMemory
from app.memory.team_memory import TeamMemory
from app.memory.vector_store import VectorMemory


class MemorySystem:
    """Unified memory system combining all memory layers."""

    def __init__(self) -> None:
        self.short_term = ShortTermMemory()
        self.long_term = LongTermMemory()
        self.vector = VectorMemory()
        self.graph = GraphMemory()
        self.team = TeamMemory()

    async def store(
        self,
        content: str,
        memory_type: str = "short_term",
        agent_id: str = "",
        session_id: str = "",
        polarity: str = "",
        archetype: str = "",
        importance: float = 0.5,
        tags: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        """Store memory in the appropriate layer based on type and importance."""
        memory_id = ""

        if memory_type == "short_term" or importance < 0.3:
            memory_id = await self.short_term.store(
                content=content,
                agent_id=agent_id,
                session_id=session_id,
                polarity=polarity,
                archetype=archetype,
                tags=tags or [],
                metadata=metadata or {},
            )
        elif memory_type == "long_term" or importance >= 0.7:
            memory_id = await self.long_term.store(
                content=content,
                agent_id=agent_id,
                session_id=session_id,
                polarity=polarity,
                archetype=archetype,
                importance=importance,
                tags=tags or [],
                metadata=metadata or {},
            )
        elif memory_type == "vector":
            memory_id = await self.vector.store(
                content=content,
                agent_id=agent_id,
                session_id=session_id,
                polarity=polarity,
                tags=tags or [],
                metadata=metadata or {},
            )

        if memory_type == "graph" or tags:
            await self.graph.store(
                content=content,
                agent_id=agent_id,
                session_id=session_id,
                polarity=polarity,
                archetype=archetype,
                tags=tags or [],
                metadata=metadata or {},
            )

        return memory_id

    async def recall(
        self,
        query: str,
        memory_types: list[str] | None = None,
        agent_id: str = "",
        polarity: str = "",
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """Recall memories across multiple layers."""
        memory_types = memory_types or ["short_term", "long_term", "vector"]
        results = []

        if "short_term" in memory_types:
            results.extend(
                await self.short_term.recall(
                    query=query,
                    agent_id=agent_id,
                    polarity=polarity,
                    limit=limit,
                )
            )

        if "long_term" in memory_types:
            results.extend(
                await self.long_term.recall(
                    query=query,
                    agent_id=agent_id,
                    polarity=polarity,
                    limit=limit,
                )
            )

        if "vector" in memory_types:
            results.extend(
                await self.vector.search(
                    query=query,
                    agent_id=agent_id,
                    polarity=polarity,
                    limit=limit,
                )
            )

        if "rag" in memory_types or "knowledge" in memory_types:
            try:
                from app.rag.retriever import query as rag_query
                rag_results = await rag_query(query, top_k=limit, min_score=0.3)
                for r in rag_results:
                    results.append({
                        "id": r.get("id", ""),
                        "content": r.get("content", ""),
                        "importance": 0.8,
                        "source": "rag",
                        "metadata": r.get("metadata", {}),
                    })
            except Exception as e:
                logger.warning("Memory RAG query failed", error=str(e))

        # Sort by relevance/importance and deduplicate
        seen_ids = set()
        unique_results = []
        for r in sorted(results, key=lambda x: x.get("importance", 0), reverse=True):
            rid = r.get("id", "")
            if rid not in seen_ids:
                seen_ids.add(rid)
                unique_results.append(r)

        return unique_results[:limit]

    async def remember_recent(
        self,
        session_id: str = "",
        limit: int = 5,
    ) -> list[dict[str, Any]]:
        """Recall most recent memories."""
        return await self.short_term.get_recent(session_id=session_id, limit=limit)

    async def search_team_memory(
        self,
        query: str,
        limit: int = 5,
    ) -> list[dict[str, Any]]:
        """Search team shared memory."""
        return await self.team.search(query=query, limit=limit)


memory_system = MemorySystem()
