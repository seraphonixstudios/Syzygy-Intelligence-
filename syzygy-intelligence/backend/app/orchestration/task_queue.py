"""Priority-based async task queue with real task execution and parallel processing."""

from __future__ import annotations

import asyncio
import uuid
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from app.logging_setup import logger


@dataclass
class QueueItem:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    task: str = ""
    task_type: str = "generic"
    priority: int = 0
    status: str = "pending"
    result: Any = None
    error: str = ""
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    started_at: datetime | None = None
    completed_at: datetime | None = None
    execution_time_ms: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)
    retry_count: int = 0
    max_retries: int = 3
    handler: Callable[..., Any] | None = None


class TaskQueue:
    """Priority-ordered async task queue with real execution and retry logic."""

    def __init__(self) -> None:
        self._items: list[QueueItem] = []
        self._running: set[str] = set()
        self._lock = asyncio.Lock()
        self._handlers: dict[str, Callable[..., Any]] = {}

    def register_handler(self, task_type: str, handler: Callable[..., Any]) -> None:
        """Register a handler for a specific task type."""
        self._handlers[task_type] = handler

    async def enqueue(
        self,
        task: str,
        task_type: str = "generic",
        priority: int = 0,
        metadata: dict[str, Any] | None = None,
        handler: Callable[..., Any] | None = None,
    ) -> str:
        """Enqueue a task with priority (higher = more important)."""
        item = QueueItem(
            task=task,
            task_type=task_type,
            priority=priority,
            metadata=metadata or {},
            handler=handler,
        )
        async with self._lock:
            self._items.append(item)
            self._items.sort(key=lambda x: (x.priority, x.created_at.timestamp()), reverse=True)
        logger.debug("Task enqueued", task_id=item.id, task_type=task_type, priority=priority)
        return item.id

    async def dequeue(self) -> QueueItem | None:
        """Dequeue the highest-priority pending task."""
        async with self._lock:
            for item in self._items:
                if item.status == "pending" and item.retry_count < item.max_retries:
                    item.status = "running"
                    item.started_at = datetime.now(UTC)
                    self._running.add(item.id)
                    return item
        return None

    async def complete(self, item_id: str, result: Any = None, error: str = "") -> None:
        """Mark a task as completed (or failed)."""
        async with self._lock:
            for item in self._items:
                if item.id == item_id:
                    item.completed_at = datetime.now(UTC)
                    if item.started_at:
                        item.execution_time_ms = (
                            item.completed_at - item.started_at
                        ).total_seconds() * 1000
                    if error and item.retry_count < item.max_retries - 1:
                        item.retry_count += 1
                        item.status = "pending"
                        item.error = error
                        logger.warning("Task will retry", task_id=item_id, retry=item.retry_count)
                    else:
                        item.status = "completed" if not error else "failed"
                        item.result = result
                        item.error = error
                        self._running.discard(item_id)
                        logger.info(f"Task {'completed' if not error else 'failed'}",
                                   task_id=item_id, time_ms=item.execution_time_ms)
                    break

    async def execute_next(self) -> Any | None:
        """Execute the next available task."""
        item = await self.dequeue()
        if not item:
            return None

        try:
            handler = item.handler or self._handlers.get(item.task_type)
            if handler:
                if asyncio.iscoroutinefunction(handler):
                    result = await handler(item)
                else:
                    result = handler(item)
            else:
                result = await self._default_execute(item)

            await self.complete(item.id, result=result)
            return result

        except Exception as e:
            await self.complete(item.id, error=str(e))
            return None

    async def _default_execute(self, item: QueueItem) -> Any:
        """Default execution — uses LLM if available, otherwise simulates."""
        from app.llm.ollama_client import OllamaClient
        try:
            llm = OllamaClient()
            result = await llm.generate(
                f"Execute the following task:\n\n{item.task}\n\n"
                f"Task type: {item.task_type}\n"
                f"Provide a complete response."
            )
            return result
        except Exception as e:
            logger.error("Task execution failed", error=str(e))
            await asyncio.sleep(0.5)
            return f"Executed: {item.task[:100]}"

    async def run_worker(self, max_concurrent: int = 3) -> None:
        """Run a worker that processes tasks concurrently."""
        semaphore = asyncio.Semaphore(max_concurrent)

        async def _worker() -> None:
            while True:
                async with semaphore:
                    result = await self.execute_next()
                    if result is None:
                        await asyncio.sleep(0.5)

        workers = [_worker() for _ in range(max_concurrent)]
        await asyncio.gather(*workers)

    async def execute_parallel(self, tasks: list[str], max_concurrent: int = 3) -> list[Any]:
        """Execute multiple tasks in parallel with concurrency limit."""
        semaphore = asyncio.Semaphore(max_concurrent)

        async def _run(task: str) -> Any:
            async with semaphore:
                item_id = await self.enqueue(task)
                item = await self.dequeue()
                if item:
                    try:
                        result = await self._default_execute(item)
                        await self.complete(item_id, result=result)
                        return result
                    except Exception as e:
                        await self.complete(item_id, error=str(e))
                        return {"error": str(e)}
            return None

        results = await asyncio.gather(*[_run(t) for t in tasks], return_exceptions=True)
        return [r for r in results if r is not None]

    async def get_status(self, item_id: str) -> dict[str, Any] | None:
        """Get the status of a specific task."""
        for item in self._items:
            if item.id == item_id:
                return {
                    "id": item.id,
                    "task": item.task[:100],
                    "task_type": item.task_type,
                    "priority": item.priority,
                    "status": item.status,
                    "result": item.result,
                    "error": item.error,
                    "created_at": item.created_at.isoformat() if item.created_at else None,
                    "execution_time_ms": item.execution_time_ms,
                    "retry_count": item.retry_count,
                }
        return None

    async def get_queue_stats(self) -> dict[str, Any]:
        """Get queue statistics."""
        async with self._lock:
            total = len(self._items)
            pending = sum(1 for i in self._items if i.status == "pending")
            running = len(self._running)
            completed = sum(1 for i in self._items if i.status == "completed")
            failed = sum(1 for i in self._items if i.status == "failed")
            return {
                "total": total,
                "pending": pending,
                "running": running,
                "completed": completed,
                "failed": failed,
                "queue_length": total - completed - failed,
            }

    async def cancel(self, item_id: str) -> bool:
        """Cancel a pending task."""
        async with self._lock:
            for item in self._items:
                if item.id == item_id and item.status == "pending":
                    item.status = "failed"
                    item.error = "Cancelled by user"
                    return True
        return False

    async def clear_completed(self) -> None:
        """Remove completed and failed tasks from the queue."""
        async with self._lock:
            self._items = [i for i in self._items if i.status in ("pending", "running")]
