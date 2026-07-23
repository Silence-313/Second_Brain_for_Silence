"""Skill protocol — abstract base for privileged system capabilities."""

from abc import ABC, abstractmethod
from typing import Any

from agent.models.skills import SkillResult


class Skill(ABC):
    """Privileged system capability. May require user permission."""

    name: str = ""
    description: str = ""
    permissions: str = "safe"  # "safe" | "privileged"

    @abstractmethod
    async def execute(self, args: dict[str, Any]) -> SkillResult:
        """Execute the skill with given arguments."""
        ...

    def validate_args(self, args: dict[str, Any]) -> bool:
        return True

    def to_info(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "permissions": self.permissions,
        }
