"""Plugin discovery — scan directories for plugin.json manifests."""

import json
import os

from agent.plugins.manifest import PluginManifest


class PluginDiscovery:
    """Scan a package directory for plugins (each subdir with plugin.json)."""

    def discover(self, plugins_dir: str) -> list[PluginManifest]:
        manifests: list[PluginManifest] = []

        if not os.path.isdir(plugins_dir):
            return manifests

        for entry in os.listdir(plugins_dir):
            entry_path = os.path.join(plugins_dir, entry)
            if not os.path.isdir(entry_path):
                continue

            manifest_path = os.path.join(entry_path, "plugin.json")
            if not os.path.isfile(manifest_path):
                continue

            try:
                with open(manifest_path, encoding="utf-8") as f:
                    data = json.load(f)
                manifest = PluginManifest.model_validate(data)
                manifests.append(manifest)
            except (json.JSONDecodeError, Exception):
                continue

        return manifests
