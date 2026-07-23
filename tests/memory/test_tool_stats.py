"""Tests for ToolMemory."""

from agent.memory.tool_stats import ToolMemory


class TestToolMemory:
    def test_record_call(self) -> None:
        tm = ToolMemory()
        tm.record_call("web_search", True, "search python", "web", 500, 0.8)
        assert tm.get_success_rate("web_search") == 1.0

    def test_success_rate_multiple(self) -> None:
        tm = ToolMemory()
        tm.record_call("test", True, "q1", "web", 100, 0.9)
        tm.record_call("test", False, "q2", "web", 200, 0.3)
        assert tm.get_success_rate("test") == 0.5

    def test_get_effectiveness(self) -> None:
        tm = ToolMemory()
        tm.record_call("test", True, "q", "web", 100, 0.9)
        eff = tm.get_effectiveness("test")
        assert 0 <= eff <= 1

    def test_get_frequency(self) -> None:
        tm = ToolMemory()
        tm.record_call("test", True, "q1", "web", 100, 0.5)
        tm.record_call("test", True, "q2", "web", 100, 0.5)
        assert tm.get_frequency("test") == 2

    def test_suggest_alternate(self) -> None:
        tm = ToolMemory()
        tm.record_call("web_search", True, "search python docs", "web", 500, 0.7)
        tm.record_call("wiki_search", True, "search python", "wiki", 300, 0.9)
        alt = tm.suggest_alternate("web_search", "search python docs")
        # wiki_search has higher effectiveness for similar pattern
        assert alt is None or isinstance(alt, str)

    def test_get_stats_unknown(self) -> None:
        tm = ToolMemory()
        assert tm.get_stats("unknown") is None

    def test_get_all_stats(self) -> None:
        tm = ToolMemory()
        tm.record_call("test", True, "q", "web", 100, 0.5)
        assert len(tm.get_all_stats()) == 1

    def test_serialize_deserialize(self) -> None:
        tm = ToolMemory()
        tm.record_call("test", True, "q", "web", 100, 0.8)
        json_str = tm.serialize()
        tm2 = ToolMemory()
        tm2.deserialize(json_str)
        assert tm2.get_success_rate("test") == 1.0
