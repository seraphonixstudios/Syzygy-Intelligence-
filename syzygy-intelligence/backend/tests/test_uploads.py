"""Tests for file and link upload routes."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException


class TestUploadFile:
    @pytest.mark.asyncio
    async def test_upload_valid_image(self):
        mock_file = MagicMock()
        mock_file.content_type = "image/png"
        mock_file.filename = "test.png"
        mock_file.read = AsyncMock(return_value=b"fake_image_data")

        with (
            patch("app.api.routes.uploads.UPLOAD_DIR", MagicMock()),
            patch("app.api.routes.uploads.MAX_FILE_SIZE", 10 * 1024 * 1024),
            patch("app.api.routes.uploads.Path.write_bytes"),
            patch("app.api.routes.uploads.settings") as mock_settings,
        ):
            mock_settings.max_upload_size_mb = 10
            from app.api.routes.uploads import upload_file

            result = await upload_file(file=mock_file)
            assert "url" in result
            assert result["filename"].endswith(".png")
            assert result["size"] == len(b"fake_image_data")
            assert result["content_type"] == "image/png"

    @pytest.mark.asyncio
    async def test_rejects_unsupported_type(self):
        mock_file = MagicMock()
        mock_file.content_type = "application/pdf"
        mock_file.filename = "doc.pdf"
        mock_file.read = AsyncMock(return_value=b"data")

        from app.api.routes.uploads import upload_file

        with pytest.raises(HTTPException) as exc:
            await upload_file(file=mock_file)
        assert exc.value.status_code == 400
        assert "Unsupported file type" in str(exc.value.detail)

    @pytest.mark.asyncio
    async def test_rejects_no_content_type(self):
        mock_file = MagicMock()
        mock_file.content_type = None
        mock_file.filename = "test.png"

        from app.api.routes.uploads import upload_file

        # No content type means skip the check
        mock_file.read = AsyncMock(return_value=b"small")
        with (
            patch("app.api.routes.uploads.UPLOAD_DIR", MagicMock()),
            patch("app.api.routes.uploads.MAX_FILE_SIZE", 10 * 1024 * 1024),
            patch("app.api.routes.uploads.Path.write_bytes"),
        ):
            result = await upload_file(file=mock_file)
            assert "url" in result

    @pytest.mark.asyncio
    async def test_rejects_oversized_file(self):
        mock_file = MagicMock()
        mock_file.content_type = "image/jpeg"
        mock_file.filename = "large.jpg"
        mock_file.read = AsyncMock(return_value=b"x" * 5 * 1024 * 1024)

        with patch("app.api.routes.uploads.MAX_FILE_SIZE", 1024):
            from app.api.routes.uploads import upload_file

            with pytest.raises(HTTPException) as exc:
                await upload_file(file=mock_file)
            assert exc.value.status_code == 400
            assert "MB limit" in str(exc.value.detail)

    @pytest.mark.asyncio
    async def test_handles_missing_extension(self):
        mock_file = MagicMock()
        mock_file.content_type = "image/gif"
        mock_file.filename = "noext"
        mock_file.read = AsyncMock(return_value=b"data")

        with (
            patch("app.api.routes.uploads.UPLOAD_DIR", MagicMock()),
            patch("app.api.routes.uploads.MAX_FILE_SIZE", 10 * 1024 * 1024),
            patch("app.api.routes.uploads.Path.write_bytes"),
        ):
            from app.api.routes.uploads import upload_file

            result = await upload_file(file=mock_file)
            assert result["filename"].endswith(".png")

    @pytest.mark.asyncio
    async def test_handles_none_filename(self):
        mock_file = MagicMock()
        mock_file.content_type = "image/jpeg"
        mock_file.filename = None
        mock_file.read = AsyncMock(return_value=b"data")

        with (
            patch("app.api.routes.uploads.UPLOAD_DIR", MagicMock()),
            patch("app.api.routes.uploads.MAX_FILE_SIZE", 10 * 1024 * 1024),
            patch("app.api.routes.uploads.Path.write_bytes"),
        ):
            from app.api.routes.uploads import upload_file

            result = await upload_file(file=mock_file)
            assert result["filename"].endswith(".png")


class TestUploadLink:
    @pytest.mark.asyncio
    async def test_fetches_link_successfully(self):
        mock_response = AsyncMock()
        mock_response.text = (
            "<html><head><title>Test Page</title>"
            '<meta name="description" content="A test page">'
            '<link rel="icon" href="/favicon.ico"></head></html>'
        )
        mock_response.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.__aenter__.return_value.get = AsyncMock(return_value=mock_response)

        with patch("httpx.AsyncClient", return_value=mock_client):
            from app.api.routes.uploads import LinkPayload, upload_link

            result = await upload_link(LinkPayload(url="https://example.com"))
            assert result.url == "https://example.com"
            assert result.title == "Test Page"
            assert result.description == "A test page"
            assert result.favicon == "https://example.com/favicon.ico"

    @pytest.mark.asyncio
    async def test_adds_scheme_if_missing(self):
        mock_response = AsyncMock()
        mock_response.text = "<html><head><title>My Site</title></head></html>"
        mock_response.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.__aenter__.return_value.get = AsyncMock(return_value=mock_response)

        with patch("httpx.AsyncClient", return_value=mock_client):
            from app.api.routes.uploads import LinkPayload, upload_link

            result = await upload_link(LinkPayload(url="example.com"))
            assert result.url.startswith("https://")

    @pytest.mark.asyncio
    async def test_handles_missing_title(self):
        mock_response = AsyncMock()
        mock_response.text = "<html><head></head><body></body></html>"
        mock_response.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.__aenter__.return_value.get = AsyncMock(return_value=mock_response)

        with patch("httpx.AsyncClient", return_value=mock_client):
            from app.api.routes.uploads import LinkPayload, upload_link

            result = await upload_link(LinkPayload(url="https://example.com"))
            assert result.title == "https://example.com"

    @pytest.mark.asyncio
    async def test_handles_og_description(self):
        mock_response = AsyncMock()
        mock_response.text = (
            "<html><head><title>Page</title>"
            '<meta property="og:description" content="OG desc"></head></html>'
        )
        mock_response.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.__aenter__.return_value.get = AsyncMock(return_value=mock_response)

        with patch("httpx.AsyncClient", return_value=mock_client):
            from app.api.routes.uploads import LinkPayload, upload_link

            result = await upload_link(LinkPayload(url="https://example.com"))
            assert result.description == "OG desc"

    @pytest.mark.asyncio
    async def test_handles_absolute_favicon(self):
        mock_response = AsyncMock()
        mock_response.text = (
            "<html><head><title>Site</title>"
            '<link rel="icon" href="https://cdn.example.com/favicon.ico"></head></html>'
        )
        mock_response.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.__aenter__.return_value.get = AsyncMock(return_value=mock_response)

        with patch("httpx.AsyncClient", return_value=mock_client):
            from app.api.routes.uploads import LinkPayload, upload_link

            result = await upload_link(LinkPayload(url="https://example.com"))
            assert result.favicon == "https://cdn.example.com/favicon.ico"

    @pytest.mark.asyncio
    async def test_handles_no_favicon(self):
        mock_response = AsyncMock()
        mock_response.text = "<html><head><title>No Icon</title></head></html>"
        mock_response.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.__aenter__.return_value.get = AsyncMock(return_value=mock_response)

        with patch("httpx.AsyncClient", return_value=mock_client):
            from app.api.routes.uploads import LinkPayload, upload_link

            result = await upload_link(LinkPayload(url="https://example.com"))
            assert result.favicon == ""

    @pytest.mark.asyncio
    async def test_handles_favicon_tag_no_href(self):
        mock_response = AsyncMock()
        mock_response.text = (
            "<html><head><title>Fav</title>"
            '<link rel="icon"></head></html>'
        )
        mock_response.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.__aenter__.return_value.get = AsyncMock(return_value=mock_response)

        with patch("httpx.AsyncClient", return_value=mock_client):
            from app.api.routes.uploads import LinkPayload, upload_link

            result = await upload_link(LinkPayload(url="https://example.com"))
            assert result.favicon == ""

    @pytest.mark.asyncio
    async def test_handles_exception_gracefully(self):
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value.get = AsyncMock(
            side_effect=RuntimeError("connection failed")
        )

        with patch("httpx.AsyncClient", return_value=mock_client):
            from app.api.routes.uploads import LinkPayload, upload_link

            result = await upload_link(LinkPayload(url="https://example.com"))
            assert result.url == "https://example.com"
            assert result.title == "https://example.com"
            assert result.description == ""
            assert result.favicon == ""
