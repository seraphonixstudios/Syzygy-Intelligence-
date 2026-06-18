"""Workflow definitions for Syzygy — task decomposition, parallel execution, priority queuing."""

from __future__ import annotations

from typing import Any

from app.workflows.agentic_rag import AGENTIC_RAG_WORKFLOW, AgenticRagWorkflow
from app.workflows.api_designer import API_DESIGNER_WORKFLOW, ApiDesignerWorkflow
from app.workflows.audit import AUDIT_WORKFLOW, AuditWorkflow
from app.workflows.ci_piper import CI_PIPER_WORKFLOW, CiPiperWorkflow
from app.workflows.coding import CODING_WORKFLOW, CodingWorkflow
from app.workflows.compliance import COMPLIANCE_WORKFLOW, ComplianceWorkflow
from app.workflows.content import CONTENT_WORKFLOW, ContentWorkflow
from app.workflows.data_analyzer import DATA_ANALYZER_WORKFLOW, DataAnalyzerWorkflow
from app.workflows.data_pipeline import DATA_PIPELINE_WORKFLOW, DataPipelineWorkflow
from app.workflows.debate import DEBATE_WORKFLOW, DebateWorkflow
from app.workflows.interview_coach import INTERVIEW_COACH_WORKFLOW, InterviewCoachWorkflow
from app.workflows.qa_bot import QA_BOT_WORKFLOW, QABotWorkflow
from app.workflows.report_gen import REPORT_GEN_WORKFLOW, ReportGenWorkflow
from app.workflows.research import RESEARCH_WORKFLOW, ResearchWorkflow
from app.workflows.summary import SUMMARY_WORKFLOW, SummaryWorkflow
from app.workflows.task_decomposition import TASK_DECOMPOSITION_WORKFLOW, TaskDecompositionWorkflow
from app.workflows.test_gen import TEST_GEN_WORKFLOW, TestGenWorkflow
from app.workflows.translate import TRANSLATE_WORKFLOW, TranslateWorkflow
from app.workflows.image_gen import IMAGE_GEN_WORKFLOW, ImageGenWorkflow
from app.workflows.self_improvement import SELF_IMPROVEMENT_WORKFLOW, RecursiveSelfImprovementWorkflow

WORKFLOW_REGISTRY: dict[str, Any] = {
    "coding": CODING_WORKFLOW,
    "research": RESEARCH_WORKFLOW,
    "content": CONTENT_WORKFLOW,
    "debate": DEBATE_WORKFLOW,
    "task_decomposition": TASK_DECOMPOSITION_WORKFLOW,
    "audit": AUDIT_WORKFLOW,
    "test_gen": TEST_GEN_WORKFLOW,
    "summary": SUMMARY_WORKFLOW,
    "compliance": COMPLIANCE_WORKFLOW,
    "qa_bot": QA_BOT_WORKFLOW,
    "translate": TRANSLATE_WORKFLOW,
    "interview_coach": INTERVIEW_COACH_WORKFLOW,
    "data_analyzer": DATA_ANALYZER_WORKFLOW,
    "api_designer": API_DESIGNER_WORKFLOW,
    "agentic_rag": AGENTIC_RAG_WORKFLOW,
    "report_gen": REPORT_GEN_WORKFLOW,
    "data_pipeline": DATA_PIPELINE_WORKFLOW,
    "ci_piper": CI_PIPER_WORKFLOW,
    "self_improvement": SELF_IMPROVEMENT_WORKFLOW,
    "image_gen": IMAGE_GEN_WORKFLOW,
}


def get_workflow(name: str) -> Any:
    return WORKFLOW_REGISTRY.get(name)


__all__ = [
    "WORKFLOW_REGISTRY", "get_workflow",
    "CodingWorkflow", "ResearchWorkflow",
    "ContentWorkflow", "DebateWorkflow",
    "TaskDecompositionWorkflow",
    "AuditWorkflow", "TestGenWorkflow",
    "SummaryWorkflow", "ComplianceWorkflow",
    "QABotWorkflow",     "TranslateWorkflow",
    "InterviewCoachWorkflow",
    "DataAnalyzerWorkflow",
    "ApiDesignerWorkflow",
    "AgenticRagWorkflow",
    "ReportGenWorkflow",
    "DataPipelineWorkflow",
    "CiPiperWorkflow",
    "RecursiveSelfImprovementWorkflow",
    "ImageGenWorkflow",
]
