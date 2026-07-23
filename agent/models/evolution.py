"""Evolution data models — scoring, merge/split candidates, cycle results."""

from datetime import datetime

from pydantic import BaseModel, Field


class ScoredMemory(BaseModel, frozen=True):
    id: str
    importance_score: float = Field(default=0.5, ge=0, le=1)
    usage_frequency: int = 0
    last_access_time: datetime = Field(default_factory=datetime.now)
    decay_score: float = Field(default=1.0, ge=0, le=1)
    usefulness_score: float = Field(default=0.5, ge=0, le=1)
    marked_for_removal: bool = False
    content: str = ""
    tags: list[str] = Field(default_factory=list)


class EvolutionSignal(BaseModel, frozen=True):
    type: str  # access, reuse, positive_feedback, negative_feedback, correction
    amount: float = 0.0
    source: str = ""


class ConsolidationResult(BaseModel, frozen=True):
    merged: bool = False
    target_id: str | None = None
    similarity: float = 0.0


class MergeCandidate(BaseModel, frozen=True):
    source_slug: str
    target_slug: str
    similarity: float = Field(default=0.5, ge=0, le=1)
    shared_episodes: list[str] = Field(default_factory=list)


class SplitCandidate(BaseModel, frozen=True):
    concept_slug: str
    conflicting_groups: list[list[str]] = Field(default_factory=list)


class DecayResult(BaseModel, frozen=True):
    slug: str
    old_confidence: float
    new_confidence: float


class EvolutionResult(BaseModel, frozen=True):
    merges_applied: int = 0
    splits_marked: int = 0
    decayed: int = 0
    errors: list[str] = Field(default_factory=list)
