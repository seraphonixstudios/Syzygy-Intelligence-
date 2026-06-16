"""Unit tests for Syzygy Workflow System."""

import asyncio
import subprocess
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.workflows.agentic_rag import AgenticRagWorkflow
from app.workflows.api_designer import ApiDesignerWorkflow
from app.workflows.audit import AuditWorkflow
from app.workflows.ci_piper import CiPiperWorkflow
from app.workflows.coding import CodingWorkflow
from app.workflows.compliance import ComplianceWorkflow
from app.workflows.content import ContentWorkflow
from app.workflows.data_analyzer import DataAnalyzerWorkflow
from app.workflows.data_pipeline import DataPipelineWorkflow
from app.workflows.debate import DebateWorkflow
from app.workflows.interview_coach import InterviewCoachWorkflow
from app.workflows.qa_bot import QABotWorkflow
from app.workflows.report_gen import ReportGenWorkflow
from app.workflows.research import ResearchWorkflow
from app.workflows.summary import SummaryWorkflow
from app.workflows.self_improvement import (
    ImprovementCycle,
    RecursiveImprovementSession,
    RecursiveSelfImprovementWorkflow,
)
from app.workflows.task_decomposition import Subtask, TaskDecompositionWorkflow
from app.workflows.test_gen import TestGenWorkflow
from app.workflows.translate import TranslateWorkflow

EXECUTE_TIMEOUT = 30.0


@pytest.fixture
def mock_llm():
    llm = AsyncMock()
    llm.generate.return_value = "mock output"
    return llm


# ===================================================================
# Metadata tests for all workflows
# ===================================================================

WORKFLOW_META: list[tuple[type, str, list[str], list[str]]] = [
    (AgenticRagWorkflow, "agentic_rag", ["RAG", "retrieval"], ["query_planning", "retrieval"]),
    (ApiDesignerWorkflow, "api_designer", ["API", "OpenAPI"], ["api_design", "openapi_generation"]),
    (AuditWorkflow, "audit", ["security", "review"], ["code_review", "vulnerability_scanning"]),
    (CiPiperWorkflow, "ci_piper", ["CI/CD", "GitHub"], ["ci_cd_design", "config_generation"]),
    (CodingWorkflow, "coding", ["software", "code"], ["code_generation", "code_review"]),
    (ComplianceWorkflow, "compliance", ["compliance", "GDPR"], ["compliance_analysis", "policy_mapping"]),
    (ContentWorkflow, "content", ["content", "writing"], ["writing", "storytelling"]),
    (DataAnalyzerWorkflow, "data_analyzer", ["analysis", "data"], ["statistical_analysis", "anomaly_detection"]),
    (DataPipelineWorkflow, "data_pipeline", ["pipeline", "ETL"], ["data_ingestion", "data_cleaning"]),
    (DebateWorkflow, "debate", ["debate", "polarity"], ["argumentation", "critique"]),
    (InterviewCoachWorkflow, "interview_coach", ["interview", "questions"], ["question_generation", "answer_evaluation"]),
    (QABotWorkflow, "qa_bot", ["QA", "knowledge"], ["document_qa", "retrieval"]),
    (ReportGenWorkflow, "report_gen", ["report", "chart"], ["research", "writing"]),
    (ResearchWorkflow, "research", ["research", "source"], []),
    (SummaryWorkflow, "summary", ["summarization", "summary"], ["summarization", "information_extraction"]),
    (TestGenWorkflow, "test_gen", ["test", "code"], ["test_generation", "code_analysis"]),
    (TranslateWorkflow, "translate", ["translation", "language"], ["translation", "cultural_adaptation"]),
]


class TestAllWorkflowMeta:
    @pytest.mark.parametrize("cls,expected_name,desc_keywords,caps", WORKFLOW_META)
    def test_name(self, cls, expected_name, desc_keywords, caps):
        wf = cls()
        assert wf.name == expected_name

    @pytest.mark.parametrize("cls,expected_name,desc_keywords,caps", WORKFLOW_META)
    def test_description_contains_keyword(self, cls, expected_name, desc_keywords, caps):
        wf = cls()
        desc = wf.description.lower()
        assert any(kw.lower() in desc for kw in desc_keywords), f"None of {desc_keywords} found in description"

    @pytest.mark.parametrize("cls,expected_name,desc_keywords,caps", WORKFLOW_META)
    def test_required_capabilities(self, cls, expected_name, desc_keywords, caps):
        wf = cls()
        wf_caps = getattr(wf, "required_capabilities", [])
        for cap in caps:
            assert cap in wf_caps, f"Capability {cap!r} not in {wf_caps}"


# ===================================================================
# execute() for untested workflows
# ===================================================================

