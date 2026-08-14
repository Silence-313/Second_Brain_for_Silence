"""Planner — orchestrate Intent parsing → Execution planning."""

import uuid
from typing import Any, Literal

from agent.planner.intent import IntentParser
from agent.planner.plan import ExecutionPlan, FallbackStrategy, Intent, PlanStep


class Planner:
    """Orchestrate Intent parsing and Execution plan building."""

    def __init__(
        self,
        intent_parser: IntentParser | None = None,
    ) -> None:
        self._intent_parser = intent_parser or IntentParser()

    async def plan(
        self,
        query: str,
        context: Any = None,  # MemoryContext | None
        *,
        available_tools: list[dict[str, Any]] | None = None,
        available_skills: list[dict[str, Any]] | None = None,
        available_providers: list[dict[str, Any]] | None = None,
        chat_history: list[dict[str, str]] | None = None,
    ) -> ExecutionPlan:
        intent = self._intent_parser.parse(query, context)
        plan_id = f"plan-{uuid.uuid4().hex[:12]}"

        # Short follow-up: "搜"/"链接"/"搜一下" → reuse last search query from history
        if len(query.strip()) <= 5 and intent.action == "search" and chat_history:
            for h in reversed(chat_history):
                user_text = h.get("text") or h.get("content", "")
                if len(user_text) > 10 and any(kw in user_text for kw in ("搜", "找", "查")):
                    intent = intent.model_copy(update={"query": user_text})
                    break
        steps: list[PlanStep] = []
        strategy: Literal["sequential", "parallel", "mixed"] = "sequential"

        if intent.action == "search":
            steps, strategy = self._build_search_plan(intent, available_providers or [])
        elif intent.action == "read":
            steps = self._build_read_plan(intent, available_tools or [])
        elif intent.action == "write":
            steps = self._build_write_plan(intent, available_tools or [])
        elif intent.action == "analyze":
            steps = self._build_analyze_plan(intent, query)
        elif intent.action == "maintain":
            steps = self._build_maintain_plan(intent)
        elif intent.action in ("chat", "summarize"):
            steps = []

        return ExecutionPlan(
            plan_id=plan_id,
            steps=steps,
            strategy=strategy,
            fallback=FallbackStrategy(),
        )

    # -- Private plan builders --

    def _build_search_plan(
        self, intent: Intent, providers: list[dict[str, Any]]
    ) -> tuple[list[PlanStep], Literal["sequential", "parallel", "mixed"]]:
        matching = [
            p
            for p in providers
            if intent.platform in (p.get("platforms") or []) or p.get("domain") == intent.domain
        ]
        if not matching:
            # Fallback: try any provider whose domain or platforms include "web"
            matching = [
                p
                for p in providers
                if "web" in (p.get("platforms") or []) or p.get("domain") == "web"
            ]
        if not matching:
            return [], "sequential"

        if len(matching) == 1:
            p = matching[0]
            return [
                PlanStep(
                    step_id="search-1",
                    capability_type="search",
                    capability_name=p.get("name", ""),
                    priority=0,
                    timeout_ms=15_000,
                    args={"query": intent.query or ""},
                )
            ], "sequential"

        steps = [
            PlanStep(
                step_id=f"search-{i}",
                capability_type="search",
                capability_name=p.get("name", ""),
                priority=0,
                parallel_group=1 if i > 0 else 1,
                timeout_ms=15_000,
                args={"query": intent.query or ""},
            )
            for i, p in enumerate(matching)
        ]
        return steps, "parallel" if len(steps) > 1 else "sequential"

    def _build_read_plan(self, intent: Intent, tools: list[dict[str, Any]]) -> list[PlanStep]:
        tool_names = [t.get("name", "") for t in tools]

        if "read_wiki_file" in tool_names and intent.platform == "obsidian":
            return [
                PlanStep(
                    step_id="read-1",
                    capability_type="tool",
                    capability_name="read_wiki_file",
                    priority=0,
                )
            ]
        if "read_local_file" in tool_names and intent.platform == "local":
            return [
                PlanStep(
                    step_id="read-1",
                    capability_type="skill",
                    capability_name="read_local_file",
                    priority=0,
                )
            ]
        return []

    def _build_write_plan(self, intent: Intent, tools: list[dict[str, Any]]) -> list[PlanStep]:
        tool_names = [t.get("name", "") for t in tools]

        if "write_wiki_file" in tool_names and intent.domain == "code":
            return [
                PlanStep(
                    step_id="write-1",
                    capability_type="tool",
                    capability_name="write_wiki_file",
                    priority=0,
                )
            ]
        return []

    def _build_maintain_plan(self, intent: Intent) -> list[PlanStep]:
        return [
            PlanStep(
                step_id="maintain-1",
                capability_type="tool",
                capability_name="kb_maintain",
                priority=0,
                timeout_ms=60_000,
            ),
        ]

    def _build_analyze_plan(self, intent: Intent, query: str) -> list[PlanStep]:
        return [
            PlanStep(
                step_id="analyze-1",
                capability_type="tool",
                capability_name="search_wiki",
                priority=0,
                args={"query": intent.query or query},
            ),
            PlanStep(
                step_id="analyze-2",
                capability_type="tool",
                capability_name="web_search",
                priority=1,
                depends_on=["analyze-1"],
                args={"query": intent.query or query, "num_results": 5},
            ),
        ]
