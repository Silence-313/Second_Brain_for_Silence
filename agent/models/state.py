"""Cognitive state snapshots — read-only SSOT for the 5-layer cognitive stack."""

from datetime import datetime

from pydantic import BaseModel, Field


class MemoryState(BaseModel, frozen=True):
    episodic_count: int = 0
    episodic_active: int = 0
    working_memory_size: int = 0
    profile_fields: int = 0
    profile_initialized: bool = False


class ConceptGraphState(BaseModel, frozen=True):
    concept_count: int = 0
    avg_confidence: float = 0.0
    total_edges: int = 0
    domains_tracked: list[str] = Field(default_factory=list)


class ReasoningState(BaseModel, frozen=True):
    last_reasoning_confidence: float = 0.0
    key_concepts_used: list[str] = Field(default_factory=list)
    last_query: str = ""
    reasoning_cycles_run: int = 0


class FeedbackState(BaseModel, frozen=True):
    traces_stored: int = 0
    concepts_reinforced: int = 0
    insights_reinforced: int = 0
    contradictions_detected: int = 0
    policy_updates: int = 0


class PolicyState(BaseModel, frozen=True):
    domain_preferences: dict[str, float] = Field(default_factory=dict)
    strategy_weights: dict[str, float] = Field(default_factory=dict)
    exploration_rate: float = 0.2
    compression_threshold: float = 0.6
    version: int = 0


class CognitiveState(BaseModel, frozen=True):
    memory: MemoryState = Field(default_factory=MemoryState)
    concepts: ConceptGraphState = Field(default_factory=ConceptGraphState)
    reasoning: ReasoningState = Field(default_factory=ReasoningState)
    feedback: FeedbackState = Field(default_factory=FeedbackState)
    policy: PolicyState = Field(default_factory=PolicyState)
    version: int = 0
    last_updated: datetime = Field(default_factory=datetime.now)
