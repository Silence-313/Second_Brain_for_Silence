"""Reasoning data models — results and traces from the 3-strategy reasoner."""

from datetime import datetime

from pydantic import BaseModel, Field


class ReasoningResult(BaseModel, frozen=True):
    key_concepts: list[str] = Field(default_factory=list)
    relationships: list[str] = Field(default_factory=list)
    inferred_insights: list[str] = Field(default_factory=list)
    contradictions: list[str] = Field(default_factory=list)
    bridging_concepts: list[str] = Field(default_factory=list)
    concept_clusters: list[list[str]] = Field(default_factory=list)
    confidence: float = Field(default=0.5, ge=0, le=1)


class ReasoningTrace(BaseModel, frozen=True):
    id: str
    query: str
    key_concepts: list[str] = Field(default_factory=list)
    insights: list[str] = Field(default_factory=list)
    confidence: float = Field(default=0.5, ge=0, le=1)
    strategies_used: list[str] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=datetime.now)
