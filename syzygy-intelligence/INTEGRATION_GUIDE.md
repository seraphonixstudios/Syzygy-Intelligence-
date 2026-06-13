"""Integration guide for recursive self-improvement workflow into main API.

This file shows how to integrate the self-improvement workflow into the
existing Syzygy FastAPI application.
"""

# ============================================================================
# STEP 1: Update backend/app/api/routes/__init__.py  ✅ COMPLETED
# ============================================================================

# Done — see backend/app/api/routes/__init__.py line 14:
#     from app.api.routes.self_improvement import router as self_improvement_router
# And line 22 in __all__


# ============================================================================
# STEP 2: Update backend/app/main.py to register the self-improvement router  ✅ COMPLETED
# ============================================================================

# Done — see backend/app/main.py:
#   - Line 30: import self_improvement added to the app.api.routes import block
#   - Line 134: app.include_router(self_improvement.router, prefix="/api", tags=["Self-Improvement"])


# ============================================================================
# STEP 3: Verify imports in backend/app/workflows/__init__.py (DONE)
# ============================================================================

# The workflow registry integration is already complete. Verify:

"""
from app.workflows.self_improvement import SELF_IMPROVEMENT_WORKFLOW, RecursiveSelfImprovementWorkflow

WORKFLOW_REGISTRY = {
    ...
    "self_improvement": SELF_IMPROVEMENT_WORKFLOW,
}
"""


# ============================================================================
# STEP 4: Optional - Add database models for session persistence
# ============================================================================

"""
# Create backend/app/db/models/improvement_session.py

from sqlalchemy import JSON, Column, DateTime, String, Table, Text, create_engine, func
from sqlalchemy.orm import declarative_base, mapped_column

Base = declarative_base()


class ImprovementSession(Base):
    __tablename__ = "improvement_sessions"

    id: mapped_column(String, primary_key=True)
    task: mapped_column(Text)
    domain: mapped_column(String)
    status: mapped_column(String)  # pending, running, completed, failed
    max_cycles: mapped_column(int)
    current_cycle: mapped_column(int)
    total_performance_gain: mapped_column(float)
    final_output: mapped_column(Text, nullable=True)
    meta_insights: mapped_column(JSON, nullable=True)
    learned_patterns: mapped_column(JSON, nullable=True)
    created_at: mapped_column(DateTime, default=func.now())
    completed_at: mapped_column(DateTime, nullable=True)
    error_message: mapped_column(Text, nullable=True)


class ImprovementCycle(Base):
    __tablename__ = "improvement_cycles"

    id: mapped_column(String, primary_key=True)
    session_id: mapped_column(String, ForeignKey("improvement_sessions.id"))
    cycle_number: mapped_column(int)
    initial_output: mapped_column(Text)
    initial_assessment: mapped_column(JSON)
    improvements_applied: mapped_column(JSON)
    improved_output: mapped_column(Text)
    final_assessment: mapped_column(JSON)
    performance_delta: mapped_column(float)
    convergence_reached: mapped_column(bool)
    completed_at: mapped_column(DateTime)
"""


# ============================================================================
# STEP 5: Optional - Update API route for persistence
# ============================================================================

"""
# In backend/app/api/routes/self_improvement.py, update the storage:

from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_async_session
from app.db.models.improvement_session import ImprovementSession, ImprovementCycle

@router.post("/")
async def start_self_improvement(
    request: SelfImprovementRequest,
    session: AsyncSession = Depends(get_async_session),
) -> dict:
    # ... existing code ...
    
    # After execution, store in database:
    db_session = ImprovementSession(
        id=session.id,
        task=session.task,
        domain=session.domain,
        status=session.status,
        max_cycles=session.max_cycles,
        current_cycle=session.current_cycle,
        total_performance_gain=session.total_performance_gain,
        final_output=session.final_output,
        meta_insights=session.meta_insights,
        learned_patterns=session.learned_patterns,
    )
    session.add(db_session)
    await session.commit()
    
    return {...}
"""


# ============================================================================
# STEP 6: Test the integration
# ============================================================================

"""
# Test via curl:

curl -X POST http://localhost:8000/api/workflows/self-improvement \
  -H "Content-Type: application/json" \
  -d '{
    "task": "Write a comprehensive blog post on async Python",
    "domain": "content",
    "max_cycles": 3,
    "convergence_threshold": 0.85
  }'

# Response:
{
  "session_id": "impr_1705123456.789",
  "status": "running",
  "message": "Self-improvement session started successfully"
}

# Check status:
curl http://localhost:8000/api/workflows/self-improvement/impr_1705123456.789

# Get cycles:
curl http://localhost:8000/api/workflows/self-improvement/impr_1705123456.789/cycles
"""


# ============================================================================
# STEP 7: Optional - Add to OpenAI-compatible endpoint
# ============================================================================

"""
# In backend/app/api/openai_compat.py, you could add self-improvement as an option:

from app.workflows.self_improvement import RecursiveSelfImprovementWorkflow

@router.post("/v1/chat/completions")
async def chat_completions(request: ChatCompletionRequest) -> dict:
    # Check for self-improvement flag
    if request.syzygy_self_improve:
        workflow = RecursiveSelfImprovementWorkflow()
        session = await workflow.execute(
            task=request.messages[-1]["content"],
            agents=get_agents(request.syzygy_agent_team),
            domain=request.syzygy_domain or "general",
            max_cycles=request.syzygy_improvement_cycles or 3,
        )
        return {
            "id": f"chatcmpl-{session.id}",
            "object": "text_completion",
            "created": int(time.time()),
            "model": request.model,
            "choices": [
                {
                    "index": 0,
                    "message": {"role": "assistant", "content": session.final_output},
                    "finish_reason": "stop",
                    "syzygy_improvement_session": session.id,
                    "syzygy_performance_gain": session.total_performance_gain,
                }
            ],
        }
    
    # ... rest of implementation
"""


