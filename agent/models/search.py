"""Search data models — results, queries, provider info."""

from datetime import datetime

from pydantic import BaseModel, Field


class SearchResult(BaseModel, frozen=True):
    title: str
    url: str
    snippet: str = ""
    provider: str = ""
    domain: str = ""
    timestamp: datetime = Field(default_factory=datetime.now)


class SearchQuery(BaseModel, frozen=True):
    query: str
    providers: list[str] = Field(default_factory=list)
    num_results: int = 10


class SearchProviderInfo(BaseModel, frozen=True):
    name: str
    domain: str
    platforms: list[str] = Field(default_factory=list)


class MergedSearchResult(BaseModel, frozen=True):
    query: str
    results: list[SearchResult] = Field(default_factory=list)
    providers_used: list[str] = Field(default_factory=list)
    total_results: int = 0
    latency_ms: float = 0.0
