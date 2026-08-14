"""Pure scoring functions — memory decay, reinforcement, consolidation. No I/O."""

import math

from agent.models.evolution import ConsolidationResult, EvolutionSignal, ScoredMemory


def compute_decay_score(importance: float, usage_freq: int, cycles_since_access: int) -> float:
    effective_rate = 0.03 * (1 - usage_freq * 0.6)
    decay = importance * math.exp(-effective_rate * max(cycles_since_access, 0))
    return round(max(0.0, min(1.0, decay)), 4)


def compute_usefulness_score(
    access_count: int, positive_feedback: int, negative_feedback: int
) -> float:
    total = access_count + positive_feedback + negative_feedback
    if total == 0:
        return 0.5
    return round((access_count + positive_feedback * 2) / (total + 1), 4)


def reinforce(memory: ScoredMemory, signal: EvolutionSignal) -> ScoredMemory:
    amount = max(-0.05, min(0.05, signal.amount))
    new_score = max(0.0, min(1.0, memory.importance_score + amount))
    return memory.model_copy(
        update={
            "importance_score": round(new_score, 4),
            "usefulness_score": round(memory.usefulness_score + (0.01 if amount > 0 else -0.01), 4),
        }
    )


def consolidate(new_memory: ScoredMemory, existing: list[ScoredMemory]) -> ConsolidationResult:
    for ex in existing:
        similarity = _jaccard_bigrams(
            new_memory.content + " ".join(new_memory.tags),
            ex.content + " ".join(ex.tags),
        )
        if similarity > 0.85:
            return ConsolidationResult(
                merged=True, target_id=ex.id, similarity=round(similarity, 4)
            )
    return ConsolidationResult(merged=False, similarity=0.0)


def merge_memories(a: ScoredMemory, b: ScoredMemory) -> ScoredMemory:
    return ScoredMemory(
        id=a.id,
        importance_score=max(a.importance_score, b.importance_score),
        usage_frequency=max(a.usage_frequency, b.usage_frequency),
        last_access_time=max(a.last_access_time, b.last_access_time),
        decay_score=min(a.decay_score, b.decay_score),
        usefulness_score=(a.usefulness_score + b.usefulness_score) / 2,
        content=f"{a.content}; {b.content}",
        tags=list(set(a.tags + b.tags)),
    )


def apply_batch_decay(memories: list[ScoredMemory]) -> dict[str, int]:
    decayed = 0
    marked = 0
    for mem in memories:
        if mem.marked_for_removal:
            continue
        decay = compute_decay_score(mem.importance_score, mem.usage_frequency, 1)
        if decay < 0.25 and mem.usage_frequency == 0:
            marked += 1
        decayed += 1
    return {"decayed": decayed, "marked_for_removal": marked}


def _jaccard_bigrams(a: str, b: str) -> float:
    def bigrams(s: str) -> set[str]:
        return {s[i : i + 2] for i in range(len(s) - 1)} if len(s) >= 2 else set()

    ba = bigrams(a.lower())
    bb = bigrams(b.lower())
    if not ba or not bb:
        return 0.0
    return len(ba & bb) / len(ba | bb)
