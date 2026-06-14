"""Unit tests for Syzygy Workflow System."""

import asyncio
from unittest.mock import AsyncMock

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
