"""Built-in tool: web search via HTML scraping."""

import re
from typing import Any
from urllib.parse import quote_plus

from agent.models.search import SearchResult
from agent.models.tools import ToolResult
from agent.tools.protocol import Tool


class WebSearchTool(Tool):
    name = "web_search"
    description = "搜索网页内容，使用Bing搜索引擎"
    permissions = "safe"
    parameters = {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "搜索关键词"},
            "num_results": {"type": "integer", "description": "结果数量，默认5"},
        },
        "required": ["query"],
    }

    def __init__(self, http_client: Any = None) -> None:
        self._http = http_client

    async def execute(self, args: dict[str, Any]) -> ToolResult:
        query = args["query"]
        num = args.get("num_results", 5)

        if self._http is None:
            return ToolResult(
                success=False, error="HTTP client not configured", data={"results": []}
            )

        try:
            results = await self._search_duckduckgo(query, num)
            if results:
                return ToolResult(
                    success=True,
                    data={"results": [r.model_dump(mode="json") for r in results], "count": len(results)},
                )
        except Exception:
            pass

        try:
            results = await self._search_bing(query, num)
            if results:
                return ToolResult(
                    success=True,
                    data={"results": [r.model_dump(mode="json") for r in results], "count": len(results)},
                )
        except Exception:
            pass

        try:
            results = await self._search_sogou(query, num)
            return ToolResult(
                success=True,
                data={"results": [r.model_dump(mode="json") for r in results], "count": len(results)},
            )
        except Exception as e:
            return ToolResult(
                success=False, error=str(e), data={"results": [], "count": 0}
            )

    async def _search_bing(self, query: str, num: int) -> list[SearchResult]:
        url = f"https://www.bing.com/search?q={quote_plus(query)}&setlang=zh-cn&count={num}"
        resp = await self._http.get(url, headers={"User-Agent": "Mozilla/5.0"})
        html = resp.text

        results: list[SearchResult] = []
        blocks = re.findall(r'<li class="b_algo"[^>]*>(.*?)</li>', html, re.DOTALL)

        for block in blocks[:num]:
            title_m = re.search(r'<h2[^>]*><a[^>]*>(.*?)</a>', block, re.DOTALL)
            url_m = re.search(r'<a[^>]*href="(https?://[^"]+)"', block)
            snippet_m = re.search(r'<p[^>]*>(.*?)</p>', block, re.DOTALL)

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

    async def _search_duckduckgo(self, query: str, num: int) -> list[SearchResult]:
        from urllib.parse import unquote

        url = f"https://html.duckduckgo.com/html/?q={quote_plus(query)}"
        resp = await self._http.get(url, headers={"User-Agent": "Mozilla/5.0"})
        html = resp.text

        results: list[SearchResult] = []
        title_blocks = re.findall(r'class="result__a"[^>]*href="([^"]*)"[^>]*>(.*?)</a>', html, re.DOTALL)
        snippet_blocks = re.findall(r'class="result__snippet"[^>]*>(.*?)</', html, re.DOTALL)

        for i, (href, title_raw) in enumerate(title_blocks[:num]):
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

    async def _search_sogou(self, query: str, num: int) -> list[SearchResult]:
        from urllib.parse import unquote

        url = f"https://www.sogou.com/web?query={quote_plus(query)}"
        resp = await self._http.get(url, headers={
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        })
        html = resp.text

        results: list[SearchResult] = []
        blocks = re.findall(r'<div[^>]*class="[^"]*vrwrap[^"]*"[^>]*>(.*?)</div>\s*</div>\s*</div>', html, re.DOTALL)

        for block in blocks[:num]:
            title_m = re.search(r'<a[^>]*href="([^"]+)"[^>]*>(.*?)</a>', block, re.DOTALL)
            snippet_m = re.search(r'(?:star-wiki|space-txt)[^>]*>(.*?)</', block, re.DOTALL)

            if title_m:
                href = title_m.group(1)
                real_url = href
                redirect = re.search(r'url=([^&"\']+)', href)
                if redirect:
                    real_url = unquote(redirect.group(1))

                results.append(
                    SearchResult(
                        title=re.sub(r"<[^>]+>", "", title_m.group(2)).strip(),
                        url=real_url,
                        snippet=re.sub(r"<[^>]+>", "", snippet_m.group(1)).strip() if snippet_m else "",
                        provider="sogou",
                        domain="web",
                    )
                )

        return results
