"""Tests for InMemoryEventBus."""

import pytest

from agent.bus.memory_bus import InMemoryEventBus
from agent.models.events import ErrorOccurred, ToolExecuted


class TestInMemoryEventBus:
    @pytest.mark.asyncio
    async def test_emit_single_subscriber(self) -> None:
        bus = InMemoryEventBus()
        received: list[ToolExecuted] = []

        def handler(event: ToolExecuted) -> None:
            received.append(event)

        bus.subscribe(ToolExecuted, handler)
        event = ToolExecuted(tool_name="test", success=True)
        await bus.emit(event)
        assert len(received) == 1
        assert received[0].tool_name == "test"

    @pytest.mark.asyncio
    async def test_multiple_subscribers(self) -> None:
        bus = InMemoryEventBus()
        results: list[str] = []

        def h1(event: ErrorOccurred) -> None:
            results.append("h1")

        def h2(event: ErrorOccurred) -> None:
            results.append("h2")

        bus.subscribe(ErrorOccurred, h1)
        bus.subscribe(ErrorOccurred, h2)
        await bus.emit(ErrorOccurred(stage="test", error="err"))
        assert len(results) == 2

    @pytest.mark.asyncio
    async def test_unsubscribe(self) -> None:
        bus = InMemoryEventBus()
        received: list[ToolExecuted] = []

        def handler(event: ToolExecuted) -> None:
            received.append(event)

        bus.subscribe(ToolExecuted, handler)
        bus.unsubscribe(ToolExecuted, handler)
        await bus.emit(ToolExecuted(tool_name="test", success=True))
        assert len(received) == 0

    @pytest.mark.asyncio
    async def test_subscriber_exception_does_not_crash(self) -> None:
        bus = InMemoryEventBus()
        results: list[str] = []

        def failing_handler(event: ErrorOccurred) -> None:
            raise RuntimeError("boom")

        def good_handler(event: ErrorOccurred) -> None:
            results.append("good")

        bus.subscribe(ErrorOccurred, failing_handler)
        bus.subscribe(ErrorOccurred, good_handler)
        await bus.emit(ErrorOccurred(stage="test", error="err"))
        assert "good" in results

    @pytest.mark.asyncio
    async def test_different_event_types(self) -> None:
        bus = InMemoryEventBus()
        received: list[str] = []

        def tool_handler(event: ToolExecuted) -> None:
            received.append("tool")

        def error_handler(event: ErrorOccurred) -> None:
            received.append("error")

        bus.subscribe(ToolExecuted, tool_handler)
        bus.subscribe(ErrorOccurred, error_handler)
        await bus.emit(ToolExecuted(tool_name="test", success=True))
        assert received == ["tool"]
