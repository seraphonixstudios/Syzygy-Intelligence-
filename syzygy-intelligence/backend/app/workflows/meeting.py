"""Meeting / Email Assistant — meeting summarization, action items, follow-up drafts.

Multi-agent pattern:
1. Summarizer: extract key topics, decisions, and discussion points
2. Action Items: identify tasks, assignees, and deadlines
3. Calendar: suggest follow-up meeting times / reminders
4. Email Drafts: generate follow-up emails for attendees
"""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from app.logging_setup import logger

ProgressCallback = Callable[[str, int, dict[str, Any]], Awaitable[None]]

SAMPLE_MEETINGS = {
    "sprint": """Sprint Planning — June 28, 2026
Attendees: Alice (PM), Bob (Dev), Carol (Dev), Dave (Design)

Discussion:
- Sprint goal: Complete user dashboard redesign and API rate limiting
- Alice presented the Q3 roadmap priorities
- Bob reported the auth module refactor is 80% complete
- Carol demoed the new rate limiting middleware
- Dave shared mockups for the dashboard redesign

Decisions:
- Dashboard redesign to start next sprint, use the new component library
- Rate limiting to be merged by EOD Friday
- Auth refactor deadline extended to next Wednesday

Action Items:
- Alice: Schedule design review for dashboard mockups
- Bob: Merge auth refactor by Wednesday
- Carol: Write tests for rate limiting middleware
- Dave: Finalize dashboard mockups by Monday
Next Meeting: Friday standup, 10 AM
""",
    "standup": """Daily Standup — June 28, 2026
Attendees: Alice, Bob, Carol, Dave, Eve (QA)

Updates:
- Alice: Reviewed PRs, updated sprint backlog, unblocked Carol
- Bob: Finished auth module tests, started integration docs
- Carol: Rate limiting PR ready for review, needs Dave's feedback on UI
- Dave: Dashboard mockups at 80%, blocked on brand color decisions
- Eve: Regression tests passing, found 2 edge cases in billing flow

Blockers:
- Dave needs brand color decisions from Alice
- Eve needs test environment for billing edge cases

Decisions:
- Brand colors to be decided by end of day
- Billing edge cases to be tested in staging
Next Meeting: Tomorrow, 10 AM
""",
}


