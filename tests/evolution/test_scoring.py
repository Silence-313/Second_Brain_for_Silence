"""Tests for evolution scoring functions."""


from agent.evolution.scoring import (
    apply_batch_decay,
    compute_decay_score,
    compute_usefulness_score,
    consolidate,
    merge_memories,
    reinforce,
)
from agent.models.evolution import EvolutionSignal, ScoredMemory


class TestComputeDecayScore:
    def test_recently_accessed(self) -> None:
        score = compute_decay_score(1.0, 0, 0)
        assert score == 1.0

    def test_old_unused(self) -> None:
        score = compute_decay_score(1.0, 0, 14)
        assert score < 0.8

    def test_high_usage_dampens_decay(self) -> None:
        score_no_use = compute_decay_score(1.0, 0, 10)
        score_high_use = compute_decay_score(1.0, 5, 10)
        assert score_high_use > score_no_use


class TestComputeUsefulnessScore:
    def test_no_feedback(self) -> None:
        score = compute_usefulness_score(0, 0, 0)
        assert score == 0.5

    def test_positive_feedback(self) -> None:
        score = compute_usefulness_score(1, 2, 0)
        assert score > 0.5


class TestReinforce:
    def test_positive(self) -> None:
        mem = ScoredMemory(id="ep-1", importance_score=0.5)
        signal = EvolutionSignal(type="positive_feedback", amount=0.05)
        result = reinforce(mem, signal)
        assert result.importance_score == 0.55

    def test_clamp(self) -> None:
        mem = ScoredMemory(id="ep-1", importance_score=0.99)
        signal = EvolutionSignal(type="positive_feedback", amount=0.1)
        result = reinforce(mem, signal)
        assert result.importance_score == 1.0


class TestConsolidate:
    def test_high_similarity_merge(self) -> None:
        existing = [ScoredMemory(id="ep-2", content="python programming is great")]
        new_mem = ScoredMemory(id="ep-1", content="python programming is great")
        result = consolidate(new_mem, existing)
        assert result.merged
        assert result.target_id == "ep-2"

    def test_low_similarity_no_merge(self) -> None:
        existing = [ScoredMemory(id="ep-2", content="python programming")]
        new_mem = ScoredMemory(id="ep-1", content="rust language")
        result = consolidate(new_mem, existing)
        assert not result.merged


class TestMergeMemories:
    def test_merge(self) -> None:
        a = ScoredMemory(id="ep-1", importance_score=0.7, content="python")
        b = ScoredMemory(id="ep-2", importance_score=0.8, content="rust")
        result = merge_memories(a, b)
        assert result.id == a.id
        assert result.importance_score == 0.8
        assert "python" in result.content
        assert "rust" in result.content


class TestApplyBatchDecay:
    def test_decay(self) -> None:
        memories = [
            ScoredMemory(id="ep-1", importance_score=0.8, usage_frequency=0),
            ScoredMemory(id="ep-2", importance_score=0.5, usage_frequency=2),
        ]
        result = apply_batch_decay(memories)
        assert result["decayed"] >= 0
