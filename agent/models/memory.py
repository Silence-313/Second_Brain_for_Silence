"""Memory data models — Episodes, WorkingMemory, UserProfile, ToolUsage."""

from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel, Field


class WorkingMemoryEntry(BaseModel, frozen=True):
    role: Literal["user", "assistant", "system"]
    content: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))


class Episode(BaseModel, frozen=True):
    id: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    type: Literal["event", "goal", "decision", "milestone", "question"]
    summary: str
    detail: str = ""
    importance: float = Field(default=0.5, ge=0, le=1)
    tags: list[str] = Field(default_factory=list)
    related_files: list[str] = Field(default_factory=list)
    importance_score: float = Field(default=0.5, ge=0, le=1)
    usage_frequency: int = 0
    last_access_time: datetime = Field(default_factory=lambda: datetime.now(UTC))
    decay_score: float = Field(default=1.0, ge=0, le=1)
    usefulness_score: float = Field(default=0.5, ge=0, le=1)
    marked_for_removal: bool = False


class UserProfileData(BaseModel, frozen=True):
    name: str = ""
    preferred_name: str = ""
    role: str = ""
    timezone: str = ""
    language: str = ""
    interests: list[str] = Field(default_factory=list)
    expertise: list[str] = Field(default_factory=list)
    work_habits: list[str] = Field(default_factory=list)
    active_projects: list[str] = Field(default_factory=list)
    common_tools: list[str] = Field(default_factory=list)
    response_style: Literal["concise", "detailed", "casual"] = "concise"
    preferred_format: Literal["bullet", "paragraph", "mixed"] = "mixed"
    current_focus: list[str] = Field(default_factory=list)
    long_term_goals: list[str] = Field(default_factory=list)
    last_updated: datetime = Field(default_factory=datetime.now)
    confidence_scores: dict[str, float] = Field(default_factory=dict)


class ToolUsageRecord(BaseModel, frozen=True):
    tool_name: str
    call_count: int = 0
    success_count: int = 0
    failure_count: int = 0
    top_query_patterns: list[str] = Field(default_factory=list)
    pattern_counts: dict[str, int] = Field(default_factory=dict)
    avg_response_quality: float = 0.0
    avg_latency_ms: float = 0.0
    first_used: datetime = Field(default_factory=datetime.now)
    last_used: datetime = Field(default_factory=datetime.now)
    context_effectiveness: dict[str, dict[str, int | float]] = Field(default_factory=dict)


class MemoryWriteDecision(BaseModel, frozen=True):
    type: Literal["profile", "episodic", "semantic", "tool"]
    importance: float = Field(default=0.5, ge=0, le=1)
    action: Literal["append", "ignore", "merge"]
    target_field: str | None = None
    detected_value: str | None = None
    confidence: float = Field(default=0.5, ge=0, le=1)
    reason: str = ""