class TestAgenticRagWorkflow:
    @pytest.mark.asyncio
    async def test_execute(self, mock_llm):
        wf = AgenticRagWorkflow()
        wf.llm = mock_llm
        result = await asyncio.wait_for(
            wf.execute("Test query"),
            timeout=EXECUTE_TIMEOUT,
        )
        assert result["status"] == "completed"
        assert "synthesized_answer" in result

    @pytest.mark.asyncio
    async def test_execute_with_context(self, mock_llm):
        wf = AgenticRagWorkflow()
        wf.llm = mock_llm
        result = await asyncio.wait_for(
            wf.execute("Query", {"domain": "tech"}),
            timeout=EXECUTE_TIMEOUT,
        )
        assert result["status"] == "completed"


class TestApiDesignerWorkflow:
    @pytest.mark.asyncio
    async def test_execute(self, mock_llm):
        wf = ApiDesignerWorkflow()
        wf.llm = mock_llm
        result = await asyncio.wait_for(
            wf.execute("Design user API"),
            timeout=EXECUTE_TIMEOUT,
        )
        assert result["status"] == "completed"
        assert "endpoint_design" in result

    @pytest.mark.asyncio
    async def test_execute_with_language(self, mock_llm):
        wf = ApiDesignerWorkflow()
        wf.llm = mock_llm
        result = await asyncio.wait_for(
            wf.execute("API", {"language": "python"}),
            timeout=EXECUTE_TIMEOUT,
        )
        assert result["status"] == "completed"


class TestAuditWorkflow:
    @pytest.mark.asyncio
    async def test_execute(self, mock_llm):
        wf = AuditWorkflow()
        wf.llm = mock_llm
        result = await asyncio.wait_for(
            wf.execute("Review code"),
            timeout=EXECUTE_TIMEOUT,
        )
        assert result["status"] == "completed"
        assert "vulnerabilities" in result

    @pytest.mark.asyncio
    async def test_execute_with_language(self, mock_llm):
        wf = AuditWorkflow()
        wf.llm = mock_llm
        result = await asyncio.wait_for(
            wf.execute("Code", {"language": "python"}),
            timeout=EXECUTE_TIMEOUT,
        )
        assert result["status"] == "completed"


class TestCiPiperWorkflow:
    @pytest.mark.asyncio
    async def test_execute(self, mock_llm):
        wf = CiPiperWorkflow()
        wf.llm = mock_llm
        result = await asyncio.wait_for(
            wf.execute("Set up CI"),
            timeout=EXECUTE_TIMEOUT,
        )
        assert result["status"] == "completed"
        assert "configs" in result


class TestComplianceWorkflow:
    @pytest.mark.asyncio
    async def test_execute(self, mock_llm):
        wf = ComplianceWorkflow()
        wf.llm = mock_llm
        result = await asyncio.wait_for(
            wf.execute("GDPR compliance check"),
            timeout=EXECUTE_TIMEOUT,
        )
        assert result["status"] == "completed"
        assert "frameworks_checked" in result

    @pytest.mark.asyncio
    async def test_execute_with_frameworks(self, mock_llm):
        wf = ComplianceWorkflow()
        wf.llm = mock_llm
        result = await asyncio.wait_for(
            wf.execute("Check", {"frameworks": ["GDPR", "SOC2"]}),
            timeout=EXECUTE_TIMEOUT,
        )
        assert result["status"] == "completed"


class TestDataAnalyzerWorkflow:
    @pytest.mark.asyncio
    async def test_execute(self, mock_llm):
        wf = DataAnalyzerWorkflow()
        wf.llm = mock_llm
        result = await asyncio.wait_for(
            wf.execute("Analyze sales data"),
            timeout=EXECUTE_TIMEOUT,
        )
        assert result["status"] == "completed"
        assert "summary" in result


class TestDataPipelineWorkflow:
    @pytest.mark.asyncio
    async def test_execute(self, mock_llm):
        wf = DataPipelineWorkflow()
        wf.llm = mock_llm
        result = await asyncio.wait_for(
            wf.execute("Build ETL pipeline"),
            timeout=EXECUTE_TIMEOUT,
        )
        assert result["status"] == "completed"
        assert "ingestion_analysis" in result


class TestInterviewCoachWorkflow:
    @pytest.mark.asyncio
    async def test_execute(self, mock_llm):
        wf = InterviewCoachWorkflow()
        wf.llm = mock_llm
        result = await asyncio.wait_for(
            wf.execute("Software engineer interview"),
            timeout=EXECUTE_TIMEOUT,
        )
        assert result["status"] == "completed"
        assert "questions" in result


