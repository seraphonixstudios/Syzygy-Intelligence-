"""Web browser tool — browse and scrape web content using Playwright."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class BrowserTool:
    name: str = "browser"
    description: str = "Browse web pages, scrape content, and interact with websites"

    async def execute(
        self,
        url: str = "",
        action: str = "navigate",
        selector: str = "",
        timeout: int = 30000,
    ) -> dict[str, Any]:
        try:
            from playwright.async_api import async_playwright
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()
                await page.goto(url, timeout=timeout)

                if action == "screenshot":
                    screenshot = await page.screenshot(full_page=True)
                    import base64
                    return {
                        "screenshot": base64.b64encode(screenshot).decode(),
                        "url": url,
                    }

                if action == "text":
                    content = await page.inner_text("body")
                    return {"content": content[:10000], "url": url}

                if action == "extract" and selector:
                    elements = await page.query_selector_all(selector)
                    texts = [await el.inner_text() for el in elements[:10]]
                    return {"elements": texts, "url": url}

                await browser.close()
                return {"content": f"Navigated to {url}", "url": url}

        except ImportError:
            return {"error": "Playwright not installed. Run: pip install playwright && playwright install"}
        except Exception as e:
            return {"error": str(e)}
