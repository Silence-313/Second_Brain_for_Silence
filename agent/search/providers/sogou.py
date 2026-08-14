"""Sogou search provider — HTML scraping implementation."""

import re
from typing import Any
from urllib.parse import quote_plus, unquote

from agent.models.search import SearchResult
from agent.search.protocol import SearchProvider


class SogouSearchProvider(SearchProvider):
    name = "sogou"
    domain = "web"
    platforms = ["web", "bilibili", "video", "github", "arxiv", "paper", "code", "general"]
    fallback_providers = ["duckduckgo"]

    def __init__(self, http_client: Any = None) -> None:
        self._http = http_client

    async def search(self, query: str, num_results: int = 10) -> list[SearchResult]:
        if self._http is None:
            return []

        url = f"https://www.sogou.com/web?query={quote_plus(query)}"
        resp = await self._http.get(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
            },
            timeout=15,
        )
        html = resp.text

        results: list[SearchResult] = []
        blocks = re.findall(
            r'<div[^>]*class="[^"]*vrwrap[^"]*"[^>]*>(.*?)</div>\s*</div>\s*</div>', html, re.DOTALL
        )

        for block in blocks[:num_results]:
            title_m = re.search(r'<a[^>]*href="([^"]+)"[^>]*>(.*?)</a>', block, re.DOTALL)
            snippet_m = re.search(
                r"(?:star-wiki|space-txt|str-text-info)[^>]*>(.*?)</", block, re.DOTALL
            )

            if title_m:
                href = title_m.group(1)
                # Sogou uses redirect links, extract real URL
                real_url = href
                redirect = re.search(r'url=([^&"\']+)', href)
                if redirect:
                    real_url = unquote(redirect.group(1))

                results.append(
                    SearchResult(
                        title=re.sub(r"<[^>]+>", "", title_m.group(2)).strip(),
                        url=real_url,
                        snippet=re.sub(r"<[^>]+>", "", snippet_m.group(1)).strip()
                        if snippet_m
                        else "",
                        provider="sogou",
                        domain="web",
                    )
                )

        return results
