"""Built-in tool: get current time."""

from datetime import UTC, datetime
from typing import Any

from agent.models.tools import ToolResult
from agent.tools.protocol import Tool


class GetCurrentTimeTool(Tool):
    name = "get_current_time"
    description = "获取当前日期和时间"
    permissions = "safe"
    parameters = {
        "type": "object",
        "properties": {
            "timezone": {
                "type": "string",
                "description": "时区，如 Asia/Shanghai",
            }
        },
    }

    async def execute(self, args: dict[str, Any]) -> ToolResult:
        now = datetime.now(UTC)
        data = {
            "datetime": now.isoformat(),
            "date": now.strftime("%Y-%m-%d"),
            "time": now.strftime("%H:%M:%S"),
            "weekday": now.strftime("%A"),
            "timestamp_ms": int(now.timestamp() * 1000),
        }
        return ToolResult(success=True, data=data, latency_ms=0.0)
