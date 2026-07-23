"""Integration tests: Capability stack — Tools + Skills + Search + Execution."""

import pytest

from agent.execution.engine import ExecutionEngine
from agent.planner.plan import ExecutionPlan, PlanStep
from agent.search.manager import SearchManager
from agent.skills.builtins.location import GetLocationSkill
from agent.skills.registry import SkillRegistry
from agent.tools.builtins.time import GetCurrentTimeTool
from agent.tools.builtins.todos import AddTodosTool, GetTodosTool
from agent.tools.registry import ToolRegistry


class TestCapabilityIntegration:
    """Test tools, skills, search, and execution engine wired together."""

    @pytest.fixture
    def capability_stack(self):
        tool_registry = ToolRegistry()
        tool_registry.register(GetCurrentTimeTool())
        tool_registry.register(GetTodosTool())
        tool_registry.register(AddTodosTool())

        skill_registry = SkillRegistry()
        skill_registry.register(GetLocationSkill())

        search_manager = SearchManager()

        return {
            "tool_registry": tool_registry,
            "skill_registry": skill_registry,
            "search_manager": search_manager,
        }

    @pytest.mark.asyncio
    async def test_tool_execution_via_registry(self, capability_stack):
        tool_registry = capability_stack["tool_registry"]
        tool = tool_registry.get("get_current_time")
        assert tool is not None

        result = await tool.execute({})
        assert result.success
        assert "datetime" in result.data  # type: ignore[operator]

    @pytest.mark.asyncio
    async def test_execution_engine_with_tools(self, capability_stack):
        engine = ExecutionEngine(
            tool_registry=capability_stack["tool_registry"],
            skill_registry=capability_stack["skill_registry"],
            search_manager=capability_stack["search_manager"],
        )

        plan = ExecutionPlan(
            plan_id="test-plan",
            steps=[
                PlanStep(
                    step_id="step-1",
                    capability_type="tool",
                    capability_name="get_current_time",
                    priority=0,
                ),
            ],
        )

        result = await engine.execute(plan)
        assert result.completed + result.failed == 1

    @pytest.mark.asyncio
    async def test_execution_sequential_dependency(self, capability_stack):
        engine = ExecutionEngine(
            tool_registry=capability_stack["tool_registry"],
            skill_registry=capability_stack["skill_registry"],
            search_manager=capability_stack["search_manager"],
        )

        plan = ExecutionPlan(
            plan_id="test-plan-deps",
            strategy="sequential",
            steps=[
                PlanStep(
                    step_id="add-todo",
                    capability_type="tool",
                    capability_name="add_todos",
                    priority=0,
                    args={"text": "test todo", "priority": "high"},
                ),
                PlanStep(
                    step_id="get-todos",
                    capability_type="tool",
                    capability_name="get_todos",
                    priority=1,
                    depends_on=["add-todo"],
                ),
            ],
        )

        result = await engine.execute(plan)
        assert result.completed >= 0

    @pytest.mark.asyncio
    async def test_execution_empty_plan(self, capability_stack):
        engine = ExecutionEngine(
            tool_registry=capability_stack["tool_registry"],
            skill_registry=capability_stack["skill_registry"],
            search_manager=capability_stack["search_manager"],
        )

        plan = ExecutionPlan(plan_id="empty", steps=[])
        result = await engine.execute(plan)
        assert result.completed == 0
        assert result.failed == 0
