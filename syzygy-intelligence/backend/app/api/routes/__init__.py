"""API routes package index — import all route modules."""

from app.api.routes.agents import router as agents_router
from app.api.routes.audit import router as audit_router
from app.api.routes.auth import router as auth_router
from app.api.routes.chat import router as chat_router
from app.api.routes.consensus import router as consensus_router
from app.api.routes.memory import router as memory_router
from app.api.routes.meta import router as meta_router
from app.api.routes.rag import router as rag_router
from app.api.routes.sessions import router as sessions_router
from app.api.routes.tools import router as tools_router
from app.api.routes.uploads import router as uploads_router
from app.api.routes.workflows import router as workflows_router
from app.api.routes.self_improvement import router as self_improvement_router

from app.api.routes.telemetry import router as telemetry_router

__all__ = [
    "agents_router",
    "audit_router",
    "auth_router",
    "chat_router",
    "consensus_router",
    "memory_router",
    "meta_router",
    "rag_router",
    "self_improvement_router",
    "sessions_router",
    "telemetry_router",
    "tools_router",
    "uploads_router",
    "workflows_router",
]
