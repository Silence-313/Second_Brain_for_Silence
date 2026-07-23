"""Tests for built-in tools."""

import pytest

from agent.tools.builtins.time import GetCurrentTimeTool
from agent.tools.builtins.todos import AddTodosTool, GetTodosTool, TodoStatsTool


class TestGetCurrentTimeTool:
    @pytest.mark.asyncio
    async def test_execute(self) -> None:
        tool = GetCurrentTimeTool()
        result = await tool.execute({})
        assert result.success
        assert "datetime" in result.data  # type: ignore[operator]

    @pytest.mark.asyncio
    async def test_validate_args(self) -> None:
        tool = GetCurrentTimeTool()
        assert tool.validate_args({})
        assert tool.validate_args({"timezone": "Asia/Shanghai"})


class TestTodosTools:
    @pytest.mark.asyncio
    async def test_add_and_get(self) -> None:
        add_tool = AddTodosTool()
        get_tool = GetTodosTool()

        await add_tool.execute({"text": "test todo", "priority": "high"})
        result = await get_tool.execute({})
        assert result.success
        assert result.data["count"] >= 1  # type: ignore[index]

    @pytest.mark.asyncio
    async def test_add_requires_text(self) -> None:
        add_tool = AddTodosTool()
        assert not add_tool.validate_args({})
        assert add_tool.validate_args({"text": "something"})

    @pytest.mark.asyncio
    async def test_stats(self) -> None:
        stats_tool = TodoStatsTool()
        result = await stats_tool.execute({})
        assert result.success
        assert "total" in result.data["stats"]  # type: ignore[index]
