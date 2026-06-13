"""Base memory abstraction for Syzygy.

Provides the Memory interface used by workflows for persistent storage.
"""

from __future__ import annotations

from typing import Any

from app.logging_setup import logger


class Memory:
    """Abstract memory interface for workflow persistence.

    Concrete implementations should subclass and override add_memory.
    The default implementation logs and stores in an in-memory dict.
    """

    def __init__(self) -> None:
        self._store: dict[str, dict[str, Any]] = {}

    async def add_memory(
        self,
        key: str,
        value: dict[str, Any],
        embedding_text: str = "",
    ) -> None:
        """Store a memory entry with optional embedding text."""
        self._store[key] = value
        logger.debug(
            "Memory stored",
            key=key,
            embedding_length=len(embedding_text),
        )

    async def recall(self, key: str) -> dict[str, Any] | None:
        """Recall a memory entry by key."""
        return self._store.get(key)


__all__ = ["Memory"]
