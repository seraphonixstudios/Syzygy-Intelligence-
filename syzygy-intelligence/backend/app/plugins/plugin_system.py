"""Plugin system for Syzygy — extensible third-party module support."""

from __future__ import annotations

import importlib
import inspect
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from app.logging_setup import logger


@dataclass
class PluginManifest:
    name: str
    version: str = "0.1.0"
    description: str = ""
    author: str = ""
    entry_point: str = ""
    dependencies: list[str] = field(default_factory=list)


class PluginBase:
    """Base class for all Syzygy plugins."""

    name: str = ""
    version: str = "0.1.0"
    description: str = ""

    async def on_load(self) -> None:
        """Called when plugin is loaded."""

    async def on_unload(self) -> None:
        """Called when plugin is unloaded."""

    async def execute(self, action: str, params: dict[str, Any]) -> Any:
        """Execute a plugin action."""
        raise NotImplementedError


class PluginSystem:
    """Manages plugin discovery, loading, and execution."""

    def __init__(self) -> None:
        self._plugins: dict[str, PluginBase] = {}
        self._plugin_dirs: list[Path] = []

    def add_plugin_dir(self, path: str) -> None:
        self._plugin_dirs.append(Path(path))

    async def discover_plugins(self) -> list[PluginManifest]:
        """Discover available plugins."""
        manifests = []

        for plugin_dir in self._plugin_dirs:
            if not plugin_dir.exists():
                continue

            for manifest_file in plugin_dir.glob("**/plugin.json"):
                try:
                    import json
                    data = json.loads(manifest_file.read_text())
                    manifests.append(PluginManifest(**data))
                except Exception as e:
                    logger.warning("Failed to load plugin manifest", manifest=str(manifest_file), error=str(e))
                    continue

        return manifests

    async def load_plugin(self, name: str) -> PluginBase | None:
        """Load a plugin by name."""
        if name in self._plugins:
            return self._plugins[name]

        for plugin_dir in self._plugin_dirs:
            for py_file in plugin_dir.glob("**/*.py"):
                if py_file.stem == "plugin" or py_file.stem == name:
                    try:
                        spec = importlib.util.spec_from_file_location(  # type: ignore[attr-defined]
                            f"syzygy_plugin_{name}", py_file
                        )
                        if spec and spec.loader:
                            module = importlib.util.module_from_spec(spec)  # type: ignore[attr-defined]
                            spec.loader.exec_module(module)

                            for _, obj in inspect.getmembers(module):
                                if (
                                    inspect.isclass(obj)
                                    and issubclass(obj, PluginBase)
                                    and obj is not PluginBase
                                ):
                                    plugin = obj()
                                    await plugin.on_load()
                                    self._plugins[name] = plugin
                                    return plugin
                    except Exception as e:
                        logger.warning("Failed to load plugin", plugin=name, error=str(e))
                        continue

        return None

    async def unload_plugin(self, name: str) -> bool:
        """Unload a plugin."""
        if name in self._plugins:
            await self._plugins[name].on_unload()
            del self._plugins[name]
            return True
        return False

    async def execute_action(
        self,
        plugin_name: str,
        action: str,
        params: dict[str, Any] | None = None,
    ) -> Any:
        """Execute a plugin action."""
        plugin = self._plugins.get(plugin_name)
        if not plugin:
            raise ValueError(f"Plugin '{plugin_name}' not loaded")
        return await plugin.execute(action, params or {})

    def get_loaded_plugins(self) -> list[str]:
        return list(self._plugins.keys())


plugin_system = PluginSystem()
