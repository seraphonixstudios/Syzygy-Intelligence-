"""REST API endpoints for recursive self-improvement workflow.

Provides:
- POST /api/workflows/self_improvement — start a new improvement session
- GET /api/workflows/self_improvement/{session_id} — get session status and results
- GET /api/workflows/self_improvement/{session_id}/cycles — list all improvement cycles
- WebSocket /ws/self_improvement/{session_id} — stream real-time improvement events
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.agents.registry import agent_registry
from app.consensus.engine import ConsensusEngine
from app.llm.model_manager import ModelManager
from app.logging_setup import logger
from app.self_improvement.assessment import SelfAssessmentEngine
from app.self_improvement.learning_optimizer import LearningOptimizer
from app.self_improvement.performance_tracker import PerformanceTracker
from app.workflows.self_improvement import RecursiveSelfImprovementWorkflow

router = APIRouter(prefix="/workflows/self_improvement", tags=["workflows"])

# Global session storage (in production, use database)
_active_sessions: dict[str, dict] = {}


class SelfImprovementRequest(BaseModel):
    """Request to start a recursive self-improvement session."""

    task: str = Field(..., description="The task to improve on")
    domain: str = Field("general", description="Domain: code, content, research, analysis, etc.")
    max_cycles: int = Field(5, ge=1, le=10, description="Maximum improvement cycles")
    convergence_threshold: float = Field(
        0.90, ge=0.5, le=1.0, description="Target quality threshold"
    )
    agent_team: list[str] | None = Field(
        None, description="List of agent names; uses default team if None"
    )


class ImprovementCycleResponse(BaseModel):
    """Response for a single improvement cycle."""

    cycle_number: int
    task: str
    initial_score: float
    final_score: float
    performance_delta: float
    improvements_applied: int
    convergence_reached: bool
    completed_at: str | None


class SelfImprovementSessionResponse(BaseModel):
    """Response for a complete improvement session."""

    session_id: str
    task: str
    domain: str
    status: str
    current_cycle: int
    max_cycles: int
    total_performance_gain: float
    final_output: str
    meta_insights: list[str]
    cycles: list[ImprovementCycleResponse]
    created_at: str
    completed_at: str | None


@router.post("/")
async def start_self_improvement(request: SelfImprovementRequest) -> dict:
    """Start a new recursive self-improvement session.

    Returns session ID for polling or WebSocket subscription.
    """

    logger.info(
        "Starting self-improvement session",
        task=request.task[:100],
        domain=request.domain,
        max_cycles=request.max_cycles,
    )

    # Get or create agent team
    if request.agent_team:
        agents = [
            agent_registry.get(name) for name in request.agent_team
            if agent_registry.get(name)
        ]
        if not agents:
            agents = agent_registry.create_default_team()
    else:
        agents = agent_registry.create_default_team()

    # Initialize workflow components
    consensus_engine = ConsensusEngine()
    assessment_engine = SelfAssessmentEngine()
    performance_tracker = PerformanceTracker()
    learning_optimizer = LearningOptimizer()
    llm = ModelManager()

    workflow = RecursiveSelfImprovementWorkflow(
        consensus_engine=consensus_engine,
        assessment_engine=assessment_engine,
        performance_tracker=performance_tracker,
        learning_optimizer=learning_optimizer,
        llm=llm,
    )

    # Execute workflow (non-blocking in production, use task queue)
    try:
        session = await workflow.execute(
            task=request.task,
            agents=agents,
            domain=request.domain,
            max_cycles=request.max_cycles,
            convergence_threshold=request.convergence_threshold,
        )

        # Store session for retrieval
        _active_sessions[session.id] = session

        return {
            "session_id": session.id,
            "status": session.status,
            "message": "Self-improvement session started successfully",
        }

    except Exception as e:
        logger.error(f"Self-improvement session failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{session_id}")
async def get_session(session_id: str) -> SelfImprovementSessionResponse:
    """Get a self-improvement session by ID."""

    session = _active_sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Build cycle responses
    cycles = [
        ImprovementCycleResponse(
            cycle_number=cycle.cycle_number,
            task=cycle.task,
            initial_score=cycle.initial_assessment.overall_score if cycle.initial_assessment else 0.0,
            final_score=cycle.final_assessment.overall_score if cycle.final_assessment else 0.0,
            performance_delta=cycle.performance_delta,
            improvements_applied=len(cycle.improvements_applied),
            convergence_reached=cycle.convergence_reached,
            completed_at=cycle.completed_at.isoformat() if cycle.completed_at else None,
        )
        for cycle in session.cycles
    ]

    return SelfImprovementSessionResponse(
        session_id=session.id,
        task=session.task,
        domain=session.domain,
        status=session.status,
        current_cycle=session.current_cycle,
        max_cycles=session.max_cycles,
        total_performance_gain=session.total_performance_gain,
        final_output=session.final_output[:2000],  # Truncate for API
        meta_insights=session.meta_insights,
        cycles=cycles,
        created_at=session.created_at.isoformat(),
        completed_at=session.completed_at.isoformat() if session.completed_at else None,
    )


@router.get("/{session_id}/cycles")
async def get_cycles(
    session_id: str,
    cycle_number: int | None = Query(None, description="Filter by cycle number"),
) -> dict:
    """Get cycles from a session."""

    session = _active_sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    cycles = session.cycles
    if cycle_number:
        cycles = [c for c in cycles if c.cycle_number == cycle_number]

    return {
        "session_id": session_id,
        "total_cycles": len(session.cycles),
        "cycles": [
            {
                "cycle_number": c.cycle_number,
                "initial_score": c.initial_assessment.overall_score if c.initial_assessment else 0.0,
                "final_score": c.final_assessment.overall_score if c.final_assessment else 0.0,
                "performance_delta": c.performance_delta,
                "improvements": [
                    {
                        "type": imp.get("type"),
                        "target": imp.get("target_agent"),
                        "action": imp.get("action", "")[:100],
                    }
                    for imp in c.improvements_applied
                ],
                "converged": c.convergence_reached,
            }
            for c in cycles
        ],
    }


__all__ = [
    "router",
    "SelfImprovementRequest",
    "SelfImprovementSessionResponse",
]
