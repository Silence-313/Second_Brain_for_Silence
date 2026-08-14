"""Router telemetry — self-tuning routing through per-tool success tracking."""

import json

from agent.models.routing import RoutingRecord, ToolMetrics


class RouterTelemetry:
    """Per-tool metrics with adaptive threshold and policy weight evolution."""

    def __init__(self) -> None:
        self._metrics: dict[str, ToolMetrics] = {}

    def record_routing(self, record: RoutingRecord) -> None:
        metrics = self._metrics.get(record.selected_tool)
        if metrics is None:
            metrics = ToolMetrics(tool_name=record.selected_tool)

        new_total = metrics.selection_count + 1
        new_success_rate = (
            metrics.success_rate
            + (int(record.execution_success) - metrics.success_rate) / new_total
        )
        new_avg_confidence = (
            metrics.avg_confidence + (record.confidence - metrics.avg_confidence) / new_total
        )

        recent = list(metrics.recent_decisions[-19:]) + [record.execution_success]

        threshold = max(0.1, min(0.6, 0.2 + (1 - new_success_rate) * 0.4))

        self._metrics[record.selected_tool] = metrics.model_copy(
            update={
                "selection_count": new_total,
                "success_rate": round(new_success_rate, 4),
                "avg_confidence": round(new_avg_confidence, 4),
                "recent_decisions": recent,
                "adaptive_threshold": round(threshold, 4),
            }
        )

        self._update_policy_weights(record.selected_tool)

    def get_adaptive_threshold(self, tool_name: str) -> float:
        metrics = self._metrics.get(tool_name)
        if metrics is None:
            return 0.2
        return metrics.adaptive_threshold

    def get_metrics(self, tool_name: str) -> ToolMetrics | None:
        return self._metrics.get(tool_name)

    def get_all_metrics(self) -> dict[str, ToolMetrics]:
        return dict(self._metrics)

    def serialize(self) -> str:
        data = {name: m.model_dump(mode="json") for name, m in self._metrics.items()}
        return json.dumps(data, ensure_ascii=False, default=str)

    def deserialize(self, json_str: str) -> None:
        try:
            data = json.loads(json_str)
            for name, raw in data.items():
                self._metrics[name] = ToolMetrics.model_validate(raw)
        except (json.JSONDecodeError, KeyError):
            pass

    def _update_policy_weights(self, tool_name: str) -> None:
        metrics = self._metrics.get(tool_name)
        if metrics is None:
            return

        recent = metrics.recent_decisions
        weight = metrics.policy_weight

        if len(recent) >= 3:
            last3 = recent[-3:]
            if all(last3):
                weight = min(1.0, weight + 0.02)
            elif not any(last3) and metrics.selection_count >= 3:
                weight = max(0.1, weight - 0.03)

        self._metrics[tool_name] = metrics.model_copy(update={"policy_weight": round(weight, 4)})
