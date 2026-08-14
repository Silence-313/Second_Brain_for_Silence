"""DuckDuckGo search provider — HTML scraping implementation."""

import re
from typing import Any
from urllib.parse import quote_plus, unquote

from agent.models.search import SearchResult
from agent.search.protocol import SearchProvider


class DuckDuckGoSearchProvider(SearchProvider):
    name = "duckduckgo"
    domain = "web"
    platforms = ["web", "bilibili", "video", "github", "arxiv", "paper", "code", "general"]
    fallback_providers = []

    def __init__(self, http_client: Any = None) -> None:
        self._http = http_client

    async def search(self, query: str, num_results: int = 10) -> list[SearchResult]:
        if self._http is None:
            return []

        url = f"https://html.duckduckgo.com/html/?q={quote_plus(query)}"
        resp = await self._http.get(
            url, headers={"User-Agent": "Mozilla/5.0 (compatible; Agent/1.0)"}, timeout=15
        )
        html = resp.text

        results: list[SearchResult] = []
        title_blocks = re.findall(
            r'class="result__a"[^>]*href="([^"]*)"[^>]*>(.*?)</a>', html, re.DOTALL
        )
        snippet_blocks = re.findall(r'class="result__snippet"[^>]*>(.*?)</', html, re.DOTALL)

        for i, (href, title_raw) in enumerate(title_blocks[:num_results]):
            real_url = ""
            uddg = re.search(r'uddg=([^&"\']+)', href)
            if uddg:
                real_url = unquote(uddg.group(1))
            else:
                real_url = href

            snippet = ""
            if i < len(snippet_blocks):
                snippet = re.sub(r"<[^>]+>", "", snippet_blocks[i]).strip()

            results.append(
                SearchResult(
                    title=re.sub(r"<[^>]+>", "", title_raw).strip(),
                    url=real_url,
                    snippet=snippet,
                    provider="duckduckgo",
                    domain="web",
                )
            )

        return results
