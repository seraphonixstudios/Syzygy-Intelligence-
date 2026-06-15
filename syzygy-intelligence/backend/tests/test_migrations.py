"""Verify alembic migration files are valid Python and maintain chain integrity."""

import importlib.util
import os
import py_compile
import sys

import pytest

MIGRATIONS_DIR = os.path.join(os.path.dirname(__file__), "..", "migrations", "versions")
MIGRATION_FILES = sorted(
    f for f in os.listdir(MIGRATIONS_DIR) if f.endswith(".py") and f != "__init__.py"
)
ENV_PY = os.path.join(os.path.dirname(__file__), "..", "migrations", "env.py")


@pytest.mark.parametrize("filename", MIGRATION_FILES)
def test_migration_syntax(filename: str) -> None:
    """Each migration file should be valid Python syntax."""
    filepath = os.path.join(MIGRATIONS_DIR, filename)
    py_compile.compile(filepath, doraise=True)


@pytest.mark.parametrize("filename", MIGRATION_FILES)
def test_migration_imports(filename: str) -> None:
    """Each migration file should be importable (all deps available)."""
    filepath = os.path.join(MIGRATIONS_DIR, filename)
    spec = importlib.util.spec_from_file_location(filename.replace(".py", ""), filepath)
    assert spec is not None, f"Could not create spec for {filename}"
    mod = importlib.util.module_from_spec(spec)
    # Using exec_module instead of load_module (deprecated)
    spec.loader.exec_module(mod)
    assert hasattr(mod, "upgrade"), f"{filename} missing upgrade()"
    assert hasattr(mod, "downgrade"), f"{filename} missing downgrade()"


def test_migration_chain() -> None:
    """Verify the revision chain: 0001 -> 0002 -> 0003."""
    revisions = {}
    for filename in MIGRATION_FILES:
        filepath = os.path.join(MIGRATIONS_DIR, filename)
        spec = importlib.util.spec_from_file_location(filename.replace(".py", ""), filepath)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        revisions[mod.revision] = mod.down_revision

    # Check chain integrity
    for rev, down in revisions.items():
        if down is None:
            assert rev == "0001", f"Only revision 0001 should have no parent, got {rev}"
        else:
            assert down in revisions, f"Revision {rev} points to missing parent {down}"


def test_env_py_syntax() -> None:
    """env.py should at least be valid Python."""
    py_compile.compile(ENV_PY, doraise=True)


@pytest.mark.parametrize("filename", MIGRATION_FILES)
def test_migration_has_revision_fields(filename: str) -> None:
    """Each migration must define revision, down_revision, branch_labels, depends_on."""
    filepath = os.path.join(MIGRATIONS_DIR, filename)
    spec = importlib.util.spec_from_file_location(filename.replace(".py", ""), filepath)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert isinstance(mod.revision, str), f"{filename}: revision not a string"
    assert mod.branch_labels is None, f"{filename}: branch_labels must be None"
    assert mod.depends_on is None, f"{filename}: depends_on must be None"
