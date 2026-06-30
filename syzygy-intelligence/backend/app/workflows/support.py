"""Customer Support Agent — ticket triage, resolution drafting, escalation monitoring.

Multi-agent pattern:
1. Triage: classify issue type (billing/technical/account/general) + priority
2. Knowledge retrieval: match against KB articles / past solutions
3. Resolution drafting: generate step-by-step solution
4. Escalation check: confidence + complexity → human escalation recommendation
"""

from __future__ import annotations

import asyncio
import json
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from app.logging_setup import logger

ProgressCallback = Callable[[str, int, dict[str, Any]], Awaitable[None]]

SUPPORT_CATEGORIES = ["billing", "technical", "account", "feature_request", "general"]
PRIORITY_LEVELS = ["critical", "high", "medium", "low"]
KB_ARTICLES = {
    "billing": [
        "How to update your payment method",
        "Understanding your invoice",
        "Request a refund",
        "Cancel your subscription",
    ],
    "technical": [
        "Troubleshooting connection issues",
        "API authentication guide",
        "Common error codes and solutions",
        "Platform performance best practices",
    ],
    "account": [
        "How to reset your password",
        "Managing team members",
        "Changing your account settings",
        "Data export and privacy",
    ],
    "feature_request": [
        "How to submit feature requests",
        "Our product roadmap",
        "Beta program access",
    ],
    "general": [
        "Getting started guide",
        "Frequently asked questions",
        "Contact our support team",
    ],
}


@dataclass
class SupportWorkflow:
    name: str = "support"
    description: str = "Customer support ticket triage, resolution drafting, and escalation monitoring"
    required_capabilities: list[str] = field(
        default_factory=lambda: ["classification", "knowledge_retrieval", "response_generation"]
    )

    async def _simulate_triage(self, query: str, on_progress: ProgressCallback | None = None) -> tuple[str, str, float]:
        await asyncio.sleep(0.3)
        query_lower = query.lower()
        if any(w in query_lower for w in ["bill", "pay", "refund", "charge", "invoice", "subscription", "price"]):
            category = "billing"
        elif any(w in query_lower for w in ["error", "bug", "crash", "broken", "fail", "issue", "not working"]):
            category = "technical"
        elif any(w in query_lower for w in ["password", "login", "account", "profile", "settings", "delete my data"]):
            category = "account"
        elif any(w in query_lower for w in ["feature", "suggestion", "request", "would like"]):
            category = "feature_request"
        else:
            category = "general"

        if any(w in query_lower for w in ["urgent", "emergency", "critical", "down", "outage", "lost", "breach"]):
            priority = "critical"
        elif any(w in query_lower for w in ["broken", "error", "fail", "blocked", "important"]):
            priority = "high"
        elif any(w in query_lower for w in ["help", "question", "how do I", "can you"]):
            priority = "medium"
        else:
            priority = "low"

        confidence = 0.85 + (hash(query) % 10) / 100
        confidence = min(confidence, 0.98)

        if on_progress:
            await on_progress("triage", 25, {"category": category, "priority": priority, "confidence": round(confidence, 2)})
        return category, priority, confidence

    async def _simulate_resolution(self, query: str, category: str, on_progress: ProgressCallback | None = None) -> list[str]:
        await asyncio.sleep(0.5)
        kb = KB_ARTICLES.get(category, KB_ARTICLES["general"])
        steps = [
            f"Thank you for reaching out. I've identified this as a {category} issue.",
            f"Based on your description, here are the steps to resolve this:",
        ]

        if category == "billing":
            steps += [
                "1. Verify your current payment method in Settings > Billing",
                "2. Check your invoice history for any recent charges",
                "3. If you need a refund, submit a request from the Billing dashboard",
                "4. For subscription changes, navigate to Settings > Plan",
            ]
        elif category == "technical":
            steps += [
                "1. Clear your browser cache and cookies, then try again",
                "2. Check our status page for any ongoing incidents",
                "3. Review the error message and reference our error code guide",
                "4. If the issue persists, include your logs when contacting support",
            ]
        elif category == "account":
            steps += [
                "1. Go to Settings > Account to update your profile",
                "2. Use the 'Forgot Password' link on the login page to reset",
                "3. Check your email for verification messages",
                "4. Review team management settings if you need to add/remove members",
            ]
        elif category == "feature_request":
            steps += [
                "1. Thank you for your suggestion! We value user feedback",
                "2. Check our public roadmap to see if this is already planned",
                "3. Submit your feature request through the Feedback portal",
                "4. Join our beta program for early access to new features",
            ]
        else:
            steps += [
                "1. Check our getting started guide for an overview",
                "2. Visit our FAQ page for common questions",
                "3. Search our knowledge base for more specific topics",
                "4. Contact our support team if you need further assistance",
            ]

        if on_progress:
            await on_progress("resolution", 60, {"steps": len(steps), "kb_articles": kb})
        return steps

    async def _simulate_escalation(self, query: str, category: str, priority: str, confidence: float, on_progress: ProgressCallback | None = None) -> tuple[bool, str, float]:
        await asyncio.sleep(0.2)
        needs_escalation = priority == "critical" or (priority == "high" and confidence < 0.8)
        escalation_reason = ""
        if needs_escalation:
            if priority == "critical":
                escalation_reason = "Critical priority issues require human agent intervention"
            else:
                escalation_reason = "Low confidence in automated resolution for this issue type"

        escalation_score = 0.95 if needs_escalation else (0.2 if confidence > 0.9 else 0.5)

        if on_progress:
            await on_progress("escalation", 85, {
                "needs_escalation": needs_escalation,
                "escalation_reason": escalation_reason,
                "escalation_score": escalation_score,
            })
        return needs_escalation, escalation_reason, escalation_score

    async def _generate_ticket_id(self) -> str:
        rand = hash(datetime.now(UTC).isoformat()) % 100000
        return f"TKT-{abs(rand):05d}"

    async def execute(
        self,
        task: str | dict[str, Any],
        on_progress: ProgressCallback | None = None,
    ) -> dict[str, Any]:
        if isinstance(task, str):
            query = task
        elif isinstance(task, dict):
            query = task.get("query", task.get("task", ""))
        else:
            query = str(task)

        ticket_id = await self._generate_ticket_id()
        start_time = datetime.now(UTC)

        if on_progress:
            await on_progress("started", 0, {"ticket_id": ticket_id, "status": "analyzing"})

        category, priority, triage_confidence = await self._simulate_triage(query, on_progress)
        resolution_steps = await self._simulate_resolution(query, category, on_progress)
        needs_escalation, escalation_reason, escalation_score = await self._simulate_escalation(
            query, category, priority, triage_confidence, on_progress
        )

        kb_articles = KB_ARTICLES.get(category, KB_ARTICLES["general"])
        elapsed = (datetime.now(UTC) - start_time).total_seconds()

        result = {
            "ticket_id": ticket_id,
            "category": category,
            "priority": priority,
            "status": "resolved" if not needs_escalation else "escalated",
            "resolution_steps": resolution_steps,
            "kb_articles": kb_articles,
            "needs_escalation": needs_escalation,
            "escalation_reason": escalation_reason,
            "escalation_score": round(escalation_score, 2),
            "confidence": round(triage_confidence, 2),
            "elapsed_seconds": round(elapsed, 1),
            "support_email": "support@syzygy.com",
            "response_time_estimate": "immediate" if not needs_escalation else "within 4 hours",
        }

        if on_progress:
            await on_progress("completed", 100, result)
        return result


SUPPORT_WORKFLOW = SupportWorkflow()
