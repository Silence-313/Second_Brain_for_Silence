"""Plugin loader — validate, install, uninstall plugins into the Agent."""

import importlib
from typing import Any

from agent.plugins.manifest import CapabilityRegistration, PluginManifest


class PluginLoader:
    """Load, validate, and install plugins into the Agent."""

    def __init__(self, agent: Any = None) -> None:  # Agent | None
        self._agent = agent
        self._installed: dict[str, PluginManifest] = {}

    def validate(self, manifest: PluginManifest) -> list[str]:
        errors: list[str] = []

        if not manifest.name or not manifest.name.strip():
            errors.append("Plugin name is required")
        if not manifest.version:
            errors.append("Plugin version is required")

        for cap in manifest.capabilities:
            parts = cap.class_path.rsplit(".", 1)
            if len(parts) != 2:
                errors.append(f"Invalid class_path: {cap.class_path}")
                continue

            module_path, class_name = parts
            try:
                module = importlib.import_module(module_path)
                if not hasattr(module, class_name):
                    errors.append(f"Class {class_name} not found in {module_path}")
            except ModuleNotFoundError:
                errors.append(f"Module not found: {module_path}")
            except Exception as e:
                errors.append(f"Error loading {cap.class_path}: {e}")

        return errors

    async def install(self, manifest: PluginManifest) -> None:
        if manifest.name in self._installed:
            raise ValueError(f"Plugin already installed: {manifest.name}")

        for cap in manifest.capabilities:
            capability = self._instantiate(cap)
            if capability is None:
                continue

            if self._agent is not None:
                if cap.type == "tool":
                    self._agent.register_tool(capability)
                elif cap.type == "skill":
                    self._agent.register_skill(capability)
                elif cap.type == "search_provider":
                    self._agent.register_search_provider(capability)
                elif cap.type == "pipeline_stage":
                    self._agent.register_pipeline_stage(capability)

        self._installed[manifest.name] = manifest

    async def uninstall(self, name: str) -> bool:
        if name not in self._installed:
            return False
        del self._installed[name]
        return True

    def list_installed(self) -> list[str]:
        return list(self._installed.keys())

    def get_manifest(self, name: str) -> PluginManifest | None:
        return self._installed.get(name)

    @staticmethod
    def _instantiate(registration: CapabilityRegistration) -> Any:
        try:
            module_path, class_name = registration.class_path.rsplit(".", 1)
            module = importlib.import_module(module_path)
            cls = getattr(module, class_name)
            config = dict(registration.config)
            return cls(**config) if config else cls()
        except Exception:
            return None
