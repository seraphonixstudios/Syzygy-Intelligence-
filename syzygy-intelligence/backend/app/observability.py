"""Observability module — metrics, tracing, and structured logging for Syzygy."""

from __future__ import annotations

# ─── Request Tracing Context ───────────────────────────────────
import contextvars
import time
import uuid
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from typing import Any

from fastapi import Request
from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Gauge, Histogram, generate_latest

from app.config import settings
from app.logging_setup import logger

request_id_context: contextvars.ContextVar[str] = contextvars.ContextVar(
    "request_id", default=""
)
user_id_context: contextvars.ContextVar[str] = contextvars.ContextVar(
    "user_id", default=""
)
correlation_id_context: contextvars.ContextVar[str] = contextvars.ContextVar(
    "correlation_id", default=""
)


# ─── Prometheus Metrics ────────────────────────────────────────
class SyzygyMetrics:
    """Central metrics registry for Syzygy operations."""

    def __init__(self) -> None:
        # Auth metrics
        self.auth_login_attempts = Counter(
            "syzygy_auth_login_attempts_total",
            "Total login attempts by status",
            ["status"],  # success, failed
        )
        self.auth_token_refreshes = Counter(
            "syzygy_auth_token_refreshes_total",
            "Total token refresh operations",
            ["token_type"],  # access, refresh
        )
        self.auth_password_resets = Counter(
            "syzygy_auth_password_resets_total",
            "Total password reset requests",
            ["result"],  # success, invalid_token, user_not_found
        )
        self.auth_email_verifications = Counter(
            "syzygy_auth_email_verifications_total",
            "Total email verification attempts",
            ["result"],  # success, invalid_token, already_verified
        )
        self.auth_api_keys_created = Counter(
            "syzygy_auth_api_keys_created_total",
            "Total API keys created",
        )
        self.auth_api_keys_revoked = Counter(
            "syzygy_auth_api_keys_revoked_total",
            "Total API keys revoked",
        )

        # Usage metrics
        self.message_count_charged = Counter(
            "syzygy_messages_charged_total",
            "Total messages charged to users",
            ["subscription_tier"],  # free, premium, enterprise
        )
        self.usage_limit_exceeded = Counter(
            "syzygy_usage_limit_exceeded_total",
            "Total usage limit exceeded errors",
            ["subscription_tier"],
        )
        self.trial_expirations = Counter(
            "syzygy_trial_expirations_total",
            "Total trial period expirations",
        )
        self.premium_upgrades = Counter(
            "syzygy_premium_upgrades_total",
            "Total upgrades to premium tier",
        )

        # API metrics
        self.http_requests = Counter(
            "syzygy_http_requests_total",
            "Total HTTP requests by endpoint and status",
            ["method", "endpoint", "status"],
        )
        self.http_request_duration_seconds = Histogram(
            "syzygy_http_request_duration_seconds",
            "HTTP request latency by endpoint",
            ["method", "endpoint"],
            buckets=(0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0),
        )

        # Database metrics
        self.db_query_duration_seconds = Histogram(
            "syzygy_db_query_duration_seconds",
            "Database query latency by operation",
            ["operation"],  # select, insert, update, delete
            buckets=(0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0),
        )
        self.db_connection_errors = Counter(
            "syzygy_db_connection_errors_total",
            "Total database connection errors",
        )

        # Agent/consensus metrics
        self.consensus_rounds_completed = Counter(
            "syzygy_consensus_rounds_completed_total",
            "Total consensus rounds completed",
            ["result"],  # converged, failed
        )
        self.consensus_round_duration_seconds = Histogram(
            "syzygy_consensus_round_duration_seconds",
            "Consensus round execution time",
            buckets=(0.1, 0.5, 1.0, 5.0, 10.0, 30.0, 60.0),
        )
        self.active_sessions = Gauge(
            "syzygy_active_sessions",
            "Current active sessions",
        )

        # LLM metrics
        self.llm_calls = Counter(
            "syzygy_llm_calls_total",
            "Total LLM API calls by model",
            ["model", "status"],  # success, timeout, error
        )
        self.llm_latency_seconds = Histogram(
            "syzygy_llm_latency_seconds",
            "LLM response latency by model",
            ["model"],
            buckets=(0.5, 1.0, 2.0, 5.0, 10.0, 30.0),
        )

        # System metrics
        self.cache_hits = Counter(
            "syzygy_cache_hits_total",
            "Total cache hits by cache type",
            ["cache_type"],
        )
        self.cache_misses = Counter(
            "syzygy_cache_misses_total",
            "Total cache misses by cache type",
            ["cache_type"],
        )


metrics_registry = SyzygyMetrics()


