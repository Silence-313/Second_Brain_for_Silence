"""Tool data models — definitions, results, call records."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class ToolDefinition(BaseModel, frozen=True):
    name: str
    description: str
    parameters: dict[str, Any] = Field(default_factory=dict)


class ToolResult(BaseModel, frozen=True):
    success: bool
    data: Any = None
    error: str | None = None
    latency_ms: float = 0.0


class ToolCallRecord(BaseModel, frozen=True):
    tool_name: str
    args: dict[str, Any] = Field(default_factory=dict)
    result: ToolResult | None = None
    success: bool = False
    timestamp: datetime = Field(default_factory=datetime.now)
    latency_ms: float = 0.0


class ToolInfo(BaseModel, frozen=True):
    name: str
    description: str
    permissions: str = "safe"
