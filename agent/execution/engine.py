"""Execution engine — execute plan steps sequentially/parallel, handle failures."""

import asyncio
import time
from collections import defaultdict
from typing import Any

from pydantic import BaseModel, Field

from agent.execution.fallback import FallbackAction, FallbackStrategy
from agent.execution.verifier import ResultVerifier
from agent.models.tools import ToolResult


class ExecutionResult(BaseModel, frozen=True):
    plan_id: str
    results: dict[str, ToolResult] = Field(default_factory=dict)
    failures: list[dict[str, Any]] = Field(default_factory=list)
    completed: int = 0
    failed: int = 0
    total_ms: float = 0.0


class ExecutionEngine:
    """Execute ExecutionPlan steps. Resolves dependencies, runs parallel groups."""

    def __init__(
        self,
        tool_registry: Any = None,  # ToolRegistry | None
        skill_registry: Any = None,  # SkillRegistry | None
        search_manager: Any = None,  # SearchManager | None
        fallback: FallbackStrategy | None = None,
        verifier: ResultVerifier | None = None,
        event_bus: Any = None,  # EventBus | None
    ) -> None:
        self._tools = tool_registry
        self._skills = skill_registry
        self._search = search_manager
        self._fallback = fallback or FallbackStrategy()
        self._verifier = verifier or ResultVerifier()
        self._event_bus = event_bus

    async def execute(self, plan: Any) -> ExecutionResult:  # ExecutionPlan
        start = time.monotonic()
        results: dict[str, ToolResult] = {}
        failures: list[dict[str, Any]] = []
        completed = 0
        failed = 0

        if not plan.steps:
            return ExecutionResult(
                plan_id=plan.plan_id,
                results=results,
                failures=failures,
                total_ms=round((time.monotonic() - start) * 1000, 2),
            )

        sorted_steps = self._topological_sort(plan.steps)

        if plan.strategy == "parallel" and all(s.parallel_group is not None for s in sorted_steps):
            groups = self._group_by_parallel(sorted_steps)
            for group_steps in groups:
                group_results = await self._execute_parallel(group_steps, results, failures)
                for step_id, r in group_results.items():
                    if r.success:
                        completed += 1
                    else:
                        failed += 1
                    results[step_id] = r
        else:
            for step in sorted_steps:
                for dep_id in step.depends_on:
                    if dep_id in results and not results[dep_id].success:
                        failures.append(
                            {"step": step.step_id, "error": f"dependency {dep_id} failed"}
                        )
                        failed += 1
                        results[step.step_id] = ToolResult(
                            success=False, error=f"dependency {dep_id} failed"
                        )
                        continue

                result = await self._execute_step(step)
                if result.success:
                    completed += 1
                else:
                    failed += 1
                results[step.step_id] = result

        return ExecutionResult(
            plan_id=plan.plan_id,
            results=results,
            failures=failures,
            completed=completed,
            failed=failed,
            total_ms=round((time.monotonic() - start) * 1000, 2),
        )

    async def _execute_step(self, step: Any) -> ToolResult:  # PlanStep
        capability = self._resolve_capability(step.capability_type, step.capability_name)

        for attempt in range(1, self._fallback._max_retries + 2):
            try:
                result = await asyncio.wait_for(
                    self._invoke_capability(capability, step),
                    timeout=step.timeout_ms / 1000,
                )

                verification = self._verifier.verify(result, step.capability_type)
                if verification.valid:
                    return result

                action = await self._fallback.on_failure(
                    step.step_id,
                    Exception(
                        verification.issues[0] if verification.issues else "verification failed"
                    ),
                    attempt,
                    [],
                )
                if action == FallbackAction.SKIP:
                    return ToolResult(success=False, error=str(verification.issues))

            except TimeoutError:
                action = await self._fallback.on_failure(
                    step.step_id, TimeoutError("timeout"), attempt, []
                )
                if action == FallbackAction.RETRY:
                    continue
                return ToolResult(success=False, error=f"timeout after {step.timeout_ms}ms")

            except Exception as e:
                action = await self._fallback.on_failure(
                    step.step_id, e, attempt, self._get_alternatives(step)
                )
                if action == FallbackAction.RETRY:
                    continue
                if action == FallbackAction.SWITCH_PROVIDER and self._get_alternatives(step):
                    alt = self._get_alternatives(step)[0]
                    new_step = step.model_copy(
                        update={"capability_name": alt, "step_id": f"{step.step_id}-fb"}
                    )
                    return await self._execute_step(new_step)
                return ToolResult(success=False, error=str(e))

        return ToolResult(success=False, error="max retries exceeded")

    async def _execute_parallel(
        self,
        steps: list[Any],
        results: dict[str, ToolResult],
        failures: list[dict[str, Any]],
    ) -> dict[str, ToolResult]:
        tasks = []
        for step in steps:
            deps_ok = all(
                results.get(dep_id, ToolResult(success=True)).success for dep_id in step.depends_on
            )
            if deps_ok:
                tasks.append(self._execute_step(step))
            else:
                tasks.append(
                    asyncio.sleep(0, result=ToolResult(success=False, error="dependency failed"))
                )

        step_results = await asyncio.gather(*tasks, return_exceptions=True)

        output: dict[str, ToolResult] = {}
        for step, raw in zip(steps, step_results, strict=True):
            if isinstance(raw, Exception):
                output[step.step_id] = ToolResult(success=False, error=str(raw))
            else:
                output[step.step_id] = raw  # type: ignore[assignment]
        return output

    def _resolve_capability(self, cap_type: str, name: str) -> Any:
        if cap_type == "tool" and self._tools:
            cap = self._tools.get(name)
            if cap is not None:
                return cap
        elif cap_type == "skill" and self._skills:
            return self._skills.get(name)
        elif cap_type == "search" and self._search:
            cap = self._search.get_provider(name)
            if cap is not None:
                return cap

        raise ValueError(f"Capability not found: {cap_type}/{name}")

    async def _invoke_capability(self, capability: Any, step: Any) -> ToolResult:
        cap_type = step.capability_type
        if cap_type == "search":
            results = await capability.search(step.args.get("query", ""))
            return ToolResult(
                success=True,
                data={"results": [r.model_dump(mode="json") for r in results]},
            )
        else:
            return await capability.execute(step.args)  # type: ignore[no-any-return]

    @staticmethod
    def _get_alternatives(step: Any) -> list[str]:
        return getattr(step, "fallback", None) or []

    @staticmethod
    def _topological_sort(steps: list[Any]) -> list[Any]:
        step_ids = {s.step_id for s in steps}
        in_degree: dict[str, int] = {}
        dependents: dict[str, list[str]] = defaultdict(list)

        for s in steps:
            in_degree[s.step_id] = len([d for d in s.depends_on if d in step_ids])
            for dep in s.depends_on:
                if dep in step_ids:
                    dependents[dep].append(s.step_id)

        queue = [s.step_id for s in steps if in_degree[s.step_id] == 0]
        sorted_ids: list[str] = []

        while queue:
            sid = queue.pop(0)
            sorted_ids.append(sid)
            for dep_id in dependents[sid]:
                in_degree[dep_id] -= 1
                if in_degree[dep_id] == 0:
                    queue.append(dep_id)

        id_to_step = {s.step_id: s for s in steps}
        sorted_steps = [id_to_step[sid] for sid in sorted_ids if sid in id_to_step]

        # append any remaining (cycles)
        for s in steps:
            if s.step_id not in sorted_ids:
                sorted_steps.append(s)

        return sorted_steps

    @staticmethod
    def _group_by_parallel(steps: list[Any]) -> list[list[Any]]:
        groups: dict[int, list[Any]] = defaultdict(list)
        for s in steps:
            group = s.parallel_group if s.parallel_group is not None else 0
            groups[group].append(s)
        return list(groups.values())
