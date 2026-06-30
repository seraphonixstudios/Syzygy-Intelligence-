"""Tests for the Sales / CRM workflow."""

from __future__ import annotations

import pytest

from app.workflows.sales import SALES_WORKFLOW


@pytest.fixture
def workflow():
    return SALES_WORKFLOW


@pytest.mark.asyncio
async def test_execute_with_string(workflow):
    result = await workflow.execute("Enterprise CTO interested in AI platform")
    assert result["lead_summary"]["status"] in ("qualified", "nurture", "disqualified")
    assert 0 <= result["lead_summary"]["score"] <= 10
    assert len(result["followup_sequence"]) > 0
    assert len(result["next_steps"]) > 0


@pytest.mark.asyncio
async def test_execute_with_dict(workflow):
    result = await workflow.execute({"lead": "VP of Engineering at Fortune 500 company"})
    assert result["lead_summary"]["title_level"] == "executive"


@pytest.mark.asyncio
async def test_executive_detected(workflow):
    result = await workflow.execute("Chief Technology Officer at enterprise")
    assert result["lead_summary"]["title_level"] == "executive"


@pytest.mark.asyncio
async def test_senior_detected(workflow):
    result = await workflow.execute("Senior software engineer evaluating tools")
    assert result["lead_summary"]["title_level"] in ("senior_ic", "individual_contributor")


@pytest.mark.asyncio
async def test_enterprise_size(workflow):
    result = await workflow.execute("Large enterprise corporation looking for AI")
    assert result["lead_summary"]["company_size"] == "enterprise"


@pytest.mark.asyncio
async def test_startup_size(workflow):
    result = await workflow.execute("Small startup founder needs ML platform")
    assert result["lead_summary"]["company_size"] == "startup"


@pytest.mark.asyncio
async def test_high_relevance(workflow):
    result = await workflow.execute("AI and machine learning automation platform")
    assert result["lead_summary"]["relevance"] == "high"


@pytest.mark.asyncio
async def test_followup_sequence_qualified(workflow):
    result = await workflow.execute("Enterprise CTO AI platform urgent")
    emails = result["followup_sequence"]
    assert len(emails) >= 2
    for email in emails:
        assert "subject" in email
        assert "body" in email
        assert "timing" in email


@pytest.mark.asyncio
async def test_followup_has_demo(workflow):
    result = await workflow.execute("Fortune 500 VP ML tools")
    emails = result["followup_sequence"]
    subjects = [e["subject"] for e in emails]
    assert any("demo" in s.lower() for s in subjects)


@pytest.mark.asyncio
async def test_pipeline_analysis(workflow):
    result = await workflow.execute("Enterprise lead AI automation")
    pa = result["pipeline_analysis"]
    assert "current_stage" in pa
    assert "recommended_next_stage" in pa
    assert "recommendation" in pa
    assert "pipeline_velocity" in pa


@pytest.mark.asyncio
async def test_next_steps(workflow):
    result = await workflow.execute("Test lead")
    assert len(result["next_steps"]) >= 2


@pytest.mark.asyncio
async def test_elapsed_time(workflow):
    result = await workflow.execute("Test timing")
    assert result["elapsed_seconds"] > 0


@pytest.mark.asyncio
async def test_progress_callback(workflow):
    phases = []
    async def cb(phase: str, pct: int, _data: dict) -> None:
        phases.append((phase, pct))
    await workflow.execute("Lead with callback", on_progress=cb)
    assert phases[0][0] == "started"
    assert phases[-1][0] == "completed"
    assert phases[-1][1] == 100


@pytest.mark.asyncio
async def test_progress_callback_phases(workflow):
    phase_names = []
    async def cb(phase: str, _pct: int, _data: dict) -> None:
        phase_names.append(phase)
    await workflow.execute("Progress test", on_progress=cb)
    assert "qualification" in phase_names
    assert "followup" in phase_names
    assert "pipeline" in phase_names


@pytest.mark.asyncio
async def test_score_range(workflow):
    result = await workflow.execute("Test scoring")
    assert 0 <= result["lead_summary"]["score"] <= 10


@pytest.mark.asyncio
async def test_recommended_action_present(workflow):
    result = await workflow.execute("Test action")
    assert result["lead_summary"]["recommended_action"] in ("schedule demo", "send nurture sequence", "archive")
