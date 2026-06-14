"""Tests for the async task queue system."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.orchestration.task_queue import QueueItem, TaskQueue


def _make_item(task="test", task_type="generic", priority=0, status="pending", retries=0, max_retries=3):
    item = MagicMock(spec=QueueItem)
    item.id = f"task-{task}-{priority}"
    item.task = task
    item.task_type = task_type
    item.priority = priority
    item.status = status
    item.result = None
    item.error = ""
    item.retry_count = retries
    item.max_retries = max_retries
    item.handler = None
    item.created_at = MagicMock()
    item.created_at.timestamp.return_value = float(priority)
    item.started_at = None
    item.completed_at = None
    item.execution_time_ms = 0.0
    item.metadata = {}
    return item


class TestQueueItem:
    def test_default_id_generated(self):
        item = QueueItem(task="test")
        assert item.id is not None
        assert item.status == "pending"

    def test_custom_values(self):
        item = QueueItem(task="work", task_type="research", priority=5)
        assert item.task == "work"
        assert item.priority == 5
        assert item.max_retries == 3


class TestTaskQueue:
    @pytest.mark.asyncio
    async def test_enqueue_returns_id(self):
        q = TaskQueue()
        task_id = await q.enqueue("do something", task_type="generic", priority=1)
        assert task_id is not None
        assert len(q._items) == 1

    @pytest.mark.asyncio
    async def test_enqueue_sorts_by_priority(self):
        q = TaskQueue()
        await q.enqueue("low", priority=0)
        await q.enqueue("high", priority=10)
        await q.enqueue("medium", priority=5)
        assert q._items[0].priority == 10
        assert q._items[1].priority == 5
        assert q._items[2].priority == 0

    @pytest.mark.asyncio
    async def test_enqueue_stores_handler(self):
        q = TaskQueue()
        handler = MagicMock()
        await q.enqueue("task", handler=handler)
        assert q._items[0].handler is handler

    @pytest.mark.asyncio
    async def test_register_handler(self):
        q = TaskQueue()
        handler = MagicMock()
        q.register_handler("test_type", handler)
        assert q._handlers["test_type"] is handler

    @pytest.mark.asyncio
    async def test_dequeue_returns_highest_priority(self):
        q = TaskQueue()
        await q.enqueue("low", priority=0)
        await q.enqueue("high", priority=10)
        item = await q.dequeue()
        assert item is not None
        assert item.priority == 10
        assert item.status == "running"

    @pytest.mark.asyncio
    async def test_dequeue_returns_none_when_empty(self):
        q = TaskQueue()
        item = await q.dequeue()
        assert item is None

    @pytest.mark.asyncio
    async def test_dequeue_skips_completed(self):
        q = TaskQueue()
        q._items = [_make_item("done", status="completed"), _make_item("pending", status="pending")]
        item = await q.dequeue()
        assert item.task == "pending"

    @pytest.mark.asyncio
    async def test_dequeue_skips_max_retries_exceeded(self):
        q = TaskQueue()
        q._items = [_make_item("exhausted", status="pending", retries=3, max_retries=3)]
        item = await q.dequeue()
        assert item is None

    @pytest.mark.asyncio
    async def test_complete_success(self):
        q = TaskQueue()
        task_id = await q.enqueue("test")
        item = await q.dequeue()
        await q.complete(task_id, result="success")
        assert next(i for i in q._items if i.id == task_id).status == "completed"

    @pytest.mark.asyncio
    async def test_complete_failure_with_retry(self):
        q = TaskQueue()
        task_id = await q.enqueue("test", priority=1)
        await q.dequeue()
        await q.complete(task_id, error="temporary error")
        item = next(i for i in q._items if i.id == task_id)
        assert item.status == "pending"
        assert item.retry_count == 1

    @pytest.mark.asyncio
    async def test_complete_failure_no_more_retries(self):
        q = TaskQueue()
        q._items = [_make_item("fail", status="running", retries=2, max_retries=3)]
        q._running.add("task-fail-0")
        await q.complete("task-fail-0", error="final error")
        item = q._items[0]
        assert item.status == "failed"
        assert item.error == "final error"

    @pytest.mark.asyncio
    async def test_execute_next_with_handler(self):
        q = TaskQueue()
        handler = AsyncMock(return_value="handler result")
        q.register_handler("test_type", handler)
        await q.enqueue("work", task_type="test_type")
        result = await q.execute_next()
        assert result == "handler result"
        handler.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_execute_next_with_item_handler(self):
        q = TaskQueue()
        handler = AsyncMock(return_value="item handler result")
        await q.enqueue("work", handler=handler)
        result = await q.execute_next()
        assert result == "item handler result"

    @pytest.mark.asyncio
    async def test_execute_next_default(self):
        q = TaskQueue()
        await q.enqueue("work")
        with patch("app.orchestration.task_queue.TaskQueue._default_execute", new_callable=AsyncMock) as m_def:
            m_def.return_value = "default result"
            result = await q.execute_next()
            assert result == "default result"

    @pytest.mark.asyncio
    async def test_execute_next_none_available(self):
        q = TaskQueue()
        result = await q.execute_next()
        assert result is None

    @pytest.mark.asyncio
    async def test_execute_next_handles_exception(self):
        q = TaskQueue()
        handler = AsyncMock(side_effect=ValueError("boom"))
        q.register_handler("test_type", handler)
        await q.enqueue("work", task_type="test_type")
        result = await q.execute_next()
        assert result is None

    @pytest.mark.asyncio
    async def test_default_execute_uses_model_manager(self):
        q = TaskQueue()
        item = QueueItem(task="do work")
        with patch("app.llm.model_manager.ModelManager") as mm:
            mm.return_value.generate = AsyncMock(return_value="llm result")
            result = await q._default_execute(item)
            assert result == "llm result"

    @pytest.mark.asyncio
    async def test_default_execute_fallback(self):
        q = TaskQueue()
        item = QueueItem(task="do fallback")
        with patch("app.llm.model_manager.ModelManager") as mm:
            mm.return_value.generate = AsyncMock(side_effect=RuntimeError("no llm"))
            result = await q._default_execute(item)
            assert "Executed:" in str(result)

    @pytest.mark.asyncio
    async def test_get_status_returns_item(self):
        q = TaskQueue()
        task_id = await q.enqueue("my task", task_type="code", priority=3)
        status = await q.get_status(task_id)
        assert status is not None
        assert status["task"] == "my task"
        assert status["task_type"] == "code"
        assert status["priority"] == 3

    @pytest.mark.asyncio
    async def test_get_status_returns_none_for_unknown(self):
        q = TaskQueue()
        status = await q.get_status("nonexistent")
        assert status is None

    @pytest.mark.asyncio
    async def test_get_queue_stats(self):
        q = TaskQueue()
        await q.enqueue("t1", priority=1)
        await q.enqueue("t2", priority=2)
        await q.enqueue("t3", priority=3)
        stats = await q.get_queue_stats()
        assert stats["total"] == 3
        assert stats["pending"] == 3
        assert stats["running"] == 0

    @pytest.mark.asyncio
    async def test_get_queue_stats_after_complete(self):
        q = TaskQueue()
        tid = await q.enqueue("t1")
        await q.dequeue()
        await q.complete(tid, result="done")
        stats = await q.get_queue_stats()
        assert stats["completed"] == 1

    @pytest.mark.asyncio
    async def test_cancel_pending_task(self):
        q = TaskQueue()
        task_id = await q.enqueue("cancel me")
        result = await q.cancel(task_id)
        assert result is True
        status = await q.get_status(task_id)
        assert status["status"] == "failed"
        assert "Cancelled" in status["error"]

    @pytest.mark.asyncio
    async def test_cancel_completed_task_fails(self):
        q = TaskQueue()
        task_id = await q.enqueue("done")
        await q.dequeue()
        await q.complete(task_id, result="done")
        result = await q.cancel(task_id)
        assert result is False

    @pytest.mark.asyncio
    async def test_cancel_unknown_task(self):
        q = TaskQueue()
        result = await q.cancel("nonexistent")
        assert result is False

    @pytest.mark.asyncio
    async def test_clear_completed(self):
        q = TaskQueue()
        t1 = await q.enqueue("keep")
        t2 = await q.enqueue("remove")
        await q.dequeue()
        await q.complete(t2, result="done")
        await q.clear_completed()
        assert any(i.id == t1 for i in q._items)
        assert not any(i.id == t2 for i in q._items)

    @pytest.mark.asyncio
    async def test_execute_parallel(self):
        q = TaskQueue()
        with patch("app.orchestration.task_queue.TaskQueue._default_execute", new_callable=AsyncMock) as m_def:
            m_def.return_value = "done"
            results = await q.execute_parallel(["task1", "task2"], max_concurrent=2)
            assert len(results) == 2

    @pytest.mark.asyncio
    async def test_execute_parallel_handles_errors(self):
        q = TaskQueue()
        with patch("app.orchestration.task_queue.TaskQueue._default_execute", new_callable=AsyncMock) as m_def:
            m_def.side_effect = RuntimeError("fail")
            results = await q.execute_parallel(["task"], max_concurrent=1)
            assert len(results) >= 1
