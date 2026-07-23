"""Tests for ToolRegistry."""

from agent.tools.builtins.time import GetCurrentTimeTool
from agent.tools.builtins.todos import AddTodosTool, GetTodosTool
from agent.tools.registry import ToolRegistry


class TestToolRegistry:
    def test_register(self) -> None:
        reg = ToolRegistry()
        reg.register(GetCurrentTimeTool())
        assert reg.count == 1

    def test_get(self) -> None:
        reg = ToolRegistry()
        reg.register(GetCurrentTimeTool())
        tool = reg.get("get_current_time")
        assert tool is not None
        assert tool.name == "get_current_time"

    def test_get_nonexistent(self) -> None:
        reg = ToolRegistry()
        assert reg.get("nonexistent") is None

    def test_unregister(self) -> None:
        reg = ToolRegistry()
        reg.register(GetCurrentTimeTool())
        assert reg.unregister("get_current_time")
        assert reg.count == 0

    def test_unregister_nonexistent(self) -> None:
        reg = ToolRegistry()
        assert not reg.unregister("nonexistent")

    def test_list_all(self) -> None:
        reg = ToolRegistry()
        reg.register(GetCurrentTimeTool())
        reg.register(GetTodosTool())
        tools = reg.list_all()
        assert len(tools) == 2

    def test_get_for_llm(self) -> None:
        reg = ToolRegistry()
        reg.register(GetCurrentTimeTool())
        descs = reg.get_for_llm()
        assert len(descs) == 1
        assert "name" in descs[0]

    def test_names(self) -> None:
        reg = ToolRegistry()
        reg.register(GetCurrentTimeTool())
        reg.register(AddTodosTool())
        assert "get_current_time" in reg.names
        assert "add_todos" in reg.names
