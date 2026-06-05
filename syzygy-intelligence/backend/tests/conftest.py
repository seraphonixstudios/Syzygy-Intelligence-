"""PyTest configuration for Syzygy Intelligence tests."""

import os
import sys

os.environ["SYZYGY_ENV"] = "testing"
os.environ["SYZYGY_LOG_LEVEL"] = "CRITICAL"

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async fixtures."""
    import asyncio
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def tmp_path(tmp_path):
    return tmp_path
