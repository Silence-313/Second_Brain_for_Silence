"""Execution tracer — audit trail for debugging and analysis."""

from datetime import UTC, datetime

from pydantic import BaseModel, Field


class TraceRecord(BaseModel, frozen=True):
    session_id: str = ""
    user_input: str = ""
    response: str = ""
    stage_timings: dict[str, float] = Field(default_factory=dict)
    errors: list[str] = Field(default_factory=list)
    duration_ms: float = 0.0
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))


class ExecutionTracer:
    """Record complete execution trace for audit/debug."""

    def __init__(self, max_traces: int = 100) -> None:
        self._traces: dict[str, TraceRecord] = {}
        self._max_traces = max_traces

    async def trace_interaction(
        self,
        session_id: str,
        user_input: str,
        response: str,
        stage_timings: dict[str, float],
        errors: list[str],
        duration_ms: float,
    ) -> TraceRecord:
        record = TraceRecord(
            session_id=session_id,
            user_input=user_input[:500],
            response=response[:500],
            stage_timings=stage_timings,
            errors=errors,
            duration_ms=duration_ms,
        )
        self._traces[session_id] = record

        if len(self._traces) > self._max_traces:
            oldest = min(self._traces, key=lambda k: self._traces[k].timestamp)
            del self._traces[oldest]

        return record

    def get_trace(self, session_id: str) -> TraceRecord | None:
        return self._traces.get(session_id)

    def list_recent(self, limit: int = 10) -> list[TraceRecord]:
        sorted_traces = sorted(
            self._traces.values(),
            key=lambda t: t.timestamp,
            reverse=True,
        )
        return sorted_traces[:limit]
