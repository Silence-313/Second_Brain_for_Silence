"""Learn stage — record telemetry, RAG feedback, trigger evolution cycles."""

from typing import Any

from agent.pipeline.context import PipelineContext
from agent.pipeline.protocol import PipelineStage


class LearnStage(PipelineStage):
    name = "learn"
    priority = 11

    def __init__(
        self,
        router_telemetry: Any = None,  # RouterTelemetry | None
        rag_feedback: Any = None,  # RagFeedback | None
        feedback_processor: Any = None,  # FeedbackProcessor | None
        memory_evolution: Any = None,  # MemoryEvolution | None
        concept_evolver: Any = None,  # ConceptEvolver | None
        kb_manager: Any = None,  # KnowledgeBaseManager | None
        kb_maintain_interval: int = 5,
        llm_client: Any = None,
    ) -> None:
        self._telemetry = router_telemetry
        self._rag = rag_feedback
        self._feedback = feedback_processor
        self._mem_evolution = memory_evolution
        self._concept_evolver = concept_evolver
        self._kb = kb_manager
        self._kb_interval = kb_maintain_interval
        self._llm = llm_client
        self._interaction_count: int = 0

    async def execute(self, context: PipelineContext) -> PipelineContext:
        self._interaction_count += 1

        # Router telemetry
        if self._telemetry and context.router_result:
            try:
                from agent.models.routing import RoutingRecord

                self._telemetry.record_routing(
                    RoutingRecord(
                        query=context.user_input_raw,
                        selected_tool=(
                            context.router_result.tool
                            if hasattr(context.router_result, "tool")
                            else "unknown"
                        ),
                        confidence=(
                            context.router_result.confidence
                            if hasattr(context.router_result, "confidence")
                            else 0.5
                        ),
                        execution_success=context.llm_response_clean is not None,
                    )
                )
            except Exception:
                pass

        # RAG feedback
        if self._rag:
            try:
                from agent.models.retrieval import RetrievalRecord

                mc = context.memory_context or {}
                wiki = mc.get("wiki_results", [])
                self._rag.record_retrieval(
                    RetrievalRecord(
                        query=context.user_input_raw,
                        retrieved_docs=[
                            r.source_path if hasattr(r, "source_path") else "" for r in wiki
                        ],
                        used_docs=[],
                        answer_quality=0.5,
                    )
                )
            except Exception:
                pass

        # KB maintenance
        if self._interaction_count % self._kb_interval == 0 and self._kb:
            try:
                from agent.knowledge.tools import MaintainKBTool

                tool = MaintainKBTool(kb_manager=self._kb, llm_client=self._llm)
                await tool.execute({})
            except Exception:
                pass

        # Evolution cycles
        if self._interaction_count % 10 == 0 and self._mem_evolution:
            try:
                self._mem_evolution.run_cycle()
            except Exception:
                pass

        if self._interaction_count % 20 == 0 and self._concept_evolver:
            try:
                await self._concept_evolver.evolve({})
            except Exception:
                pass

        return context
