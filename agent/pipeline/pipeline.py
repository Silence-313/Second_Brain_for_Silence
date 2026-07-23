"""Pipeline — ordered sequence of pipeline stages."""

import time

from agent.pipeline.context import PipelineContext
from agent.pipeline.protocol import PipelineStage


class Pipeline:
    """Ordered sequence of pipeline stages. Executes in priority order."""

    def __init__(self, stages: list[PipelineStage]) -> None:
        self._stages = sorted(stages, key=lambda s: s.priority)

    async def execute(self, context: PipelineContext) -> PipelineContext:
        for stage in self._stages:
            t0 = time.monotonic()
            try:
                context = await stage.execute(context)
            except Exception as e:
                context = context.with_error(stage.name, str(e))
            finally:
                duration = (time.monotonic() - t0) * 1000
                context = context.with_timing(stage.name, duration)
        return context

    def add_stage(self, stage: PipelineStage) -> None:
        self._stages.append(stage)
        self._stages.sort(key=lambda s: s.priority)

    def remove_stage(self, name: str) -> bool:
        for i, s in enumerate(self._stages):
            if s.name == name:
                del self._stages[i]
                return True
        return False

    @property
    def stage_names(self) -> list[str]:
        return [s.name for s in self._stages]
