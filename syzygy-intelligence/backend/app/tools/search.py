"""Web search tool — search the web for information."""

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
            import httpx
            from urllib.parse import quote

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

            return {"query": query, "results": results, "count": len(results)}

        except ImportError:
            return {"error": "httpx not installed", "query": query, "results": []}
        except Exception as e:
            return {"error": str(e), "query": query, "results": []}
