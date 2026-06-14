"""Tests for the plugin system."""
from __future__ import annotations

import json
import types
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.plugins.plugin_system import PluginBase, PluginManifest, PluginSystem


class _TestPlugin(PluginBase):
    name = "test-plugin"
    version = "1.0.0"

    async def execute(self, action: str, params: dict | None = None) -> str:
        return f"{action}:{params}"


class TestPluginManifest:
    def test_default_values(self):
        m = PluginManifest(name="test-plugin")
        assert m.name == "test-plugin"
        assert m.version == "0.1.0"
        assert m.description == ""
        assert m.author == ""
        assert m.entry_point == ""
        assert m.dependencies == []

    def test_custom_values(self):
        m = PluginManifest(
            name="my-plugin", version="1.0.0", description="A plugin",
            author="me", entry_point="main", dependencies=["requests"],
        )
        assert m.name == "my-plugin"
        assert m.version == "1.0.0"
        assert "requests" in m.dependencies


class TestPluginBase:
    @pytest.mark.asyncio
    async def test_on_load_does_nothing(self):
        p = PluginBase()
        assert await p.on_load() is None

    @pytest.mark.asyncio
    async def test_on_unload_does_nothing(self):
        p = PluginBase()
        assert await p.on_unload() is None

    @pytest.mark.asyncio
    async def test_execute_raises_not_implemented(self):
        p = PluginBase()
        with pytest.raises(NotImplementedError):
            await p.execute("action", {})


class TestPluginSystem:
    def test_add_plugin_dir(self):
        ps = PluginSystem()
        ps.add_plugin_dir("/some/path")
        assert len(ps._plugin_dirs) == 1

    def test_get_loaded_plugins_empty(self):
        ps = PluginSystem()
        assert ps.get_loaded_plugins() == []

    def test_get_loaded_plugins_after_load(self):
        ps = PluginSystem()
        ps._plugins["test"] = PluginBase()
        assert "test" in ps.get_loaded_plugins()

    @pytest.mark.asyncio
    async def test_discover_plugins_none(self):
        ps = PluginSystem()
        ps.add_plugin_dir("/nonexistent")
        manifests = await ps.discover_plugins()
        assert manifests == []

    @pytest.mark.asyncio
    async def test_discover_plugins_finds_manifests(self):
        ps = PluginSystem()
        mock_data = json.dumps({"name": "test", "version": "1.0.0"})

        with (
            patch("app.plugins.plugin_system.Path.exists", return_value=True),
            patch("app.plugins.plugin_system.Path.glob") as m_glob,
            patch("app.plugins.plugin_system.Path.read_text", return_value=mock_data),
        ):
            m_glob.return_value = [Path("/plugins/test/plugin.json")]
            ps.add_plugin_dir("/plugins")
            manifests = await ps.discover_plugins()
            assert len(manifests) == 1
            assert manifests[0].name == "test"

    @pytest.mark.asyncio
    async def test_discover_plugins_skips_invalid(self):
        ps = PluginSystem()
        with (
            patch("app.plugins.plugin_system.Path.exists", return_value=True),
            patch("app.plugins.plugin_system.Path.glob") as m_glob,
            patch("app.plugins.plugin_system.Path.read_text", return_value="invalid json"),
        ):
            m_glob.return_value = [Path("/plugins/bad/plugin.json")]
            ps.add_plugin_dir("/plugins")
            manifests = await ps.discover_plugins()
            assert manifests == []

    @pytest.mark.asyncio
    async def test_load_plugin_returns_cached(self):
        ps = PluginSystem()
        plugin = PluginBase()
        ps._plugins["cached"] = plugin
        result = await ps.load_plugin("cached")
        assert result is plugin

    @pytest.mark.asyncio
    async def test_unload_plugin_removes_and_calls_on_unload(self):
        ps = PluginSystem()
        plugin = MagicMock(spec=PluginBase)
        plugin.on_unload = AsyncMock()
        ps._plugins["test"] = plugin
        result = await ps.unload_plugin("test")
        assert result is True
        assert "test" not in ps._plugins
        plugin.on_unload.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_unload_plugin_not_found(self):
        ps = PluginSystem()
        result = await ps.unload_plugin("nonexistent")
        assert result is False

    @pytest.mark.asyncio
    async def test_execute_action_runs_plugin_action(self):
        ps = PluginSystem()
        plugin = _TestPlugin()
        ps._plugins["test"] = plugin
        result = await ps.execute_action("test", "do_stuff", {"key": "val"})
        assert result == "do_stuff:{'key': 'val'}"

    @pytest.mark.asyncio
    async def test_execute_action_raises_if_not_loaded(self):
        ps = PluginSystem()
        with pytest.raises(ValueError, match="not loaded"):
            await ps.execute_action("unknown", "action")

    @pytest.mark.asyncio
    async def test_execute_action_defaults_params(self):
        ps = PluginSystem()
        plugin = _TestPlugin()
        ps._plugins["test"] = plugin
        result = await ps.execute_action("test", "action")
        assert result == "action:{}"

    @pytest.mark.asyncio
    async def test_load_plugin_from_file(self):
        ps = PluginSystem()
        mock_module = types.ModuleType("syzygy_plugin_test")
        mock_module.MyPlugin = _TestPlugin

        with (
            patch("app.plugins.plugin_system.Path.exists", return_value=True),
            patch("app.plugins.plugin_system.Path.glob") as m_glob,
            patch("app.plugins.plugin_system.importlib.util.spec_from_file_location") as m_spec,
            patch("app.plugins.plugin_system.importlib.util.module_from_spec") as m_mod,
        ):
            m_glob.return_value = [Path("/plugins/test/plugin.py")]
            mock_spec = MagicMock()
            mock_spec.loader = MagicMock()
            m_spec.return_value = mock_spec
            m_mod.return_value = mock_module

            ps.add_plugin_dir("/plugins")
            result = await ps.load_plugin("test")
            assert isinstance(result, _TestPlugin)
            assert "test" in ps._plugins

    @pytest.mark.asyncio
    async def test_load_plugin_returns_none_on_failure(self):
        ps = PluginSystem()
        with (
            patch("app.plugins.plugin_system.Path.exists", return_value=True),
            patch("app.plugins.plugin_system.Path.glob") as m_glob,
        ):
            m_glob.return_value = [Path("/plugins/test/plugin.py")]
            ps.add_plugin_dir("/plugins")
            result = await ps.load_plugin("test")
            assert result is None

    @pytest.mark.asyncio
    async def test_load_plugin_no_py_files(self):
        ps = PluginSystem()
        with (
            patch("app.plugins.plugin_system.Path.exists", return_value=True),
            patch("app.plugins.plugin_system.Path.glob") as m_glob,
        ):
            m_glob.return_value = []
            ps.add_plugin_dir("/plugins")
            result = await ps.load_plugin("test")
            assert result is None
