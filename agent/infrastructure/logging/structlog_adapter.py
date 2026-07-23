"""Structlog logger adapter — implements Logger protocol."""

import json
import sys
from typing import Any


class StructlogLogger:
    """Implements Logger protocol using structlog. Falls back to plain JSON logging."""

    def __init__(self, level: str = "INFO") -> None:
        self._level = level.upper()
        self._levels = {"DEBUG": 10, "INFO": 20, "WARNING": 30, "ERROR": 40}

    def _log(self, level: str, event: str, **kwargs: Any) -> None:
        if self._levels.get(level, 0) < self._levels.get(self._level, 20):
            return

        record = {"level": level, "event": event, **kwargs}
        print(json.dumps(record, ensure_ascii=False, default=str), file=sys.stderr)

    def info(self, event: str, **kwargs: Any) -> None:
        self._log("INFO", event, **kwargs)

    def warning(self, event: str, **kwargs: Any) -> None:
        self._log("WARNING", event, **kwargs)

    def error(self, event: str, **kwargs: Any) -> None:
        self._log("ERROR", event, **kwargs)

    def debug(self, event: str, **kwargs: Any) -> None:
        self._log("DEBUG", event, **kwargs)
