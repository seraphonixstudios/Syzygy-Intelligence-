"""Self-improvement and meta-cognition API routes."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter

from app.meta import meta_engine

router = APIRouter()


@router.get("/summary")
async def get_meta_summary() -> dict[str, Any]:
    return meta_engine.get_summary()


@router.post("/evaluate")
async def evaluate_output(data: dict[str, Any]) -> dict[str, Any]:
    output = data.get("output", "")
    context = data.get("context", {})
    result = meta_engine.evaluate_output(output, context)
    proposals = meta_engine.propose_improvements(result)
    return {
        "evaluation": {
            "score": result.score,
            "dimensions": result.dimensions,
            "feedback": result.feedback,
            "suggestions": result.suggestions,
        },
        "proposals": [
            {
                "id": p.id,
                "target": p.target,
                "change": p.change,
                "rationale": p.rationale,
                "expected_impact": p.expected_impact,
            }
            for p in proposals
        ],
    }


@router.get("/history")
async def get_evaluation_history() -> dict[str, Any]:
    return {
        "evaluations": [
            {
                "score": e.score,
                "dimensions": e.dimensions,
                "feedback": e.feedback,
                "timestamp": e.timestamp,
            }
            for e in meta_engine.get_history()
        ],
        "proposals": [
            {
                "id": p.id,
                "target": p.target,
                "change": p.change,
                "status": p.status,
                "created_at": p.created_at,
                "applied_at": p.applied_at,
            }
            for p in meta_engine.get_proposals()
        ],
    }


@router.post("/proposals/{proposal_id}/apply")
async def apply_proposal(proposal_id: str) -> dict[str, Any]:
    proposal = meta_engine.apply_proposal(proposal_id)
    if not proposal:
        return {"status": "error", "message": "Proposal not found or already applied"}
    return {"status": "applied", "proposal": {"id": proposal.id, "target": proposal.target, "change": proposal.change}}


@router.post("/improve")
async def run_self_improvement(data: dict[str, Any]) -> dict[str, Any]:
    """Run a full self-improvement cycle: evaluate, propose, and apply."""
    output = data.get("output", "")
    context = data.get("context", {})
    auto_apply = data.get("auto_apply", False)

    eval_result = meta_engine.evaluate_output(output, context)
    proposals = meta_engine.propose_improvements(eval_result)

    applied = []
    if auto_apply:
        for p in proposals:
            meta_engine.apply_proposal(p.id)
            applied.append(p.id)

    return {
        "evaluation": {
            "score": eval_result.score,
            "dimensions": eval_result.dimensions,
            "feedback": eval_result.feedback,
            "suggestions": eval_result.suggestions,
        },
        "proposals": [
            {
                "id": p.id,
                "target": p.target,
                "change": p.change,
                "expected_impact": p.expected_impact,
            }
            for p in proposals
        ],
        "auto_applied": applied,
        "summary": meta_engine.get_summary(),
    }
