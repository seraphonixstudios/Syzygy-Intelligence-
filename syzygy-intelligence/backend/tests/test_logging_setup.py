"""Tests for logging setup utilities."""

from __future__ import annotations

import logging

from app.logging_setup import JsonFormatter


class TestJsonFormatter:
    def test_format_with_unserializable_extra(self):
        class NonSerializable:
            pass

        record = logging.LogRecord(
            name="test", level=logging.INFO, pathname="", lineno=0,
            msg="test message", args=(), exc_info=None,
        )
        record.extra = {"data": NonSerializable()}
        result = JsonFormatter().format(record)
        assert "test message" in result
        assert "NonSerializable" in result