class TestQABotWorkflow:
    @pytest.mark.asyncio
    async def test_execute_ask(self, mock_llm):
        wf = QABotWorkflow()
        wf.llm = mock_llm
        result = await asyncio.wait_for(
            wf.execute("What is AI?", {"action": "ask"}),
            timeout=EXECUTE_TIMEOUT,
        )
        assert result["status"] == "completed"
        assert "answer" in result

    @pytest.mark.asyncio
    async def test_execute_ingest(self, mock_llm):
        wf = QABotWorkflow()
        wf.llm = mock_llm
        result = await asyncio.wait_for(
            wf.execute("Some text", {"action": "ingest"}),
            timeout=EXECUTE_TIMEOUT,
        )
        assert result["status"] == "completed"


class TestReportGenWorkflow:
    @pytest.mark.asyncio
    async def test_execute(self, mock_llm):
        wf = ReportGenWorkflow()
        wf.llm = mock_llm
        result = await asyncio.wait_for(
            wf.execute("Annual report"),
            timeout=EXECUTE_TIMEOUT,
        )
        assert result["status"] == "completed"
        assert "report" in result


class TestSummaryWorkflow:
    @pytest.mark.asyncio
    async def test_execute(self, mock_llm):
        wf = SummaryWorkflow()
        wf.llm = mock_llm
        result = await asyncio.wait_for(
            wf.execute("Summarize this text"),
            timeout=EXECUTE_TIMEOUT,
        )
        assert result["status"] == "completed"
        assert "summary" in result


class TestTestGenWorkflow:
    @pytest.mark.asyncio
    async def test_execute(self, mock_llm):
        wf = TestGenWorkflow()
        wf.llm = mock_llm
        result = await asyncio.wait_for(
            wf.execute("Test calculator function"),
            timeout=EXECUTE_TIMEOUT,
        )
        assert result["status"] == "completed"
        assert "unit_tests" in result

    @pytest.mark.asyncio
    async def test_execute_with_language(self, mock_llm):
        wf = TestGenWorkflow()
        wf.llm = mock_llm
        result = await asyncio.wait_for(
            wf.execute("Test code", {"language": "python"}),
            timeout=EXECUTE_TIMEOUT,
        )
        assert result["status"] == "completed"


class TestTranslateWorkflow:
    @pytest.mark.asyncio
    async def test_execute(self, mock_llm):
        wf = TranslateWorkflow()
        wf.llm = mock_llm
        result = await asyncio.wait_for(
            wf.execute("Hello world", {"target_language": "French"}),
            timeout=EXECUTE_TIMEOUT,
        )
        assert result["status"] == "completed"
        assert "direct_translation" in result

    @pytest.mark.asyncio
    async def test_execute_with_language_detection(self, mock_llm):
        wf = TranslateWorkflow()
        wf.llm = mock_llm
        result = await asyncio.wait_for(
            wf.execute("Bonjour le monde", {"source_language": "French", "target_language": "English"}),
            timeout=EXECUTE_TIMEOUT,
        )
        assert result["status"] == "completed"


class TestCodingWorkflow:
    @pytest.mark.asyncio
    async def test_execute(self, mock_llm):
        wf = CodingWorkflow()
        wf.llm = mock_llm
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
    async def test_execute(self, mock_llm):
        wf = ResearchWorkflow()
        wf.llm = mock_llm
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
    async def test_execute(self, mock_llm):
        wf = ContentWorkflow()
        wf.llm = mock_llm
        result = await asyncio.wait_for(
            wf.execute("Write about AI", {"polarity": "balanced"}),
            timeout=EXECUTE_TIMEOUT,
        )
        assert result["status"] == "completed"
        assert "final" in result

    @pytest.mark.asyncio
    async def test_execute_masculine(self, mock_llm):
        wf = ContentWorkflow()
        wf.llm = mock_llm
        result = await asyncio.wait_for(
            wf.execute("Technical topic", {"polarity": "masculine"}),
            timeout=EXECUTE_TIMEOUT,
        )
        assert result["status"] == "completed"

    @pytest.mark.asyncio
    async def test_execute_feminine(self, mock_llm):
        wf = ContentWorkflow()
        wf.llm = mock_llm
        result = await asyncio.wait_for(
            wf.execute("Creative topic", {"polarity": "feminine"}),
            timeout=EXECUTE_TIMEOUT,
        )
        assert result["status"] == "completed"


class TestDebateWorkflow:
    @pytest.mark.asyncio
    async def test_execute(self, mock_llm):
        wf = DebateWorkflow()
        wf.llm = mock_llm
        result = await asyncio.wait_for(
            wf.execute("AI safety debate"),
            timeout=EXECUTE_TIMEOUT,
        )
        assert result["status"] == "completed"
        assert "openings" in result
        assert "synthesis" in result

    @pytest.mark.asyncio
    async def test_cross_examine(self, mock_llm):
        wf = DebateWorkflow()
        wf.llm = mock_llm
        result = await wf.cross_examine(topic="AI", position="pro", opponent_args="test opponent")
        assert result == "mock output"

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
    async def test_decompose(self, mock_llm):
        wf = TaskDecompositionWorkflow()
        wf.llm = mock_llm
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


