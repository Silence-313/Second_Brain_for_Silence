"""Tests for ToolRouter."""

from agent.routing.router import ToolRouter


class TestToolRouter:
    def test_route_add_todos(self) -> None:
        router = ToolRouter()
        result = router.route_tool("添加待办：明天下午开会")
        assert result.tool == "add_todos"

    def test_route_get_time(self) -> None:
        router = ToolRouter()
        result = router.route_tool("现在几点")
        assert result.tool == "get_current_time"

    def test_route_web_search(self) -> None:
        router = ToolRouter()
        result = router.route_tool("帮我搜索Python最新版本")
        assert result.tool == "web_search"

    def test_route_memory_search(self) -> None:
        router = ToolRouter()
        result = router.route_tool("你还记得我之前说过什么吗")
        assert result.tool == "memory_search"

    def test_route_wiki_search(self) -> None:
        router = ToolRouter()
        result = router.route_tool("看看笔记里有没有关于ML的内容")
        assert result.tool == "wiki_search"

    def test_route_get_todos(self) -> None:
        router = ToolRouter()
        result = router.route_tool("今天有什么待办事项")
        assert result.tool == "get_todos"

    def test_route_default(self) -> None:
        router = ToolRouter()
        result = router.route_tool("你好")
        assert result.tool == "memory_search"
        assert result.confidence <= 0.3

    def test_confidence_range(self) -> None:
        router = ToolRouter()
        result = router.route_tool("添加待办")
        assert 0 <= result.confidence <= 1

    def test_empty_query(self) -> None:
        router = ToolRouter()
        result = router.route_tool("")
        assert result.tool == "memory_search"
