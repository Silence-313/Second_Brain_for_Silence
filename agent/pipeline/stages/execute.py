"""Execute stage — run execution plan steps via ExecutionEngine."""

from typing import Any

from agent.pipeline.context import PipelineContext
from agent.pipeline.protocol import PipelineStage


class ExecuteStage(PipelineStage):
    name = "execute"
    priority = 6

    def __init__(self, engine: Any = None) -> None:  # ExecutionEngine | None
        self._engine = engine

    async def execute(self, context: PipelineContext) -> PipelineContext:
        if self._engine is None or context.execution_plan is None:
            return context

        try:
            result = await self._engine.execute(context.execution_plan)
            return context.with_updates(execution_result=result)
        except Exception:
            return context