@dataclass
class MeetingWorkflow:
    name: str = "meeting"
    description: str = "Meeting summarization, action item extraction, follow-up email drafting"
    required_capabilities: list[str] = field(
        default_factory=lambda: ["summarization", "entity_extraction", "generation"]
    )

    async def _detect_meeting_type(self, notes: str, on_progress: ProgressCallback | None = None) -> str:
        await asyncio.sleep(0.2)
        title_line = notes.split("\n")[0].lower() if notes else ""
        if any(w in title_line for w in ["standup", "daily standup", "daily sync", "stand-up"]):
            mtype = "standup"
        elif any(w in title_line for w in ["sprint", "planning", "retro", "backlog"]):
            mtype = "sprint_planning"
        elif any(w in title_line for w in ["design", "review", "feedback"]):
            mtype = "design_review"
        elif any(w in title_line for w in ["one-on-one", "1:1", "1-1"]):
            mtype = "one_on_one"
        else:
            mtype = "general"
        if on_progress:
            await on_progress("classify", 15, {"meeting_type": mtype})
        return mtype

    async def _extract_summary(self, notes: str, on_progress: ProgressCallback | None = None) -> dict[str, Any]:
        await asyncio.sleep(0.4)
        lines = notes.strip().split("\n")
        title = lines[0] if lines else "Untitled Meeting"

        attendees = []
        decisions = []
        discussion_points = []

        for line in lines:
            if line.lower().startswith("attendees"):
                raw = line.split(":", 1)[1] if ":" in line else ""
                attendees = [a.strip().split(" (")[0] for a in raw.split(",") if a.strip()]
            elif line.lower().startswith("decisions"):
                in_decisions = True
            elif line.lower().startswith("action"):
                in_decisions = False
            elif line.lower().startswith("discussion"):
                in_decisions = False

        for line in lines:
            if line.lower().startswith("- ") and ("attendees" not in line.lower()):
                discussion_points.append(line.strip("- ").strip())

        for line in lines:
            if line.lower().strip().startswith("- ") and ":" in line:
                if line.split(":", 1)[1].strip():
                    discussion_points.append(line.strip("- ").strip())

        decisions = [
            line.strip("- ").strip()
            for line in lines
            if line.strip().startswith("- ") and "to" in line.lower()
        ]

        if on_progress:
            await on_progress("summarize", 40, {
                "title": title,
                "attendees_count": len(attendees),
                "decisions_count": len(decisions),
            })
        return {"title": title, "attendees": attendees, "decisions": decisions, "discussion_points": discussion_points}

    async def _extract_action_items(self, notes: str, on_progress: ProgressCallback | None = None) -> list[dict[str, str]]:
        await asyncio.sleep(0.3)
        items = []
        lines = notes.split("\n")
        in_action_section = False

        for line in lines:
            if line.lower().startswith("action items") or line.lower().startswith("action"):
                in_action_section = True
                continue
            if in_action_section and (line.strip() == "" or line.lower().startswith("next meeting")):
                in_action_section = False
                continue
            if in_action_section:
                line = line.strip("- ").strip()
                if ":" in line:
                    parts = line.split(":", 1)
                    assignee = parts[0].strip()
                    action = parts[1].strip()
                    items.append({"assignee": assignee, "action": action, "status": "pending"})

        if on_progress:
            await on_progress("action_items", 65, {"count": len(items), "items": items})
        return items

    async def _extract_blockers(self, notes: str, on_progress: ProgressCallback | None = None) -> list[str]:
        await asyncio.sleep(0.2)
        blockers = []
        lines = notes.split("\n")
        in_blockers = False
        for line in lines:
            if line.lower().startswith("blockers"):
                in_blockers = True
                continue
            if in_blockers:
                if line.strip() == "" or any(line.lower().startswith(w) for w in ["next meeting", "decisions", "action"]):
                    break
                blockers.append(line.strip("- ").strip())

        if on_progress:
            await on_progress("blockers", 80, {"count": len(blockers), "blockers": blockers})
        return blockers

    async def _generate_email_drafts(self, title: str, action_items: list[dict[str, str]]) -> list[dict[str, str]]:
        await asyncio.sleep(0.3)
        drafts = []
        summary_line = f"Following up on our meeting: {title}"

        attendees_seen = set()
        for item in action_items:
            assignee = item.get("assignee", "")
            if assignee and assignee not in attendees_seen:
                attendees_seen.add(assignee)
                body = (
                    f"Hi {assignee},\n\n"
                    f"{summary_line}\n\n"
                    f"Your action item: {item['action']}\n\n"
                    f"Please update the team once completed.\n\n"
                    f"Best,\nSyzygy Meeting Assistant"
                )
                drafts.append({
                    "to": assignee,
                    "subject": f"Action Item: {item['action'][:50]}",
                    "body": body,
                })

        body_all = (
            f"Hi team,\n\n"
            f"{summary_line}\n\n"
            f"Summary of action items:\n"
        )
        for i, item in enumerate(action_items, 1):
            body_all += f"{i}. [{item.get('assignee', 'TBD')}] {item['action']}\n"
        body_all += "\nPlease review and update your items.\n\nBest,\nSyzygy Meeting Assistant"

        drafts.insert(0, {
            "to": "all_attendees",
            "subject": f"Meeting Summary: {title}",
            "body": body_all,
        })
        return drafts

    async def execute(
        self,
        task: str | dict[str, Any],
        on_progress: ProgressCallback | None = None,
    ) -> dict[str, Any]:
        if isinstance(task, str):
            notes = task
        elif isinstance(task, dict):
            notes = task.get("notes", task.get("transcript", task.get("task", "")))
        else:
            notes = str(task)

        start_time = datetime.now(UTC)

        if on_progress:
            await on_progress("started", 0, {"status": "processing meeting notes"})

        meeting_type = await self._detect_meeting_type(notes, on_progress)
        summary = await self._extract_summary(notes, on_progress)
        action_items = await self._extract_action_items(notes, on_progress)
        blockers = await self._extract_blockers(notes, on_progress)
        email_drafts = await self._generate_email_drafts(summary.get("title", "Meeting"), action_items)

        elapsed = (datetime.now(UTC) - start_time).total_seconds()

        result = {
            "meeting_type": meeting_type,
            "title": summary.get("title", "Untitled Meeting"),
            "attendees": summary.get("attendees", []),
            "decisions": summary.get("decisions", []),
            "discussion_points": summary.get("discussion_points", []),
            "action_items": action_items,
            "blockers": blockers,
            "email_drafts": email_drafts,
            "elapsed_seconds": round(elapsed, 1),
            "next_steps": [
                "Send meeting summary to all attendees",
                "Follow up on action items before next meeting",
                "Resolve blockers identified during the meeting",
            ],
        }

        if on_progress:
            await on_progress("completed", 100, result)
        return result


MEETING_WORKFLOW = MeetingWorkflow()
