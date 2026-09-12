"""Web search tool — search the web for information.

Primary source is DuckDuckGo HTML. Where DuckDuckGo bot-gates (HTTP 202 with a
challenge page instead of results), falls back to Wikipedia full-text search so
research workflows can still ground their output in retrieved sources.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class SearchTool:
    name: str = "search"
    description: str = "Search the web for information"

    async def execute(
        self,
        query: str = "",
        num_results: int = 5,
    ) -> dict[str, Any]:
        try:
            results = await self._duckduckgo(query, num_results)
            source = "duckduckgo"
            if not results:
                results = await self._wikipedia(query, num_results)
                source = "wikipedia" if results else "none"
            return {"query": query, "results": results, "count": len(results), "source": source}

        except ImportError:
            return {"error": "httpx not installed", "query": query, "results": []}
        except Exception as e:
            return {"error": str(e), "query": query, "results": []}

    async def _duckduckgo(self, query: str, num_results: int) -> list[dict[str, Any]]:
        from urllib.parse import quote

        import httpx

        # Use DuckDuckGo as a free search option
        url = f"https://html.duckduckgo.com/html/?q={quote(query)}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }

        async with httpx.AsyncClient(follow_redirects=True, timeout=15.0) as client:
            response = await client.get(url, headers=headers)

        # Simple HTML parsing for results
        results = []
        if response.status_code == 200:
            import re
            # Extract result links and snippets
            links = re.findall(
                r'<a[^>]+class="result__a"[^>]+href="([^"]+)"[^>]*>(.*?)</a>',
                response.text,
            )
            snippets = re.findall(
                r'<a[^>]+class="result__snippet"[^>]*>(.*?)</a>',
                response.text,
            )

            for i, (url_link, title) in enumerate(links[:num_results]):
                snippet = snippets[i] if i < len(snippets) else ""
                import html
                results.append({
                    "title": html.unescape(re.sub(r'<[^>]+>', '', title)).strip(),
                    "url": url_link,
                    "snippet": html.unescape(re.sub(r'<[^>]+>', '', snippet)).strip(),
                })

        return results

    async def _wikipedia(self, query: str, num_results: int) -> list[dict[str, Any]]:
        """Fallback: Wikipedia full-text search (free, no key, rarely gated)."""
        import re
        from html import unescape

        import httpx

        if not query.strip():
            return []
        params = {
            "action": "query",
            "list": "search",
            "srsearch": query,
            "srlimit": max(1, num_results),
            "format": "json",
        }
        headers = {"User-Agent": "SyzygyIntelligence/0.1 (research workflow; local dev)"}
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(
                    "https://en.wikipedia.org/w/api.php", params=params, headers=headers
                )
            if response.status_code != 200:
                return []
            items = response.json().get("query", {}).get("search", [])
        except Exception:
            return []

        results = []
        for item in items[:num_results]:
            title = item.get("title", "Untitled")
            url = "https://en.wikipedia.org/wiki/" + title.replace(" ", "_")
            snippet = unescape(re.sub(r"<[^>]+>", "", item.get("snippet", ""))).strip()
            results.append({"title": title, "url": url, "snippet": snippet})
        return results