# ============================================================================
# STEP 8: Optional - Add monitoring and metrics
# ============================================================================

"""
# In backend/app/observability.py, add metrics:

from prometheus_client import Counter, Histogram, Gauge

improvement_sessions_total = Counter(
    'syzygy_improvement_sessions_total',
    'Total improvement sessions started',
    ['domain'],
)

improvement_performance_gain = Histogram(
    'syzygy_improvement_performance_gain',
    'Performance improvement per session',
    ['domain'],
)

improvement_cycles_used = Gauge(
    'syzygy_improvement_cycles_used',
    'Number of improvement cycles used',
    ['domain'],
)

# In the API route, record metrics:
improvement_sessions_total.labels(domain=request.domain).inc()
improvement_performance_gain.labels(domain=session.domain).observe(session.total_performance_gain)
improvement_cycles_used.labels(domain=session.domain).set(session.current_cycle)
"""


# ============================================================================
# TESTING CHECKLIST
# ============================================================================

"""
Before deploying to production:

☐ Unit tests for SelfAssessmentEngine
  → Test assessment scoring for each dimension
  → Test root-cause analysis
  → Test domain-specific metrics

☐ Unit tests for PerformanceTracker
  → Test metric recording
  → Test trend analysis
  → Test plateau detection
  → Test convergence estimation

☐ Unit tests for LearningOptimizer
  → Test each scheduling strategy
  → Test early stopping
  → Test performance-adaptive adjustment

☐ Integration tests for RecursiveSelfImprovementWorkflow
  → Test single cycle (execute → assess → improve)
  → Test convergence on realistic tasks
  → Test memory integration
  → Test with different agent teams

☐ API endpoint tests
  → POST /api/workflows/self-improvement with valid input
  → GET /api/workflows/self-improvement/{session_id}
  → GET /api/workflows/self-improvement/{session_id}/cycles
  → Error handling for invalid requests
  → Rate limiting

☐ Performance tests
  → Measure token usage per cycle
  → Measure latency per cycle
  → Test with max_cycles=10 (stress test)
  → Memory usage monitoring

☐ Integration with existing components
  → Works with all agent archetypes
  → Works with consensus engine
  → Works with memory layers
  → Doesn't break existing workflows
"""


# ============================================================================
# EXAMPLE INTEGRATION TEST
# ============================================================================

"""
# backend/tests/test_self_improvement_integration.py

import pytest
from app.workflows.self_improvement import RecursiveSelfImprovementWorkflow
from app.agents.registry import agent_registry
from app.consensus.engine import ConsensusEngine


@pytest.mark.asyncio
async def test_self_improvement_basic():
    '''Test basic improvement cycle.'''
    
    workflow = RecursiveSelfImprovementWorkflow()
    agents = agent_registry.create_default_team()
    
    session = await workflow.execute(
        task="Write a Python function to compute fibonacci",
        agents=agents,
        domain="code",
        max_cycles=2,
        convergence_threshold=0.8,
    )
    
    assert session.status == "completed"
    assert session.current_cycle >= 1
    assert len(session.cycles) >= 1
    assert session.total_performance_gain >= 0  # Should be non-negative
    assert len(session.meta_insights) > 0


@pytest.mark.asyncio
async def test_self_improvement_convergence():
    '''Test early convergence detection.'''
    
    workflow = RecursiveSelfImprovementWorkflow()
    agents = agent_registry.create_default_team()
    
    session = await workflow.execute(
        task="Fix this bug: function returns None instead of value",
        agents=agents,
        domain="code",
        max_cycles=5,
        convergence_threshold=0.95,
    )
    
    # Should stop before max_cycles if converged
    if session.total_performance_gain > 0:
        assert session.current_cycle < 5


@pytest.mark.asyncio
async def test_api_endpoint():
    '''Test REST API endpoint.'''
    
    from fastapi.testclient import TestClient
    from app.main import app
    
    client = TestClient(app)
    
    response = client.post(
        "/api/workflows/self-improvement",
        json={
            "task": "Summarize machine learning",
            "domain": "content",
            "max_cycles": 2,
        }
    )
    
    assert response.status_code == 200
    assert "session_id" in response.json()
    
    # Poll for completion
    session_id = response.json()["session_id"]
    import time
    time.sleep(30)  # Wait for async completion
    
    response = client.get(f"/api/workflows/self-improvement/{session_id}")
    assert response.status_code == 200
    assert response.json()["status"] in ["running", "completed"]
"""


# ============================================================================
# DEPLOYMENT NOTES
# ============================================================================

"""
Production deployment considerations:

1. Async Execution
   - Self-improvement sessions are CPU/time-intensive
   - Run in background task queue (Celery, RQ, Dramatiq)
   - Don't block HTTP request - return session_id immediately
   - Client polls /api/workflows/self-improvement/{session_id} for results

2. Token Budget
   - Each cycle uses ~30-50K tokens (varies by model size)
   - 5 cycles = ~150-250K tokens
   - Monitor token usage and set rate limits

3. Resource Constraints
   - Run max 2-3 improvement sessions in parallel
   - Use resource reservations in Docker (CPU, memory)
   - Set timeouts for LLM calls (30-60 seconds per call)

4. Error Handling
   - Gracefully handle LLM timeouts
   - Store failed sessions for debugging
   - Log all improvement actions for audit trail

5. Caching
   - Cache assessment rubrics in memory
   - Cache learning optimizer configs
   - Cache agent team definitions

6. Monitoring
   - Track session completion rate
   - Monitor average performance gain
   - Alert on failed sessions
   - Track tokens-per-session
"""
