"""Event bus protocol — abstract interface for typed event pub/sub."""

from collections.abc import Callable
from typing import Any, Protocol


class EventBus(Protocol):
    """Typed event emission and subscription. Implementation: InMemoryEventBus."""

    async def emit(self, event: Any) -> None:
        """Emit an event to all subscribers of its type."""
        ...

    def subscribe(self, event_type: type, handler: Callable[[Any], Any]) -> None:
        """Subscribe a handler to a specific event type."""
        ...

    def unsubscribe(self, event_type: type, handler: Callable[[Any], Any]) -> None:
        """Remove a subscription."""
        ...
