"""Planner data models — Intent, ExecutionPlan, PlanStep."""

from datetime import UTC, datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class Intent(BaseModel, frozen=True):
    action: Literal["search", "read", "write", "analyze", "summarize", "chat", "maintain", "execute"] = "chat"
    domain: Literal["code", "video", "paper", "local_file", "knowledge", "general"] = "general"
    platform: Literal[
        "bilibili", "github", "arxiv", "obsidian", "local", "web", "none"
    ] = "none"
    confidence: float = Field(default=0.5, ge=0, le=1)
    query: str = ""


class FallbackStrategy(BaseModel, frozen=True):
    max_retries: int = 2
    alternative_providers: list[str] = Field(default_factory=list)
    degrade_policy: Literal["best_available", "fail_fast", "partial_results"] = "best_available"


class PlanStep(BaseModel, frozen=True):
    step_id: str
    capability_type: Literal["tool", "skill", "search"]
    capability_name: str
    args: dict[str, Any] = Field(default_factory=dict)
    priority: int = 0
    parallel_group: int | None = None
    depends_on: list[str] = Field(default_factory=list)
    timeout_ms: int = 30_000


class ExecutionPlan(BaseModel, frozen=True):
    plan_id: str
    steps: list[PlanStep] = Field(default_factory=list)
    strategy: Literal["sequential", "parallel", "mixed"] = "sequential"
    fallback: FallbackStrategy = Field(default_factory=FallbackStrategy)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