class TestGetWorkflow:
    def test_returns_code_workflow(self):
        from app.workflows import get_workflow
        from app.workflows.coding import CodingWorkflow

        wf = get_workflow("coding")
        assert isinstance(wf, CodingWorkflow)

    def test_returns_none_for_invalid_name(self):
        from app.workflows import get_workflow

        wf = get_workflow("invalid")
        assert wf is None


class TestQABotWorkflowEdgeCases:
    @pytest.mark.asyncio
    async def test_retrieve_context_with_knowledge_base(self, mock_llm):
        wf = QABotWorkflow()
        wf.llm = mock_llm
        wf.knowledge_base = {"doc1": "Content about AI.", "doc2": "More content."}
        result = await wf.retrieve_context("What is AI?")
        assert result["sources"] == ["doc1", "doc2"]
        assert "Retrieved from knowledge base" in result["note"]

    @pytest.mark.asyncio
    async def test_retrieve_context_empty_knowledge_base(self, mock_llm):
        wf = QABotWorkflow()
        wf.llm = mock_llm
        result = await wf.retrieve_context("Some query")
        assert "No documents ingested" in result["note"]

    @pytest.mark.asyncio
    async def test_generate_follow_ups_fallback(self, mock_llm):
        wf = QABotWorkflow()
        wf.llm = mock_llm
        mock_llm.generate.return_value = "No numbered items here"
        result = await wf.generate_follow_ups("What?", "Answer text")
        assert len(result) == 3


class TestDataPipelineWorkflowEdgeCases:
    @pytest.mark.asyncio
    async def test_validate_schema(self, mock_llm):
        wf = DataPipelineWorkflow()
        wf.llm = mock_llm
        result = await wf.validate_schema("col1,col2\n1,2", "col1:int,col2:int")
        assert "validation" in result

    @pytest.mark.asyncio
    async def test_execute_with_target_schema(self, mock_llm):
        wf = DataPipelineWorkflow()
        wf.llm = mock_llm
        result = await asyncio.wait_for(
            wf.execute("data", {"source_data": "col1,col2\n1,2", "target_schema": "schema"}),
            timeout=EXECUTE_TIMEOUT,
        )
        assert result["status"] == "completed"
        assert "schema_validation" in result

    @pytest.mark.asyncio
    async def test_execute_without_target_schema(self, mock_llm):
        wf = DataPipelineWorkflow()
        wf.llm = mock_llm
        result = await asyncio.wait_for(
            wf.execute("data", {"source_data": "col1,col2\n1,2"}),
            timeout=EXECUTE_TIMEOUT,
        )
        assert result["status"] == "completed"
        assert result["schema_validation"] == {}


# ===================================================================
# CodingWorkflow edge cases — edit(), test(), debug() uncovered paths
# ===================================================================

