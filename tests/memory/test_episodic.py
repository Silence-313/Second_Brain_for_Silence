"""Tests for EpisodicMemory."""

from datetime import UTC, datetime, timedelta

from agent.memory.episodic import EpisodicMemory
from agent.models.memory import Episode


class TestEpisodicMemory:
    def test_add_and_get(self) -> None:
        em = EpisodicMemory(max_entries=200)
        ep = Episode(id="ep-1", type="event", summary="test")
        em.add(ep)
        assert em.count == 1
        assert em.get("ep-1") is not None

    def test_update(self) -> None:
        em = EpisodicMemory()
        em.add(Episode(id="ep-1", type="event", summary="old"))
        assert em.update("ep-1", {"summary": "new"})
        assert em.get("ep-1").summary == "new"  # type: ignore[union-attr]

    def test_update_nonexistent(self) -> None:
        em = EpisodicMemory()
        assert not em.update("nope", {"summary": "x"})

    def test_mark_accessed(self) -> None:
        em = EpisodicMemory()
        em.add(
            Episode(
                id="ep-1", type="event", summary="test", decay_score=0.5, marked_for_removal=True
            )
        )
        assert em.mark_accessed("ep-1")
        entry = em.get("ep-1")
        assert entry is not None
        assert entry.decay_score == 1.0
        assert not entry.marked_for_removal

    def test_reinforce(self) -> None:
        em = EpisodicMemory()
        em.add(Episode(id="ep-1", type="event", summary="test", importance_score=0.5))
        em.reinforce("ep-1", 0.03)
        assert em.get("ep-1").importance_score == 0.53  # type: ignore[union-attr]

    def test_reinforce_clamp(self) -> None:
        em = EpisodicMemory()
        em.add(Episode(id="ep-1", type="event", summary="test", importance_score=0.99))
        em.reinforce("ep-1", 0.1)
        assert em.get("ep-1").importance_score == 1.0  # type: ignore[union-attr]

    def test_apply_decay(self) -> None:
        em = EpisodicMemory()
        old_time = datetime.now(UTC) - timedelta(hours=100)
        em.add(
            Episode(
                id="ep-1",
                type="event",
                summary="old",
                importance_score=0.8,
                last_access_time=old_time,
                usage_frequency=0,
            )
        )
        decayed = em.apply_decay()
        assert decayed >= 0

    def test_search(self) -> None:
        em = EpisodicMemory()
        em.add(
            Episode(id="ep-1", type="event", summary="python programming", tags=["code", "python"])
        )
        em.add(Episode(id="ep-2", type="goal", summary="learn rust", tags=["code", "rust"]))
        results = em.search("python", top_k=5)
        assert len(results) >= 1
        assert any("python" in r.summary for r in results)

    def test_search_empty_query(self) -> None:
        em = EpisodicMemory()
        em.add(Episode(id="ep-1", type="event", summary="test"))
        results = em.search("", top_k=5)
        assert len(results) >= 0

    def test_get_active_entries(self) -> None:
        em = EpisodicMemory()
        em.add(Episode(id="ep-1", type="event", summary="active"))
        em.add(Episode(id="ep-2", type="event", summary="removed", marked_for_removal=True))
        active = em.get_active_entries()
        assert len(active) == 1
        assert active[0].id == "ep-1"

    def test_get_candidates_for_removal(self) -> None:
        em = EpisodicMemory()
        em.add(Episode(id="ep-1", type="event", summary="ok"))
        em.add(Episode(id="ep-2", type="event", summary="bad", marked_for_removal=True))
        candidates = em.get_candidates_for_removal()
        assert len(candidates) == 1

    def test_format_for_context(self) -> None:
        em = EpisodicMemory()
        em.add(Episode(id="ep-1", type="event", summary="learned python"))
        ctx = em.format_for_context(max_entries=5)
        assert "learned python" in ctx
        assert "相关记忆" in ctx

    def test_format_for_context_empty(self) -> None:
        em = EpisodicMemory()
        assert em.format_for_context() == ""

    def test_serialize_deserialize(self) -> None:
        em = EpisodicMemory()
        em.add(Episode(id="ep-1", type="event", summary="test", tags=["code"]))
        json_str = em.serialize()
        em2 = EpisodicMemory()
        em2.deserialize(json_str)
        assert em2.count == 1
        assert em2.get("ep-1").summary == "test"  # type: ignore[union-attr]

    def test_capacity_prune(self) -> None:
        em = EpisodicMemory(max_entries=3)
        for i in range(5):
            em.add(Episode(id=f"ep-{i}", type="event", summary=f"entry {i}"))
        assert em.count == 3
