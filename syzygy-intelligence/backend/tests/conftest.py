"""PyTest configuration for Syzygy Intelligence tests."""

import os
import sys

os.environ["SYZYGY_ENV"] = "testing"
os.environ["SYZYGY_LOG_LEVEL"] = "CRITICAL"

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# Mock chromadb to avoid protobuf metaclass issues on Python 3.14
import types
_chromadb_mock = types.ModuleType("chromadb")
_chromadb_mock.__dict__.update({
    "PersistentClient": None,
    "Client": None,
    "DEFAULT_TENANT": "default_tenant",
    "DEFAULT_DATABASE": "default_database",
    "__file__": "<mocked>",
    "__package__": "chromadb",
    "__path__": [],
})
# submodules needed by app.rag.retriever
_chromadb_errors = types.ModuleType("chromadb.errors")
_chromadb_errors.__dict__.update({"InvalidCollectionException": type("InvalidCollectionException", (Exception,), {})})
_chromadb_config = types.ModuleType("chromadb.config")
_chromadb_config.__dict__.update({"Settings": type("Settings", (), {"__init__": lambda self, **kwargs: None})})
sys.modules["chromadb"] = _chromadb_mock
sys.modules["chromadb.errors"] = _chromadb_errors
sys.modules["chromadb.config"] = _chromadb_config
_chromadb_utils = types.ModuleType("chromadb.utils")
_chromadb_utils.__dict__.update({"__file__": "<mocked>", "__package__": "chromadb.utils", "__path__": []})
_chromadb_ef = types.ModuleType("chromadb.utils.embedding_functions")
_chromadb_ef.DefaultEmbeddingFunction = type("DefaultEmbeddingFunction", (), {})
_chromadb_utils.embedding_functions = _chromadb_ef
sys.modules["chromadb.utils"] = _chromadb_utils
sys.modules["chromadb.utils.embedding_functions"] = _chromadb_ef

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
