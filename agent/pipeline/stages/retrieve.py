"""Retrieve stage — gather memory context: wiki, episodic, profile."""

from typing import Any

from agent.pipeline.context import PipelineContext
from agent.pipeline.protocol import PipelineStage


class RetrieveStage(PipelineStage):
    name = "retrieve"
    priority = 3

    def __init__(
        self,
        vector_store: Any = None,  # VectorStore | None
        episodic_memory: Any = None,  # EpisodicMemory | None
        user_profile: Any = None,  # UserProfile | None
    ) -> None:
        self._vector = vector_store
        self._episodic = episodic_memory
        self._profile = user_profile

    async def execute(self, context: PipelineContext) -> PipelineContext:
        query = context.user_input_sanitized or context.user_input_raw
        wiki_results: list[Any] = []
        episodic_ctx: str = ""
        profile_ctx: str = ""

        if self._vector is not None:
            try:
                wiki_results = await self._vector.search(query)
            except Exception:
                pass

        if self._episodic is not None:
            try:
                self._episodic.search(query, top_k=5)
                episodic_ctx = self._episodic.format_for_context(5)
            except Exception:
                pass

        if self._profile is not None:
            try:
                profile_ctx = self._profile.format_for_context()
            except Exception:
                pass

        memory_context = {
            "wiki_results": wiki_results,
            "episodic_context": episodic_ctx,
            "profile_context": profile_ctx,
        }
        return context.with_updates(memory_context=memory_context)
