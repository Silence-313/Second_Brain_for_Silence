"""Working memory — short-term conversation buffer, in-memory only."""

from agent.models.memory import WorkingMemoryEntry


class WorkingMemory:
    """Short-term conversation buffer. Last N messages. Never persisted."""

    def __init__(self, capacity: int = 20) -> None:
        self._capacity = capacity
        self._entries: list[WorkingMemoryEntry] = []

    def push(self, entry: WorkingMemoryEntry) -> None:
        self._entries.append(entry)
        if len(self._entries) > self._capacity:
            self._entries = self._entries[-self._capacity :]

    def get_all(self) -> list[WorkingMemoryEntry]:
        return list(self._entries)

    def get_last(self, n: int) -> list[WorkingMemoryEntry]:
        return self._entries[-n:] if n > 0 else []

    def get_by_role(self, role: str) -> list[WorkingMemoryEntry]:
        return [e for e in self._entries if e.role == role]

    def get_recent_context(self, max_tokens: int = 4000) -> str:
        chars_per_token = 2
        max_chars = max_tokens * chars_per_token
        lines: list[str] = []
        total = 0
        for entry in reversed(self._entries):
            line = f"{entry.role}: {entry.content}"
            if total + len(line) > max_chars:
                break
            lines.append(line)
            total += len(line)
        return "\n".join(reversed(lines))

    def clear(self) -> None:
        self._entries.clear()

    @property
    def count(self) -> int:
        return len(self._entries)
