"""Routing data models — intent classification results and telemetry."""

from datetime import datetime

from pydantic import BaseModel, Field


class RouterResult(BaseModel, frozen=True):
    tool: str
    confidence: float = Field(default=0.5, ge=0, le=1)
    reason: str = ""


class RoutingRecord(BaseModel, frozen=True):
    query: str
    selected_tool: str
    confidence: float = Field(default=0.5, ge=0, le=1)
    execution_success: bool = False
    latency_ms: float = 0.0
    timestamp: datetime = Field(default_factory=datetime.now)


class ToolMetrics(BaseModel, frozen=True):
    tool_name: str
    success_rate: float = Field(default=0.5, ge=0, le=1)
    avg_confidence: float = Field(default=0.5, ge=0, le=1)
    context_match_score: float = Field(default=0.5, ge=0, le=1)
    selection_count: int = 0
    adaptive_threshold: float = Field(default=0.2, ge=0.1, le=0.6)
    policy_weight: float = Field(default=0.5, ge=0.1, le=1.0)
    recent_decisions: list[bool] = Field(default_factory=list)
