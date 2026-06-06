"""Workflow definitions for Syzygy — task decomposition, parallel execution, priority queuing."""

from __future__ import annotations

from typing import Any

from app.workflows.coding import CodingWorkflow, CODING_WORKFLOW
from app.workflows.research import ResearchWorkflow, RESEARCH_WORKFLOW
from app.workflows.content import ContentWorkflow, CONTENT_WORKFLOW
from app.workflows.debate import DebateWorkflow, DEBATE_WORKFLOW
from app.workflows.task_decomposition import TaskDecompositionWorkflow, TASK_DECOMPOSITION_WORKFLOW
from app.workflows.audit import AuditWorkflow, AUDIT_WORKFLOW
from app.workflows.test_gen import TestGenWorkflow, TEST_GEN_WORKFLOW
from app.workflows.summary import SummaryWorkflow, SUMMARY_WORKFLOW
from app.workflows.compliance import ComplianceWorkflow, COMPLIANCE_WORKFLOW
from app.workflows.qa_bot import QABotWorkflow, QA_BOT_WORKFLOW
from app.workflows.translate import TranslateWorkflow, TRANSLATE_WORKFLOW
from app.workflows.interview_coach import InterviewCoachWorkflow, INTERVIEW_COACH_WORKFLOW
from app.workflows.data_analyzer import DataAnalyzerWorkflow, DATA_ANALYZER_WORKFLOW
from app.workflows.api_designer import ApiDesignerWorkflow, API_DESIGNER_WORKFLOW
from app.workflows.agentic_rag import AgenticRagWorkflow, AGENTIC_RAG_WORKFLOW
from app.workflows.report_gen import ReportGenWorkflow, REPORT_GEN_WORKFLOW
from app.workflows.data_pipeline import DataPipelineWorkflow, DATA_PIPELINE_WORKFLOW
from app.workflows.ci_piper import CiPiperWorkflow, CI_PIPER_WORKFLOW


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
}


def get_workflow(name: str):
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
]
