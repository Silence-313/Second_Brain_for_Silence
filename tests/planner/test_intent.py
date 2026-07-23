"""Tests for IntentParser."""

from agent.planner.intent import IntentParser


class TestIntentParser:
    def test_bilibili_search(self) -> None:
        parser = IntentParser()
        intent = parser.parse("搜索B站编译原理")
        assert intent.action == "search"
        assert intent.platform == "bilibili"

    def test_code_write(self) -> None:
        parser = IntentParser()
        intent = parser.parse("帮我写个函数")
        assert intent.action == "write"
        assert intent.domain == "code"

    def test_greeting(self) -> None:
        parser = IntentParser()
        intent = parser.parse("你好")
        assert intent.action == "chat"
        assert intent.confidence >= 0.8

    def test_knowledge_read(self) -> None:
        parser = IntentParser()
        intent = parser.parse("读一下笔记")
        assert intent.action == "read"
        assert intent.platform == "obsidian"

    def test_web_search(self) -> None:
        parser = IntentParser()
        intent = parser.parse("搜索Python最新版本")
        assert intent.action == "search"
        assert intent.platform == "web"

    def test_empty_query(self) -> None:
        parser = IntentParser()
        intent = parser.parse("")
        assert intent.action == "chat"

    def test_confidence_range(self) -> None:
        parser = IntentParser()
        intent = parser.parse("测试")
        assert 0 <= intent.confidence <= 1
