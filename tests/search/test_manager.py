"""Tests for SearchManager."""

import pytest

from agent.models.search import SearchResult
from agent.search.manager import SearchManager
from agent.search.protocol import SearchProvider


class _MockProvider(SearchProvider):
    name = "mock"
    domain = "web"
    platforms = ["web"]

    async def search(self, query: str, num_results: int = 10) -> list[SearchResult]:
        return [
            SearchResult(title=f"Result {i}", url=f"https://example.com/{i}", snippet=f"Snippet {i}", provider="mock", domain="web")
            for i in range(min(3, num_results))
        ]


class TestSearchManager:
    def test_register_provider(self) -> None:
        sm = SearchManager()
        sm.register_provider(_MockProvider())
        assert sm.get_provider("mock") is not None

    @pytest.mark.asyncio
    async def test_search(self) -> None:
        sm = SearchManager()
        sm.register_provider(_MockProvider())
        result = await sm.search("test query")
        assert result.query == "test query"
        assert result.total_results > 0

    @pytest.mark.asyncio
    async def test_search_specific_providers(self) -> None:
        sm = SearchManager()
        sm.register_provider(_MockProvider())
        result = await sm.search("test", providers=["mock"])
        assert "mock" in result.providers_used

    @pytest.mark.asyncio
    async def test_search_unknown_provider(self) -> None:
        sm = SearchManager()
        result = await sm.search("test", providers=["nonexistent"])
        assert result.total_results == 0

    def test_list_providers(self) -> None:
        sm = SearchManager()
        sm.register_provider(_MockProvider())
        providers = sm.list_providers()
        assert len(providers) == 1

    @pytest.mark.asyncio
    async def test_deduplicate_urls(self) -> None:
        sm = SearchManager()
        sm.register_provider(_MockProvider())
        result = await sm.search("test")
        urls = [r.url for r in result.results]
        assert len(urls) == len(set(urls))
