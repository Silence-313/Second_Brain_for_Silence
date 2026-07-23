"""Tool protocol — abstract base for all executable tools."""

from abc import ABC, abstractmethod
from typing import Any

from agent.models.tools import ToolResult


class Tool(ABC):
    """External-world interaction capability. All tools are safe (no privileged access)."""

    name: str = ""
    description: str = ""
    permissions: str = "safe"
    parameters: dict[str, Any] = {}

    @abstractmethod
    async def execute(self, args: dict[str, Any]) -> ToolResult:
        """Execute the tool with given arguments."""
        ...

    def validate_args(self, args: dict[str, Any]) -> bool:
        """Validate arguments against the tool's parameter schema."""
        required = self.parameters.get("required", [])
        return all(k in args for k in required)

    def to_info(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "permissions": self.permissions,
        }

    def to_llm_description(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters,
        }
