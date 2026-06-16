"""Tests for AuditService and SyzygyLogger."""

from unittest.mock import patch

import pytest


class TestAuditService:
    @pytest.fixture
    def service(self):
        from app.audit import AuditService
        return AuditService()

    @pytest.mark.asyncio
    async def test_log_no_db(self, service):
        with patch("app.audit._get_session_factory") as mock_factory:
            mock_factory.side_effect = Exception("No DB")
            result = await service.log("test", "action")
            assert result == ""

    @pytest.mark.asyncio
    async def test_log_with_details(self, service):
        with patch("app.audit._get_session_factory") as mock_factory:
            mock_factory.side_effect = Exception("No DB")
            result = await service.log("test", "action", agent_id="a1", details={"key": "val"})
            assert result == ""

    @pytest.mark.asyncio
    async def test_query_no_db(self, service):
        with patch("app.audit._get_session_factory") as mock_factory:
            mock_factory.side_effect = Exception("No DB")
            results = await service.query()
            assert results == []

    @pytest.mark.asyncio
    async def test_query_with_filters(self, service):
        with patch("app.audit._get_session_factory") as mock_factory:
            mock_factory.side_effect = Exception("No DB")
            results = await service.query(event_type="test", agent_id="a1", limit=50, offset=10)
            assert results == []

    @pytest.mark.asyncio
    async def test_count_no_db(self, service):
        with patch("app.audit._get_session_factory") as mock_factory:
            mock_factory.side_effect = Exception("No DB")
            count = await service.count()
            assert count == 0

    @pytest.mark.asyncio
    async def test_count_with_filters(self, service):
        with patch("app.audit._get_session_factory") as mock_factory:
            mock_factory.side_effect = Exception("No DB")
            count = await service.count(event_type="test", session_id="s1")
            assert count == 0

    @pytest.mark.asyncio
    async def test_log_error_in_execute(self, service):
        with patch("app.audit._get_session_factory") as mock_factory:
            mock_factory.side_effect = Exception("No DB")
            result = await service.log("test", "fail_action")
            assert result == ""


class TestSyzygyLogger:
    @pytest.fixture
    def logger(self, tmp_path):
        with patch("app.logging_setup.settings") as ms:
            ms.data_dir = str(tmp_path)
            ms.log_level = "DEBUG"
            from app.logging_setup import SyzygyLogger
            yield SyzygyLogger(name="test_logger", log_dir=str(tmp_path / "logs"))

    def test_init_creates_log_dir(self, tmp_path):
        log_dir = tmp_path / "custom_logs"
        with patch("app.logging_setup.settings") as ms:
            ms.data_dir = str(tmp_path)
            ms.log_level = "INFO"
            from app.logging_setup import SyzygyLogger
            SyzygyLogger(name="test", log_dir=str(log_dir))
            assert log_dir.exists()

    def test_context_injection(self, logger):
        logger.with_context(component="test")
        assert logger._context.get()["component"] == "test"

    def test_context_merging(self, logger):
        logger.with_context(app="syzygy")
        assert logger._context.get()["app"] == "syzygy"

    def test_info_logs_with_context(self, logger):
        logger.with_context(env="test")
        logger.info("hello")

    def test_warning_logs(self, logger):
        logger.warning("warning msg")

    def test_error_logs(self, logger):
        logger.error("error msg")

    def test_critical_logs(self, logger):
        logger.critical("critical msg")

    def test_audit_logs(self, logger):
        logger.audit("user_login")

    def test_log_exception(self, logger):
        try:
            raise ValueError("test error")
        except ValueError as e:
            logger.log_exception(e, "something broke")

    def test_debug_logs(self, logger):
        logger.debug("debug msg")

    def test_structured_message_with_kwargs(self):
        from app.logging_setup import StructuredMessage
        msg = StructuredMessage("test", key="value", count=42)
        s = str(msg)
        assert "test" in s
        assert "value" in s
        assert "42" in s

    def test_json_formatter(self, logger):
        from app.logging_setup import JsonFormatter
        import logging
        fmt = JsonFormatter()
        record = logging.LogRecord(
            name="test", level=logging.INFO, pathname="", lineno=0,
            msg="json test", args=(), exc_info=None,
        )
        record.extra = {"user_email": "user@test.com"}
        output = fmt.format(record)
        assert "json test" in output
        assert "user@test.com" in output

    def test_json_formatter_with_exception(self, logger):
        from app.logging_setup import JsonFormatter
        import logging
        fmt = JsonFormatter()
        try:
            raise ValueError("boom")
        except ValueError:
            import sys
            record = logging.LogRecord(
                name="test", level=logging.ERROR, pathname="", lineno=0,
                msg="error", args=(), exc_info=sys.exc_info(),
            )
            output = fmt.format(record)
            assert "exception" in output
            assert "ValueError" in output

    def test_setup_handlers_json_format(self, tmp_path):
        with patch("app.logging_setup.settings") as ms:
            ms.data_dir = str(tmp_path)
            ms.log_level = "DEBUG"
            ms.effective_log_format = "json"
            from app.logging_setup import SyzygyLogger
            log = SyzygyLogger(name="json_logger", log_dir=str(tmp_path / "json_logs"))
            log.info("json format test")
            # Should not raise

    def test_audit_with_action(self, logger):
        import io
        import logging
        # Capture audit output
        logger.audit("user_action", user_id="u1", details={"key": "val"})
        # Should not raise; the audit handler uses a filter

    def test_with_context_twice_merges(self, logger):
        logger.with_context(env="prod")
        logger.with_context(region="us-east")
        ctx = logger._context.get()
        assert ctx["env"] == "prod"
        assert ctx["region"] == "us-east"

    def test_log_exception_with_extra_context(self, logger):
        try:
            raise RuntimeError("system failure")
        except RuntimeError as e:
            logger.log_exception(e, "context", extra_field="value")
            # Should not raise


class TestAuditServiceCountWithSessionId:
    @pytest.mark.asyncio
    async def test_filters_by_session_id(self):
        import uuid
        from unittest.mock import patch

        from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

        from app.audit import AuditService
        from app.db.models import AuditLog, Base

        engine = create_async_engine("sqlite+aiosqlite://")
        factory = async_sessionmaker(engine, expire_on_commit=False)

        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        session_a = uuid.uuid4()
        session_b = uuid.uuid4()

        async with factory() as db:
            db.add_all([
                AuditLog(id=uuid.uuid4(), event_type="t1", action="a1", session_id=session_a, details={}),
                AuditLog(id=uuid.uuid4(), event_type="t1", action="a2", session_id=session_a, details={}),
                AuditLog(id=uuid.uuid4(), event_type="t1", action="a3", session_id=session_b, details={}),
            ])
            await db.commit()

        with patch("app.audit._get_session_factory", return_value=factory):
            svc = AuditService()
            count_a = await svc.count(session_id=str(session_a))
            assert count_a == 2

            count_b = await svc.count(session_id=str(session_b))
            assert count_b == 1

            count_none = await svc.count(session_id="00000000-0000-0000-0000-000000000000")
            assert count_none == 0
