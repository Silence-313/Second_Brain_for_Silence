"""Generate stage — call LLM with streaming response."""

from typing import Any

from agent.pipeline.context import PipelineContext
from agent.pipeline.protocol import PipelineStage


class GenerateStage(PipelineStage):
    name = "generate"
    priority = 8

    def __init__(
        self,
        llm_client: Any = None,  # DeepSeekLLMClient | None
        max_history: int = 10,
    ) -> None:
        self._llm = llm_client
        self._max_history = max_history

    async def execute(self, context: PipelineContext) -> PipelineContext:
        if self._llm is None:
            return context.with_updates(
                llm_response="LLM client not configured.",
                llm_response_clean="LLM client not configured.",
            )

        system_prompt = context.system_prompt or ""
        user_text = context.user_input_raw

        messages: list[dict[str, Any]] = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

        history = context.chat_history or []
        for h in history[-self._max_history * 2 :]:
            role = h.get("role", "user")
            content = h.get("text") or h.get("content", "")
            if content.strip():
                messages.append(
                    {"role": role if role in ("user", "assistant") else "user", "content": content}
                )

        messages.append({"role": "user", "content": user_text})

        try:
            response = await self._llm.complete(messages)
            content = response.get("content", "")
            return context.with_updates(
                llm_response=content,
                llm_response_clean=content,
            )
        except Exception as e:
            return context.with_error("generate", str(e)).with_updates(
                llm_response="Sorry, I encountered an error processing your request.",
                llm_response_clean="Sorry, I encountered an error processing your request.",
            )
