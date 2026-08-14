"""Tests for ConceptReasoner."""

from agent.models.concepts import Concept, ConceptSubgraph
from agent.reasoning.graph import ConceptGraphBuilder
from agent.reasoning.reasoner import ConceptReasoner


class TestConceptReasoner:
    @staticmethod
    def _make_subgraph() -> ConceptSubgraph:
        concepts = [
            Concept(
                id="c1",
                name="ML",
                slug="ml",
                confidence=0.9,
                source_episodes=["ep1", "ep2"],
                related=["dl", "nn"],
                tags=["ai"],
            ),
            Concept(
                id="c2",
                name="DL",
                slug="dl",
                confidence=0.85,
                source_episodes=["ep2"],
                related=["ml"],
                tags=["ai"],
            ),
            Concept(
                id="c3",
                name="NN",
                slug="nn",
                confidence=0.8,
                source_episodes=["ep3"],
                related=["ml"],
                tags=["neural"],
            ),
        ]
        builder = ConceptGraphBuilder()
        full = builder.build_full(concepts)
        return builder.build_subgraph(full, ["ml", "dl"])

    def test_reason_produces_result(self) -> None:
        reasoner = ConceptReasoner()
        subgraph = self._make_subgraph()
        full = ConceptGraphBuilder().build_full(
            [
                Concept(id="c1", name="ML", slug="ml", related=["dl"]),
                Concept(id="c2", name="DL", slug="dl", related=["ml"]),
            ]
        )
        result = reasoner.reason("deep learning and ml", subgraph, full)
        assert isinstance(result.key_concepts, list)
        assert 0 <= result.confidence <= 1

    def test_reason_empty_subgraph(self) -> None:
        reasoner = ConceptReasoner()
        from agent.models.concepts import ConceptGraph

        result = reasoner.reason("test", ConceptSubgraph(), ConceptGraph())
        assert result.key_concepts == []
        assert result.confidence == 0.5

    def test_reason_single_concept(self) -> None:
        reasoner = ConceptReasoner()
        concepts = [Concept(id="c1", name="Only", slug="only")]
        builder = ConceptGraphBuilder()
        full = builder.build_full(concepts)
        sub = builder.build_subgraph(full, ["only"])
        result = reasoner.reason("test", sub, full)
        assert result.confidence >= 0

    def test_three_strategies_run(self) -> None:
        reasoner = ConceptReasoner()
        concepts = [
            Concept(id="c1", name="A", slug="a", related=["b"], tags=["x"]),
            Concept(id="c2", name="B", slug="b", related=["a", "c"], tags=["x"]),
            Concept(id="c3", name="C", slug="c", related=["b"], tags=["y"]),
        ]
        builder = ConceptGraphBuilder()
        full = builder.build_full(concepts)
        sub = builder.build_subgraph(full, ["a", "b"])
        result = reasoner.reason("A B C", sub, full)
        assert result.confidence > 0

    def test_confidence_range(self) -> None:
        reasoner = ConceptReasoner()
        subgraph = self._make_subgraph()
        full = ConceptGraphBuilder().build_full(
            [
                Concept(id="c1", name="ML", slug="ml", related=["dl"]),
                Concept(id="c2", name="DL", slug="dl", related=["ml"]),
            ]
        )
        result = reasoner.reason("test", subgraph, full)
        assert 0 <= result.confidence <= 1
