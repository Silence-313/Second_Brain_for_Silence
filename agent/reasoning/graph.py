"""Concept graph builder — full graph + 1-hop subgraph construction."""

from agent.models.concepts import (
    Concept,
    ConceptGraph,
    ConceptGraphEdge,
    ConceptGraphNode,
    ConceptSubgraph,
)


class ConceptGraphBuilder:
    """Builds in-memory concept graphs from loaded concept data."""

    def build_full(
        self, concepts: list[Concept], episode_slugs: list[str] | None = None
    ) -> ConceptGraph:
        nodes: dict[str, ConceptGraphNode] = {}
        for c in concepts:
            nodes[c.slug] = ConceptGraphNode(
                id=c.id,
                name=c.name,
                slug=c.slug,
                confidence=c.confidence,
                source_episodes=list(c.source_episodes),
                related=list(c.related),
                tags=list(c.tags),
                degree=0,
            )

        edges = self._build_edges(list(nodes.values()), episode_slugs or [])
        self._compute_degrees(nodes, edges)

        return ConceptGraph(nodes=nodes, edges=edges)

    def build_subgraph(
        self, full_graph: ConceptGraph, seed_slugs: list[str]
    ) -> ConceptSubgraph:
        seed_set = {s for s in seed_slugs if s in full_graph.nodes}
        if not seed_set:
            return ConceptSubgraph()

        neighbor_slugs: set[str] = set()
        for edge in full_graph.edges:
            if edge.from_slug in seed_set and edge.to_slug not in seed_set:
                neighbor_slugs.add(edge.to_slug)
            if edge.to_slug in seed_set and edge.from_slug not in seed_set:
                neighbor_slugs.add(edge.from_slug)

        subgraph_slugs = seed_set | neighbor_slugs
        subgraph_nodes = {
            slug: node
            for slug, node in full_graph.nodes.items()
            if slug in subgraph_slugs
        }
        subgraph_edges = [
            edge
            for edge in full_graph.edges
            if edge.from_slug in subgraph_slugs and edge.to_slug in subgraph_slugs
        ]

        self._compute_degrees(subgraph_nodes, subgraph_edges)

        central = sorted(
            subgraph_nodes.values(), key=lambda n: n.degree, reverse=True
        )
        central_concepts = [n.slug for n in central[:3] if n.degree > 0]

        return ConceptSubgraph(
            nodes=subgraph_nodes,
            edges=subgraph_edges,
            central_concepts=central_concepts,
        )

    # -- Private --

    @staticmethod
    def _build_edges(
        nodes: list[ConceptGraphNode], episode_slugs: list[str]
    ) -> list[ConceptGraphEdge]:
        edges: list[ConceptGraphEdge] = []
        slug_set = {n.slug for n in nodes}
        episode_counts: dict[str, int] = {}

        for node in nodes:
            for ep in node.source_episodes:
                episode_counts[ep] = episode_counts.get(ep, 0) + 1

        # Type 1: explicit related[] links (weight 0.8)
        for node in nodes:
            for rel_slug in node.related:
                if rel_slug in slug_set and rel_slug != node.slug:
                    edges.append(
                        ConceptGraphEdge(
                            from_slug=node.slug,
                            to_slug=rel_slug,
                            weight=0.8,
                            type="related",
                        )
                    )

        # Type 2: shared episodes
        for i, a in enumerate(nodes):
            for b in nodes[i + 1 :]:
                shared = set(a.source_episodes) & set(b.source_episodes)
                if shared:
                    min_sources = min(len(a.source_episodes), len(b.source_episodes))
                    denominator = max(2, min_sources)
                    weight = round(
                        min(1.0, 0.3 + len(shared) / denominator), 4
                    )
                    edges.append(
                        ConceptGraphEdge(
                            from_slug=a.slug,
                            to_slug=b.slug,
                            weight=weight,
                            type="shared-episode",
                        )
                    )

        # Type 3: tag overlap
        for i, a in enumerate(nodes):
            for b in nodes[i + 1 :]:
                shared_tags = set(a.tags) & set(b.tags)
                if shared_tags:
                    max_tags = max(len(a.tags), len(b.tags), 1)
                    weight = round(
                        min(1.0, 0.3 + len(shared_tags) / max_tags), 4
                    )
                    edges.append(
                        ConceptGraphEdge(
                            from_slug=a.slug,
                            to_slug=b.slug,
                            weight=weight,
                            type="tag-overlap",
                        )
                    )

        return edges

    @staticmethod
    def _compute_degrees(
        nodes: dict[str, ConceptGraphNode], edges: list[ConceptGraphEdge]
    ) -> None:
        degree: dict[str, int] = dict.fromkeys(nodes, 0)
        for edge in edges:
            degree[edge.from_slug] = degree.get(edge.from_slug, 0) + 1
            degree[edge.to_slug] = degree.get(edge.to_slug, 0) + 1
        for slug, count in degree.items():
            if slug in nodes:
                nodes[slug] = nodes[slug].model_copy(update={"degree": count})
