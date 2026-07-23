"""Tool registry — central registration and discovery of tools."""

from agent.tools.protocol import Tool


class ToolRegistry:
    """Register and manage tools. Supports auto-discovery."""

    def __init__(self) -> None:
        self._tools: dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        if not tool.name:
            raise ValueError("Tool must have a name")
        self._tools[tool.name] = tool

    def unregister(self, name: str) -> bool:
        if name in self._tools:
            del self._tools[name]
            return True
        return False

    def get(self, name: str) -> Tool | None:
        return self._tools.get(name)

    def list_all(self) -> list[dict[str, object]]:
        return [t.to_info() for t in self._tools.values()]

    def get_for_llm(self) -> list[dict[str, object]]:
        return [t.to_llm_description() for t in self._tools.values()]

    @property
    def count(self) -> int:
        return len(self._tools)

    @property
    def names(self) -> list[str]:
        return list(self._tools.keys())
