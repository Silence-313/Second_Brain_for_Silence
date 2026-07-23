"""Drift controller — global cognitive stability governor. Pure policy computation."""

from agent.models.policy import CognitivePolicy, CompressionSignal, DriftMetrics


class DriftController:
    """Global cognitive governor: preference balance, compression detection, health scoring."""

    def __init__(self, policy: CognitivePolicy | None = None) -> None:
        self._policy = policy or CognitivePolicy()

    def reinforce_domain(self, tag: str, amount: float = 0.03) -> None:
        prefs = dict(self._policy.concept_preferences)
        prefs[tag] = max(0.1, min(1.0, prefs.get(tag, 0.5) + amount))
        self._policy = self._policy.model_copy(
            update={"concept_preferences": prefs, "version": self._policy.version + 1}
        )

    def suppress_domain(self, tag: str, amount: float = 0.02) -> None:
        prefs = dict(self._policy.concept_preferences)
        prefs[tag] = max(0.1, min(1.0, prefs.get(tag, 0.5) - amount))
        self._policy = self._policy.model_copy(
            update={"concept_preferences": prefs, "version": self._policy.version + 1}
        )

    def adjust_strategy_weight(self, strategy: str, delta: float) -> None:
        clamped = max(-0.05, min(0.05, delta))
        weights = dict(self._policy.reasoning_strategy_weights)
        weights[strategy] = max(0.1, min(1.0, weights.get(strategy, 0.3) + clamped))
        self._policy = self._policy.model_copy(
            update={"reasoning_strategy_weights": weights, "version": self._policy.version + 1}
        )

    def adapt_exploration_rate(self, concept_count: int) -> None:
        if concept_count > 20:
            rate = max(0.05, 0.3 - concept_count * 0.01)
        elif concept_count < 5:
            rate = 0.4
        else:
            rate = 0.2
        self._policy = self._policy.model_copy(
            update={"exploration_rate": round(rate, 4), "version": self._policy.version + 1}
        )

    def enforce_balance(self) -> None:
        prefs = list(self._policy.concept_preferences.values())
        if not prefs:
            return

        max_pref = max(prefs)
        min_pref = min(prefs)
        if max_pref - min_pref > 0.6:
            new_prefs = dict(self._policy.concept_preferences)
            for key in new_prefs:
                if new_prefs[key] == max_pref:
                    new_prefs[key] = max(0.1, max_pref - 0.05)
                elif new_prefs[key] == min_pref:
                    new_prefs[key] = min(1.0, min_pref + 0.03)
            self._policy = self._policy.model_copy(
                update={"concept_preferences": new_prefs, "version": self._policy.version + 1}
            )

    def detect_compression_signals(
        self,
        concept_confidences: list[float],
        concept_count: int,
        unstable_rel_count: int = 0,
    ) -> list[CompressionSignal]:
        signals: list[CompressionSignal] = []

        if concept_count > 0:
            low_conf = [c for c in concept_confidences if c < 0.3]
            low_ratio = len(low_conf) / concept_count
            if low_ratio > self._policy.compression_threshold:
                signals.append(
                    CompressionSignal(
                        type="low-confidence",
                        severity=round(low_ratio, 4),
                        details={"low_conf_count": str(len(low_conf)), "total": str(concept_count)},
                    )
                )

        if concept_count > 15 and sum(concept_confidences) / max(1, concept_count) < 0.5:
            signals.append(
                CompressionSignal(
                    type="high-entropy",
                    severity=round(1.0 - sum(concept_confidences) / max(1, concept_count), 4),
                )
            )

        if unstable_rel_count >= 3:
            signals.append(
                CompressionSignal(
                    type="unstable-pattern",
                    severity=min(1.0, unstable_rel_count / 10),
                    details={"unstable_count": str(unstable_rel_count)},
                )
            )

        return signals

    def compute_health(
        self,
        concept_confidences: list[float],
        concept_count: int,
        unstable_rel_count: int = 0,
    ) -> DriftMetrics:
        confidence_avg = sum(concept_confidences) / max(1, len(concept_confidences))

        signals = self.detect_compression_signals(
            concept_confidences, concept_count, unstable_rel_count
        )
        signal_penalty = min(1.0, len(signals) * 0.2)

        stability = 1.0 - signal_penalty
        health = round(0.3 * confidence_avg + 0.4 * stability + 0.3 * max(0, 1.0 - signal_penalty), 4)

        return DriftMetrics(
            health_score=health,
            confidence_avg=round(confidence_avg, 4),
            stability=round(stability, 4),
            signal_count=len(signals),
        )

    def serialize(self) -> str:
        return self._policy.model_dump_json()

    def deserialize(self, json_str: str) -> None:
        try:
            self._policy = CognitivePolicy.model_validate_json(json_str)
        except Exception:
            pass

    @property
    def current_policy(self) -> CognitivePolicy:
        return self._policy
