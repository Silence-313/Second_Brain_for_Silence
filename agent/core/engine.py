"""State mutation engine — validate, clamp, apply mutations authoritatively."""

from typing import Any

from agent.models.mutations import (
    ConceptDecayMutation,
    ConceptMergeMutation,
    ConceptUpdateMutation,
    MemoryWriteMutation,
    PolicyUpdateMutation,
    ReasoningTraceMutation,
    RelationshipMarkMutation,
    StateMutation,
)


class StateMutationEngine:
    """Authoritative validator and applier for all cognitive state changes."""

    def __init__(
        self,
        store: Any = None,  # MemoryStore | None
        episodic: Any = None,  # EpisodicMemory | None
        profile: Any = None,  # UserProfile | None
    ) -> None:
        self._store = store
        self._episodic = episodic
        self._profile = profile

    def validate(self, mutation: StateMutation) -> bool:
        if isinstance(mutation, ConceptUpdateMutation):
            return -0.05 <= mutation.delta <= 0.05 and bool(mutation.concept_name)
        if isinstance(mutation, ConceptMergeMutation):
            return bool(mutation.source_slug) and bool(mutation.target_slug)
        if isinstance(mutation, ConceptDecayMutation):
            return mutation.delta >= -0.05 and bool(mutation.concept_slug)
        if isinstance(mutation, MemoryWriteMutation):
            return bool(mutation.entry_id)
        if isinstance(mutation, PolicyUpdateMutation):
            return bool(mutation.field)
        if isinstance(mutation, ReasoningTraceMutation):
            return bool(mutation.trace_id)
        if isinstance(mutation, RelationshipMarkMutation):
            return bool(mutation.concept_a) and bool(mutation.concept_b)
        return False

    async def apply(self, mutation: StateMutation) -> bool:
        if not self.validate(mutation):
            return False

        if isinstance(mutation, ConceptUpdateMutation) and self._store:
            try:
                await self._store.update_concept_weight(mutation.concept_name, mutation.delta)
                return True
            except Exception:
                return False

        if isinstance(mutation, ConceptMergeMutation) and self._store:
            try:
                await self._store.mark_concept_relationship(
                    mutation.source_slug, mutation.target_slug, 0.85
                )
                return True
            except Exception:
                return False

        if isinstance(mutation, ConceptDecayMutation) and self._store:
            try:
                await self._store.update_concept_weight(mutation.concept_slug, mutation.delta)
                return True
            except Exception:
                return False

        if isinstance(mutation, RelationshipMarkMutation) and self._store:
            try:
                await self._store.mark_concept_relationship(
                    mutation.concept_a, mutation.concept_b, mutation.weight
                )
                return True
            except Exception:
                return False

        return False

    async def apply_batch(self, mutations: list[StateMutation]) -> dict[str, Any]:
        applied = 0
        rejected = 0
        errors: list[str] = []

        for mutation in mutations:
            try:
                if await self.apply(mutation):
                    applied += 1
                else:
                    rejected += 1
            except Exception as e:
                rejected += 1
                errors.append(str(e))

        return {"applied": applied, "rejected": rejected, "errors": errors}
