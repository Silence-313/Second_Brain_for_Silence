"""Tests for ExecutionEngine."""

from agent.execution.engine import ExecutionEngine
from agent.planner.plan import ExecutionPlan, PlanStep


class TestExecutionEngine:
    def test_empty_plan(self) -> None:
        engine = ExecutionEngine()

        async def run():
            plan = ExecutionPlan(plan_id="p1", steps=[])
            result = await engine.execute(plan)
            assert result.completed == 0
            assert result.failed == 0

    def test_topological_sort(self) -> None:
        engine = ExecutionEngine()
        steps = [
            PlanStep(
                step_id="s2",
                capability_type="tool",
                capability_name="test",
                priority=1,
                depends_on=["s1"],
            ),
            PlanStep(step_id="s1", capability_type="tool", capability_name="test", priority=0),
        ]
        sorted_steps = engine._topological_sort(steps)
        assert sorted_steps[0].step_id == "s1"
        assert sorted_steps[1].step_id == "s2"

    def test_topological_sort_cycle(self) -> None:
        engine = ExecutionEngine()
        steps = [
            PlanStep(
                step_id="s1", capability_type="tool", capability_name="test", depends_on=["s2"]
            ),
            PlanStep(
                step_id="s2", capability_type="tool", capability_name="test", depends_on=["s1"]
            ),
        ]
        sorted_steps = engine._topological_sort(steps)
        assert len(sorted_steps) == 2  # doesn't crash on cycle

    def test_group_by_parallel(self) -> None:
        engine = ExecutionEngine()
        steps = [
            PlanStep(step_id="s1", capability_type="tool", capability_name="a", parallel_group=1),
            PlanStep(step_id="s2", capability_type="tool", capability_name="b", parallel_group=1),
            PlanStep(step_id="s3", capability_type="tool", capability_name="c", parallel_group=2),
        ]
        groups = engine._group_by_parallel(steps)
        assert len(groups) == 2  # two distinct groups
