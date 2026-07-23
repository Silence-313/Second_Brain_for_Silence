"""Route stage — classify user intent via keyword router."""

from typing import Any

from agent.pipeline.context import PipelineContext
from agent.pipeline.protocol import PipelineStage


class RouteStage(PipelineStage):
    name = "route"
    priority = 2

    def __init__(self, router: Any = None) -> None:  # ToolRouter | None
        self._router = router

    async def execute(self, context: PipelineContext) -> PipelineContext:
        if self._router is None or not context.user_input_sanitized:
            return context

        result = self._router.route_tool(context.user_input_sanitized)
        return context.with_updates(router_result=result)
