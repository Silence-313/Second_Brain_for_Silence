"""Concept data models — graph nodes, edges, extraction results."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class Concept(BaseModel, frozen=True):
    id: str
    name: str
    slug: str
    confidence: float = Field(default=0.5, ge=0, le=1)
    source_episodes: list[str] = Field(default_factory=list)
    related: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class ExtractedConcept(BaseModel, frozen=True):
    name: str
    slug: str
    confidence: float = Field(default=0.5, ge=0, le=1)
    source_terms: list[str] = Field(default_factory=list)


class ConceptGraphNode(BaseModel, frozen=True):
    id: str
    name: str
    slug: str
    confidence: float = Field(default=0.5, ge=0, le=1)
    source_episodes: list[str] = Field(default_factory=list)
    related: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    degree: int = 0


class ConceptGraphEdge(BaseModel, frozen=True):
    from_slug: str
    to_slug: str
    weight: float = Field(default=0.5, ge=0, le=1)
    type: Literal["related", "shared-episode", "tag-overlap"]


class ConceptGraph(BaseModel, frozen=True):
    nodes: dict[str, ConceptGraphNode] = Field(default_factory=dict)
    edges: list[ConceptGraphEdge] = Field(default_factory=list)


class ConceptSubgraph(BaseModel, frozen=True):
    nodes: dict[str, ConceptGraphNode] = Field(default_factory=dict)
    edges: list[ConceptGraphEdge] = Field(default_factory=list)
    central_concepts: list[str] = Field(default_factory=list)


