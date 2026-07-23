"""In-memory event bus — implements EventBus protocol."""

import asyncio
from collections import defaultdict
from collections.abc import Callable
from typing import Any

Callback = Callable[[Any], Any]


class InMemoryEventBus:
    """Implements EventBus protocol. In-process pub/sub."""

    def __init__(self) -> None:
        self._subscribers: dict[type, list[Callback]] = defaultdict(list)

    async def emit(self, event: Any) -> None:
        event_type = type(event)
        handlers = self._subscribers.get(event_type, [])
        if not handlers:
            return

        tasks = []
        for handler in handlers:
            try:
                result = handler(event)
                if asyncio.iscoroutine(result):
                    tasks.append(result)
            except Exception:
                pass

        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    def subscribe(self, event_type: type, handler: Callback) -> None:
        if handler not in self._subscribers[event_type]:
            self._subscribers[event_type].append(handler)

    def unsubscribe(self, event_type: type, handler: Callback) -> None:
        if handler in self._subscribers[event_type]:
            self._subscribers[event_type].remove(handler)

    @property
    def subscriber_count(self) -> int:
        return sum(len(h) for h in self._subscribers.values())
