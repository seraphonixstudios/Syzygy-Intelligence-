"""Syzygy Intelligence — FastAPI entry point with logging, error handling, and audit."""

from __future__ import annotations

import time
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response

from app.api.routes import (
    admin,
    agents,
    audit,
    auth,
    chat,
    consensus,
    health,
    memory,
    meta,
    oauth,
    payments,
    self_improvement,
    sessions,
    tools,
    uploads,
    workflows,
)
from app.api.routes import rag as rag_route
from app.api.websockets import ws_handler
from app.config import settings
from app.db.session import close_db, init_db
from app.errors import setup_error_handlers
from app.logging_setup import logger
from app.middleware.rate_limiter import setup_rate_limiter
from app.observability import RequestTracingMiddleware, metrics_endpoint, setup_tracing

_start_time = time.time()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    db_type = "SQLite" if settings.db_is_sqlite else "PostgreSQL"
    logger.info(
        "Syzygy Intelligence starting",
        env=settings.env,
        db=db_type,
        db_url=settings.database_url.replace(settings.db_password, "****"),
        version="0.1.0",
    )

    # Check critical dependencies
    missing = []
    try:
        import sqlalchemy
        logger.info("sqlalchemy", version=sqlalchemy.__version__)
    except ImportError:
        missing.append("sqlalchemy")
    try:
        import httpx
        logger.info("httpx", version=httpx.__version__)
    except ImportError:
        missing.append("httpx")
    try:
        import bcrypt
        logger.info("bcrypt", version=bcrypt.__version__)  # type: ignore[attr-defined]
    except ImportError:
        missing.append("bcrypt")
    try:
        import jwt
        logger.info("PyJWT", version=jwt.__version__)
    except ImportError:
        missing.append("PyJWT")

    if missing:
        logger.warning(f"Missing dependencies: {', '.join(missing)} — install with: pip install {' '.join(missing)}")

    try:
        ok = await init_db()
        if ok:
            logger.info("Database initialized successfully")
        else:
            msg = "Database initialization failed — cannot start without database"
            if settings.env == "production":
                logger.error(msg)
                raise RuntimeError(msg)
            else:
                logger.warning("Database unavailable — features requiring DB will fail")
    except Exception as e:
        if settings.env == "production":
            logger.error(f"Database initialization failed (production): {e}")
            raise
        else:
            logger.warning(f"Database initialization error (dev): {e}")

    # Initialize tracing for production
    setup_tracing()

    yield
    logger.info("Syzygy Intelligence shutting down")
    await close_db()


app = FastAPI(
    title="Syzygy Intelligence API",
    description="Multi-agent platform with polarity-aware consensus and Jungian archetypes",
    version="0.1.0",
    lifespan=lifespan,
)

# Add request tracing middleware first (so it wraps everything)
app.add_middleware(RequestTracingMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["content-type", "authorization"],
    max_age=600,
)

setup_error_handlers(app)
setup_rate_limiter(app)

app.include_router(agents.router, prefix="/api/agents", tags=["Agents"])
app.include_router(sessions.router, prefix="/api/sessions", tags=["Sessions"])
app.include_router(consensus.router, prefix="/api/consensus", tags=["Consensus"])
app.include_router(memory.router, prefix="/api/memory", tags=["Memory"])
app.include_router(tools.router, prefix="/api/tools", tags=["Tools"])
app.include_router(workflows.router, prefix="/api/workflows", tags=["Workflows"])
app.include_router(chat.router, prefix="/api/chat", tags=["Chat"])
app.include_router(auth.router, prefix="/api/auth", tags=["Auth"])
app.include_router(oauth.router, prefix="/api/auth", tags=["Auth"])
app.include_router(audit.router, prefix="/api/audit", tags=["Audit"])
app.include_router(meta.router, prefix="/api/meta", tags=["Meta"])
app.include_router(uploads.router, prefix="/api/uploads", tags=["Uploads"])
app.include_router(rag_route.router, prefix="/api/rag", tags=["RAG"])
app.include_router(self_improvement.router, prefix="/api", tags=["Self-Improvement"])
app.include_router(admin.router, prefix="/api/admin", tags=["Admin"])
app.include_router(payments.router, prefix="/api/payments", tags=["Payments"])
app.include_router(health.router, prefix="", tags=["Health"])

app.add_api_websocket_route("/ws", ws_handler)


@app.get("/")
async def root() -> dict[str, Any]:
    return {
        "service": "Syzygy Intelligence",
        "version": "0.1.0",
        "tagline": "Aligning opposites into unified intelligence",
        "status": "operational",
    }


@app.get("/metrics")
async def get_metrics() -> Response:
    """Prometheus metrics endpoint."""
    body, content_type = await metrics_endpoint()
    return Response(content=body, media_type=content_type)
