"""Plugin SDK — auto-discovery, manifest validation, installation."""

from agent.plugins.discovery import PluginDiscovery
from agent.plugins.loader import PluginLoader
from agent.plugins.manifest import CapabilityRegistration, PluginManifest

__all__ = ["PluginDiscovery", "PluginLoader", "PluginManifest", "CapabilityRegistration"]