# ─── OpenTelemetry Setup ───────────────────────────────────────
def setup_tracing() -> None:
    """Initialize OpenTelemetry tracing with Jaeger exporter."""
    try:
        from opentelemetry.exporter.jaeger.thrift import JaegerExporter  # pragma: no cover
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor  # pragma: no cover
        from opentelemetry.instrumentation.redis import RedisInstrumentor  # pragma: no cover
        from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor  # pragma: no cover
    except ImportError as e:  # pragma: no cover
        logger.warning(f"Tracing imports failed: {e}")
        return

    if not settings.env == "production":  # pragma: no cover
        logger.info("Tracing disabled outside production")
        return

    jaeger_exporter = JaegerExporter(  # pragma: no cover
        agent_host_name=settings.jaeger_host,
        agent_port=settings.jaeger_port,
    )

    trace_provider = TracerProvider(  # pragma: no cover
        resource=Resource.create(
            {
                "service.name": "syzygy-intelligence",
                "service.version": "0.1.0",
                "environment": settings.env,
            }
        )
    )
    trace_provider.add_span_processor(BatchSpanProcessor(jaeger_exporter))  # pragma: no cover
    trace.set_tracer_provider(trace_provider)  # pragma: no cover

    FastAPIInstrumentor.instrument_app(None, tracer_provider=trace_provider)  # pragma: no cover
    SQLAlchemyInstrumentor().instrument()  # pragma: no cover
    RedisInstrumentor().instrument()  # pragma: no cover

    logger.info("OpenTelemetry tracing initialized with Jaeger")  # pragma: no cover


# ─── Middleware for Request Tracing ────────────────────────────
class RequestTracingMiddleware:
    """Middleware to inject request ID and correlation ID into logs and traces."""

    def __init__(self, app: Any) -> None:
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request = Request(scope, receive=receive)
        req_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        correlation_id = request.headers.get(
            "X-Correlation-ID",
            request.headers.get("X-Request-ID", str(uuid.uuid4())),
        )

        request_id_context.set(req_id)
        correlation_id_context.set(correlation_id)

        status_code = [200]
        start_time = time.time()

        async def wrapped_send(message):
            if message["type"] == "http.response.start":
                status_code[0] = message["status"]
            await send(message)

        try:
            await self.app(scope, receive, wrapped_send)
            duration = time.time() - start_time
            endpoint = request.url.path

            metrics_registry.http_requests.labels(
                method=request.method,
                endpoint=endpoint,
                status=status_code[0],
            ).inc()
            metrics_registry.http_request_duration_seconds.labels(
                method=request.method,
                endpoint=endpoint,
            ).observe(duration)

            logger.info(
                f"HTTP {request.method} {endpoint}",
                status=status_code[0],
                duration_ms=int(duration * 1000),
            )
        except Exception as e:
            duration = time.time() - start_time
            logger.error(
                f"HTTP {request.method} {request.url.path} failed",
                error=str(e),
                duration_ms=int(duration * 1000),
            )
            raise


# ─── Auth Event Logging ────────────────────────────────────────
def log_auth_event(
    event: str,
    user_email: str | None = None,
    user_id: str | None = None,
    result: str = "success",
    details: dict[str, Any] | None = None,
) -> None:
    """Log authentication events with consistent structure."""
    logger.audit(
        event,
        event_type="auth",
        user_email=user_email,
        user_id=user_id,
        result=result,
        timestamp=datetime.now(UTC).isoformat(),
        **(details or {}),
    )


def log_usage_event(
    event: str,
    user_id: str,
    subscription_tier: str,
    message_count: int,
    details: dict[str, Any] | None = None,
) -> None:
    """Log usage/billing events."""
    logger.audit(
        event,
        event_type="usage",
        user_id=user_id,
        subscription_tier=subscription_tier,
        message_count=message_count,
        timestamp=datetime.now(UTC).isoformat(),
        **(details or {}),
    )


def log_consensus_event(
    event: str,
    session_id: str,
    round_number: int,
    status: str,
    duration_ms: float,
    details: dict[str, Any] | None = None,
) -> None:
    """Log consensus engine events."""
    logger.info(
        event,
        event_type="consensus",
        session_id=session_id,
        round_number=round_number,
        status=status,
        duration_ms=int(duration_ms),
        timestamp=datetime.now(UTC).isoformat(),
        **(details or {}),
    )


def log_llm_call(
    model: str,
    prompt_tokens: int,
    completion_tokens: int,
    duration_ms: float,
    status: str = "success",
    details: dict[str, Any] | None = None,
) -> None:
    """Log LLM API calls."""
    logger.info(
        f"LLM call to {model}",
        event_type="llm",
        model=model,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        total_tokens=prompt_tokens + completion_tokens,
        duration_ms=int(duration_ms),
        status=status,
        timestamp=datetime.now(UTC).isoformat(),
        **(details or {}),
    )


# ─── Context Manager for Timing Operations ────────────────────
@asynccontextmanager
async def trace_operation(
    operation_name: str,
    operation_type: str = "operation",
    **context_data: Any,
):
    """Context manager for tracing operation duration and logging."""
    start_time = time.time()
    try:
        yield
    except Exception as e:
        duration = time.time() - start_time
        logger.error(
            f"{operation_name} failed",
            operation_type=operation_type,
            duration_ms=int(duration * 1000),
            error=str(e),
            **context_data,
        )
        raise
    else:
        duration = time.time() - start_time
        logger.info(
            f"{operation_name} completed",
            operation_type=operation_type,
            duration_ms=int(duration * 1000),
            **context_data,
        )


# ─── Metrics Endpoint ──────────────────────────────────────────
async def metrics_endpoint() -> tuple[str, str]:
    """Prometheus metrics endpoint."""
    return generate_latest(), CONTENT_TYPE_LATEST
