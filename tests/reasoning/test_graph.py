"""Tests for ConceptGraphBuilder."""

from agent.models.concepts import Concept
from agent.reasoning.graph import ConceptGraphBuilder


class TestConceptGraphBuilder:
    @staticmethod
    def _make_concepts() -> list[Concept]:
        return [
            Concept(
                id="c1",
                name="ML",
                slug="ml",
                confidence=0.9,
                source_episodes=["ep1", "ep2"],
                related=["dl", "nn"],
                tags=["ai", "ml"],
            ),
            Concept(
                id="c2",
                name="DL",
                slug="dl",
                confidence=0.85,
                source_episodes=["ep2", "ep3"],
                related=["ml"],
                tags=["ai", "dl"],
            ),
            Concept(
                id="c3",
                name="NN",
                slug="nn",
                confidence=0.8,
                source_episodes=["ep3"],
                related=["ml", "dl"],
                tags=["ai", "neural"],
            ),
            Concept(
                id="c4",
                name="Python",
                slug="python",
                confidence=0.9,
                source_episodes=["ep4"],
                related=[],
                tags=["code"],
            ),
        ]

    def test_build_full(self) -> None:
        builder = ConceptGraphBuilder()
        concepts = self._make_concepts()
        graph = builder.build_full(concepts)
        assert len(graph.nodes) == 4
        assert len(graph.edges) > 0

    def test_edge_types(self) -> None:
        builder = ConceptGraphBuilder()
        concepts = self._make_concepts()
        graph = builder.build_full(concepts)
        types = {e.type for e in graph.edges}
        assert "related" in types

    def test_node_degrees(self) -> None:
        builder = ConceptGraphBuilder()
        concepts = self._make_concepts()
        graph = builder.build_full(concepts)
        for node in graph.nodes.values():
            assert node.degree >= 0

    def test_build_subgraph(self) -> None:
        builder = ConceptGraphBuilder()
        concepts = self._make_concepts()
        full = builder.build_full(concepts)
        sub = builder.build_subgraph(full, ["ml", "dl"])
        assert len(sub.nodes) >= 2
        assert "ml" in sub.nodes or "dl" in sub.nodes

    def test_build_subgraph_empty_seeds(self) -> None:
        builder = ConceptGraphBuilder()
        concepts = self._make_concepts()
        full = builder.build_full(concepts)
        sub = builder.build_subgraph(full, [])
        assert len(sub.nodes) == 0

    def test_build_subgraph_unknown_seed(self) -> None:
        builder = ConceptGraphBuilder()
        concepts = self._make_concepts()
        full = builder.build_full(concepts)
        sub = builder.build_subgraph(full, ["nonexistent"])
        assert len(sub.nodes) == 0

    def test_subgraph_central_concepts(self) -> None:
        builder = ConceptGraphBuilder()
        concepts = self._make_concepts()
        full = builder.build_full(concepts)
        sub = builder.build_subgraph(full, ["ml", "dl"])
        assert len(sub.central_concepts) <= 3

    def test_empty_concepts(self) -> None:
        builder = ConceptGraphBuilder()
        graph = builder.build_full([])
        assert len(graph.nodes) == 0
        assert len(graph.edges) == 0
