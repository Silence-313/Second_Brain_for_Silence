"""Sanitize stage — strip injection vectors, truncate overlong input."""

import re

from agent.pipeline.context import PipelineContext
from agent.pipeline.protocol import PipelineStage

_CODE_BLOCK_RE = re.compile(r"```[\s\S]*?```", re.DOTALL)
_SYSTEM_INJECT_RE = re.compile(
    r"(?:system|assistant)\s*:\s*", re.IGNORECASE
)


class SanitizeStage(PipelineStage):
    name = "sanitize"
    priority = 1

    def __init__(self, max_chars: int = 4000) -> None:
        self._max_chars = max_chars

    async def execute(self, context: PipelineContext) -> PipelineContext:
        text = context.user_input_raw

        # Strip code blocks (prevent injection via markdown)
        text = _CODE_BLOCK_RE.sub("[code removed]", text)

        # Strip system-prompt injection patterns
        text = _SYSTEM_INJECT_RE.sub("", text)

        # Truncate
        text = text[: self._max_chars].strip()

        return context.with_updates(
            user_input_sanitized=text,
        )
