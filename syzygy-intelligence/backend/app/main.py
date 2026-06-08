"""Syzygy Intelligence — FastAPI entry point with logging, error handling, and audit."""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import agents, sessions, consensus, memory, tools, workflows, chat, audit, meta, uploads, rag as rag_route
from app.api.websockets import ws_handler
from app.config import settings
from app.db.session import init_db, close_db
from app.errors import setup_error_handlers
from app.logging_setup import logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Syzygy Intelligence starting", env=settings.env, version="0.1.0")
    
    try:
        await init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.warning(f"Database init skipped (will retry on first request): {e}")
    yield
    logger.info("Syzygy Intelligence shutting down")
    await close_db()


app = FastAPI(
    title="Syzygy Intelligence API",
    description="Multi-agent platform with polarity-aware consensus and Jungian archetypes",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    max_age=600,
)

setup_error_handlers(app)

app.include_router(agents.router, prefix="/api/agents", tags=["Agents"])
app.include_router(sessions.router, prefix="/api/sessions", tags=["Sessions"])
app.include_router(consensus.router, prefix="/api/consensus", tags=["Consensus"])
app.include_router(memory.router, prefix="/api/memory", tags=["Memory"])
app.include_router(tools.router, prefix="/api/tools", tags=["Tools"])
app.include_router(workflows.router, prefix="/api/workflows", tags=["Workflows"])
app.include_router(chat.router, prefix="/api/chat", tags=["Chat"])
app.include_router(audit.router, prefix="/api/audit", tags=["Audit"])
app.include_router(meta.router, prefix="/api/meta", tags=["Meta"])
app.include_router(uploads.router, prefix="/api/uploads", tags=["Uploads"])
app.include_router(rag_route.router, prefix="/api/rag", tags=["RAG"])

app.add_api_websocket_route("/ws", ws_handler)


@app.get("/")
async def root():
    return {
        "service": "Syzygy Intelligence",
        "version": "0.1.0",
        "tagline": "Aligning opposites into unified intelligence",
        "status": "operational",
    }


@app.get("/health")
async def health():
    return {"status": "healthy", "env": settings.env}
