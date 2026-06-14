"""Tests for BrowserTool — web browsing and scraping via Playwright."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.tools.browser import BrowserTool


class TestBrowserTool:
    def test_name(self):
        assert BrowserTool().name == "browser"

    def test_description(self):
        assert "browse" in BrowserTool().description.lower()

    @pytest.mark.asyncio
    async def test_import_error_returns_error_dict(self):
        tool = BrowserTool()
        with patch("playwright.async_api.async_playwright", side_effect=ImportError("No module")):
            result = await tool.execute(url="http://example.com")
            assert "error" in result
            assert "Playwright not installed" in result["error"]

    @pytest.mark.asyncio
    async def test_generic_exception_returns_error_dict(self):
        tool = BrowserTool()
        with patch("playwright.async_api.async_playwright") as mock_pw:
            mock_pw.return_value.__aenter__.return_value.chromium.launch.side_effect = RuntimeError("Crash")
            result = await tool.execute(url="http://example.com")
            assert "error" in result
            assert "Crash" in result["error"]

    @pytest.mark.asyncio
    async def test_navigate_action(self):
        tool = BrowserTool()
        mock_page = AsyncMock()
        mock_browser = AsyncMock()
        mock_browser.new_page = AsyncMock(return_value=mock_page)

        mock_playwright = MagicMock()
        mock_playwright.chromium.launch = AsyncMock(return_value=mock_browser)

        with patch("playwright.async_api.async_playwright") as mock_pw:
            mock_pw.return_value.__aenter__.return_value = mock_playwright
            result = await tool.execute(url="http://example.com", action="navigate")
            assert "Navigated to" in result["content"]
            mock_page.goto.assert_called_once_with("http://example.com", timeout=30000)

    @pytest.mark.asyncio
    async def test_screenshot_action(self):
        tool = BrowserTool()
        mock_page = AsyncMock()
        mock_page.screenshot = AsyncMock(return_value=b"fake_png_bytes")
        mock_browser = AsyncMock()
        mock_browser.new_page = AsyncMock(return_value=mock_page)

        mock_playwright = MagicMock()
        mock_playwright.chromium.launch = AsyncMock(return_value=mock_browser)

        with patch("playwright.async_api.async_playwright") as mock_pw:
            mock_pw.return_value.__aenter__.return_value = mock_playwright
            result = await tool.execute(url="http://example.com", action="screenshot")
            assert "screenshot" in result
            assert result["url"] == "http://example.com"
            mock_page.screenshot.assert_called_once_with(full_page=True)

    @pytest.mark.asyncio
    async def test_text_action(self):
        tool = BrowserTool()
        mock_page = AsyncMock()
        mock_page.inner_text = AsyncMock(return_value="Page body text content")
        mock_browser = AsyncMock()
        mock_browser.new_page = AsyncMock(return_value=mock_page)

        mock_playwright = MagicMock()
        mock_playwright.chromium.launch = AsyncMock(return_value=mock_browser)

        with patch("playwright.async_api.async_playwright") as mock_pw:
            mock_pw.return_value.__aenter__.return_value = mock_playwright
            result = await tool.execute(url="http://example.com", action="text")
            assert result["content"] == "Page body text content"
            mock_page.inner_text.assert_called_once_with("body")

    @pytest.mark.asyncio
    async def test_extract_action(self):
        tool = BrowserTool()
        mock_el1 = AsyncMock()
        mock_el1.inner_text = AsyncMock(return_value="Element 1")
        mock_el2 = AsyncMock()
        mock_el2.inner_text = AsyncMock(return_value="Element 2")
        mock_page = AsyncMock()
        mock_page.query_selector_all = AsyncMock(return_value=[mock_el1, mock_el2])
        mock_browser = AsyncMock()
        mock_browser.new_page = AsyncMock(return_value=mock_page)

        mock_playwright = MagicMock()
        mock_playwright.chromium.launch = AsyncMock(return_value=mock_browser)

        with patch("playwright.async_api.async_playwright") as mock_pw:
            mock_pw.return_value.__aenter__.return_value = mock_playwright
            result = await tool.execute(url="http://example.com", action="extract", selector="p")
            assert result["elements"] == ["Element 1", "Element 2"]
            mock_page.query_selector_all.assert_called_once_with("p")
