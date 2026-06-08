"""Unit tests for Syzygy Workflow System."""

import asyncio

import pytest
from app.workflows.coding import CodingWorkflow
from app.workflows.research import ResearchWorkflow
from app.workflows.content import ContentWorkflow
from app.workflows.debate import DebateWorkflow
from app.workflows.task_decomposition import TaskDecompositionWorkflow, Subtask

EXECUTE_TIMEOUT = 300.0


class TestCodingWorkflow:
    @pytest.mark.asyncio
    async def test_execute(self):
        wf = CodingWorkflow()
        result = await asyncio.wait_for(
            wf.execute("Build a hello world app", {"language": "python"}),
            timeout=EXECUTE_TIMEOUT,
        )
        assert result["status"] == "completed"
        assert "steps" in result
        assert "scaffold" in result["steps"]

    def test_required_capabilities(self):
        wf = CodingWorkflow()
        assert "code_generation" in wf.required_capabilities

    def test_name(self):
        assert CodingWorkflow().name == "coding"


class TestResearchWorkflow:
    @pytest.mark.asyncio
    async def test_execute(self):
        wf = ResearchWorkflow()
        result = await asyncio.wait_for(
            wf.execute("Test research query"),
            timeout=EXECUTE_TIMEOUT,
        )
        assert result["status"] == "completed"
        assert "synthesis" in result
        assert "findings" in result

    def test_description(self):
        assert "research" in ResearchWorkflow().description.lower()


class TestContentWorkflow:
    @pytest.mark.asyncio
    async def test_execute(self):
        wf = ContentWorkflow()
        result = await asyncio.wait_for(
            wf.execute("Write about AI", {"polarity": "balanced"}),
            timeout=EXECUTE_TIMEOUT,
        )
        assert result["status"] == "completed"
        assert "final" in result

    @pytest.mark.asyncio
    async def test_execute_masculine(self):
        wf = ContentWorkflow()
        result = await asyncio.wait_for(
            wf.execute("Technical topic", {"polarity": "masculine"}),
            timeout=EXECUTE_TIMEOUT,
        )
        assert result["status"] == "completed"

    @pytest.mark.asyncio
    async def test_execute_feminine(self):
        wf = ContentWorkflow()
        result = await asyncio.wait_for(
            wf.execute("Creative topic", {"polarity": "feminine"}),
            timeout=EXECUTE_TIMEOUT,
        )
        assert result["status"] == "completed"


class TestDebateWorkflow:
    @pytest.mark.asyncio
    async def test_execute(self):
        wf = DebateWorkflow()
        result = await asyncio.wait_for(
            wf.execute("AI safety debate"),
            timeout=EXECUTE_TIMEOUT,
        )
        assert result["status"] == "completed"
        assert "openings" in result
        assert "synthesis" in result

    def test_rounds_definition(self):
        assert len(DebateWorkflow.ROUNDS) == 5
        assert "opening" in DebateWorkflow.ROUNDS
        assert "synthesis" in DebateWorkflow.ROUNDS


class TestTaskDecomposition:
    def test_subtask_creation(self):
        st = Subtask(id="test_1", description="Do something", priority=3)
        assert st.id == "test_1"
        assert st.status == "pending"

    def test_subtask_with_dependencies(self):
        st = Subtask(id="child", description="Child task", dependencies=["parent"])
        assert "parent" in st.dependencies

    @pytest.mark.asyncio
    async def test_decompose(self):
        wf = TaskDecompositionWorkflow()
        subtasks = await asyncio.wait_for(
            wf.decompose("Build a web application"),
            timeout=EXECUTE_TIMEOUT,
        )
        assert len(subtasks) >= 3
        assert all(isinstance(s, Subtask) for s in subtasks)
        assert all(s.id for s in subtasks)
        assert all(s.description for s in subtasks)

    def test_fallback_subtasks(self):
        wf = TaskDecompositionWorkflow()
        subtasks = wf._get_fallback_subtasks("Test task")
        assert len(subtasks) == 6
        assert subtasks[0].polarity == "masculine"
        assert subtasks[-1].polarity == "unified"
        assert subtasks[-1].agent_archetype == "self"
