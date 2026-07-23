"""Reason stage — concept graph construction and 3-strategy reasoning."""

from typing import Any

from agent.pipeline.context import PipelineContext
from agent.pipeline.protocol import PipelineStage


class ReasonStage(PipelineStage):
    name = "reason"
    priority = 4

    def __init__(
        self,
        graph_builder: Any = None,  # ConceptGraphBuilder | None
        reasoner: Any = None,  # ConceptReasoner | None
        store: Any = None,  # MemoryStore | None
    ) -> None:
        self._builder = graph_builder
        self._reasoner = reasoner
        self._store = store

    async def execute(self, context: PipelineContext) -> PipelineContext:
        if self._builder is None or self._reasoner is None or self._store is None:
            return context

        try:
            concepts = await self._store.load_concepts()
            if len(concepts) < 2:
                return context

            graph = self._builder.build_full(concepts)

            query = context.user_input_sanitized or context.user_input_raw
            seeds = self._select_seeds(query, concepts)
            subgraph = self._builder.build_subgraph(graph, seeds)

            reasoning = self._reasoner.reason(query, subgraph, graph)

            mc = context.memory_context or {}
            mc["reasoning_context"] = reasoning
            return context.with_updates(memory_context=mc)
        except Exception:
            return context

    @staticmethod
    def _select_seeds(query: str, concepts: list[Any]) -> list[str]:
        query_lower = query.lower()
        scored: list[tuple[str, float]] = []
        for c in concepts:
            score = 0.0
            for term in query_lower.split():
                if term in c.name.lower() or term in c.slug.lower():
                    score += 1.0
            if score > 0:
                scored.append((c.slug, score))
        scored.sort(key=lambda x: x[1], reverse=True)
        seeds = [s for s, _ in scored[:5]]
        return seeds if seeds else [c.slug for c in concepts[:3]]
