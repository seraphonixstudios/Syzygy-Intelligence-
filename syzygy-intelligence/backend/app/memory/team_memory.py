"""Team memory — shared memory accessible across all agents in a session."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from app.config import settings


class TeamMemory:
    """Shared team memory store accessible by all agents."""

    def __init__(self):
        self.storage_path = Path(f"{settings.data_dir}/memories/team")
        self.storage_path.mkdir(parents=True, exist_ok=True)

    async def store(
        self,
        content: str,
        session_id: str = "",
        agent_id: str = "",
        memory_type: str = "insight",
        tags: list[str] = None,
        metadata: dict[str, Any] = None,
    ) -> str:
        memory_id = str(uuid.uuid4())
        entry = {
            "id": memory_id,
            "content": content,
            "session_id": session_id,
            "agent_id": agent_id,
            "memory_type": memory_type,
            "tags": tags or [],
            "metadata": metadata or {},
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

        file_path = self.storage_path / f"{memory_id}.json"
        file_path.write_text(json.dumps(entry, indent=2))
        return memory_id

    async def search(
        self,
        query: str = "",
        session_id: str = "",
        memory_type: str = "",
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        results = []
        for f in sorted(self.storage_path.glob("*.json"), reverse=True):
            entry = json.loads(f.read_text())
            if session_id and entry.get("session_id") != session_id:
                continue
            if memory_type and entry.get("memory_type") != memory_type:
                continue
            if query and query.lower() not in entry.get("content", "").lower():
                continue
            results.append(entry)
            if len(results) >= limit:
                break
        return results

    async def store_individuation_moment(
        self,
        session_id: str,
        description: str,
        polarity_insight: str = "",
    ) -> str:
        """Store a significant individuation moment / learning."""
        return await self.store(
            content=description,
            session_id=session_id,
            memory_type="individuation",
            tags=["learning", "individuation", polarity_insight] if polarity_insight else ["learning", "individuation"],
            metadata={"polarity_insight": polarity_insight},
        )
