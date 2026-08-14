"""Built-in tools: todo management — get, add, stats."""

from datetime import UTC, datetime
from typing import Any

from agent.models.tools import ToolResult
from agent.tools.protocol import Tool


class _TodoStore:
    """Simple in-memory todo storage. Replaced by persistent store in production."""

    def __init__(self) -> None:
        self._todos: list[dict[str, Any]] = []

    def add(self, text: str, due: str | None = None, priority: str = "medium") -> dict[str, Any]:
        todo = {
            "id": f"todo-{len(self._todos) + 1:04d}",
            "text": text,
            "due": due,
            "priority": priority,
            "status": "pending",
            "created_at": datetime.now(UTC).isoformat(),
        }
        self._todos.append(todo)
        return todo

    def list_all(
        self, status: str | None = None, priority: str | None = None
    ) -> list[dict[str, Any]]:
        result = self._todos
        if status:
            result = [t for t in result if t["status"] == status]
        if priority:
            result = [t for t in result if t["priority"] == priority]
        return result

    def stats(self) -> dict[str, int]:
        total = len(self._todos)
        pending = sum(1 for t in self._todos if t["status"] == "pending")
        completed = sum(1 for t in self._todos if t["status"] == "completed")
        return {"total": total, "pending": pending, "completed": completed}


_store = _TodoStore()


class GetTodosTool(Tool):
    name = "get_todos"
    description = "查询待办事项列表，可按状态和优先级过滤"
    permissions = "safe"
    parameters = {
        "type": "object",
        "properties": {
            "status": {"type": "string", "enum": ["pending", "completed"]},
            "priority": {"type": "string", "enum": ["low", "medium", "high"]},
        },
    }

    async def execute(self, args: dict[str, Any]) -> ToolResult:
        todos = _store.list_all(status=args.get("status"), priority=args.get("priority"))
        return ToolResult(success=True, data={"todos": todos, "count": len(todos)})


class AddTodosTool(Tool):
    name = "add_todos"
    description = "添加新的待办事项"
    permissions = "safe"
    parameters = {
        "type": "object",
        "properties": {
            "text": {"type": "string", "description": "待办内容"},
            "due": {"type": "string", "description": "截止日期 YYYY-MM-DD"},
            "priority": {"type": "string", "enum": ["low", "medium", "high"]},
        },
        "required": ["text"],
    }

    async def execute(self, args: dict[str, Any]) -> ToolResult:
        todo = _store.add(
            text=args["text"],
            due=args.get("due"),
            priority=args.get("priority", "medium"),
        )
        return ToolResult(success=True, data={"todo": todo})


class TodoStatsTool(Tool):
    name = "get_todo_stats"
    description = "获取待办事项统计信息"
    permissions = "safe"
    parameters = {}

    async def execute(self, args: dict[str, Any]) -> ToolResult:
        stats = _store.stats()
        return ToolResult(success=True, data={"stats": stats})
