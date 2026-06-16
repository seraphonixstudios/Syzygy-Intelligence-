"""Unit tests for Syzygy Tools."""

import subprocess
from unittest.mock import patch

import pytest

from app.tools.code_execution import CodeExecutionTool
from app.tools.filesystem import FileSystemTool
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
    async def test_delete_file(self, tmp_path):
        tool = FileSystemTool()
        test_file = str(tmp_path / "delete_me.txt")
        await tool.execute(action="write", path=test_file, content="delete me")

        result = await tool.execute(action="delete", path=test_file)
        assert result["status"] == "deleted"
        assert not tmp_path.joinpath("delete_me.txt").exists()

    @pytest.mark.asyncio
    async def test_delete_directory(self, tmp_path):
        tool = FileSystemTool()
        subdir = tmp_path / "mydir"
        subdir.mkdir()
        (subdir / "nested.txt").write_text("nested")

        result = await tool.execute(action="delete", path=str(subdir))
        assert result["status"] == "deleted"
        assert not subdir.exists()

    @pytest.mark.asyncio
    async def test_delete_nonexistent_path(self):
        tool = FileSystemTool()
        result = await tool.execute(action="delete", path="/nonexistent/path")
        assert "error" in result

    @pytest.mark.asyncio
    async def test_unknown_action(self):
        tool = FileSystemTool()
        result = await tool.execute(action="unknown")
        assert "error" in result
        assert "Unknown action" in result["error"]

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

    @pytest.mark.asyncio
    async def test_shell_execution(self):
        tool = CodeExecutionTool()
        result = await tool.execute(code="echo hello_shell", language="shell")
        assert result["success"]
        assert "hello_shell" in result["stdout"]

    @pytest.mark.asyncio
    async def test_shell_error(self):
        tool = CodeExecutionTool()
        result = await tool.execute(code="exit 1", language="shell")
        assert not result["success"]
        assert result["return_code"] == 1

    @pytest.mark.asyncio
    async def test_shell_timeout(self):
        tool = CodeExecutionTool()
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.TimeoutExpired(cmd="sleep", timeout=0.001)
            result = await tool.execute(code="sleep 100", language="shell", timeout=0.001)
        assert "error" in result
        assert "timed out" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_execution_generic_exception(self):
        tool = CodeExecutionTool()
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = RuntimeError("unexpected failure")
            result = await tool.execute(code="test", language="python")
        assert not result["success"]
        assert "error" in result


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

    @pytest.mark.asyncio
    async def test_search_import_error(self):
        tool = SearchTool()
        with patch.dict("sys.modules", {"httpx": None}):
            with patch("builtins.__import__", side_effect=ImportError("no httpx")):
                result = await tool.execute(query="test")
        assert "error" in result
        assert "httpx" in result["error"]

    @pytest.mark.asyncio
    async def test_search_httpx_exception(self):
        tool = SearchTool()
        with patch("httpx.AsyncClient") as mock_client:
            mock_client.side_effect = RuntimeError("HTTP connection failed")
            result = await tool.execute(query="test")
        assert "error" in result


class TestGitTool:
    @pytest.fixture
    def tool(self):
        from app.tools.git_tool import GitTool
        return GitTool()

    @pytest.fixture
    def git_repo(self, tmp_path):
        subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True, timeout=10)
        subprocess.run(
            ["git", "config", "user.email", "test@test.com"],
            cwd=tmp_path, capture_output=True, timeout=10,
        )
        subprocess.run(
            ["git", "config", "user.name", "Test"],
            cwd=tmp_path, capture_output=True, timeout=10,
        )
        (tmp_path / "file.txt").write_text("hello")
        subprocess.run(["git", "add", "file.txt"], cwd=tmp_path, capture_output=True, timeout=10)
        subprocess.run(
            ["git", "commit", "-m", "initial"],
            cwd=tmp_path, capture_output=True, timeout=10,
        )
        return tmp_path

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

    @pytest.mark.asyncio
    async def test_status_in_repo(self, tool, git_repo):
        result = await tool.execute(action="status", repo_path=str(git_repo))
        assert "status" in result

    @pytest.mark.asyncio
    async def test_log_in_repo(self, tool, git_repo):
        result = await tool.execute(action="log", repo_path=str(git_repo))
        assert "log" in result
        assert isinstance(result["log"], list)
        assert len(result["log"]) >= 1

    @pytest.mark.asyncio
    async def test_branch_in_repo(self, tool, git_repo):
        result = await tool.execute(action="branch", repo_path=str(git_repo))
        assert "branches" in result
        assert isinstance(result["branches"], list)
        assert len(result["branches"]) >= 1
        assert any(b.strip() for b in result["branches"])

    @pytest.mark.asyncio
    async def test_commit_in_repo(self, tool, git_repo):
        (git_repo / "new.txt").write_text("new content")
        result = await tool.execute(
            action="commit", repo_path=str(git_repo), message="second commit",
        )
        assert result["committed"] is True
        assert result["message"] == "second commit"

    @pytest.mark.asyncio
    async def test_diff_with_uncommitted(self, tool, git_repo):
        (git_repo / "file.txt").write_text("modified content")
        result = await tool.execute(action="diff", repo_path=str(git_repo))
        assert "diff" in result
        assert "modified" in result["diff"] or "+modified" in result["diff"]


