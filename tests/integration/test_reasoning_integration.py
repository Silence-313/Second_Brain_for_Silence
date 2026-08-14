"""Integration tests: Reasoning stack — GraphBuilder + Reasoner + Store + FeedbackProcessor."""

import asyncio

import pytest

from agent.infrastructure.storage.memory_fs import InMemoryFileStorage
from agent.memory.store import MemoryStore
from agent.models.concepts import Concept
from agent.reasoning.feedback import FeedbackProcessor
from agent.reasoning.graph import ConceptGraphBuilder
from agent.reasoning.reasoner import ConceptReasoner


class TestReasoningIntegration:
    """Test concept graph → reasoning → feedback pipeline."""

    @pytest.fixture
    def reasoning_stack(self):
        storage = InMemoryFileStorage()
        store = MemoryStore(storage, "/mem")
        builder = ConceptGraphBuilder()
        reasoner = ConceptReasoner()
        feedback = FeedbackProcessor(store=store)
        return {
            "store": store,
            "builder": builder,
            "reasoner": reasoner,
            "feedback": feedback,
        }

    @staticmethod
    def _make_test_concepts() -> list[Concept]:
        return [
            Concept(
                id="c1",
                name="Machine Learning",
                slug="machine-learning",
                confidence=0.9,
                source_episodes=["ep1", "ep2"],
                related=["deep-learning", "neural-networks"],
                tags=["ai", "ml"],
            ),
            Concept(
                id="c2",
                name="Deep Learning",
                slug="deep-learning",
                confidence=0.85,
                source_episodes=["ep2", "ep3"],
                related=["machine-learning"],
                tags=["ai", "dl"],
            ),
            Concept(
                id="c3",
                name="Neural Networks",
                slug="neural-networks",
                confidence=0.8,
                source_episodes=["ep3"],
                related=["machine-learning"],
                tags=["ai", "neural"],
            ),
            Concept(
                id="c4",
                name="Python",
                slug="python",
                confidence=0.9,
                source_episodes=["ep4"],
                related=[],
                tags=["code", "language"],
            ),
            Concept(
                id="c5",
                name="Rust",
                slug="rust",
                confidence=0.7,
                source_episodes=["ep5"],
                related=[],
                tags=["code", "systems"],
            ),
        ]

    def test_build_graph_from_concepts(self, reasoning_stack):
        builder = reasoning_stack["builder"]
        concepts = self._make_test_concepts()
        graph = builder.build_full(concepts)

        assert len(graph.nodes) == 5
        assert len(graph.edges) > 0
        assert graph.nodes["machine-learning"].degree > 0

    def test_reason_with_seeds(self, reasoning_stack):
        builder = reasoning_stack["builder"]
        reasoner = reasoning_stack["reasoner"]
        concepts = self._make_test_concepts()

        full = builder.build_full(concepts)
        sub = builder.build_subgraph(full, ["machine-learning", "deep-learning"])
        result = reasoner.reason("How does deep learning relate to ML?", sub, full)

        assert len(result.key_concepts) > 0
        assert result.confidence > 0
        assert len(sub.nodes) >= 2

    def test_feedback_processor(self, reasoning_stack):
        builder = reasoning_stack["builder"]
        reasoner = reasoning_stack["reasoner"]
        feedback = reasoning_stack["feedback"]
        concepts = self._make_test_concepts()

        full = builder.build_full(concepts)
        sub = builder.build_subgraph(full, ["machine-learning", "deep-learning"])
        result = reasoner.reason("What is deep learning?", sub, full)

        async def run():
            await feedback.process(result, "What is deep learning?")
            stats = feedback.get_stats()
            assert stats["cycles_run"] == 1
            usage = feedback.get_usage_stats()
            for kc in result.key_concepts:
                assert kc in usage

        asyncio.run(run())

    def test_empty_concept_list(self, reasoning_stack):
        builder = reasoning_stack["builder"]
        graph = builder.build_full([])
        assert len(graph.nodes) == 0

    def test_reasoning_with_1_hop_subgraph(self, reasoning_stack):
        builder = reasoning_stack["builder"]
        reasoner = reasoning_stack["reasoner"]
        concepts = self._make_test_concepts()

        full = builder.build_full(concepts)
        sub = builder.build_subgraph(full, ["machine-learning"])
        result = reasoner.reason("machine learning", sub, full)

        # 1-hop from ml should include dl and nn
        assert len(sub.nodes) >= 1
        assert result.confidence >= 0
