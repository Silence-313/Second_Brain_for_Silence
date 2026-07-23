"""Logger protocol — abstract interface for structured logging."""

from typing import Any, Protocol


class Logger(Protocol):
    """Abstract logger. Implementation: StructlogLogger."""

    def info(self, event: str, **kwargs: Any) -> None:
        """Log an informational event."""
        ...

    def warning(self, event: str, **kwargs: Any) -> None:
        """Log a warning event."""
        ...

    def error(self, event: str, **kwargs: Any) -> None:
        """Log an error event."""
        ...

    def debug(self, event: str, **kwargs: Any) -> None:
        """Log a debug event."""
        ...
