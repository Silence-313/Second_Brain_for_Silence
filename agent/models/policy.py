"""Policy data models — cognitive governance and drift control."""

from datetime import datetime

from pydantic import BaseModel, Field


class CognitivePolicy(BaseModel, frozen=True):
    concept_preferences: dict[str, float] = Field(default_factory=dict)
    reasoning_strategy_weights: dict[str, float] = Field(
        default_factory=lambda: {
            "graph_traversal": 0.4,
            "pattern_matching": 0.3,
            "abstraction": 0.3,
        }
    )
    concept_stability_preference: float = Field(default=0.5, ge=0, le=1)
    exploration_rate: float = Field(default=0.2, ge=0.05, le=0.5)
    compression_threshold: float = Field(default=0.6, ge=0.4, le=0.9)
    last_updated: datetime = Field(default_factory=datetime.now)
    version: int = 0


class CompressionSignal(BaseModel, frozen=True):
    type: str  # low-confidence, redundant-cluster, high-entropy, unstable-pattern
    severity: float = Field(default=0.5, ge=0, le=1)
    details: dict[str, str] = Field(default_factory=dict)


class DriftMetrics(BaseModel, frozen=True):
    health_score: float = Field(default=1.0, ge=0, le=1)
    confidence_avg: float = Field(default=0.5, ge=0, le=1)
    stability: float = Field(default=1.0, ge=0, le=1)
    signal_count: int = 0
