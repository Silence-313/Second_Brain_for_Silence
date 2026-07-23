"""State mutation discriminated union — all 7 mutation variants."""

from typing import Annotated, Any, Literal

from pydantic import BaseModel, Field


class ConceptUpdateMutation(BaseModel, frozen=True):
    type: Literal["concept_update"] = "concept_update"
    concept_name: str
    field: str
    delta: float = Field(default=0.0, ge=-0.05, le=0.05)


class ConceptMergeMutation(BaseModel, frozen=True):
    type: Literal["concept_merge"] = "concept_merge"
    source_slug: str
    target_slug: str


class ConceptDecayMutation(BaseModel, frozen=True):
    type: Literal["concept_decay"] = "concept_decay"
    concept_slug: str
    delta: float = Field(default=-0.05, ge=-0.05, le=0.0)


class MemoryWriteMutation(BaseModel, frozen=True):
    type: Literal["memory_write"] = "memory_write"
    entry_id: str
    entry_type: str  # episodic, profile, tool
    payload: dict[str, Any] = Field(default_factory=dict)


class PolicyUpdateMutation(BaseModel, frozen=True):
    type: Literal["policy_update"] = "policy_update"
    field: str
    value: float


class ReasoningTraceMutation(BaseModel, frozen=True):
    type: Literal["reasoning_trace"] = "reasoning_trace"
    trace_id: str
    query: str
    key_concepts: list[str] = Field(default_factory=list)
    confidence: float = 0.0


class RelationshipMarkMutation(BaseModel, frozen=True):
    type: Literal["relationship_mark"] = "relationship_mark"
    concept_a: str
    concept_b: str
    weight: float = Field(default=0.5, ge=0, le=1)


StateMutation = Annotated[
    ConceptUpdateMutation
    | ConceptMergeMutation
    | ConceptDecayMutation
    | MemoryWriteMutation
    | PolicyUpdateMutation
    | ReasoningTraceMutation
    | RelationshipMarkMutation,
    Field(discriminator="type"),
]

# Priority order: lower number = higher priority
MUTATION_PRIORITY: dict[str, int] = {
    "policy_update": 1,
    "concept_merge": 2,
    "concept_update": 3,
    "concept_decay": 4,
    "memory_write": 5,
    "reasoning_trace": 6,
    "relationship_mark": 7,
}
