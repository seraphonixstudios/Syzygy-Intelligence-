"""Graph memory — Neo4j knowledge graph for relationship-based memory with full CRUD."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from app.config import settings
from app.logging_setup import logger

try:
    from neo4j import Driver as Neo4jDriver
except ImportError:
    Neo4jDriver = Any  # type: ignore[assignment,misc]


class GraphMemory:
    """Neo4j-based graph memory for relationship tracking with Cypher queries."""

    def __init__(self) -> None:
        self._driver: Neo4jDriver | None = None
        self._initialized = False

    async def _ensure_init(self) -> None:
        if not self._initialized:
            try:
                from neo4j import GraphDatabase
                self._driver = GraphDatabase.driver(
                    settings.neo4j_uri,
                    auth=(settings.neo4j_user, settings.neo4j_password),
                    max_connection_lifetime=300,
                    connection_timeout=10,
                )
                self._initialized = True
                logger.info("Neo4j graph memory initialized")
            except Exception as e:
                logger.warning(f"Neo4j not available, graph memory disabled: {e}")
                self._initialized = True

    async def store(
        self,
        content: str,
        agent_id: str = "",
        session_id: str = "",
        polarity: str = "",
        archetype: str = "",
        tags: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        """Store a memory node in the graph with relationships."""
        await self._ensure_init()
        memory_id = str(uuid.uuid4())

        if self._driver:
            try:
                async with self._driver.session() as session:  # type: ignore[attr-defined]
                    await session.run(
                        """
                        CREATE (m:Memory {
                            id: $id,
                            content: $content,
                            agent_id: $agent_id,
                            session_id: $session_id,
                            polarity: $polarity,
                            archetype: $archetype,
                            tags: $tags,
                            created_at: $created_at
                        })
                        """,
                        id=memory_id,
                        content=content[:2000],
                        agent_id=agent_id or "",
                        session_id=session_id or "",
                        polarity=polarity or "unknown",
                        archetype=archetype or "unknown",
                        tags=tags or [],
                        created_at=datetime.now(UTC).isoformat(),
                    )

                    # Create relationships to agent if provided
                    if agent_id:
                        await session.run(
                            """
                            MATCH (m:Memory {id: $memory_id})
                            MERGE (a:Agent {id: $agent_id})
                            CREATE (m)-[:BELONGS_TO]->(a)
                            """,
                            memory_id=memory_id,
                            agent_id=agent_id,
                        )

                    # Create relationships to session if provided
                    if session_id:
                        await session.run(
                            """
                            MATCH (m:Memory {id: $memory_id})
                            MERGE (s:Session {id: $session_id})
                            CREATE (m)-[:PART_OF]->(s)
                            """,
                            memory_id=memory_id,
                            session_id=session_id,
                        )

                    # Link to similar memories by polarity/tags
                    if tags:
                        await session.run(
                            """
                            MATCH (m:Memory {id: $memory_id})
                            MATCH (other:Memory)
                            WHERE other.id <> $memory_id
                              AND any(tag IN $tags WHERE tag IN other.tags)
                            CREATE (m)-[:RELATED_TO]->(other)
                            """,
                            memory_id=memory_id,
                            tags=tags,
                        )

            except Exception as e:
                logger.error(f"Neo4j store failed: {e}", memory_id=memory_id)

        return memory_id

    async def query(
        self,
        query_text: str = "",
        agent_id: str = "",
        polarity: str = "",
        archetype: str = "",
        tags: list[str] | None = None,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """Query memory graph with Cypher."""
        await self._ensure_init()
        results: list[dict[str, Any]] = []

        if not self._driver:
            return results

        try:
            async with self._driver.session() as session:  # type: ignore[attr-defined]
                cypher = "MATCH (m:Memory) WHERE 1=1"
                params: dict[str, Any] = {}

                if agent_id:
                    cypher += " AND m.agent_id = $agent_id"
                    params["agent_id"] = agent_id
                if polarity:
                    cypher += " AND m.polarity = $polarity"
                    params["polarity"] = polarity
                if archetype:
                    cypher += " AND m.archetype = $archetype"
                    params["archetype"] = archetype
                if tags:
                    cypher += " AND any(tag IN $tags WHERE tag IN m.tags)"
                    params["tags"] = tags
                if query_text:
                    cypher += " AND m.content CONTAINS $query"
                    params["query"] = query_text

                cypher += " RETURN m ORDER BY m.created_at DESC LIMIT $limit"
                params["limit"] = limit

                result = await session.run(cypher, **params)
                records = await result.fetch(limit)

                for record in records:
                    node = record["m"]
                    results.append({
                        "id": node.get("id"),
                        "content": node.get("content"),
                        "agent_id": node.get("agent_id"),
                        "session_id": node.get("session_id"),
                        "polarity": node.get("polarity"),
                        "archetype": node.get("archetype"),
                        "tags": node.get("tags", []),
                        "created_at": node.get("created_at"),
                        "memory_type": "graph",
                        "importance": 0.6,
                    })

        except Exception as e:
            logger.error(f"Neo4j query failed: {e}")

        return results

    async def get_related_memories(
        self,
        memory_id: str,
        relationship: str = "RELATED_TO",
        depth: int = 1,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """Traverse graph relationships from a memory node."""
        await self._ensure_init()
        results: list[dict[str, Any]] = []

        if not self._driver:
            return results

        try:
            async with self._driver.session() as session:  # type: ignore[attr-defined]
                result = await session.run(
                    f"""
                    MATCH (m:Memory {{id: $memory_id}})
                    OPTIONAL MATCH path = (m)-[:{relationship}]-(connected)
                    WHERE connected IS NOT NULL
                    RETURN connected
                    ORDER BY connected.created_at DESC
                    LIMIT $limit
                    """,
                    memory_id=memory_id,
                    limit=limit,
                )
                records = await result.fetch(limit)
                for record in records:
                    node = record.get("connected")
                    if node:
                        results.append({
                            "id": node.get("id"),
                            "content": node.get("content"),
                            "agent_id": node.get("agent_id"),
                            "polarity": node.get("polarity"),
                            "tags": node.get("tags", []),
                        })

        except Exception as e:
            logger.error(f"Neo4j relationship query failed: {e}")

        return results

    async def get_polarity_cluster(self, polarity: str, limit: int = 20) -> list[dict[str, Any]]:
        """Get memories clustered by polarity."""
        return await self.query(polarity=polarity, limit=limit)

    async def delete_memory(self, memory_id: str) -> bool:
        """Delete a memory node and its relationships."""
        await self._ensure_init()
        if not self._driver:
            return False
        try:
            async with self._driver.session() as session:  # type: ignore[attr-defined]
                await session.run(
                    "MATCH (m:Memory {id: $id}) DETACH DELETE m",
                    id=memory_id,
                )
                return True
        except Exception as e:
            logger.error(f"Neo4j delete failed: {e}")
            return False

    async def close(self) -> None:
        if self._driver:
            await self._driver.close()  # type: ignore[misc,func-returns-value]
            self._driver = None
            self._initialized = False
