"""Example custom tool: CalculatorTool."""

from typing import Any

from agent.models.tools import ToolResult
from agent.tools.protocol import Tool


class CalculatorTool(Tool):
    name = "calculator"
    description = "执行基本的数学计算（加减乘除、幂运算）"
    permissions = "safe"
    parameters = {
        "type": "object",
        "properties": {
            "expression": {"type": "string", "description": "数学表达式，如 2+3*4"},
        },
        "required": ["expression"],
    }

    async def execute(self, args: dict[str, Any]) -> ToolResult:
        expression = args.get("expression", "")
        try:
            # Safe eval with limited builtins
            result = eval(
                expression,
                {"__builtins__": {}},
                {
                    "abs": abs, "round": round, "min": min, "max": max,
                    "sum": sum, "pow": pow, "int": int, "float": float,
                },
            )
            return ToolResult(
                success=True,
                data={"expression": expression, "result": result},
            )
        except Exception as e:
            return ToolResult(success=False, error=str(e))
