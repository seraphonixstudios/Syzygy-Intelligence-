"""Tests for the Legal Contract Reviewer workflow."""

from __future__ import annotations

import pytest

from app.workflows.legal import LEGAL_WORKFLOW, RISK_LEVELS, CONTRACT_TYPES

NDA_TEXT = """This Mutual Non-Disclosure Agreement (NDA) is entered into between the parties. Confidential information shall be protected for 2 years. Standard exclusions apply. This agreement contains no unlimited liability clauses."""

SAAS_TEXT = """This Software as a Service Agreement includes auto-renewal terms and limitation of liability clauses. Data processing is GDPR-compliant. Service Level Agreement targets 99.9% uptime."""

MSA_TEXT = """This Master Service Agreement includes mutual indemnification provisions and insurance requirements. Termination requires 30 days written notice."""


@pytest.fixture
def workflow():
    return LEGAL_WORKFLOW


@pytest.mark.asyncio
async def test_execute_with_string(workflow):
    result = await workflow.execute(NDA_TEXT)
    assert result["contract_type"] in CONTRACT_TYPES
    assert len(result["clauses"]) >= 3
    assert "risk_assessment" in result
    assert "recommendations" in result


@pytest.mark.asyncio
async def test_execute_with_dict(workflow):
    result = await workflow.execute({"contract": SAAS_TEXT})
    assert result["contract_type"] == "saas_agreement"


@pytest.mark.asyncio
async def test_nda_detection(workflow):
    result = await workflow.execute(NDA_TEXT)
    assert result["contract_type"] == "nda"


@pytest.mark.asyncio
async def test_saas_detection(workflow):
    result = await workflow.execute(SAAS_TEXT)
    assert result["contract_type"] == "saas_agreement"


@pytest.mark.asyncio
async def test_msa_detection(workflow):
    result = await workflow.execute(MSA_TEXT)
    assert result["contract_type"] == "msa"


@pytest.mark.asyncio
async def test_risk_levels_in_clauses(workflow):
    result = await workflow.execute(NDA_TEXT)
    for clause in result["clauses"]:
        assert clause["risk"] in RISK_LEVELS


@pytest.mark.asyncio
async def test_risk_counts_present(workflow):
    result = await workflow.execute(NDA_TEXT)
    r = result["risk_assessment"]
    assert "risk_counts" in r
    for lvl in ("critical", "high", "medium", "low"):
        assert lvl in r["risk_counts"]


@pytest.mark.asyncio
async def test_overall_risk_level(workflow):
    result = await workflow.execute(NDA_TEXT)
    assert result["risk_assessment"]["overall_risk"] in RISK_LEVELS


@pytest.mark.asyncio
async def test_risk_score_range(workflow):
    result = await workflow.execute(NDA_TEXT)
    score = result["risk_assessment"]["risk_score"]
    assert 0 <= score <= 10


@pytest.mark.asyncio
async def test_high_risk_saas(workflow):
    result = await workflow.execute("This SaaS agreement includes auto-renewal clauses and unlimited liability terms with no caps")
    assert result["risk_assessment"]["overall_risk"] in ("critical", "high")


@pytest.mark.asyncio
async def test_recommendations_list(workflow):
    result = await workflow.execute(NDA_TEXT)
    assert len(result["recommendations"]) >= 3


@pytest.mark.asyncio
async def test_clauses_extracted(workflow):
    result = await workflow.execute("NDA with confidentiality for 3 years")
    assert len(result["clauses"]) > 0


@pytest.mark.asyncio
async def test_elapsed_time(workflow):
    result = await workflow.execute(NDA_TEXT)
    assert result["elapsed_seconds"] > 0


@pytest.mark.asyncio
async def test_progress_callback(workflow):
    phases = []
    async def cb(phase: str, pct: int, _data: dict) -> None:
        phases.append((phase, pct))
    await workflow.execute(NDA_TEXT, on_progress=cb)
    assert phases[0][0] == "started"
    assert phases[-1][0] == "completed"
    assert phases[-1][1] == 100


@pytest.mark.asyncio
async def test_progress_callback_phases(workflow):
    phase_names = []
    async def cb(phase: str, _pct: int, _data: dict) -> None:
        phase_names.append(phase)
    await workflow.execute(NDA_TEXT, on_progress=cb)
    assert "detect" in phase_names
    assert "extract" in phase_names
    assert "risk" in phase_names


@pytest.mark.asyncio
async def test_recommendation_matches_risk(workflow):
    result = await workflow.execute("Safe low risk standard NDA")
    risk = result["risk_assessment"]
    rec = risk["recommendation"]
    if risk["overall_risk"] == "low":
        assert "safe" in rec.lower() or "proceed" in rec.lower()
    elif risk["overall_risk"] == "critical":
        assert "not sign" in rec.lower()
