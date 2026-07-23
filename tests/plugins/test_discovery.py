"""Tests for PluginDiscovery."""

import json
import os
import tempfile

from agent.plugins.discovery import PluginDiscovery
from agent.plugins.manifest import PluginManifest


class TestPluginDiscovery:
    def test_discover_plugins(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            plugin_dir = os.path.join(tmpdir, "my_plugin")
            os.makedirs(plugin_dir)

            manifest = {
                "name": "test-plugin",
                "version": "0.1.0",
                "description": "A test plugin",
                "capabilities": [
                    {"type": "tool", "class_path": "agent.tools.builtins.time.GetCurrentTimeTool"}
                ],
            }
            with open(os.path.join(plugin_dir, "plugin.json"), "w") as f:
                json.dump(manifest, f)

            discovery = PluginDiscovery()
            manifests = discovery.discover(tmpdir)
            assert len(manifests) == 1
            assert manifests[0].name == "test-plugin"

    def test_skip_dirs_without_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            os.makedirs(os.path.join(tmpdir, "not_a_plugin"))

            discovery = PluginDiscovery()
            manifests = discovery.discover(tmpdir)
            assert len(manifests) == 0

    def test_skip_invalid_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            plugin_dir = os.path.join(tmpdir, "bad_plugin")
            os.makedirs(plugin_dir)
            with open(os.path.join(plugin_dir, "plugin.json"), "w") as f:
                f.write("not json")

            discovery = PluginDiscovery()
            manifests = discovery.discover(tmpdir)
            assert len(manifests) == 0

    def test_nonexistent_directory(self) -> None:
        discovery = PluginDiscovery()
        manifests = discovery.discover("/nonexistent/path")
        assert manifests == []


class TestPluginLoader:
    def test_validate_valid_manifest(self) -> None:
        from agent.plugins.loader import PluginLoader

        manifest = PluginManifest(
            name="test",
            version="0.1.0",
            capabilities=[
                {"type": "tool", "class_path": "agent.tools.builtins.time.GetCurrentTimeTool"}  # type: ignore[arg-type]
            ],
        )
        loader = PluginLoader()
        errors = loader.validate(manifest)
        assert len(errors) == 0

    def test_validate_invalid_class_path(self) -> None:
        from agent.plugins.loader import PluginLoader

        manifest = PluginManifest(
            name="test",
            version="0.1.0",
            capabilities=[
                {"type": "tool", "class_path": "nonexistent.module.Class"}  # type: ignore[arg-type]
            ],
        )
        loader = PluginLoader()
        errors = loader.validate(manifest)
        assert len(errors) > 0

    def test_validate_missing_name(self) -> None:
        from agent.plugins.loader import PluginLoader

        manifest = PluginManifest(name="", version="")
        loader = PluginLoader()
        errors = loader.validate(manifest)
        assert len(errors) > 0

    def test_install_and_uninstall(self) -> None:
        import asyncio

        from agent.plugins.loader import PluginLoader

        manifest = PluginManifest(
            name="test-plugin",
            version="0.1.0",
            capabilities=[
                {"type": "tool", "class_path": "agent.tools.builtins.time.GetCurrentTimeTool"}  # type: ignore[arg-type]
            ],
        )
        loader = PluginLoader()
        asyncio.run(loader.install(manifest))
        assert "test-plugin" in loader.list_installed()

        asyncio.run(loader.uninstall("test-plugin"))
        assert "test-plugin" not in loader.list_installed()
