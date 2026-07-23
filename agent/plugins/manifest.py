"""Plugin manifest — metadata model for plugin packages."""

from typing import Literal

from pydantic import BaseModel, Field


class CapabilityRegistration(BaseModel, frozen=True):
    type: Literal["tool", "skill", "search_provider", "pipeline_stage"] = "tool"
    class_path: str
    config: dict[str, object] = Field(default_factory=dict)


class PluginManifest(BaseModel, frozen=True):
    name: str
    version: str
    description: str = ""
    author: str = ""
    capabilities: list[CapabilityRegistration] = Field(default_factory=list)

    def validate_class_paths(self) -> list[str]:
        errors: list[str] = []
        for cap in self.capabilities:
            parts = cap.class_path.rsplit(".", 1)
            if len(parts) != 2:
                errors.append(f"Invalid class_path: {cap.class_path}")
        return errors
