"""Procurement Agent — vendor matching, compliance checks, PO generation, approval routing.

Multi-agent pattern:
1. Requirement parsing: extract specs from procurement request
2. Vendor matching: match against approved vendor list
3. Compliance check: flag regulatory/compliance exceptions
4. PO generation: create purchase order draft
5. Approval routing: determine approval chain
"""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from app.logging_setup import logger

ProgressCallback = Callable[[str, int, dict[str, Any]], Awaitable[None]]

APPROVED_VENDORS = [
    {"name": "CloudScale Inc.", "category": "cloud", "tier": "preferred", "rating": 4.8},
    {"name": "DataWare Systems", "category": "data", "tier": "preferred", "rating": 4.6},
    {"name": "NetworkPro Solutions", "category": "network", "tier": "approved", "rating": 4.3},
    {"name": "SecureGuard LLC", "category": "security", "tier": "preferred", "rating": 4.9},
    {"name": "OfficeDirect Supply", "category": "office", "tier": "approved", "rating": 4.1},
    {"name": "AIWorks Technologies", "category": "software", "tier": "preferred", "rating": 4.7},
    {"name": "HardwareHub Corp", "category": "hardware", "tier": "approved", "rating": 4.2},
    {"name": "ConsultPro Group", "category": "services", "tier": "preferred", "rating": 4.5},
]

APPROVAL_THRESHOLDS = [
    {"max_amount": 5000, "approver": "Team Lead", "levels": 1},
    {"max_amount": 50000, "approver": "Department Head", "levels": 2},
    {"max_amount": 250000, "approver": "VP / Director", "levels": 3},
    {"max_amount": 1000000, "approver": "C-Level", "levels": 4},
    {"max_amount": float("inf"), "approver": "Board of Directors", "levels": 5},
]

COMPLIANCE_FLAGS = [
    "data_privacy", "export_control", "conflict_of_interest",
    "open_source_obligation", "sanctions", "diversity_requirement",
]


