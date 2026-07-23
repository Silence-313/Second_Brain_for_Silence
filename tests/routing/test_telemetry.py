"""Tests for RouterTelemetry."""

from agent.models.routing import RoutingRecord
from agent.routing.telemetry import RouterTelemetry


class TestRouterTelemetry:
    def test_record_routing(self) -> None:
        rt = RouterTelemetry()
        rt.record_routing(RoutingRecord(query="test", selected_tool="web_search", confidence=0.8, execution_success=True))
        metrics = rt.get_metrics("web_search")
        assert metrics is not None
        assert metrics.selection_count == 1

    def test_adaptive_threshold(self) -> None:
        rt = RouterTelemetry()
        for _ in range(3):
            rt.record_routing(RoutingRecord(query="test", selected_tool="web_search", confidence=0.8, execution_success=True))
        threshold = rt.get_adaptive_threshold("web_search")
        assert 0.1 <= threshold <= 0.6

    def test_get_unknown_tool(self) -> None:
        rt = RouterTelemetry()
        assert rt.get_adaptive_threshold("unknown") == 0.2

    def test_get_all_metrics(self) -> None:
        rt = RouterTelemetry()
        rt.record_routing(RoutingRecord(query="test", selected_tool="test_tool", confidence=0.5, execution_success=True))
        assert "test_tool" in rt.get_all_metrics()

    def test_serialize_deserialize(self) -> None:
        rt = RouterTelemetry()
        rt.record_routing(RoutingRecord(query="q", selected_tool="web_search", confidence=0.7, execution_success=True))
        json_str = rt.serialize()
        rt2 = RouterTelemetry()
        rt2.deserialize(json_str)
        assert rt2.get_metrics("web_search") is not None