class TestToolRegistry:
    def test_get_returns_none_for_missing(self):
        from app.tools import ToolRegistry
        registry = ToolRegistry()
        assert registry.get("nonexistent") is None

    def test_list_returns_dicts(self):
        from app.tools import ToolRegistry
        registry = ToolRegistry()
        result = registry.list()
        assert isinstance(result, list)
        assert len(result) > 0
        assert all("id" in item for item in result)
        assert all("name" in item for item in result)

    @pytest.mark.asyncio
    async def test_execute_returns_error_for_missing_tool(self):
        from app.tools import ToolRegistry
        registry = ToolRegistry()
        result = await registry.execute("nonexistent", {})
        assert "error" in result
        assert "nonexistent" in result["error"]


class TestFileSystemToolExtra:
    @pytest.mark.asyncio
    async def test_read_directory_returns_items(self, tmp_path):
        tool = FileSystemTool()
        (tmp_path / "file1.txt").write_text("a")
        (tmp_path / "subdir").mkdir()
        result = await tool.execute(action="read", path=str(tmp_path))
        assert "directory" in result
        assert "items" in result
        assert "file1.txt" in result["items"]
        assert "subdir" in result["items"]

    @pytest.mark.asyncio
    async def test_list_nonexistent_path_returns_error(self):
        tool = FileSystemTool()
        result = await tool.execute(action="list", path="/nonexistent_path_xyz")
        assert "error" in result

    @pytest.mark.asyncio
    async def test_exception_handler(self):
        tool = FileSystemTool()
        # null byte doesn't raise on Windows; None triggers TypeError in Path()
        result = await tool.execute(action="read", path=None)
        assert "error" in result


class TestSearchToolExtra:
    @pytest.mark.asyncio
    async def test_search_snippets_shorter_than_links(self):
        from unittest.mock import AsyncMock, MagicMock, patch
        tool = SearchTool()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = (
            '<a class="result__a" href="http://url1">Title1</a>'
            '<a class="result__a" href="http://url2">Title2</a>'
            '<a class="result__snippet">Snippet1</a>'
        )
        with patch("httpx.AsyncClient") as mock_cls:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_cls.return_value.__aenter__.return_value = mock_client
            result = await tool.execute(query="test", num_results=5)
        assert "results" in result
        assert len(result["results"]) == 2
        assert result["results"][0]["snippet"] == "Snippet1"
        assert result["results"][1]["snippet"] == ""


class TestGitToolExtra:
    @pytest.mark.asyncio
    async def test_clone_action(self):
        from unittest.mock import MagicMock
        from app.tools.git_tool import GitTool
        tool = GitTool()
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="cloned", stderr="")
            result = await tool.execute(
                action="clone", url="http://fake.url/repo", repo_path="/tmp/t"
            )
        assert result["cloned"] is True
        assert result["url"] == "http://fake.url/repo"
        assert result["path"] == "/tmp/t"


class TestToolRegistryExecuteWithValidTool:
    @pytest.mark.asyncio
    async def test_execute_with_valid_tool(self, tmp_path):
        from app.tools import ToolRegistry
        registry = ToolRegistry()
        test_file = str(tmp_path / "test.txt")
        result = await registry.execute("filesystem", {"action": "write", "path": test_file, "content": "hello"})
        assert result["status"] == "written"


class TestBrowserTool:
    @pytest.fixture
    def tool(self):
        pytest.importorskip("playwright")
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
