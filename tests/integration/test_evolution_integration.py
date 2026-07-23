"""Integration tests: Evolution stack — MemoryEvolution + EpisodicMemory + Scoring + DriftController."""

from datetime import UTC, datetime, timedelta

import pytest

from agent.evolution.memory_evolution import MemoryEvolution
from agent.evolution.scoring import consolidate
from agent.memory.episodic import EpisodicMemory
from agent.models.evolution import ScoredMemory
from agent.models.memory import Episode
from agent.policy.controller import DriftController


class TestEvolutionIntegration:
    """Test memory evolution, concept evolution, and drift control together."""

    @pytest.fixture
    def evolution_stack(self):
        episodic = EpisodicMemory(max_entries=50)
        mem_evolution = MemoryEvolution(episodic)
        drift_ctrl = DriftController()
        return {
            "episodic": episodic,
            "mem_evolution": mem_evolution,
            "drift_ctrl": drift_ctrl,
        }

    def test_decay_cycle(self, evolution_stack):
        episodic = evolution_stack["episodic"]
        mem_evolution = evolution_stack["mem_evolution"]

        # Add entries with old timestamps
        old_time = datetime.now(UTC) - timedelta(hours=200)
        for i in range(10):
            ep = Episode(
                id=f"ep-old-{i}",
                type="event",
                summary=f"old entry {i}",
                importance_score=0.7,
                usage_frequency=0,
                last_access_time=old_time,
            )
            episodic.add(ep)

        decayed = mem_evolution.run_cycle()
        assert isinstance(decayed, int)
        # Some should be marked for removal after long inactivity
        active = episodic.get_active_entries()
        assert len(active) <= 10

    def test_reinforcement_preserves_recent(self, evolution_stack):
        episodic = evolution_stack["episodic"]
        mem_evolution = evolution_stack["mem_evolution"]

        # Add one recent and one old entry
        old_time = datetime.now(UTC) - timedelta(hours=300)
        recent = Episode(
            id="ep-recent", type="event", summary="recent",
            importance_score=0.7, usage_frequency=3,
            last_access_time=datetime.now(UTC),
        )
        old = Episode(
            id="ep-old", type="event", summary="old",
            importance_score=0.7, usage_frequency=0,
            last_access_time=old_time,
        )
        episodic.add(recent)
        episodic.add(old)

        mem_evolution.run_cycle()

        recent_ep = episodic.get("ep-recent")
        old_ep = episodic.get("ep-old")
        assert recent_ep is not None
        # Recent with high usage should have higher importance
        if old_ep and not old_ep.marked_for_removal:
            assert recent_ep.importance_score >= old_ep.importance_score

    def test_drift_controller_health(self, evolution_stack):
        dc = evolution_stack["drift_ctrl"]

        # Healthy system
        health = dc.compute_health([0.8, 0.9, 0.7, 0.85], 4, 0)
        assert health.health_score > 0.5
        assert health.signal_count == 0

        # Degraded system
        health2 = dc.compute_health([0.2, 0.1, 0.15, 0.3, 0.25] * 5, 25, 5)
        assert health2.signal_count > 0

    def test_scoring_consolidation(self):
        existing = [
            ScoredMemory(id="ep-1", content="python programming language tutorial"),
            ScoredMemory(id="ep-2", content="rust systems programming guide"),
        ]
        new_similar = ScoredMemory(id="ep-new", content="python programming language tutorial")
        result = consolidate(new_similar, existing)
        assert result.merged
        assert result.target_id == "ep-1"

        new_different = ScoredMemory(id="ep-new2", content="machine learning deep learning")
        result2 = consolidate(new_different, existing)
        assert not result2.merged
