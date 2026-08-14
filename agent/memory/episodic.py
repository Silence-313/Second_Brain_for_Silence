"""Episodic memory — persistent event/goal/decision storage with evolution scoring."""

import json
import math
import time
from datetime import UTC, datetime

from agent.models.memory import Episode


def _now_ms() -> int:
    return int(time.time() * 1000)


class EpisodicMemory:
    """Persistent episodic memory store. Capacity: 200 entries."""

    def __init__(self, max_entries: int = 200) -> None:
        self._max_entries = max_entries
        self._entries: dict[str, Episode] = {}

    def add(self, entry: Episode) -> Episode:
        if len(self._entries) >= self._max_entries:
            self._prune(1)
        self._entries[entry.id] = entry
        return entry

    def get(self, entry_id: str) -> Episode | None:
        return self._entries.get(entry_id)

    def update(self, entry_id: str, updates: dict[str, object]) -> bool:
        entry = self._entries.get(entry_id)
        if entry is None:
            return False
        self._entries[entry_id] = entry.model_copy(update=updates)
        return True

    def mark_accessed(self, entry_id: str) -> bool:
        entry = self._entries.get(entry_id)
        if entry is None:
            return False
        self._entries[entry_id] = entry.model_copy(
            update={
                "last_access_time": datetime.now(UTC),
                "decay_score": 1.0,
                "marked_for_removal": False,
            }
        )
        return True

    def reinforce(self, entry_id: str, amount: float) -> bool:
        entry = self._entries.get(entry_id)
        if entry is None:
            return False
        new_score = max(0.0, min(1.0, entry.importance_score + amount))
        self._entries[entry_id] = entry.model_copy(update={"importance_score": new_score})
        return True

    def apply_decay(self) -> int:
        now = datetime.now(UTC)
        decayed = 0
        for eid, entry in list(self._entries.items()):
            if entry.marked_for_removal:
                continue
            hours_since = (now - entry.last_access_time).total_seconds() / 3600
            effective_rate = 0.03 * (1 - entry.usage_frequency * 0.6)
            decay = round(
                entry.importance_score * math.exp(-effective_rate * max(hours_since, 0)), 4
            )
            if decay < 0.25 and entry.usage_frequency == 0 and hours_since >= 14:
                self._entries[eid] = entry.model_copy(
                    update={"decay_score": decay, "marked_for_removal": True}
                )
                decayed += 1
            else:
                self._entries[eid] = entry.model_copy(update={"decay_score": decay})
        return decayed

    def get_candidates_for_removal(self) -> list[Episode]:
        return [e for e in self._entries.values() if e.marked_for_removal]

    def get_active_entries(self) -> list[Episode]:
        return [e for e in self._entries.values() if not e.marked_for_removal]

    def search(self, query: str, top_k: int = 5) -> list[Episode]:
        if not query.strip():
            return list(self._entries.values())[:top_k]

        query_lower = query.lower()
        scored: list[tuple[Episode, float]] = []

        for entry in self._entries.values():
            if entry.marked_for_removal:
                continue
            score = 0.0
            content = f"{entry.summary} {entry.detail} {' '.join(entry.tags)}".lower()

            query_terms = query_lower.split()
            for term in query_terms:
                if term in content:
                    score += 1.0
                if term in entry.type:
                    score += 0.5

            for tag in entry.tags:
                if tag.lower() in query_lower:
                    score += 1.5

            hours_since = (datetime.now(UTC) - entry.last_access_time).total_seconds() / 3600
            recency_boost = max(0.0, 1.0 - hours_since / 168) * 0.3
            usefulness_bonus = entry.usefulness_score * 0.2

            score += recency_boost + usefulness_bonus
            scored.append((entry, score))

        scored.sort(key=lambda x: x[1], reverse=True)
        return [entry for entry, _ in scored[:top_k]]

    def format_for_context(self, max_entries: int = 5) -> str:
        active = self.get_active_entries()
        if not active:
            return ""

        sorted_entries = sorted(active, key=lambda e: e.timestamp, reverse=True)
        lines = ["## 相关记忆"]
        for entry in sorted_entries[:max_entries]:
            ts = entry.timestamp.strftime("%Y-%m-%d %H:%M")
            lines.append(f"- [{entry.type}] {entry.summary} ({ts})")
        return "\n".join(lines)

    def serialize(self) -> str:
        data = {
            "version": 1,
            "entries": [e.model_dump(mode="json") for e in self._entries.values()],
        }
        return json.dumps(data, ensure_ascii=False, default=str)

    def deserialize(self, json_str: str) -> None:
        try:
            data = json.loads(json_str)
            for raw in data.get("entries", []):
                entry = Episode.model_validate(raw)
                self._entries[entry.id] = entry
        except (json.JSONDecodeError, KeyError):
            pass

    def _prune(self, count: int) -> None:
        candidates = sorted(
            self._entries.values(),
            key=lambda e: (e.marked_for_removal, e.decay_score),
        )
        for entry in candidates[:count]:
            del self._entries[entry.id]

    @property
    def count(self) -> int:
        return len(self._entries)

    @property
    def active_count(self) -> int:
        return len(self.get_active_entries())
