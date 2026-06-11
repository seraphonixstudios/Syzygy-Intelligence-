"""Unit tests for Syzygy LLM Layer and Orchestration."""

import pytest

from app.llm.model_manager import ModelManager
from app.orchestration.checkpointing import CheckpointManager
from app.orchestration.task_queue import QueueItem, TaskQueue
from app.orchestration.team_formation import TeamFormation
from app.plugins.plugin_system import PluginManifest, PluginSystem


class TestModelManager:
    def test_model_roles(self):
        mgr = ModelManager()
        assert "default" in mgr.MODEL_ROLES
        assert "critic" in mgr.MODEL_ROLES
        assert "coding" in mgr.MODEL_ROLES

    def test_get_model_for_role(self):
        mgr = ModelManager()
        model = mgr.get_model_for_role("default")
        assert model  # Should return a model name string

    def test_model_for_unknown_role_falls_back(self):
        mgr = ModelManager()
        model = mgr.get_model_for_role("nonexistent")
        assert model == mgr.get_model_for_role("default")


class TestTeamFormation:
    @pytest.mark.asyncio
    async def test_suggest_team_for_analysis(self):
        tf = TeamFormation()
        result = await tf.suggest_team_for_task("Analyze the market trends")
        assert "recommended_archetypes" in result
        assert "sage" in result["recommended_archetypes"]

    @pytest.mark.asyncio
    async def test_suggest_team_for_code(self):
        tf = TeamFormation()
        result = await tf.suggest_team_for_task("Write code for a Python web app")
        assert "magician" in result["recommended_archetypes"] or \
               "hero" in result["recommended_archetypes"]

    @pytest.mark.asyncio
    async def test_suggest_team_for_creation(self):
        tf = TeamFormation()
        result = await tf.suggest_team_for_task("Create a piece of art")
        assert "creator" in result["recommended_archetypes"] or \
               "great_mother" in result["recommended_archetypes"]


class TestTaskQueue:
    @pytest.mark.asyncio
    async def test_enqueue_dequeue(self):
        q = TaskQueue()
        task_id = await q.enqueue("Test task", priority=5)
        assert task_id

        item = await q.dequeue()
        assert item is not None
        assert item.id == task_id
        assert item.status == "running"

    @pytest.mark.asyncio
    async def test_priority_ordering(self):
        q = TaskQueue()
        low_id = await q.enqueue("Low priority", priority=1)
        high_id = await q.enqueue("High priority", priority=10)

        first = await q.dequeue()
        assert first.id == high_id

    @pytest.mark.asyncio
    async def test_complete(self):
        q = TaskQueue()
        task_id = await q.enqueue("Test task")
        await q.dequeue()
        await q.complete(task_id, result="Success")

        status = await q.get_status(task_id)
        assert status["status"] == "completed"
        assert status["result"] == "Success"

    @pytest.mark.asyncio
    async def test_cancel(self):
        q = TaskQueue()
        task_id = await q.enqueue("Cancel me")
        assert await q.cancel(task_id)
        status = await q.get_status(task_id)
        assert status["status"] == "failed"

    @pytest.mark.asyncio
    async def test_get_queue_stats(self):
        q = TaskQueue()
        await q.enqueue("Task 1", priority=5)
        await q.enqueue("Task 2", priority=3)
        stats = await q.get_queue_stats()
        assert stats["total"] == 2
        assert stats["pending"] == 2


class TestQueueItem:
    def test_default_retry_count(self):
        item = QueueItem(task="test")
        assert item.max_retries == 3
        assert item.retry_count == 0

    def test_to_dict(self):
        item = QueueItem(task="test task", task_type="research", priority=5)
        assert item.task == "test task"
        assert item.task_type == "research"
        assert item.priority == 5


class TestCheckpointManager:
    @pytest.mark.asyncio
    async def test_save_and_load(self, tmp_path):
        import app.config
        app.config.settings.data_dir = str(tmp_path)

        mgr = CheckpointManager()
        cid = await mgr.save_checkpoint("session_1", 1, {"test": "data"})
        assert cid

        loaded = await mgr.load_checkpoint("session_1", 1)
        assert loaded is not None
        assert loaded["state"]["test"] == "data"

    @pytest.mark.asyncio
    async def test_list_checkpoints(self, tmp_path):
        import app.config
        app.config.settings.data_dir = str(tmp_path)

        mgr = CheckpointManager()
        await mgr.save_checkpoint("session_2", 1, {"round": 1})
        await mgr.save_checkpoint("session_2", 2, {"round": 2})

        checkpoints = await mgr.list_checkpoints("session_2")
        assert len(checkpoints) == 2

    @pytest.mark.asyncio
    async def test_nonexistent_session(self):
        import tempfile

        import app.config
        app.config.settings.data_dir = tempfile.mkdtemp()

        mgr = CheckpointManager()
        assert await mgr.list_checkpoints("nonexistent") == []
        assert await mgr.load_checkpoint("nonexistent", 1) is None


class TestPluginSystem:
    def test_plugin_manifest(self):
        manifest = PluginManifest(
            name="test-plugin",
            version="1.0.0",
            description="Test plugin",
        )
        assert manifest.name == "test-plugin"
        assert manifest.version == "1.0.0"

    def test_empty_registry(self):
        ps = PluginSystem()
        assert ps.get_loaded_plugins() == []

    def test_add_plugin_dir(self):
        ps = PluginSystem()
        ps.add_plugin_dir("/tmp/plugins")
        # No error means success
