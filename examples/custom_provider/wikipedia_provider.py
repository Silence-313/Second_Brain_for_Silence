"""Example custom search provider: WikipediaSearchProvider."""

from typing import Any
from urllib.parse import quote_plus

from agent.models.search import SearchResult
from agent.search.protocol import SearchProvider


class WikipediaSearchProvider(SearchProvider):
    name = "wikipedia"
    domain = "encyclopedia"
    platforms = ["web"]
    fallback_providers = []

    def __init__(self, http_client: Any = None) -> None:
        self._http = http_client

    async def search(self, query: str, num_results: int = 10) -> list[SearchResult]:
        if self._http is None:
            return []

        url = (
            f"https://en.wikipedia.org/w/api.php"
            f"?action=opensearch&search={quote_plus(query)}&limit={num_results}&format=json"
        )
        resp = await self._http.get(url, timeout=15)
        data = resp.json()

        results: list[SearchResult] = []
        if isinstance(data, list) and len(data) >= 4:
            titles: list[str] = data[1]
            urls: list[str] = data[3]
            for title, page_url in zip(titles, urls, strict=True):
                results.append(
                    SearchResult(
                        title=title,
                        url=page_url,
                        snippet=f"Wikipedia article: {title}",
                        provider="wikipedia",
                        domain="encyclopedia",
                    )
                )

        return results[:num_results]
