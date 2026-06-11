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
