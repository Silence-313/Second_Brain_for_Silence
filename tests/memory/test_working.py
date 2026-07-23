"""Tests for WorkingMemory."""

from agent.memory.working import WorkingMemory
from agent.models.memory import WorkingMemoryEntry


class TestWorkingMemory:
    def test_push_and_get(self) -> None:
        wm = WorkingMemory(capacity=20)
        wm.push(WorkingMemoryEntry(role="user", content="hello"))
        wm.push(WorkingMemoryEntry(role="assistant", content="hi"))
        assert wm.count == 2

    def test_capacity_fifo(self) -> None:
        wm = WorkingMemory(capacity=3)
        for i in range(5):
            wm.push(WorkingMemoryEntry(role="user", content=f"msg{i}"))
        assert wm.count == 3
        assert wm.get_last(1)[0].content == "msg4"

    def test_get_last(self) -> None:
        wm = WorkingMemory(capacity=10)
        for i in range(5):
            wm.push(WorkingMemoryEntry(role="user", content=f"msg{i}"))
        last2 = wm.get_last(2)
        assert len(last2) == 2
        assert last2[0].content == "msg3"

    def test_get_by_role(self) -> None:
        wm = WorkingMemory(capacity=10)
        wm.push(WorkingMemoryEntry(role="user", content="q1"))
        wm.push(WorkingMemoryEntry(role="assistant", content="a1"))
        assert len(wm.get_by_role("user")) == 1
        assert len(wm.get_by_role("assistant")) == 1

    def test_get_all(self) -> None:
        wm = WorkingMemory(capacity=10)
        wm.push(WorkingMemoryEntry(role="user", content="hello"))
        assert len(wm.get_all()) == 1

    def test_clear(self) -> None:
        wm = WorkingMemory(capacity=10)
        wm.push(WorkingMemoryEntry(role="user", content="hello"))
        wm.clear()
        assert wm.count == 0

    def test_get_recent_context(self) -> None:
        wm = WorkingMemory(capacity=10)
        wm.push(WorkingMemoryEntry(role="user", content="hello world"))
        ctx = wm.get_recent_context(max_tokens=50)
        assert "hello world" in ctx
