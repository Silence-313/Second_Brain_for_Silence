"""Tool memory — tool usage frequency, success rate, and context effectiveness."""

from datetime import datetime

from agent.models.memory import ToolUsageRecord


class ToolMemory:
    """Tracks tool usage performance across calls."""

    def __init__(self) -> None:
        self._records: dict[str, ToolUsageRecord] = {}

    def record_call(
        self,
        tool_name: str,
        success: bool,
        query: str = "",
        context_type: str = "",
        latency_ms: float = 0.0,
        response_quality: float = 0.5,
    ) -> None:
        record = self._records.get(tool_name)
        if record is None:
            record = ToolUsageRecord(tool_name=tool_name)

        pattern = self._extract_pattern(query)
        pattern_counts = dict(record.pattern_counts)
        pattern_counts[pattern] = pattern_counts.get(pattern, 0) + 1
        top_patterns = sorted(pattern_counts, key=lambda k: pattern_counts.get(k, 0), reverse=True)[
            :10
        ]

        context_eff = dict(record.context_effectiveness)
        if context_type:
            ctx = dict(context_eff.get(context_type, {"count": 0, "avg_quality": 0.0}))
            new_count = ctx.get("count", 0) + 1
            old_avg = ctx.get("avg_quality", 0.0)
            ctx["count"] = new_count
            ctx["avg_quality"] = old_avg + (response_quality - old_avg) / new_count
            context_eff[context_type] = ctx

        new_success = record.success_count + (1 if success else 0)
        new_failure = record.failure_count + (0 if success else 1)
        new_total = new_success + new_failure
        new_avg_latency = record.avg_latency_ms + (latency_ms - record.avg_latency_ms) / new_total
        new_avg_quality = (
            record.avg_response_quality
            + (response_quality - record.avg_response_quality) / new_total
        )

        self._records[tool_name] = record.model_copy(
            update={
                "call_count": record.call_count + 1,
                "success_count": new_success,
                "failure_count": new_failure,
                "top_query_patterns": top_patterns,
                "pattern_counts": pattern_counts,
                "avg_latency_ms": round(new_avg_latency, 2),
                "avg_response_quality": round(new_avg_quality, 4),
                "last_used": datetime.now(),
            }
        )

    def get_success_rate(self, tool_name: str) -> float:
        record = self._records.get(tool_name)
        if record is None or record.call_count == 0:
            return 0.5
        return record.success_count / record.call_count

    def get_effectiveness(self, tool_name: str) -> float:
        record = self._records.get(tool_name)
        if record is None:
            return 0.5
        quality = record.avg_response_quality
        success = self.get_success_rate(tool_name)
        return round(quality * 0.6 + success * 0.4, 4)

    def get_frequency(self, tool_name: str) -> int:
        record = self._records.get(tool_name)
        return record.call_count if record else 0

    def suggest_alternate(self, tool_name: str, query: str) -> str | None:
        pattern = self._extract_pattern(query)
        best_tool: str | None = None
        best_effectiveness = self.get_effectiveness(tool_name)

        for name, record in self._records.items():
            if name == tool_name:
                continue
            if pattern in record.pattern_counts:
                eff = self.get_effectiveness(name)
                if eff > best_effectiveness:
                    best_effectiveness = eff
                    best_tool = name

        return best_tool

    def get_stats(self, tool_name: str) -> ToolUsageRecord | None:
        return self._records.get(tool_name)

    def get_all_stats(self) -> dict[str, ToolUsageRecord]:
        return dict(self._records)

    def serialize(self) -> str:
        import json

        data = {name: r.model_dump(mode="json") for name, r in self._records.items()}
        return json.dumps(data, ensure_ascii=False, default=str)

    def deserialize(self, json_str: str) -> None:
        import json

        try:
            data = json.loads(json_str)
            for name, raw in data.items():
                self._records[name] = ToolUsageRecord.model_validate(raw)
        except (json.JSONDecodeError, KeyError):
            pass

    @staticmethod
    def _extract_pattern(query: str) -> str:
        if not query:
            return "unknown"
        words = query.strip().split()
        meaningful = [w for w in words if len(w) > 1][:3]
        return " ".join(meaningful) if meaningful else query.strip()[:20]
