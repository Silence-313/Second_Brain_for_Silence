"""Search provider protocol — abstract base for search sources."""

from abc import ABC, abstractmethod
from typing import Any

from agent.models.search import SearchResult


class SearchProvider(ABC):
    """Search source capability. Implementations: Bing, DuckDuckGo, etc."""

    name: str = ""
    domain: str = "web"
    platforms: list[str] = []
    fallback_providers: list[str] = []

    @abstractmethod
    async def search(self, query: str, num_results: int = 10) -> list[SearchResult]:
        """Execute a search and return results."""
        ...

    def to_info(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "domain": self.domain,
            "platforms": self.platforms,
        }
