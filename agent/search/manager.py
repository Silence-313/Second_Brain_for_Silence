"""Search manager — orchestrate multi-provider search with merge/rank/dedup."""

import re
import time
from typing import Any
from urllib.parse import urlparse

from agent.models.search import MergedSearchResult, SearchResult
from agent.search.protocol import SearchProvider


class SearchManager:
    """Orchestrate multi-provider search: parallel execution, merge, rank, dedup."""

    def __init__(self) -> None:
        self._providers: dict[str, SearchProvider] = {}

    def register_provider(self, provider: SearchProvider) -> None:
        self._providers[provider.name] = provider

    def get_provider(self, name: str) -> SearchProvider | None:
        return self._providers.get(name)

    def list_providers(self) -> list[dict[str, Any]]:
        return [p.to_info() for p in self._providers.values()]

    async def search(
        self,
        query: str,
        providers: list[str] | None = None,
        strategy: str = "parallel",
    ) -> MergedSearchResult:
        start = time.monotonic()
        provider_names = providers or list(self._providers.keys())
        all_results: list[SearchResult] = []
        providers_used: list[str] = []
        errors: list[str] = []

        for name in provider_names:
            p = self._providers.get(name)
            if p is None:
                errors.append(f"Provider not found: {name}")
                continue

            try:
                results = await p.search(query)
                all_results.extend(results)
                providers_used.append(name)
            except Exception:
                # Try fallback providers
                for fb_name in p.fallback_providers:
                    fb = self._providers.get(fb_name)
                    if fb is None:
                        continue
                    try:
                        results = await fb.search(query)
                        all_results.extend(results)
                        providers_used.append(fb_name)
                        break
                    except Exception:
                        continue
                else:
                    errors.append(f"All providers failed for: {name}")

        if not all_results:
            return MergedSearchResult(
                query=query,
                results=[],
                providers_used=providers_used,
                total_results=0,
                latency_ms=round((time.monotonic() - start) * 1000, 2),
            )

        ranked = self._rank(all_results, query)
        deduped = self._deduplicate(ranked)

        return MergedSearchResult(
            query=query,
            results=deduped,
            providers_used=providers_used,
            total_results=len(deduped),
            latency_ms=round((time.monotonic() - start) * 1000, 2),
        )

    @staticmethod
    def _rank(results: list[SearchResult], query: str) -> list[SearchResult]:
        query_lower = query.lower()
        query_terms = set(re.findall(r"[a-zA-Z一-鿿]{2,}", query_lower))

        def score(r: SearchResult) -> float:
            s = 0.0
            content = f"{r.title} {r.snippet}".lower()
            for term in query_terms:
                if term in content:
                    s += 1.0
                if term in r.title.lower():
                    s += 2.0
            return s

        return sorted(results, key=score, reverse=True)

    @staticmethod
    def _deduplicate(results: list[SearchResult]) -> list[SearchResult]:
        seen_urls: set[str] = set()
        unique: list[SearchResult] = []

        for r in results:
            normalized = SearchManager._normalize_url(r.url)
            if normalized not in seen_urls:
                seen_urls.add(normalized)
                unique.append(r)

        return unique

    @staticmethod
    def _normalize_url(url: str) -> str:
        try:
            parsed = urlparse(url)
            return f"{parsed.scheme}://{parsed.netloc.lower()}{parsed.path.rstrip('/')}"
        except Exception:
            return url.lower().strip().rstrip("/")
