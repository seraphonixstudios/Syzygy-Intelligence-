"""Short-term memory — episodic, session-scoped, with time-based decay."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Optional


class ShortTermMemory:
    """In-memory short-term store with automatic decay."""

    def __init__(self, ttl_minutes: int = 60):
        self._store: dict[str, dict[str, Any]] = {}
        self.ttl = timedelta(minutes=ttl_minutes)

    async def store(
        self,
        content: str,
        agent_id: str = "",
        session_id: str = "",
        polarity: str = "",
        archetype: str = "",
        tags: list[str] = None,
        metadata: dict[str, Any] = None,
    ) -> str:
        memory_id = str(uuid.uuid4())
        self._store[memory_id] = {
            "id": memory_id,
            "content": content,
            "agent_id": agent_id,
            "session_id": session_id,
            "polarity": polarity,
            "archetype": archetype,
            "tags": tags or [],
            "metadata": metadata or {},
            "memory_type": "short_term",
            "importance": 0.3,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "expires_at": (datetime.now(timezone.utc) + self.ttl).isoformat(),
        }
        return memory_id

    async def recall(
        self,
        query: str = "",
        agent_id: str = "",
        polarity: str = "",
        session_id: str = "",
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        now = datetime.now(timezone.utc)
        results = []

        for mem in self._store.values():
            # Skip expired
            if "expires_at" in mem:
                expires = datetime.fromisoformat(mem["expires_at"])
                if expires < now:
                    continue

            # Filter by agent_id
            if agent_id and mem.get("agent_id") != agent_id:
                continue
            # Filter by polarity
            if polarity and mem.get("polarity") != polarity:
                continue
            # Filter by session
            if session_id and mem.get("session_id") != session_id:
                continue

            # Simple keyword match
            if query and query.lower() not in mem.get("content", "").lower():
                continue

            results.append(mem)

        return sorted(results, key=lambda x: x.get("created_at", ""), reverse=True)[:limit]

    async def get_recent(
        self,
        session_id: str = "",
        limit: int = 5,
    ) -> list[dict[str, Any]]:
        return await self.recall(session_id=session_id, limit=limit)

    async def clear(self, session_id: str = ""):
        if session_id:
            self._store = {
                k: v for k, v in self._store.items()
                if v.get("session_id") != session_id
            }
        else:
            self._store.clear()

    async def cleanup_expired(self):
        now = datetime.now(timezone.utc)
        self._store = {
            k: v for k, v in self._store.items()
            if "expires_at" not in v or datetime.fromisoformat(v["expires_at"]) >= now
        }
