"""Mutation queue — buffer, dedup, sort, flush state mutations."""

from typing import Any

from agent.models.mutations import MUTATION_PRIORITY, StateMutation


class MutationQueue:
    """Buffers mutations within a single interaction cycle, flushes batch to engine."""

    def __init__(self) -> None:
        self._buffer: list[StateMutation] = []
        self._cycle_id: int = 0

    def add(self, mutation: StateMutation) -> None:
        self._buffer.append(mutation)

    def add_batch(self, mutations: list[StateMutation]) -> None:
        self._buffer.extend(mutations)

    def resolve(self) -> list[StateMutation]:
        return self._deduplicate(self._sort_by_priority(self._buffer))

    async def flush(self, engine: Any) -> dict[str, Any]:  # StateMutationEngine
        resolved = self.resolve()
        raw = await engine.apply_batch(resolved)
        self._buffer.clear()
        return raw  # type: ignore[no-any-return]

    def new_cycle(self) -> None:
        self._buffer.clear()
        self._cycle_id += 1

    @property
    def size(self) -> int:
        return len(self._buffer)

    @property
    def cycle_id(self) -> int:
        return self._cycle_id

    @staticmethod
    def _sort_by_priority(mutations: list[StateMutation]) -> list[StateMutation]:
        return sorted(
            mutations,
            key=lambda m: MUTATION_PRIORITY.get(getattr(m, "type", ""), 99),
        )

    @staticmethod
    def _deduplicate(mutations: list[StateMutation]) -> list[StateMutation]:
        merged: dict[str, Any] = {}

        for m in mutations:
            mtype = getattr(m, "type", "")
            if mtype == "concept_update":
                key = getattr(m, "concept_name", "")
                existing = merged.get(f"update:{key}")
                if existing and hasattr(existing, "delta") and hasattr(m, "delta"):
                    merged[f"update:{key}"] = existing.model_copy(
                        update={
                            "delta": max(-0.05, min(0.05, existing.delta + m.delta))
                        }
                    )
                    continue
                merged[f"update:{key}"] = m
            elif mtype == "policy_update":
                key = getattr(m, "field", "")
                existing = merged.get(f"policy:{key}")
                if existing:
                    merged[f"policy:{key}"] = m  # latest wins for policy
                    continue
                merged[f"policy:{key}"] = m
            else:
                merged[f"{mtype}:{id(m)}"] = m

        return list(merged.values())
