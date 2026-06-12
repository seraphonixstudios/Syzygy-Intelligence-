"""Long-term memory — persistent storage with importance-based retention."""

from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from app.config import settings


class LongTermMemory:
    """File-based long-term memory with importance scoring and tagging."""

    def __init__(self, storage_path: str | None = None):
        self.storage_path = Path(storage_path or f"{settings.data_dir}/memories/long_term")
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self._index_path = self.storage_path / "_index.json"
        self._load_index()

    def _load_index(self) -> None:
        if self._index_path.exists():
            self._index = json.loads(self._index_path.read_text())
        else:
            self._index = {}

    def _save_index(self) -> None:
        self._index_path.write_text(json.dumps(self._index, indent=2))

    async def store(
        self,
        content: str,
        agent_id: str = "",
        session_id: str = "",
        polarity: str = "",
        archetype: str = "",
        importance: float = 0.5,
        tags: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        memory_id = str(uuid.uuid4())
        entry = {
            "id": memory_id,
            "content": content,
            "agent_id": agent_id,
            "session_id": session_id,
            "polarity": polarity,
            "archetype": archetype,
            "tags": tags or [],
            "metadata": metadata or {},
            "memory_type": "long_term",
            "importance": importance,
            "created_at": datetime.now(UTC).isoformat(),
        }

        file_path = self.storage_path / f"{memory_id}.json"
        file_path.write_text(json.dumps(entry, indent=2))

        self._index[memory_id] = {
            "agent_id": agent_id,
            "polarity": polarity,
            "archetype": archetype,
            "importance": importance,
            "tags": tags or [],
            "created_at": entry["created_at"],
        }
        self._save_index()

        return memory_id

    async def recall(
        self,
        query: str = "",
        agent_id: str = "",
        polarity: str = "",
        archetype: str = "",
        min_importance: float = 0.0,
        tags: list[str] | None = None,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        results = []

        for mem_id, idx_entry in self._index.items():
            if agent_id and idx_entry.get("agent_id") != agent_id:
                continue
            if polarity and idx_entry.get("polarity") != polarity:
                continue
            if archetype and idx_entry.get("archetype") != archetype:
                continue
            if idx_entry.get("importance", 0) < min_importance:
                continue
            if tags:
                mem_tags = set(idx_entry.get("tags", []))
                if not mem_tags.intersection(tags):
                    continue

            file_path = self.storage_path / f"{mem_id}.json"
            if file_path.exists():
                entry = json.loads(file_path.read_text())
                if query and query.lower() not in entry.get("content", "").lower():
                    continue
                results.append(entry)

        results.sort(key=lambda x: x.get("importance", 0), reverse=True)
        return results[:limit]

    async def forget(self, memory_id: str) -> bool:
        file_path = self.storage_path / f"{memory_id}.json"
        if file_path.exists():
            file_path.unlink()
            self._index.pop(memory_id, None)
            self._save_index()
            return True
        return False

    async def get_memories_by_polarity(
        self,
        polarity: str,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        return await self.recall(polarity=polarity, limit=limit)

    async def get_memories_by_archetype(
        self,
        archetype: str,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        return await self.recall(archetype=archetype, limit=limit)
