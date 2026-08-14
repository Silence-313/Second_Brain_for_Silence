"""Concept reasoner — 3-strategy reasoning engine. Pure computation, no I/O."""

import re
from collections import defaultdict

from agent.models.concepts import (
    ConceptGraph,
    ConceptGraphNode,
    ConceptSubgraph,
)
from agent.models.reasoning import ReasoningResult


class ConceptReasoner:
    """Graph-based reasoning with three independent strategies."""

    def reason(
        self, query: str, subgraph: ConceptSubgraph, full_graph: ConceptGraph
    ) -> ReasoningResult:
        if not subgraph.nodes:
            return ReasoningResult()

        r1 = self._strategy_traversal(subgraph)
        r2 = self._strategy_pattern_matching(query, subgraph, full_graph)
        r3 = self._strategy_abstraction(subgraph)

        key_concepts = list(dict.fromkeys(r1.key_concepts + r2.key_concepts + r3.key_concepts))
        relationships = list(dict.fromkeys(r1.relationships + r2.relationships + r3.relationships))
        insights = list(
            dict.fromkeys(r1.inferred_insights + r2.inferred_insights + r3.inferred_insights)
        )
        contradictions = list(
            dict.fromkeys(r1.contradictions + r2.contradictions + r3.contradictions)
        )
        bridging = list(
            dict.fromkeys(r1.bridging_concepts + r2.bridging_concepts + r3.bridging_concepts)
        )
        clusters = r3.concept_clusters if r3.concept_clusters else r1.concept_clusters

        confidence = round(0.4 * r1.confidence + 0.3 * r2.confidence + 0.3 * r3.confidence, 4)

        return ReasoningResult(
            key_concepts=key_concepts,
            relationships=relationships[:8],
            inferred_insights=insights[:5],
            contradictions=contradictions[:3],
            bridging_concepts=bridging,
            concept_clusters=clusters,
            confidence=confidence,
        )

    # -- Strategy 1: Graph Traversal --

    def _strategy_traversal(self, subgraph: ConceptSubgraph) -> ReasoningResult:
        nodes = list(subgraph.nodes.values())
        if not nodes:
            return ReasoningResult()

        max_degree = max(n.degree for n in nodes)
        key_concepts = [
            n.name
            for n in sorted(nodes, key=lambda x: x.degree, reverse=True)
            if n.degree > 0 and (n.degree >= max_degree * 0.5 or n.degree >= 2)
        ][:5]

        relationships: list[str] = []
        for edge in subgraph.edges[:8]:
            a = subgraph.nodes.get(edge.from_slug)
            b = subgraph.nodes.get(edge.to_slug)
            if a and b:
                relationships.append(f"{a.name} → {edge.type} → {b.name}")

        clusters = self._detect_clusters(subgraph)
        bridging = self._find_bridging(subgraph, clusters)

        confidence = min(1.0, 0.3 + len(key_concepts) * 0.1 + len(relationships) * 0.05)

        return ReasoningResult(
            key_concepts=key_concepts,
            relationships=relationships,
            bridging_concepts=bridging,
            concept_clusters=clusters,
            confidence=round(confidence, 4),
        )

    # -- Strategy 2: Pattern Matching --

    def _strategy_pattern_matching(
        self, query: str, subgraph: ConceptSubgraph, full_graph: ConceptGraph
    ) -> ReasoningResult:
        query_lower = query.lower()
        query_terms = set(re.findall(r"[一-鿿]+|[a-zA-Z]{3,}", query_lower))

        key_concepts: list[str] = []
        inferred_insights: list[str] = []
        contradictions: list[str] = []

        for slug, node in subgraph.nodes.items():
            node_text = f"{node.name} {' '.join(node.tags)}".lower()
            matches = sum(1 for t in query_terms if t in node_text)
            if matches > 0:
                key_concepts.append(node.name)

            # Check if co-occurrence exists without explicit edges
            has_explicit_edge = any(
                e.from_slug == slug or e.to_slug == slug
                for e in subgraph.edges
                if e.type == "related"
            )
            if matches > 0 and not has_explicit_edge:
                # Find other query-matched concepts this might relate to
                for other_slug, other_node in subgraph.nodes.items():
                    if other_slug == slug:
                        continue
                    other_text = f"{other_node.name} {' '.join(other_node.tags)}".lower()
                    other_matches = sum(1 for t in query_terms if t in other_text)
                    if other_matches > 0:
                        inferred_insights.append(
                            f"{node.name} 和 {other_node.name} 都与当前查询相关，可能存在隐含关联"
                        )

            # Check for contradictions (conflicting tags)
            if matches > 0:
                for other_slug, other_node in subgraph.nodes.items():
                    if other_slug == slug:
                        continue
                    conflict_tags = set(node.tags) & {f"非{t}" for t in other_node.tags}
                    if conflict_tags:
                        contradictions.append(
                            f"{node.name} 与 {other_node.name} 存在潜在矛盾: {conflict_tags}"
                        )

        confidence = min(1.0, 0.3 + len(key_concepts) * 0.1 + len(inferred_insights) * 0.05)

        return ReasoningResult(
            key_concepts=key_concepts[:5],
            inferred_insights=inferred_insights[:5],
            contradictions=contradictions[:3],
            confidence=round(confidence, 4),
        )

    # -- Strategy 3: Abstraction --

    def _strategy_abstraction(self, subgraph: ConceptSubgraph) -> ReasoningResult:
        nodes = list(subgraph.nodes.values())
        if not nodes:
            return ReasoningResult()

        clusters = self._detect_clusters(subgraph)
        insights: list[str] = []
        contradictions: list[str] = []

        for cluster in clusters:
            if len(cluster) >= 2:
                names = [subgraph.nodes[s].name for s in cluster if s in subgraph.nodes]
                tags: set[str] = set()
                for s in cluster:
                    if s in subgraph.nodes:
                        tags |= set(subgraph.nodes[s].tags)
                theme = ", ".join(sorted(tags)[:3])
                insights.append(
                    f"概念群 [{', '.join(names)}] 共享主题: {theme}"
                    if theme
                    else f"概念群 [{', '.join(names)}] 紧密关联"
                )

        # Contradictions: concepts in different clusters with conflicting tags
        for i, c1 in enumerate(clusters):
            for c2 in clusters[i + 1 :]:
                tags1: set[str] = set()
                tags2: set[str] = set()
                for s in c1:
                    if s in subgraph.nodes:
                        tags1 |= set(subgraph.nodes[s].tags)
                for s in c2:
                    if s in subgraph.nodes:
                        tags2 |= set(subgraph.nodes[s].tags)
                conflicting = {t for t in tags1 if f"非{t}" in tags2} | {
                    t for t in tags2 if f"非{t}" in tags1
                }
                if conflicting:
                    n1 = subgraph.nodes.get(c1[0], ConceptGraphNode(id="", name=c1[0], slug=c1[0]))
                    n2 = subgraph.nodes.get(c2[0], ConceptGraphNode(id="", name=c2[0], slug=c2[0]))
                    contradictions.append(
                        f"集群 {n1.name} 与 {n2.name} 存在标签冲突: {conflicting}"
                    )

        confidence = min(1.0, 0.2 + len(clusters) * 0.1 + len(insights) * 0.1)

        return ReasoningResult(
            inferred_insights=insights[:5],
            contradictions=contradictions[:3],
            concept_clusters=clusters,
            confidence=round(confidence, 4),
        )

    # -- Helpers --

    @staticmethod
    def _detect_clusters(subgraph: ConceptSubgraph) -> list[list[str]]:
        adjacency: dict[str, set[str]] = defaultdict(set)
        for edge in subgraph.edges:
            adjacency[edge.from_slug].add(edge.to_slug)
            adjacency[edge.to_slug].add(edge.from_slug)

        visited: set[str] = set()
        clusters: list[list[str]] = []

        for slug in subgraph.nodes:
            if slug in visited:
                continue
            component: list[str] = []
            stack = [slug]
            while stack:
                s = stack.pop()
                if s in visited:
                    continue
                visited.add(s)
                component.append(s)
                stack.extend(adjacency[s] - visited)
            if component:
                clusters.append(component)

        return clusters

    @staticmethod
    def _find_bridging(subgraph: ConceptSubgraph, clusters: list[list[str]]) -> list[str]:
        if len(clusters) < 2:
            return []

        bridging: list[str] = []
        for i, c1 in enumerate(clusters):
            for c2 in clusters[i + 1 :]:
                for slug in c1:
                    node = subgraph.nodes.get(slug)
                    if node is None:
                        continue
                    for other in c2:
                        if other in node.related:
                            bridging.append(node.name)
                            break

        return list(dict.fromkeys(bridging))
