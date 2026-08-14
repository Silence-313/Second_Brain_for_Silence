"""Integration tests: Routing stack — Router + Telemetry + RAG Feedback."""

import pytest

from agent.models.retrieval import RetrievalRecord
from agent.models.routing import RoutingRecord
from agent.retrieval.feedback import RagFeedback
from agent.routing.router import ToolRouter
from agent.routing.telemetry import RouterTelemetry


class TestRoutingIntegration:
    """Test router + telemetry + RAG feedback working together."""

    @pytest.fixture
    def routing_stack(self):
        return {
            "router": ToolRouter(),
            "telemetry": RouterTelemetry(),
            "rag_feedback": RagFeedback(),
        }

    def test_route_then_record(self, routing_stack):
        router = routing_stack["router"]
        telemetry = routing_stack["telemetry"]

        result = router.route_tool("搜索Python最新版本")
        assert result.tool == "web_search"

        telemetry.record_routing(
            RoutingRecord(
                query="搜索Python最新版本",
                selected_tool=result.tool,
                confidence=result.confidence,
                execution_success=True,
            )
        )
        metrics = telemetry.get_metrics("web_search")
        assert metrics is not None
        assert metrics.selection_count == 1

    def test_adaptive_threshold_evolution(self, routing_stack):
        router = routing_stack["router"]
        telemetry = routing_stack["telemetry"]

        # Record several successes, threshold should decrease
        for i in range(5):
            telemetry.record_routing(
                RoutingRecord(
                    query=f"search query {i}",
                    selected_tool="web_search",
                    confidence=0.8,
                    execution_success=True,
                )
            )

        threshold = telemetry.get_adaptive_threshold("web_search")
        assert threshold <= 0.3  # high success → low threshold

        result = router.route_tool("搜索", telemetry.get_all_metrics())
        assert result.tool == "web_search"

    def test_rag_feedback_flow(self, routing_stack):
        rag = routing_stack["rag_feedback"]

        # Simulate retrieval + feedback
        for i in range(5):
            rag.record_retrieval(
                RetrievalRecord(
                    query=f"query {i}",
                    retrieved_docs=[f"doc{i}.md", f"doc{i + 1}.md"],
                    used_docs=[f"doc{i}.md"],
                    answer_quality=0.7 + i * 0.05,
                )
            )

        w = rag.get_doc_weight("doc0.md")
        assert w is not None
        # doc0 was used, should have boosted relevance
        assert w.relevance_score >= 0.5

        w2 = rag.get_doc_weight("doc1.md")
        # doc1 was retrieved but not used first time, used second time
        assert w2 is not None

    def test_full_routing_loop(self, routing_stack):
        router = routing_stack["router"]
        telemetry = routing_stack["telemetry"]

        queries = [
            "添加待办：明天开会",
            "现在几点",
            "搜索Python教程",
            "你还记得我的名字吗",
            "看看笔记里有什么",
            "今天有哪些待办",
        ]

        for q in queries:
            result = router.route_tool(q)
            telemetry.record_routing(
                RoutingRecord(
                    query=q,
                    selected_tool=result.tool,
                    confidence=result.confidence,
                    execution_success=True,
                )
            )

        all_metrics = telemetry.get_all_metrics()
        assert len(all_metrics) >= 2  # at least some tools selected
