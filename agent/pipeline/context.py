"""Pipeline context — immutable state carrier through pipeline stages."""

from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field


class StageError(BaseModel, frozen=True):
    stage: str = ""
    error: str = ""


class PipelineContext(BaseModel, frozen=True):
    """Immutable context carried through the pipeline. Each stage returns a new instance."""

    session_id: str = ""
    user_input_raw: str = ""
    user_input_sanitized: str | None = None
    chat_history: list[dict[str, str]] = Field(default_factory=list)
    router_result: Any = None  # RouterResult | None
    memory_context: Any = None  # MemoryContext | None
    execution_plan: Any = None  # ExecutionPlan | None
    execution_result: Any = None  # ExecutionResult | None
    system_prompt: str | None = None
    llm_response: str | None = None
    llm_response_clean: str | None = None
    errors: list[StageError] = Field(default_factory=list)
    stage_timings: dict[str, float] = Field(default_factory=dict)
    started_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    def with_updates(self, **kwargs: Any) -> "PipelineContext":
        return self.model_copy(update=kwargs)

    def with_error(self, stage: str, error: str) -> "PipelineContext":
        errs = [*self.errors, StageError(stage=stage, error=error)]
        return self.model_copy(update={"errors": errs})

    def with_timing(self, stage: str, duration_ms: float) -> "PipelineContext":
        timings = dict(self.stage_timings)
        timings[stage] = round(duration_ms, 2)
        return self.model_copy(update={"stage_timings": timings})
