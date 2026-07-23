"""Skill data models — definitions, results, execution records."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class SkillDefinition(BaseModel, frozen=True):
    name: str
    description: str
    permissions: str = "safe"


class SkillResult(BaseModel, frozen=True):
    success: bool
    data: Any = None
    error: str | None = None


class SkillExecutionRecord(BaseModel, frozen=True):
    skill_name: str
    args: dict[str, Any] = Field(default_factory=dict)
    result: SkillResult | None = None
    success: bool = False
    timestamp: datetime = Field(default_factory=datetime.now)
    latency_ms: float = 0.0


class SkillInfo(BaseModel, frozen=True):
    name: str
    description: str
    permissions: str = "safe"
