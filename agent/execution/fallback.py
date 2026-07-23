"""Fallback strategy — per-step failure handling with retry, switch, abort."""

import enum

from agent.models.tools import ToolResult


class FallbackAction(enum.Enum):
    RETRY = "retry"
    SWITCH_PROVIDER = "switch_provider"
    SKIP = "skip"
    ABORT = "abort"
    PARTIAL = "partial"


class FallbackStrategy:
    """Determine next action when a step fails."""

    def __init__(
        self,
        max_retries: int = 2,
        degrade_policy: str = "best_available",
    ) -> None:
        self._max_retries = max_retries
        self._degrade_policy = degrade_policy

    async def on_failure(
        self,
        step_id: str,
        error: Exception,
        attempt: int,
        available_alternatives: list[str],
    ) -> FallbackAction:
        if attempt < self._max_retries:
            return FallbackAction.RETRY

        if available_alternatives:
            return FallbackAction.SWITCH_PROVIDER

        if self._degrade_policy == "partial_results":
            return FallbackAction.PARTIAL
        elif self._degrade_policy == "fail_fast":
            return FallbackAction.ABORT

        return FallbackAction.SKIP

    @staticmethod
    def wrap_error_result(error: str) -> ToolResult:
        return ToolResult(success=False, error=error)
