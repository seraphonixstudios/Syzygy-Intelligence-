"""Tests for the Procurement Agent workflow."""

from __future__ import annotations

import pytest

from app.workflows.procurement import PROCUREMENT_WORKFLOW, APPROVED_VENDORS


@pytest.fixture
def workflow():
    return PROCUREMENT_WORKFLOW


@pytest.mark.asyncio
async def test_execute_with_string(workflow):
    result = await workflow.execute("Need cloud hosting upgrade urgent $45k")
    assert "requirements" in result
    assert "vendor_match" in result
    assert "compliance_flags" in result
    assert "purchase_order" in result


@pytest.mark.asyncio
async def test_execute_with_dict(workflow):
    result = await workflow.execute({"request": "Software license renewal $12k"})
    assert result["requirements"]["category"] == "software"


@pytest.mark.asyncio
async def test_cloud_category(workflow):
    result = await workflow.execute("AWS cloud infrastructure upgrade")
    assert result["requirements"]["category"] == "cloud"


@pytest.mark.asyncio
async def test_software_category(workflow):
    result = await workflow.execute("Need SaaS platform license")
    assert result["requirements"]["category"] == "software"


@pytest.mark.asyncio
async def test_hardware_category(workflow):
    result = await workflow.execute("Purchase 20 laptops for developers")
    assert result["requirements"]["category"] == "hardware"


@pytest.mark.asyncio
async def test_amount_parsed(workflow):
    result = await workflow.execute("Budget is $75,000 for new servers")
    assert result["requirements"]["estimated_amount"] >= 75000


@pytest.mark.asyncio
async def test_urgency_detected(workflow):
    result = await workflow.execute("URGENT: Need firewall immediately")
    assert result["requirements"]["urgency"] == "critical"


@pytest.mark.asyncio
async def test_vendor_recommended(workflow):
    result = await workflow.execute("Cloud migration project")
    assert result["vendor_match"]["recommended_vendor"] in [v["name"] for v in APPROVED_VENDORS]


@pytest.mark.asyncio
async def test_vendor_rating(workflow):
    result = await workflow.execute("Security solution needed")
    assert 1 <= result["vendor_match"]["rating"] <= 5


@pytest.mark.asyncio
async def test_vendor_tier(workflow):
    result = await workflow.execute("Data storage solution")
    assert result["vendor_match"]["tier"] in ("preferred", "approved")


@pytest.mark.asyncio
async def test_compliance_flags_high_amount(workflow):
    result = await workflow.execute("Enterprise infrastructure $200,000 budget")
    flags = result["compliance_flags"]
    assert len(flags) >= 2


@pytest.mark.asyncio
async def test_po_id_generated(workflow):
    result = await workflow.execute("Test purchase $5k")
    po = result["purchase_order"]
    assert po["po_id"].startswith("PO-")


@pytest.mark.asyncio
async def test_po_approver_level(workflow):
    result = await workflow.execute("Purchase request $3,000")
    assert result["purchase_order"]["approval_levels"] == 1


@pytest.mark.asyncio
async def test_po_approver_high_amount(workflow):
    result = await workflow.execute("Major investment $300,000")
    po = result["purchase_order"]
    assert po["approval_levels"] >= 3


@pytest.mark.asyncio
async def test_next_steps(workflow):
    result = await workflow.execute("Test procurement")
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
    await workflow.execute("Callback test $10k", on_progress=cb)
    assert phases[0][0] == "started"
    assert phases[-1][0] == "completed"
    assert phases[-1][1] == 100


@pytest.mark.asyncio
async def test_progress_callback_phases(workflow):
    phase_names = []
    async def cb(phase: str, _pct: int, _data: dict) -> None:
        phase_names.append(phase)
    await workflow.execute("Progress test", on_progress=cb)
    assert "parse" in phase_names
    assert "vendor" in phase_names
    assert "compliance" in phase_names
    assert "po_generation" in phase_names


@pytest.mark.asyncio
async def test_compliance_high_value(workflow):
    result = await workflow.execute("Enterprise deal $500,000")
    flags = result["compliance_flags"]
    severities = [f["severity"] for f in flags]
    assert "high" in severities
