"""Retrieval data models — vector search results, feedback records."""

from datetime import datetime

from pydantic import BaseModel, Field


class VectorSearchResult(BaseModel, frozen=True):
    content: str
    source_path: str
    score: float = Field(default=0.0, ge=0, le=1)
    relevance_score: float = Field(default=0.5, ge=0, le=1)
    answer_impact_score: float = Field(default=0.0)
    downweight_factor: float = Field(default=0.0)


class RetrievalRecord(BaseModel, frozen=True):
    query: str
    retrieved_docs: list[str] = Field(default_factory=list)
    used_docs: list[str] = Field(default_factory=list)
    answer_quality: float = Field(default=0.5, ge=0, le=1)
    timestamp: datetime = Field(default_factory=datetime.now)


class DocumentWeight(BaseModel, frozen=True):
    path: str
    relevance_score: float = Field(default=0.5, ge=0, le=1)
    answer_impact_score: float = Field(default=0.0)
    downweight_factor: float = Field(default=0.0, ge=0.0, le=1.0)


class QueryCluster(BaseModel, frozen=True):
    signature: str
    count: int = 0
    success_rate: float = Field(default=0.5, ge=0, le=1)
