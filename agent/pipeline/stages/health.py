"""Health stage — periodic cognitive health check."""

from typing import Any

from agent.pipeline.context import PipelineContext
from agent.pipeline.protocol import PipelineStage


class HealthStage(PipelineStage):
    name = "health"
    priority = 12

    def __init__(
        self,
        drift_controller: Any = None,  # DriftController | None
        store: Any = None,  # MemoryStore | None
        interval: int = 15,
    ) -> None:
        self._controller = drift_controller
        self._store = store
        self._interval = interval
        self._count: int = 0

    async def execute(self, context: PipelineContext) -> PipelineContext:
        self._count += 1
        if self._count % self._interval != 0:
            return context

        if self._controller is None:
            return context

        try:
            concepts = await self._store.load_concepts() if self._store else []
            confidences = [c.confidence for c in concepts]
            _health = self._controller.compute_health(confidences, len(concepts))
        except Exception:
            pass

        return context
