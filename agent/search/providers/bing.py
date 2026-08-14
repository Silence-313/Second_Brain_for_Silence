"""Bing search provider — HTML scraping implementation."""

import re
from typing import Any
from urllib.parse import quote_plus

from agent.models.search import SearchResult
from agent.search.protocol import SearchProvider


class BingSearchProvider(SearchProvider):
    name = "bing"
    domain = "web"
    platforms = ["web"]
    fallback_providers = ["duckduckgo"]

    def __init__(self, http_client: Any = None) -> None:
        self._http = http_client

    async def search(self, query: str, num_results: int = 10) -> list[SearchResult]:
        if self._http is None:
            return []

        url = f"https://www.bing.com/search?q={quote_plus(query)}&setlang=zh-cn&count={num_results}"
        resp = await self._http.get(
            url, headers={"User-Agent": "Mozilla/5.0 (compatible; Agent/1.0)"}, timeout=15
        )
        html = resp.text

        results: list[SearchResult] = []
        blocks = re.findall(r'<li class="b_algo"[^>]*>(.*?)</li>', html, re.DOTALL)

        for block in blocks[:num_results]:
            title_m = re.search(r"<h2[^>]*><a[^>]*>(.*?)</a>", block, re.DOTALL)
            url_m = re.search(r'<a[^>]*href="(https?://[^"]+)"', block)
            snippet_m = re.search(r"<p[^>]*>(.*?)</p>", block, re.DOTALL)

            if title_m:
                results.append(
                    SearchResult(
                        title=re.sub(r"<[^>]+>", "", title_m.group(1)),
                        url=url_m.group(1) if url_m else "",
                        snippet=re.sub(r"<[^>]+>", "", snippet_m.group(1)) if snippet_m else "",
                        provider="bing",
                        domain="web",
                    )
                )

        return results
