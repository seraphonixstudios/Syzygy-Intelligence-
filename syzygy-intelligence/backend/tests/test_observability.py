"""Tests for observability module — metrics, tracing, logging events."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest


class TestSyzygyMetrics:
    def test_all_metrics_initialized(self):
        from app.observability import metrics_registry
        m = metrics_registry
        assert m.auth_login_attempts
        assert m.auth_token_refreshes
        assert m.auth_password_resets
        assert m.auth_email_verifications
        assert m.auth_api_keys_created
        assert m.auth_api_keys_revoked
        assert m.message_count_charged
        assert m.usage_limit_exceeded
        assert m.trial_expirations
        assert m.premium_upgrades
        assert m.http_requests
        assert m.http_request_duration_seconds
        assert m.db_query_duration_seconds
        assert m.db_connection_errors
        assert m.consensus_rounds_completed
        assert m.consensus_round_duration_seconds
        assert m.active_sessions
        assert m.llm_calls
        assert m.llm_latency_seconds
        assert m.cache_hits
        assert m.cache_misses

    def test_counter_increment(self):
        from app.observability import metrics_registry
        m = metrics_registry
        m.auth_login_attempts.labels(status="test_inc").inc()
        assert m.auth_login_attempts.labels(status="test_inc")._value.get() == 1


class TestLogAuthEvent:
    def test_logs_auth_event(self):
        with patch("app.observability.logger") as mock_logger:
            from app.observability import log_auth_event
            log_auth_event("login", user_email="test@example.com", user_id="u1", result="success")
            mock_logger.audit.assert_called_once()
            args, kwargs = mock_logger.audit.call_args
            assert args[0] == "login"
            assert kwargs["event_type"] == "auth"
            assert kwargs["user_email"] == "test@example.com"


class TestLogUsageEvent:
    def test_logs_usage_event(self):
        with patch("app.observability.logger") as mock_logger:
            from app.observability import log_usage_event
            log_usage_event("message_charged", user_id="u1", subscription_tier="free", message_count=10)
            mock_logger.audit.assert_called_once()
            kwargs = mock_logger.audit.call_args.kwargs
            assert kwargs["event_type"] == "usage"


class TestLogConsensusEvent:
    def test_logs_consensus_event(self):
        with patch("app.observability.logger") as mock_logger:
            from app.observability import log_consensus_event
            log_consensus_event("round_completed", session_id="s1", round_number=1, status="converged", duration_ms=100.0)
            mock_logger.info.assert_called_once()
            kwargs = mock_logger.info.call_args.kwargs
            assert kwargs["event_type"] == "consensus"


class TestLogLlmCall:
    def test_logs_llm_call(self):
        with patch("app.observability.logger") as mock_logger:
            from app.observability import log_llm_call
            log_llm_call("qwen3:8b", prompt_tokens=100, completion_tokens=50, duration_ms=200.0)
            mock_logger.info.assert_called_once()
            kwargs = mock_logger.info.call_args.kwargs
            assert kwargs["event_type"] == "llm"
            assert kwargs["total_tokens"] == 150


class TestTraceOperation:
    @pytest.mark.asyncio
    async def test_logs_completion_on_success(self):
        with patch("app.observability.logger") as mock_logger:
            from app.observability import trace_operation
            async with trace_operation("test_op", operation_type="test"):
                pass
            mock_logger.info.assert_called_once()
            assert "completed" in mock_logger.info.call_args[0][0]

    @pytest.mark.asyncio
    async def test_logs_failure_on_exception(self):
        with patch("app.observability.logger") as mock_logger:
            from app.observability import trace_operation
            with pytest.raises(ValueError):
                async with trace_operation("failing_op"):
                    raise ValueError("boom")
            mock_logger.error.assert_called_once()
            assert "failed" in mock_logger.error.call_args[0][0]


class TestRequestTracingMiddleware:
    @pytest.mark.asyncio
    async def test_sets_context_vars_and_records_metrics(self):
        with (
            patch("app.observability.logger") as mock_logger,
            patch("app.observability.request_id_context") as mock_rid,
            patch("app.observability.correlation_id_context") as mock_cid,
        ):
            from app.observability import RequestTracingMiddleware

            async def dummy_app(scope, receive, send):
                await send({"type": "http.response.start", "status": 200})
                await send({"type": "http.response.body", "body": b"ok"})

            middleware = RequestTracingMiddleware(dummy_app)
            scope = {"type": "http", "method": "GET", "path": "/test", "headers": []}
            receive = AsyncMock()
            send = AsyncMock()

            await middleware(scope, receive, send)
            assert mock_rid.set.called
            assert mock_cid.set.called
            mock_logger.info.assert_called_once()

    @pytest.mark.asyncio
    async def test_passes_non_http_scope(self):
        from app.observability import RequestTracingMiddleware
        inner = AsyncMock()
        middleware = RequestTracingMiddleware(inner)
        scope = {"type": "websocket"}
        await middleware(scope, AsyncMock(), AsyncMock())
        inner.assert_called_once()


class TestSetupTracing:
    def test_skips_when_not_production(self):
        with patch("app.observability.settings") as mock_settings:
            mock_settings.env = "development"
            from app.observability import setup_tracing
            setup_tracing()  # Should not raise

    def test_logs_warning_on_missing_deps(self):
        with (
            patch("app.observability.settings") as mock_settings,
            patch("app.observability.logger") as mock_logger,
        ):
            mock_settings.env = "production"
            from app.observability import setup_tracing
            setup_tracing()
            mock_logger.warning.assert_called_once()


class TestMetricsEndpoint:
    @pytest.mark.asyncio
    async def test_returns_metrics(self):
        from app.observability import metrics_endpoint
        data, content_type = await metrics_endpoint()
        assert content_type
        assert data


class TestSetupTracingProduction:
    def test_sets_up_tracing_in_production(self):
        """setup_tracing initializes Jaeger exporter in production with all deps."""
        pytest.importorskip("opentelemetry.exporter.jaeger.thrift", exc_type=ImportError)
        with (
            patch("app.observability.settings") as mock_settings,
            patch("app.observability.logger") as mock_logger,
            patch("opentelemetry.exporter.jaeger.thrift.JaegerExporter") as mock_je,
            patch("opentelemetry.instrumentation.fastapi.FastAPIInstrumentor") as mock_fi,
            patch("opentelemetry.instrumentation.sqlalchemy.SQLAlchemyInstrumentor") as mock_si,
            patch("opentelemetry.instrumentation.redis.RedisInstrumentor") as mock_ri,
            patch("app.observability.TracerProvider") as mock_tp,
            patch("app.observability.BatchSpanProcessor") as mock_bsp,
            patch("app.observability.trace") as mock_trace,
        ):
            mock_settings.env = "production"
            mock_settings.jaeger_host = "jaeger"
            mock_settings.jaeger_port = 6831
            from app.observability import setup_tracing
            setup_tracing()
            mock_je.assert_called_once_with(agent_host_name="jaeger", agent_port=6831)
            mock_tp.assert_called_once()
            mock_tp.return_value.add_span_processor.assert_called_once()
            mock_trace.set_tracer_provider.assert_called_once()
            mock_fi.instrument_app.assert_called_once()
            mock_si.return_value.instrument.assert_called_once()
            mock_ri.return_value.instrument.assert_called_once()
            mock_logger.info.assert_called_with("OpenTelemetry tracing initialized with Jaeger")


class TestRequestTracingMiddlewareException:
    @pytest.mark.asyncio
    async def test_logs_error_on_exception(self):
        """Middleware logs error when the wrapped app raises."""
        with (
            patch("app.observability.logger") as mock_logger,
            patch("app.observability.request_id_context") as mock_rid,
            patch("app.observability.correlation_id_context") as mock_cid,
        ):
            from app.observability import RequestTracingMiddleware

            async def failing_app(scope, receive, send):
                raise RuntimeError("app crash")

            middleware = RequestTracingMiddleware(failing_app)
            scope = {"type": "http", "method": "GET", "path": "/fail", "headers": []}
            receive = AsyncMock()
            send = AsyncMock()

            with pytest.raises(RuntimeError, match="app crash"):
                await middleware(scope, receive, send)
            mock_logger.error.assert_called_once()
            assert "failed" in mock_logger.error.call_args[0][0]
