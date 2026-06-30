"""Tests for the Meeting / Email Assistant workflow."""

from __future__ import annotations

import pytest

from app.workflows.meeting import MEETING_WORKFLOW

SPRINT_NOTES = """Sprint Planning — June 28, 2026
Attendees: Alice (PM), Bob (Dev), Carol (Dev), Dave (Design)

Discussion:
- Sprint goal: Complete user dashboard redesign
- Alice presented the Q3 roadmap priorities
- Bob reported the auth module refactor is 80% complete

Decisions:
- Dashboard redesign to start next sprint
- Rate limiting to be merged by EOD Friday

Action Items:
- Alice: Schedule design review for dashboard mockups
- Bob: Merge auth refactor by Wednesday
- Carol: Write tests for rate limiting middleware
Next Meeting: Friday standup, 10 AM
"""

STANDUP_NOTES = """Daily Standup — June 28, 2026
Attendees: Alice, Bob, Carol, Dave, Eve (QA)

Updates:
- Alice: Reviewed PRs, updated sprint backlog
- Bob: Finished auth module tests, started integration docs

Blockers:
- Dave needs brand color decisions from Alice
- Eve needs test environment for billing edge cases

Decisions:
- Brand colors to be decided by end of day
- Billing edge cases to be tested in staging
Next Meeting: Tomorrow, 10 AM
"""


@pytest.fixture
def workflow():
    return MEETING_WORKFLOW


@pytest.mark.asyncio
async def test_execute_with_string(workflow):
    result = await workflow.execute(SPRINT_NOTES)
    assert result["meeting_type"] == "sprint_planning"
    assert len(result["attendees"]) >= 3
    assert len(result["action_items"]) >= 2
    assert len(result["discussion_points"]) >= 1


@pytest.mark.asyncio
async def test_execute_with_dict(workflow):
    result = await workflow.execute({"notes": SPRINT_NOTES})
    assert result["meeting_type"] == "sprint_planning"


@pytest.mark.asyncio
async def test_standup_detection(workflow):
    result = await workflow.execute(STANDUP_NOTES)
    assert result["meeting_type"] == "standup"


@pytest.mark.asyncio
async def test_action_items_extracted(workflow):
    result = await workflow.execute(SPRINT_NOTES)
    assert len(result["action_items"]) > 0
    for item in result["action_items"]:
        assert "assignee" in item
        assert "action" in item
        assert "status" in item


@pytest.mark.asyncio
async def test_action_items_have_assignees(workflow):
    result = await workflow.execute(SPRINT_NOTES)
    for item in result["action_items"]:
        assert item["assignee"] in ("Alice", "Bob", "Carol", "Dave", "Eve")


@pytest.mark.asyncio
async def test_blockers_extracted(workflow):
    result = await workflow.execute(STANDUP_NOTES)
    assert len(result["blockers"]) >= 2


@pytest.mark.asyncio
async def test_decisions_extracted(workflow):
    result = await workflow.execute(STANDUP_NOTES)
    assert len(result["decisions"]) >= 1


@pytest.mark.asyncio
async def test_email_drafts_generated(workflow):
    result = await workflow.execute(SPRINT_NOTES)
    assert len(result["email_drafts"]) > 0
    for draft in result["email_drafts"]:
        assert "to" in draft
        assert "subject" in draft
        assert "body" in draft


@pytest.mark.asyncio
async def test_email_drafts_include_summary(workflow):
    result = await workflow.execute(SPRINT_NOTES)
    assert result["email_drafts"][0]["to"] == "all_attendees"
    assert "Meeting Summary" in result["email_drafts"][0]["subject"]


@pytest.mark.asyncio
async def test_next_steps_present(workflow):
    result = await workflow.execute(STANDUP_NOTES)
    assert len(result["next_steps"]) >= 2


@pytest.mark.asyncio
async def test_attendees_parsed(workflow):
    result = await workflow.execute(SPRINT_NOTES)
    assert "Alice" in result["attendees"]
    assert "Bob" in result["attendees"]
    assert "Carol" in result["attendees"]


@pytest.mark.asyncio
async def test_elapsed_time(workflow):
    result = await workflow.execute(STANDUP_NOTES)
    assert result["elapsed_seconds"] > 0


@pytest.mark.asyncio
async def test_progress_callback(workflow):
    phases = []

    async def cb(phase: str, pct: int, _data: dict) -> None:
        phases.append((phase, pct))

    await workflow.execute(SPRINT_NOTES, on_progress=cb)
    assert len(phases) >= 4
    assert phases[0][0] == "started"
    assert phases[-1][0] == "completed"
    assert phases[-1][1] == 100


@pytest.mark.asyncio
async def test_progress_callback_phases(workflow):
    phase_names = []

    async def cb(phase: str, _pct: int, _data: dict) -> None:
        phase_names.append(phase)

    await workflow.execute(STANDUP_NOTES, on_progress=cb)
    assert "classify" in phase_names
    assert "summarize" in phase_names
    assert "action_items" in phase_names
    assert "completed" in phase_names


@pytest.mark.asyncio
async def test_standup_has_blockers(workflow):
    result = await workflow.execute(STANDUP_NOTES)
    assert "blockers" in result
    assert len(result["blockers"]) > 0
    assert "brand color" in result["blockers"][0].lower()


@pytest.mark.asyncio
async def test_sprint_has_action_items(workflow):
    result = await workflow.execute(SPRINT_NOTES)
    assert len(result["action_items"]) >= 2
    actions = [item["action"] for item in result["action_items"]]
    assert any("schedule" in a.lower() for a in actions)


@pytest.mark.asyncio
async def test_email_drafts_per_action_item(workflow):
    result = await workflow.execute(SPRINT_NOTES)
    action_assignees = {item["assignee"] for item in result["action_items"]}
    draft_to_addresses = {d["to"] for d in result["email_drafts"] if d["to"] != "all_attendees"}
    for assignee in action_assignees:
        if assignee:
            assert assignee in draft_to_addresses or "all_attendees" in {d["to"] for d in result["email_drafts"]}


@pytest.mark.asyncio
async def test_general_meeting_type(workflow):
    result = await workflow.execute("Some random notes without specific meeting type")
    assert result["meeting_type"] == "general"
