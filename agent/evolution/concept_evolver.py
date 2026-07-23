"""Concept evolver — merge, split, decay concept evolution cycles."""

from typing import Any

from agent.models.concepts import Concept
from agent.models.evolution import (
    DecayResult,
    EvolutionResult,
    MergeCandidate,
    SplitCandidate,
)


class ConceptEvolver:
    """Lightweight concept evolution engine. Runs every ~20 interactions."""

    def __init__(
        self,
        store: Any = None,  # MemoryStore | None
        mutation_queue: Any = None,  # MutationQueue | None
    ) -> None:
        self._store = store
        self._mutation_queue = mutation_queue

    async def evolve(
        self, usage_counts: dict[str, int] | None = None
    ) -> EvolutionResult:
        usage = usage_counts or {}

        concepts = await self._load_concepts()
        if not concepts:
            return EvolutionResult()

        merges = self._detect_merges(concepts)
        splits = self._detect_splits(concepts)
        decays = self._apply_decay(concepts, usage)

        await self._apply_merges(merges)
        await self._apply_split_marks(splits)

        return EvolutionResult(
            merges_applied=len([m for m in merges if m.similarity >= 0.85]),
            splits_marked=len(splits),
            decayed=len(decays),
        )

    async def _load_concepts(self) -> list[Concept]:
        if self._store is None:
            return []
        try:
            return await self._store.load_concepts()  # type: ignore[no-any-return]
        except Exception:
            return []

    def _detect_merges(self, concepts: list[Concept]) -> list[MergeCandidate]:
        candidates: list[MergeCandidate] = []
        for i, a in enumerate(concepts):
            for b in concepts[i + 1 :]:
                shared = set(a.source_episodes) & set(b.source_episodes)
                if len(shared) >= 2:
                    min_sources = min(len(a.source_episodes), len(b.source_episodes))
                    ratio = len(shared) / max(1, min_sources)
                    if ratio >= 0.7:
                        candidates.append(
                            MergeCandidate(
                                source_slug=a.slug,
                                target_slug=b.slug,
                                similarity=round(ratio, 4),
                                shared_episodes=list(shared),
                            )
                        )

                shared_tags = set(a.tags) & set(b.tags)
                tag_overlap = len(shared_tags) / max(1, len(a.tags), len(b.tags))
                if tag_overlap >= 0.7 and len(shared) >= 1:
                    candidates.append(
                        MergeCandidate(
                            source_slug=a.slug,
                            target_slug=b.slug,
                            similarity=round(tag_overlap, 4),
                            shared_episodes=list(shared),
                        )
                    )

        return candidates

    def _detect_splits(self, concepts: list[Concept]) -> list[SplitCandidate]:
        candidates: list[SplitCandidate] = []
        for c in concepts:
            if len(c.related) < 2:
                continue

            groups: list[set[str]] = []
            for rel_slug in c.related:
                rel_concept = next((x for x in concepts if x.slug == rel_slug), None)
                if rel_concept is None:
                    continue
                rel_tags = set(rel_concept.tags)
                placed = False
                for group in groups:
                    if group & rel_tags:
                        group |= rel_tags
                        placed = True
                        break
                if not placed:
                    groups.append(rel_tags)

            if len(groups) >= 2:
                min_overlap = min(
                    len(g1 & g2) / max(1, len(g1 | g2))
                    for i, g1 in enumerate(groups)
                    for g2 in groups[i + 1 :]
                )
                if min_overlap < 0.3:
                    candidates.append(
                        SplitCandidate(
                            concept_slug=c.slug,
                            conflicting_groups=[list(g) for g in groups],
                        )
                    )

        return candidates

    def _apply_decay(
        self, concepts: list[Concept], usage_counts: dict[str, int]
    ) -> list[DecayResult]:
        results: list[DecayResult] = []
        for c in concepts:
            if c.slug not in usage_counts:
                new_conf = max(0.15, c.confidence - 0.05)
                results.append(
                    DecayResult(
                        slug=c.slug,
                        old_confidence=c.confidence,
                        new_confidence=round(new_conf, 4),
                    )
                )
        return results

    async def _apply_merges(self, candidates: list[MergeCandidate]) -> None:
        for candidate in candidates:
            if candidate.similarity >= 0.85 and self._mutation_queue is not None:
                self._mutation_queue.add(
                    type="concept_merge",
                    source_slug=candidate.source_slug,
                    target_slug=candidate.target_slug,
                )

            if self._store is not None:
                try:
                    await self._store.mark_concept_relationship(
                        candidate.source_slug,
                        candidate.target_slug,
                        candidate.similarity,
                    )
                except Exception:
                    pass

    async def _apply_split_marks(self, candidates: list[SplitCandidate]) -> None:
        if self._mutation_queue is not None and candidates:
            pass  # Splits are soft-annotated, not auto-applied