class TestCodingWorkflowEdgeCases:
    @pytest.mark.asyncio
    async def test_edit_file_not_found(self, mock_llm):
        wf = CodingWorkflow()
        wf.llm = mock_llm
        result = await wf.edit("nonexistent_path_abc123/file.py", "fix it")
        assert result["error"] is not None
        assert not result["edited"]

    @pytest.mark.asyncio
    async def test_edit_ollama_error(self, mock_llm):
        wf = CodingWorkflow()
        wf.llm = mock_llm
        mock_llm.generate.return_value = "[Ollama error] API down"
        with patch("app.workflows.coding.Path") as mock_path:
            mock_path.return_value.exists.return_value = True
            mock_path.return_value.read_text.return_value = "original"
            result = await wf.edit("dummy.py", "change it")
        assert not result["edited"]
        assert "Failed to generate edit" in result["error"]

    @pytest.mark.asyncio
    async def test_edit_success(self, mock_llm):
        wf = CodingWorkflow()
        wf.llm = mock_llm
        mock_llm.generate.return_value = "new content"
        with patch("app.workflows.coding.Path") as mock_path:
            instance = mock_path.return_value
            instance.exists.return_value = True
            instance.read_text.return_value = "original"
            result = await wf.edit("dummy.py", "change it")
        assert result["edited"] is True
        instance.write_text.assert_called_once_with("new content", encoding="utf-8")

    @pytest.mark.asyncio
    async def test_test_ollama_error(self, mock_llm):
        wf = CodingWorkflow()
        wf.llm = mock_llm
        mock_llm.generate.return_value = "[Ollama error] API error"
        result = await wf.test("print('hello')")
        assert not result["tested"]
        assert "[Ollama error]" in result["error"]

    @pytest.mark.asyncio
    async def test_test_subprocess_timeout(self, mock_llm):
        wf = CodingWorkflow()
        wf.llm = mock_llm
        with patch("app.workflows.coding.subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.TimeoutExpired(cmd="python", timeout=30)
            result = await wf.test("print('hello')")
        assert not result["tested"]
        assert "timed out" in result["error"]

    @pytest.mark.asyncio
    async def test_test_subprocess_exception(self, mock_llm):
        wf = CodingWorkflow()
        wf.llm = mock_llm
        with patch("app.workflows.coding.subprocess.run") as mock_run:
            mock_run.side_effect = Exception("unexpected error")
            result = await wf.test("print('hello')")
        assert not result["tested"]
        assert "unexpected error" in result["error"]

    @pytest.mark.asyncio
    async def test_debug(self, mock_llm):
        wf = CodingWorkflow()
        wf.llm = mock_llm
        result = await wf.debug("SyntaxError", "def foo() pass")
        assert result["error"] == "SyntaxError"
        assert "analysis" in result


# ===================================================================
# TaskDecompositionWorkflow edge cases — _parse_subtasks, execute()
# ===================================================================

class TestTaskDecompositionEdgeCases:
    def test_parse_subtasks_partial_fields(self):
        wf = TaskDecompositionWorkflow()
        text = (
            "SUBTASK: id1 | desc | dep1 | archetype | polarity\n"
            "SUBTASK: id2 | desc2 | dep2 | arch2 | pol2 | 3\n"
        )
        result = wf._parse_subtasks(text)
        assert len(result) == 1
        assert result[0].id == "id2"

    def test_parse_subtasks_value_error(self):
        wf = TaskDecompositionWorkflow()
        text = "SUBTASK: bad_id | desc | deps | arch | pol | not_a_number\n"
        result = wf._parse_subtasks(text)
        assert len(result) == 0

    @pytest.mark.asyncio
    async def test_execute_with_callback(self, mock_llm):
        wf = TaskDecompositionWorkflow()
        wf.llm = mock_llm
        mock_llm.generate.return_value = "SUBTASK: test_1 | Do the thing | ; | sage | unified | 3\n"
        called = []

        async def callback(st):
            called.append(st)

        result = await wf.execute("Do stuff", on_subtask_complete=callback)
        assert len(called) == 1
        assert called[0].id == "test_1"
        assert called[0].status == "completed"

    @pytest.mark.asyncio
    async def test_execute_unmet_dependencies(self, mock_llm):
        wf = TaskDecompositionWorkflow()
        wf.llm = mock_llm
        mock_llm.generate.return_value = (
            "SUBTASK: task_a | First task | ; | sage | masculine | 3\n"
            "SUBTASK: task_c | Depends on missing | missing_dep | sage | unified | 2\n"
        )
        result = await wf.execute("Complex task")
        task_a = next(s for s in result if s.id == "task_a")
        assert task_a.status == "completed"
        task_c = next(s for s in result if s.id == "task_c")
        assert task_c.status == "pending"


# ===================================================================
# InterviewCoachWorkflow edge cases — evaluate_answer, generate_feedback, execute
# ===================================================================

class TestInterviewCoachWorkflowEdgeCases:
    @pytest.mark.asyncio
    async def test_evaluate_answer(self, mock_llm):
        wf = InterviewCoachWorkflow()
        wf.llm = mock_llm
        result = await wf.evaluate_answer("What is OOP?", "OOP is...", "developer")
        assert "evaluation" in result
        assert result["question"] == "What is OOP?"

    @pytest.mark.asyncio
    async def test_generate_feedback(self, mock_llm):
        wf = InterviewCoachWorkflow()
        wf.llm = mock_llm
        evals = [{"question": "Q1", "evaluation": "Good"}, {"question": "Q2", "evaluation": "Bad"}]
        result = await wf.generate_feedback(evals)
        assert isinstance(result, str)

    @pytest.mark.asyncio
    async def test_generate_feedback_empty(self, mock_llm):
        wf = InterviewCoachWorkflow()
        wf.llm = mock_llm
        result = await wf.generate_feedback([])
        assert isinstance(result, str)

    @pytest.mark.asyncio
    async def test_execute_skips_empty_answers(self, mock_llm):
        wf = InterviewCoachWorkflow()
        wf.llm = mock_llm
        result = await wf.execute("role", {
            "answers": [{"question": "", "answer": ""}, {"question": "Q", "answer": ""}]
        })
        assert result["status"] == "completed"
        assert len(result["evaluations"]) == 0
        assert result["feedback"] is None

    @pytest.mark.asyncio
    async def test_execute_no_answers(self, mock_llm):
        wf = InterviewCoachWorkflow()
        wf.llm = mock_llm
        result = await wf.execute("Engineer")
        assert result["status"] == "completed"
        assert result["evaluations"] == []
        assert result["feedback"] is None


# ===================================================================
# AgenticRagWorkflow edge cases — retrieve_context, execute with KB
# ===================================================================

class TestAgenticRagWorkflowEdgeCases:
    @pytest.mark.asyncio
    async def test_retrieve_context(self, mock_llm):
        wf = AgenticRagWorkflow()
        wf.llm = mock_llm
        result = await wf.retrieve_context("What is AI?", "AI is a field of study.")
        assert result["sub_query"] == "What is AI?"
        assert "retrieved" in result

    @pytest.mark.asyncio
    async def test_execute_with_knowledge_base(self, mock_llm):
        wf = AgenticRagWorkflow()
        wf.llm = mock_llm
        mock_llm.generate.side_effect = [
            "1. First sub-query\n2. Second sub-query\n",
            "mock retrieved 1",
            "mock retrieved 2",
            "mock synthesis",
            "mock validation",
        ]
        result = await wf.execute("AI query", {"knowledge_base": "Some knowledge content"})
        assert result["status"] == "completed"
        assert len(result["retrieval_results"]) == 2


# ===================================================================
# CiPiperWorkflow edge cases — generate_gitlab_ci, generate_jenkins, execute platforms
# ===================================================================

class TestCiPiperWorkflowEdgeCases:
    @pytest.mark.asyncio
    async def test_generate_gitlab_ci(self, mock_llm):
        wf = CiPiperWorkflow()
        wf.llm = mock_llm
        result = await wf.generate_gitlab_ci("Python project", {"analysis": "Test analysis"})
        assert result["platform"] == "gitlab_ci"
        assert "config" in result

    @pytest.mark.asyncio
    async def test_generate_jenkins(self, mock_llm):
        wf = CiPiperWorkflow()
        wf.llm = mock_llm
        result = await wf.generate_jenkins("Python project", {"analysis": "Test"})
        assert result["platform"] == "jenkins"
        assert "config" in result

    @pytest.mark.asyncio
    async def test_execute_all_platforms(self, mock_llm):
        wf = CiPiperWorkflow()
        wf.llm = mock_llm
        mock_llm.generate.side_effect = [
            "analysis output",
            "github config",
            "gitlab config",
            "jenkins config",
        ]
        result = await wf.execute("CI setup", context={
            "platforms": ["github_actions", "gitlab_ci", "jenkins"]
        })
        assert result["status"] == "completed"
        assert len(result["configs"]) == 3


# ===================================================================
# ResearchWorkflow edge cases — search dedup, validate
# ===================================================================

class TestResearchWorkflowEdgeCases:
    @pytest.mark.asyncio
    async def test_search_deduplicate(self, mock_llm):
        wf = ResearchWorkflow()
        wf.llm = mock_llm
        mock_llm.generate.return_value = "- sub query 1\n- sub query 2\n"
        wf.search_tool = AsyncMock()
        wf.search_tool.execute.return_value = {
            "results": [
                {"url": "http://example.com/a", "title": "A", "snippet": "Content A"},
                {"url": "http://example.com/a", "title": "A dup", "snippet": "Content A dup"},
                {"url": "http://example.com/b", "title": "B", "snippet": "Content B"},
            ]
        }
        results = await wf.search("test query")
        assert len(results) == 2
        assert results[0]["url"] == "http://example.com/a"
        assert results[1]["url"] == "http://example.com/b"

    @pytest.mark.asyncio
    async def test_validate_with_findings(self, mock_llm):
        wf = ResearchWorkflow()
        wf.llm = mock_llm
        findings = [{"url": "http://example.com/1", "snippet": "Finding one"}]
        result = await wf.validate(findings)
        assert len(result) == 1
        assert result[0]["validated"] is True

    @pytest.mark.asyncio
    async def test_validate_empty_findings(self):
        wf = ResearchWorkflow()
        result = await wf.validate([])
        assert result == []


# ===================================================================
# RecursiveSelfImprovementWorkflow — memory path, propose/apply improvement branches
# ===================================================================

class TestInterviewCoachWorkflowAnswers:
    @pytest.mark.asyncio
    async def test_execute_with_valid_answers(self, mock_llm):
        """Lines 92-93, 97: evaluate_answer and generate_feedback with valid data."""
        wf = InterviewCoachWorkflow()
        wf.llm = mock_llm
        result = await wf.execute("Engineer interview", {
            "answers": [
                {"question": "What is OOP?", "answer": "Object-oriented programming"},
                {"question": "What is Python?", "answer": "A programming language"},
            ]
        })
        assert result["status"] == "completed"
        assert len(result["evaluations"]) >= 1
        assert result["feedback"] is not None


class TestRecursiveSelfImprovementWorkflow:
    @pytest.fixture
    def _mock_deps(self, mock_llm):
        """Returns a pre-configured workflow with all mocks in place."""
        wf = RecursiveSelfImprovementWorkflow(llm=mock_llm)
        consensus_session = MagicMock()
        consensus_session.final_synthesis = "consensus output"
        wf.consensus.run_consensus = AsyncMock(return_value=consensus_session)
        assess_result = MagicMock()
        assess_result.overall_score = 0.5
        assess_result.dimension_scores = {"accuracy": 0.5}
        assess_result.root_causes = {}
        wf.assessor.assess = AsyncMock(return_value=assess_result)
        wf.optimizer.get_learning_rate = MagicMock(return_value=0.1)
        wf._generate_improvements = AsyncMock(return_value=[])
        wf._generate_meta_insights = AsyncMock(return_value=["insight"])
        return wf

    @pytest.mark.asyncio
    async def test_execute_single_cycle(self, mock_llm, _mock_deps):
        wf = _mock_deps
        agents = [MagicMock(), MagicMock()]
        agents[0].name = "sage"
        agents[1].name = "hero"
        for a in agents:
            a.archetype = MagicMock()
            a.archetype.name = "sage"
        result = await wf.execute("task", agents=agents, max_cycles=1)
        assert result.status == "completed"
        assert len(result.cycles) == 1

    @pytest.mark.asyncio
    async def test_execute_with_memory(self, mock_llm, _mock_deps):
        wf = _mock_deps
        wf.memory = AsyncMock()
        agents = [MagicMock(), MagicMock()]
        agents[0].name = "sage"
        agents[1].name = "hero"
        for a in agents:
            a.archetype = MagicMock()
            a.archetype.name = "sage"
        wf._improvements = []
        result = await wf.execute("task", agents=agents, max_cycles=1)
        assert result.status == "completed"

    @pytest.mark.asyncio
    async def test_execute_with_performance_gain(self, mock_llm):
        """Test line 242: agents = modified_agents when performance_delta > 0."""
        from app.agents.base import SyzygyAgent
        agent = SyzygyAgent.create("sage")
        wf = RecursiveSelfImprovementWorkflow(llm=mock_llm)
        consensus_session = MagicMock()
        consensus_session.final_synthesis = "improved output"
        wf.consensus.run_consensus = AsyncMock(return_value=consensus_session)
        # Return higher score on second call for positive delta
        initial = MagicMock(overall_score=0.3, dimension_scores={"accuracy": 0.3}, root_causes={})
        final = MagicMock(overall_score=0.7, dimension_scores={"accuracy": 0.7}, root_causes={})
        wf.assessor.assess = AsyncMock(side_effect=[initial, final])
        wf.optimizer.get_learning_rate = MagicMock(return_value=0.1)
        wf._generate_improvements = AsyncMock(return_value=[
            {"type": "prompt-tuning", "target_agent": "sage", "action": "be more precise"},
        ])
        wf._generate_meta_insights = AsyncMock(return_value=["insight"])
        result = await wf.execute("task", agents=[agent], max_cycles=1)
        assert result.status == "completed"
        assert result.cycles[0].performance_delta > 0

    @pytest.mark.asyncio
    async def test_propose_improvement_parse_failure(self, mock_llm):
        wf = RecursiveSelfImprovementWorkflow(llm=mock_llm)
        mock_llm.generate.return_value = "Not valid JSON at all"
        result = await wf._propose_improvement(
            task="task", output="output", dimension="accuracy",
            score=0.3, agents=[], root_causes=["cause"],
        )
        assert result is None

    @pytest.mark.asyncio
    async def test_propose_improvement_json_parse_exception(self, mock_llm):
        """Lines 328-329: json.loads raises inside try block."""
        wf = RecursiveSelfImprovementWorkflow(llm=mock_llm)
        mock_llm.generate.return_value = "Some prefix {invalid json structure} suffix"
        result = await wf._propose_improvement(
            task="task", output="output", dimension="accuracy",
            score=0.3, agents=[], root_causes=["cause"],
        )
        assert result is None

    @pytest.mark.asyncio
    async def test_apply_improvements_target_not_found(self):
        wf = RecursiveSelfImprovementWorkflow(llm=AsyncMock())
        from app.agents.base import SyzygyAgent
        agent = SyzygyAgent.create("sage")
        improvements = [{"type": "prompt-tuning", "target_agent": "nonexistent", "action": "fix"}]
        result = await wf._apply_improvements([agent], improvements, 0.1)
        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_apply_improvements_role_change_no_attr(self):
        """Line 367: hasattr returns False, initializes role_adjustments."""
        wf = RecursiveSelfImprovementWorkflow(llm=AsyncMock())
        from app.agents.base import SyzygyAgent
        agent = SyzygyAgent.create("sage")
        # Ensure attribute doesn't exist
        if hasattr(agent, "role_adjustments"):
            del agent.role_adjustments
        improvements = [{"type": "agent-role-change", "target_agent": "sage", "action": "shift focus"}]
        result = await wf._apply_improvements([agent], improvements, 0.1)
        assert result[0].role_adjustments == ["shift focus"]

    @pytest.mark.asyncio
    async def test_apply_improvements_tool_addition_no_attr(self):
        """Line 373: hasattr returns False, initializes requested_tools."""
        wf = RecursiveSelfImprovementWorkflow(llm=AsyncMock())
        from app.agents.base import SyzygyAgent
        agent = SyzygyAgent.create("sage")
        if hasattr(agent, "requested_tools"):
            del agent.requested_tools
        improvements = [{"type": "tool-addition", "target_agent": "sage", "action": "add code executor"}]
        result = await wf._apply_improvements([agent], improvements, 0.1)
        assert "add code executor" in result[0].requested_tools

    @pytest.mark.asyncio
    async def test_apply_improvements_consensus_adjustment_no_attr(self):
        """Line 379: hasattr returns False, initializes consensus_weight."""
        wf = RecursiveSelfImprovementWorkflow(llm=AsyncMock())
        from app.agents.base import SyzygyAgent
        agent = SyzygyAgent.create("sage")
        if hasattr(agent, "consensus_weight"):
            del agent.consensus_weight
        improvements = [{"type": "consensus-adjustment", "target_agent": "sage", "action": "increase weight"}]
        result = await wf._apply_improvements([agent], improvements, 0.1)
        assert result[0].consensus_weight == 1.0 * 1.1

    @pytest.mark.asyncio
    async def test_apply_improvements_role_change(self):
        wf = RecursiveSelfImprovementWorkflow(llm=AsyncMock())
        from app.agents.base import SyzygyAgent
        agent = SyzygyAgent.create("sage")
        agent.role_adjustments = []
        improvements = [{"type": "agent-role-change", "target_agent": "sage", "action": "shift focus"}]
        result = await wf._apply_improvements([agent], improvements, 0.1)
        assert result[0].role_adjustments == ["shift focus"]

    @pytest.mark.asyncio
    async def test_apply_improvements_tool_addition(self):
        wf = RecursiveSelfImprovementWorkflow(llm=AsyncMock())
        from app.agents.base import SyzygyAgent
        agent = SyzygyAgent.create("sage")
        agent.requested_tools = []
        improvements = [{"type": "tool-addition", "target_agent": "sage", "action": "add code executor"}]
        result = await wf._apply_improvements([agent], improvements, 0.1)
        assert "add code executor" in result[0].requested_tools

    @pytest.mark.asyncio
    async def test_apply_improvements_consensus_adjustment(self):
        wf = RecursiveSelfImprovementWorkflow(llm=AsyncMock())
        from app.agents.base import SyzygyAgent
        agent = SyzygyAgent.create("sage")
        improvements = [{"type": "consensus-adjustment", "target_agent": "sage", "action": "increase weight"}]
        result = await wf._apply_improvements([agent], improvements, 0.1)
        assert result[0].consensus_weight == 1.0 * 1.1

    @pytest.mark.asyncio
    async def test_generate_meta_insights_strong(self):
        wf = RecursiveSelfImprovementWorkflow(llm=AsyncMock())
        session = RecursiveImprovementSession(id="test", task="task", domain="code")
        cycle = ImprovementCycle(cycle_number=1, task="task")
        cycle.performance_delta = 0.2
        session.cycles.append(cycle)
        session.total_performance_gain = 0.2
        insights = await wf._generate_meta_insights(session)
        assert any("Strong improvement" in i for i in insights)

    @pytest.mark.asyncio
    async def test_generate_meta_insights_gradual(self):
        wf = RecursiveSelfImprovementWorkflow(llm=AsyncMock())
        session = RecursiveImprovementSession(id="test", task="task", domain="code")
        cycle = ImprovementCycle(cycle_number=1, task="task")
        cycle.performance_delta = 0.05
        session.cycles.append(cycle)
        session.total_performance_gain = 0.05
        insights = await wf._generate_meta_insights(session)
        assert any("Gradual improvement" in i for i in insights)
