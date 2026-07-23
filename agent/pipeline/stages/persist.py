"""Persist stage — write memory, extract concepts, save state."""

from typing import Any

from agent.pipeline.context import PipelineContext
from agent.pipeline.protocol import PipelineStage


class PersistStage(PipelineStage):
    name = "persist"
    priority = 10

    def __init__(
        self,
        memory_writer: Any = None,  # MemoryWriter | None
        profile: Any = None,  # UserProfile | None
        kb_manager: Any = None,  # KnowledgeBaseManager | None
    ) -> None:
        self._writer = memory_writer
        self._profile = profile
        self._kb = kb_manager

    async def execute(self, context: PipelineContext) -> PipelineContext:
        if self._writer is None:
            return context

        user_text = context.user_input_sanitized or context.user_input_raw
        response_text = context.llm_response_clean or ""

        try:
            from agent.memory.writer import Interaction

            interaction = Interaction(
                user_message=user_text,
                assistant_response=response_text,
                tool_used=(
                    context.router_result.tool
                    if context.router_result and hasattr(context.router_result, "tool")
                    else None
                ),
            )

            decisions = self._writer.analyze(interaction)
            await self._writer.commit(decisions, interaction)
        except Exception:
            pass

        if self._kb and user_text and response_text:
            try:
                await self._kb.append_chat_log(user_text, response_text)
            except Exception:
                pass

        return context
