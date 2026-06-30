"""Sales / CRM Agent — lead qualification, follow-up automation, pipeline management.

Multi-agent pattern:
1. Lead qualification: score leads based on criteria
2. Follow-up drafting: personalized email sequences
3. CRM enrichment: suggest field updates and next actions
4. Pipeline analysis: stage movement recommendations
"""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from app.logging_setup import logger

ProgressCallback = Callable[[str, int, dict[str, Any]], Awaitable[None]]

LEAD_SOURCES = ["website", "referral", "linkedin", "conference", "cold_outreach", "partner", "trial"]
LEAD_STATUSES = ["new", "contacted", "qualified", "proposal", "negotiation", "won", "lost"]
INDUSTRIES = ["technology", "healthcare", "finance", "manufacturing", "retail", "education", "other"]

SAMPLE_PIPELINE_STAGES = [
    {"stage": "lead_scoring", "label": "Lead Scoring"},
    {"stage": "initial_outreach", "label": "Initial Outreach"},
    {"stage": "discovery", "label": "Discovery Call"},
    {"stage": "demo", "label": "Product Demo"},
    {"stage": "proposal", "label": "Proposal Sent"},
    {"stage": "negotiation", "label": "Negotiation"},
    {"stage": "closed_won", "label": "Closed Won"},
]


@dataclass
class SalesWorkflow:
    name: str = "sales"
    description: str = "Sales lead qualification, follow-up automation, and pipeline management"
    required_capabilities: list[str] = field(
        default_factory=lambda: ["classification", "generation", "analysis"]
    )

    async def _qualify_lead(self, lead_info: str, on_progress: ProgressCallback | None = None) -> dict[str, Any]:
        await asyncio.sleep(0.3)
        info_lower = lead_info.lower()

        if any(w in info_lower for w in ["cto", "vp", "director", "head of", "chief"]):
            title = "executive"
            seniority = 4
        elif any(w in info_lower for w in ["manager", "lead", "senior", "staff"]):
            title = "senior_ic"
            seniority = 3
        elif any(w in info_lower for w in ["engineer", "developer", "analyst"]):
            title = "individual_contributor"
            seniority = 2
        else:
            title = "unknown"
            seniority = 1

        if any(w in info_lower for w in ["enterprise", "corp", "large", "fortune"]):
            company_size = "enterprise"
            size_score = 5
        elif any(w in info_lower for w in ["mid", "growth", "series"]):
            company_size = "mid_market"
            size_score = 3
        elif any(w in info_lower for w in ["startup", "small", "sme"]):
            company_size = "startup"
            size_score = 2
        else:
            company_size = "unknown"
            size_score = 1

        if any(w in info_lower for w in ["ai", "ml", "data", "analytics", "automation"]):
            relevance = "high"
            relevance_score = 5
        elif any(w in info_lower for w in ["software", "saas", "cloud", "digital"]):
            relevance = "medium"
            relevance_score = 3
        else:
            relevance = "low"
            relevance_score = 1

        total_score = min(seniority + size_score + relevance_score, 10)
        if total_score >= 8:
            status = "qualified"
        elif total_score >= 5:
            status = "nurture"
        else:
            status = "disqualified"

        result = {
            "title_level": title,
            "company_size": company_size,
            "relevance": relevance,
            "score": total_score,
            "status": status,
            "recommended_action": "schedule demo" if status == "qualified" else "send nurture sequence" if status == "nurture" else "archive",
        }

        if on_progress:
            await on_progress("qualification", 30, result)
        return result

    async def _generate_followup(self, lead: dict, on_progress: ProgressCallback | None = None) -> list[dict[str, str]]:
        await asyncio.sleep(0.3)
        status = lead.get("status", "new")
        sequence = []

        if status in ("qualified", "nurture"):
            sequence.append({
                "subject": "Following up on your interest",
                "body": f"Hi there,\n\nThank you for your interest in Syzygy. I'd love to schedule a quick call to learn more about your needs and show you how our platform can help.\n\nBest,\nSyzygy Sales Team",
                "timing": "day 1",
            })
            sequence.append({
                "subject": "Quick question about your priorities",
                "body": f"Hi,\n\nJust checking in — I'd love to understand what you're looking for in an AI platform. What's the biggest challenge you're trying to solve?\n\nBest,\nSyzygy Sales Team",
                "timing": "day 3",
            })
            if status == "qualified":
                sequence.append({
                    "subject": "Ready for a demo?",
                    "body": f"Hi,\n\nWould you be available for a 30-minute demo this week? I'll show you how Syzygy can help with your specific use case.\n\nBest,\nSyzygy Sales Team",
                    "timing": "day 5",
                })
        else:
            sequence.append({
                "subject": "Thank you for your time",
                "body": f"Hi,\n\nThank you for considering Syzygy. While this may not be the right fit at this time, we'd love to stay in touch. Feel free to reach out if your needs change.\n\nBest,\nSyzygy Sales Team",
                "timing": "day 1",
            })

        if on_progress:
            await on_progress("followup", 60, {"sequence_length": len(sequence)})
        return sequence

    async def _analyze_pipeline(self, lead: dict, on_progress: ProgressCallback | None = None) -> dict[str, Any]:
        await asyncio.sleep(0.2)
        score = lead.get("score", 5)
        status = lead.get("status", "new")

        if score >= 8 and status == "qualified":
            next_stage = "demo"
            recommendation = "High-value lead — prioritize immediate demo scheduling"
        elif score >= 5 and status == "nurture":
            next_stage = "discovery"
            recommendation = "Send nurture sequence and track engagement"
        else:
            next_stage = "none"
            recommendation = "Archive — revisit in 90 days if engagement changes"

        result = {
            "current_stage": status,
            "recommended_next_stage": next_stage,
            "recommendation": recommendation,
            "pipeline_velocity": "fast" if score >= 8 else "medium" if score >= 5 else "slow",
        }

        if on_progress:
            await on_progress("pipeline", 85, result)
        return result

    async def execute(
        self,
        task: str | dict[str, Any],
        on_progress: ProgressCallback | None = None,
    ) -> dict[str, Any]:
        if isinstance(task, str):
            lead_info = task
        elif isinstance(task, dict):
            lead_info = task.get("lead", task.get("query", task.get("task", "")))
        else:
            lead_info = str(task)

        start_time = datetime.now(UTC)

        if on_progress:
            await on_progress("started", 0, {"status": "processing lead"})

        qualification = await self._qualify_lead(lead_info, on_progress)
        followup_sequence = await self._generate_followup(qualification, on_progress)
        pipeline = await self._analyze_pipeline(qualification, on_progress)

        elapsed = (datetime.now(UTC) - start_time).total_seconds()

        result = {
            "lead_summary": qualification,
            "followup_sequence": followup_sequence,
            "pipeline_analysis": pipeline,
            "elapsed_seconds": round(elapsed, 1),
            "next_steps": [
                qualification.get("recommended_action", "review"),
                "Update CRM with qualification score",
                pipeline.get("recommendation", "Track lead progress"),
            ],
        }

        if on_progress:
            await on_progress("completed", 100, result)
        return result


SALES_WORKFLOW = SalesWorkflow()
