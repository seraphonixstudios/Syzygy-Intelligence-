"""Tests for the Customer Support Agent workflow."""

from __future__ import annotations

import asyncio

import pytest

from app.workflows.support import SUPPORT_WORKFLOW, KB_ARTICLES, SUPPORT_CATEGORIES, PRIORITY_LEVELS


@pytest.fixture
def workflow():
    return SUPPORT_WORKFLOW


@pytest.mark.asyncio
async def test_execute_with_string(workflow):
    result = await workflow.execute("My account is locked")
    assert result["ticket_id"].startswith("TKT-")
    assert result["category"] in SUPPORT_CATEGORIES
    assert result["priority"] in PRIORITY_LEVELS
    assert isinstance(result["resolution_steps"], list)
    assert len(result["resolution_steps"]) >= 3
    assert isinstance(result["confidence"], float)
    assert 0 < result["confidence"] <= 1


@pytest.mark.asyncio
async def test_execute_with_dict(workflow):
    result = await workflow.execute({"query": "I was charged twice"})
    assert result["category"] == "billing"


@pytest.mark.asyncio
async def test_billing_query(workflow):
    result = await workflow.execute("I need a refund for my subscription")
    assert result["category"] == "billing"


@pytest.mark.asyncio
async def test_technical_query(workflow):
    result = await workflow.execute("The API keeps returning errors")
    assert result["category"] == "technical"


@pytest.mark.asyncio
async def test_account_query(workflow):
    result = await workflow.execute("I forgot my password and cannot login")
    assert result["category"] == "account"


@pytest.mark.asyncio
async def test_feature_request_query(workflow):
    result = await workflow.execute("I would like a feature to export data as CSV")
    assert result["category"] == "feature_request"


@pytest.mark.asyncio
async def test_general_query(workflow):
    result = await workflow.execute("How do I get started with your platform?")
    assert result["category"] == "general"


@pytest.mark.asyncio
async def test_critical_priority(workflow):
    result = await workflow.execute("URGENT: System is down, critical outage!")
    assert result["priority"] == "critical"
    assert result["needs_escalation"] is True


@pytest.mark.asyncio
async def test_low_priority_no_escalation(workflow):
    result = await workflow.execute("How do I update my profile picture?")
    assert result["needs_escalation"] is False


@pytest.mark.asyncio
async def test_kb_articles_present(workflow):
    result = await workflow.execute("Billing question about my invoice")
    assert isinstance(result["kb_articles"], list)
    assert len(result["kb_articles"]) > 0


@pytest.mark.asyncio
async def test_resolution_steps_contain_greeting(workflow):
    result = await workflow.execute("Help with your platform")
    first_step = result["resolution_steps"][0]
    assert "thank you" in first_step.lower() or "Thank you" in first_step


@pytest.mark.asyncio
async def test_support_email_present(workflow):
    result = await workflow.execute("Test query")
    assert "support_email" in result
    assert "@" in result["support_email"]


@pytest.mark.asyncio
async def test_response_time_estimate(workflow):
    result = await workflow.execute("How do I reset my password?")
    assert result["response_time_estimate"] in ("immediate", "within 4 hours")


@pytest.mark.asyncio
async def test_progress_callback(workflow):
    phases = []

    async def cb(phase: str, pct: int, _data: dict) -> None:
        phases.append((phase, pct))

    await workflow.execute("Test with callback", on_progress=cb)
    assert len(phases) >= 3
    assert phases[0][0] == "started"
    assert phases[-1][0] == "completed"
    assert phases[-1][1] == 100


@pytest.mark.asyncio
async def test_progress_callback_phases(workflow):
    phase_names = []

    async def cb(phase: str, _pct: int, _data: dict) -> None:
        phase_names.append(phase)

    await workflow.execute("Test progress phases", on_progress=cb)
    assert "triage" in phase_names
    assert "resolution" in phase_names
    assert "escalation" in phase_names
    assert "completed" in phase_names


@pytest.mark.asyncio
async def test_elapsed_time(workflow):
    result = await workflow.execute("Test timing")
    assert result["elapsed_seconds"] > 0


@pytest.mark.asyncio
async def test_escalation_score_range(workflow):
    result = await workflow.execute("Test escalation")
    assert 0 <= result["escalation_score"] <= 1


@pytest.mark.asyncio
async def test_kb_articles_match_category(workflow):
    result = await workflow.execute("Billing issue with my payment")
    for article in result["kb_articles"]:
        assert article in KB_ARTICLES["billing"]


@pytest.mark.asyncio
async def test_ticket_id_format(workflow):
    result = await workflow.execute("Test ticket")
    assert result["ticket_id"].startswith("TKT-")
    parts = result["ticket_id"].split("-")
    assert len(parts) == 2
    assert parts[1].isdigit()
