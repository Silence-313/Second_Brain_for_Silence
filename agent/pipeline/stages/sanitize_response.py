"""Sanitize response stage — strip leaked tool call text from LLM output."""

import re

from agent.pipeline.context import PipelineContext
from agent.pipeline.protocol import PipelineStage

_DSML_RE = re.compile(r"<\|dsml\|[^|]*\|>", re.IGNORECASE)
_INVOKE_RE = re.compile(r"<invoke[^>]*>.*?</invoke>", re.DOTALL | re.IGNORECASE)
_TOOL_CALLS_RE = re.compile(r"tool_calls\s*:\s*\[.*?\]", re.DOTALL)


class ResponseSanitizeStage(PipelineStage):
    name = "sanitize_response"
    priority = 9

    async def execute(self, context: PipelineContext) -> PipelineContext:
        text = context.llm_response
        if not text:
            return context

        stripped = 0
        for pattern in [_DSML_RE, _INVOKE_RE, _TOOL_CALLS_RE]:
            new_text = pattern.sub("", text)
            if len(new_text) < len(text):
                stripped += 1
            text = new_text

        return context.with_updates(llm_response_clean=text.strip())