@dataclass
class ProcurementWorkflow:
    name: str = "procurement"
    description: str = "Purchase request processing, vendor matching, compliance checks, and PO generation"
    required_capabilities: list[str] = field(
        default_factory=lambda: ["classification", "analysis", "generation"]
    )

    async def _parse_requirements(self, request: str, on_progress: ProgressCallback | None = None) -> dict[str, Any]:
        await asyncio.sleep(0.3)
        req_lower = request.lower()

        if any(w in req_lower for w in ["cloud", "hosting", "aws", "azure", "gcp", "infrastructure"]):
            category = "cloud"
        elif any(w in req_lower for w in ["software", "license", "saas", "tool", "platform", "app"]):
            category = "software"
        elif any(w in req_lower for w in ["hardware", "laptop", "server", "equipment", "device"]):
            category = "hardware"
        elif any(w in req_lower for w in ["security", "firewall", "antivirus", "vpn"]):
            category = "security"
        elif any(w in req_lower for w in ["network", "router", "switch", "wifi"]):
            category = "network"
        elif any(w in req_lower for w in ["data", "database", "storage", "backup"]):
            category = "data"
        elif any(w in req_lower for w in ["office", "supply", "furniture", "stationery"]):
            category = "office"
        elif any(w in req_lower for w in ["consult", "service", "professional"]):
            category = "services"
        else:
            category = "other"

        amount = 0
        for word in req_lower.replace(",", "").split():
            try:
                num = float(word.strip("$").strip("£").strip("€"))
                if num > amount:
                    amount = num
            except ValueError:
                pass

        if amount == 0:
            amount = 15000

        urgency = "critical" if any(w in req_lower for w in ["urgent", "asap", "immediately", "emergency"]) else "normal"

        result = {"category": category, "estimated_amount": int(amount), "urgency": urgency}
        if on_progress:
            await on_progress("parse", 25, result)
        return result

    async def _match_vendor(self, requirements: dict, on_progress: ProgressCallback | None = None) -> dict[str, Any]:
        await asyncio.sleep(0.3)
        category = requirements.get("category", "other")
        matches = [v for v in APPROVED_VENDORS if v["category"] == category]

        if not matches:
            matches = sorted(APPROVED_VENDORS, key=lambda v: v["rating"], reverse=True)[:2]

        best = max(matches, key=lambda v: v["rating"])
        alternatives = [v for v in matches if v["name"] != best["name"]]

        result = {
            "recommended_vendor": best["name"],
            "tier": best["tier"],
            "rating": best["rating"],
            "alternatives": [v["name"] for v in alternatives[:2]],
        }

        if on_progress:
            await on_progress("vendor", 50, result)
        return result

    async def _compliance_check(self, requirements: dict, vendor: dict, on_progress: ProgressCallback | None = None) -> list[dict[str, Any]]:
        await asyncio.sleep(0.3)
        flags = []
        amount = requirements.get("estimated_amount", 0)
        tier = vendor.get("tier", "")

        if amount > 50000:
            flags.append({
                "flag": "data_privacy",
                "severity": "high",
                "detail": f"Contract value (${amount:,}) exceeds data privacy review threshold",
            })
        if amount > 100000:
            flags.append({
                "flag": "conflict_of_interest",
                "severity": "medium",
                "detail": f"Amount over $100,000 requires conflict of interest disclosure",
            })
        if tier != "preferred":
            flags.append({
                "flag": "vendor_approval",
                "severity": "medium",
                "detail": f"Vendor tier '{tier}' requires additional approval",
            })

        if on_progress:
            await on_progress("compliance", 70, {"flags_count": len(flags)})
        return flags

    async def _generate_po(self, requirements: dict, vendor: dict, compliance: list[dict], on_progress: ProgressCallback | None = None) -> dict[str, Any]:
        await asyncio.sleep(0.2)
        amount = requirements.get("estimated_amount", 0)

        for threshold in sorted(APPROVAL_THRESHOLDS, key=lambda t: t["max_amount"]):
            if amount <= threshold["max_amount"]:
                approval = threshold
                break
        else:
            approval = APPROVAL_THRESHOLDS[-1]

        has_flags = any(f.get("severity") in ("critical", "high") for f in compliance)
        po_id = f"PO-{abs(hash(datetime.now(UTC).isoformat())) % 100000:05d}"

        result = {
            "po_id": po_id,
            "vendor": vendor.get("recommended_vendor", "TBD"),
            "amount": amount,
            "category": requirements.get("category"),
            "approver": approval["approver"],
            "approval_levels": approval["levels"],
            "requires_escalation": has_flags,
        }

        if on_progress:
            await on_progress("po_generation", 90, result)
        return result

    async def execute(
        self,
        task: str | dict[str, Any],
        on_progress: ProgressCallback | None = None,
    ) -> dict[str, Any]:
        if isinstance(task, str):
            req = task
        elif isinstance(task, dict):
            req = task.get("request", task.get("query", task.get("task", "")))
        else:
            req = str(task)

        start_time = datetime.now(UTC)

        if on_progress:
            await on_progress("started", 0, {"status": "processing procurement request"})

        requirements = await self._parse_requirements(req, on_progress)
        vendor = await self._match_vendor(requirements, on_progress)
        compliance = await self._compliance_check(requirements, vendor, on_progress)
        po = await self._generate_po(requirements, vendor, compliance, on_progress)

        elapsed = (datetime.now(UTC) - start_time).total_seconds()

        result = {
            "requirements": requirements,
            "vendor_match": vendor,
            "compliance_flags": compliance,
            "purchase_order": po,
            "elapsed_seconds": round(elapsed, 1),
            "next_steps": [
                f"Send PO {po.get('po_id', '')} for {po.get('approver', '')} approval",
                "Schedule delivery timeline with vendor",
                "Update procurement tracking system",
            ],
        }

        if on_progress:
            await on_progress("completed", 100, result)
        return result


PROCUREMENT_WORKFLOW = ProcurementWorkflow()
