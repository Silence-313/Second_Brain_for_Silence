"""Plan stage — parse intent and build execution plan."""

from typing import Any

from agent.pipeline.context import PipelineContext
from agent.pipeline.protocol import PipelineStage


class PlanStage(PipelineStage):
    name = "plan"
    priority = 5

    def __init__(
        self, planner: Any = None, tool_registry: Any = None, search_manager: Any = None
    ) -> None:  # Planner | None
        self._planner = planner
        self._tools = tool_registry
        self._search = search_manager

    async def execute(self, context: PipelineContext) -> PipelineContext:
        if self._planner is None or not context.user_input_sanitized:
            return context

        try:
            tools = self._tools.get_for_llm() if self._tools else []
            providers = self._search.list_providers() if self._search else []

            plan = await self._planner.plan(
                context.user_input_sanitized or context.user_input_raw,
                available_tools=tools,
                available_providers=providers,
                chat_history=context.chat_history or [],
            )
            return context.with_updates(execution_plan=plan)
        except Exception:
            return context
