"""Tests for DriftController."""

from agent.models.policy import CognitivePolicy
from agent.policy.controller import DriftController


class TestDriftController:
    def test_default_policy(self) -> None:
        dc = DriftController()
        assert dc.current_policy.exploration_rate == 0.2

    def test_custom_policy(self) -> None:
        cp = CognitivePolicy(exploration_rate=0.3)
        dc = DriftController(cp)
        assert dc.current_policy.exploration_rate == 0.3

    def test_reinforce_domain(self) -> None:
        dc = DriftController()
        dc.reinforce_domain("ai", 0.05)
        prefs = dc.current_policy.concept_preferences
        assert "ai" in prefs

    def test_suppress_domain(self) -> None:
        dc = DriftController()
        dc.reinforce_domain("ai", 0.1)
        dc.suppress_domain("ai", 0.03)
        assert dc.current_policy.concept_preferences["ai"] < 0.6

    def test_adjust_strategy_weight(self) -> None:
        dc = DriftController()
        dc.adjust_strategy_weight("graph_traversal", 0.05)
        assert dc.current_policy.reasoning_strategy_weights["graph_traversal"] > 0.4

    def test_adjust_strategy_clamped(self) -> None:
        dc = DriftController()
        dc.adjust_strategy_weight("graph_traversal", 1.0)
        assert dc.current_policy.reasoning_strategy_weights["graph_traversal"] <= 1.0

    def test_adapt_exploration_rate(self) -> None:
        dc = DriftController()
        dc.adapt_exploration_rate(25)
        assert dc.current_policy.exploration_rate < 0.2  # high concept count reduces exploration

    def test_enforce_balance(self) -> None:
        dc = DriftController()
        dc.reinforce_domain("ai", 0.5)
        dc.reinforce_domain("code", 0.05)
        dc.enforce_balance()
        # Should reduce max and boost min

    def test_detect_compression_signals(self) -> None:
        dc = DriftController()
        signals = dc.detect_compression_signals([0.2, 0.25, 0.15], 3, 0)
        assert isinstance(signals, list)

    def test_detect_low_confidence(self) -> None:
        dc = DriftController(CognitivePolicy(compression_threshold=0.4))
        signals = dc.detect_compression_signals([0.2, 0.1, 0.25, 0.3], 4, 0)
        types = [s.type for s in signals]
        assert "low-confidence" in types

    def test_detect_high_entropy(self) -> None:
        dc = DriftController()
        signals = dc.detect_compression_signals([0.3] * 20, 20, 0)
        types = [s.type for s in signals]
        assert "high-entropy" in types

    def test_detect_unstable(self) -> None:
        dc = DriftController()
        signals = dc.detect_compression_signals([0.7] * 5, 5, 3)
        types = [s.type for s in signals]
        assert "unstable-pattern" in types

    def test_compute_health(self) -> None:
        dc = DriftController()
        metrics = dc.compute_health([0.8, 0.9, 0.7], 3, 0)
        assert 0 <= metrics.health_score <= 1
        assert metrics.signal_count >= 0

    def test_serialize_deserialize(self) -> None:
        dc = DriftController()
        dc.reinforce_domain("ai", 0.1)
        json_str = dc.serialize()
        dc2 = DriftController()
        dc2.deserialize(json_str)
        assert dc2.current_policy.concept_preferences.get("ai", 0) > 0
