"""Unit tests for Syzygy Tools."""

import pytest
from unittest.mock import patch, MagicMock
from app.tools.filesystem import FileSystemTool
from app.tools.code_execution import CodeExecutionTool
from app.tools.search import SearchTool


class TestFileSystemTool:
    @pytest.mark.asyncio
    async def test_write_and_read(self, tmp_path):
        tool = FileSystemTool()
        test_file = str(tmp_path / "test.txt")

        write_result = await tool.execute(action="write", path=test_file, content="Hello World")
        assert write_result["status"] == "written"

        read_result = await tool.execute(action="read", path=test_file)
        assert read_result["content"] == "Hello World"

    @pytest.mark.asyncio
    async def test_list_directory(self, tmp_path):
        tool = FileSystemTool()
        (tmp_path / "file1.txt").write_text("a")
        (tmp_path / "file2.txt").write_text("b")

        result = await tool.execute(action="list", path=str(tmp_path))
        assert "items" in result
        assert len(result["items"]) >= 2

    @pytest.mark.asyncio
    async def test_delete(self, tmp_path):
        tool = FileSystemTool()
        test_file = str(tmp_path / "delete_me.txt")
        await tool.execute(action="write", path=test_file, content="delete me")

        result = await tool.execute(action="delete", path=test_file)
        assert result["status"] == "deleted"

    @pytest.mark.asyncio
    async def test_nonexistent_path(self):
        tool = FileSystemTool()
        result = await tool.execute(action="read", path="/nonexistent/path")
        assert "error" in result


class TestCodeExecutionTool:
    @pytest.mark.asyncio
    async def test_python_execution(self):
        tool = CodeExecutionTool()
        result = await tool.execute(
            code="print('hello from syzygy')",
            language="python",
        )
        assert result["success"]
        assert "hello from syzygy" in result["stdout"]

    @pytest.mark.asyncio
    async def test_python_error(self):
        tool = CodeExecutionTool()
        result = await tool.execute(
            code="raise ValueError('test error')",
            language="python",
        )
        assert not result["success"]

    @pytest.mark.asyncio
    async def test_unsupported_language(self):
        tool = CodeExecutionTool()
        result = await tool.execute(code="test", language="brainfuck")
        assert "error" in result or not result["success"]


class TestSearchTool:
    @pytest.mark.asyncio
    async def test_search(self):
        tool = SearchTool()
        result = await tool.execute(query="Syzygy Intelligence", num_results=3)
        assert "results" in result
        assert isinstance(result["results"], list)

    @pytest.mark.asyncio
    async def test_search_empty_query(self):
        tool = SearchTool()
        result = await tool.execute(query="", num_results=3)
        assert "results" in result or "error" in result


class TestGitTool:
    @pytest.fixture
    def tool(self):
        from app.tools.git_tool import GitTool
        return GitTool()

    @pytest.mark.asyncio
    async def test_unknown_action(self, tool):
        result = await tool.execute(action="unknown_action")
        assert "error" in result

    @pytest.mark.asyncio
    async def test_status_not_a_git_repo(self, tool, tmp_path):
        result = await tool.execute(action="status", repo_path=str(tmp_path))
        assert "error" in result or "status" in result

    @pytest.mark.asyncio
    async def test_log_empty_repo(self, tool, tmp_path):
        result = await tool.execute(action="log", repo_path=str(tmp_path))
        assert "log" in result or "error" in result

    @pytest.mark.asyncio
    async def test_diff_empty_repo(self, tool, tmp_path):
        result = await tool.execute(action="diff", repo_path=str(tmp_path))
        assert "diff" in result or "error" in result

    @pytest.mark.asyncio
    async def test_branch_not_a_repo(self, tool, tmp_path):
        result = await tool.execute(action="branch", repo_path=str(tmp_path))
        assert "branches" in result or "error" in result


class TestBrowserTool:
    @pytest.fixture
    def tool(self):
        from app.tools.browser import BrowserTool
        return BrowserTool()

    @pytest.mark.asyncio
    async def test_navigate_no_playwright(self, tool):
        with patch("playwright.async_api.async_playwright") as mock_pw:
            mock_pw.side_effect = ImportError("Playwright not installed")
            result = await tool.execute(url="http://example.com", action="navigate")
            assert "error" in result
            assert "Playwright" in result["error"]

    @pytest.mark.asyncio
    async def test_screenshot_no_playwright(self, tool):
        with patch("playwright.async_api.async_playwright") as mock_pw:
            mock_pw.side_effect = ImportError("Not installed")
            result = await tool.execute(url="http://example.com", action="screenshot")
            assert "error" in result
