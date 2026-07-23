"""Storage infrastructure adapters."""

from agent.infrastructure.storage.local_fs import LocalFileStorage
from agent.infrastructure.storage.memory_fs import InMemoryFileStorage

__all__ = ["LocalFileStorage", "InMemoryFileStorage"]
