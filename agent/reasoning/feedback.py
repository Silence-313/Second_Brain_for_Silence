"""Feedback processor — self-improving cognitive feedback loop after reasoning."""

from datetime import UTC, datetime
from typing import Any

from agent.models.policy import CognitivePolicy
from agent.models.reasoning import ReasoningResult, ReasoningTrace


class FeedbackProcessor:
    """Stores reasoning traces, reinforces concept weights, tracks strategy outcomes."""

    def __init__(
        self,
        store: Any = None,  # MemoryStore | None
        drift_controller: Any = None,  # DriftController | None
        mutation_queue: Any = None,  # MutationQueue | None
    ) -> None:
        self._store = store
        self._controller = drift_controller
        self._mutation_queue = mutation_queue
        self._concept_usage: dict[str, int] = {}
        self._insight_frequency: dict[str, int] = {}
        self._strategy_outcomes: dict[str, int] = {"traversal": 0, "pattern": 0, "abstraction": 0}
        self._cycles_run: int = 0
        self._contradictions_detected: int = 0
        self._traces_stored: int = 0
        self._concepts_reinforced: int = 0
        self._insights_reinforced: int = 0
        self._policy_updates: int = 0

    async def process(self, reasoning: ReasoningResult, query: str) -> None:
        trace = ReasoningTrace(
            id=f"trace-{datetime.now(UTC).strftime('%Y%m%d%H%M%S')}-{self._cycles_run}",
            query=query,
            key_concepts=reasoning.key_concepts,
            insights=reasoning.inferred_insights,
            confidence=reasoning.confidence,
            strategies_used=["traversal", "pattern", "abstraction"],
            timestamp=datetime.now(UTC),
        )

        # Store trace
        if self._store is not None:
            try:
                await self._store.save_reasoning_trace(trace)
                self._traces_stored += 1
            except Exception:
                pass

        # Track concept usage
        for concept in reasoning.key_concepts:
            self._concept_usage[concept] = self._concept_usage.get(concept, 0) + 1

        # Track insight frequency for cumulative learning
        for insight in reasoning.inferred_insights:
            self._insight_frequency[insight] = self._insight_frequency.get(insight, 0) + 1

        # Track contradictions
        if reasoning.contradictions:
            self._contradictions_detected += len(reasoning.contradictions)

        # Reinforce concept weights if memory store available
        if self._store is not None and reasoning.key_concepts:
            for concept_slug in self._key_concepts_to_slugs(reasoning.key_concepts):
                try:
                    delta = 0.02 if concept_slug in reasoning.key_concepts else 0.0
                    if delta != 0.0:
                        await self._store.update_concept_weight(concept_slug, delta)
                        self._concepts_reinforced += 1
                except Exception:
                    pass

        # Track strategy outcomes
        if reasoning.confidence > 0.5:
            self._strategy_outcomes["traversal"] += 1
        if reasoning.inferred_insights:
            self._strategy_outcomes["pattern"] += 1
        if reasoning.concept_clusters:
            self._strategy_outcomes["abstraction"] += 1

        self._cycles_run += 1

        # Periodic policy update
        if self._cycles_run % 10 == 0 and self._controller is not None:
            self._update_policy()

    async def load_policy(self) -> CognitivePolicy | None:
        if self._store is not None:
            try:
                return await self._store.load_policy()  # type: ignore[no-any-return]
            except Exception:
                pass
        return None

    def get_usage_stats(self) -> dict[str, int]:
        return dict(self._concept_usage)

    def get_stats(self) -> dict[str, Any]:
        return {
            "traces_stored": self._traces_stored,
            "concepts_reinforced": self._concepts_reinforced,
            "insights_reinforced": self._insights_reinforced,
            "contradictions_detected": self._contradictions_detected,
            "policy_updates": self._policy_updates,
            "cycles_run": self._cycles_run,
            "strategy_outcomes": dict(self._strategy_outcomes),
        }

    @property
    def controller(self) -> Any:  # DriftController | None
        return self._controller

    def _update_policy(self) -> None:
        if self._controller is None:
            return

        total = sum(self._strategy_outcomes.values()) or 1
        for strategy in ["traversal", "pattern", "abstraction"]:
            success_rate = self._strategy_outcomes.get(strategy, 0) / total
            delta = (success_rate - 0.33) * 0.05
            try:
                self._controller.adjust_strategy_weight(strategy, delta)
            except Exception:
                pass

        self._policy_updates += 1

    @staticmethod
    def _key_concepts_to_slugs(concepts: list[str]) -> list[str]:
        return [c.lower().replace(" ", "-") for c in concepts]
