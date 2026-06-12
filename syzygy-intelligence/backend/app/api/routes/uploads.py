"""Upload routes — file and link upload handling."""

from __future__ import annotations

import uuid
from pathlib import Path
from typing import Any

from fastapi import APIRouter, File, HTTPException, UploadFile
from pydantic import BaseModel

from app.config import settings
from app.logging_setup import logger

router = APIRouter()

UPLOAD_DIR = Path(settings.upload_dir)
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/gif", "image/webp"}
MAX_FILE_SIZE = settings.max_upload_size_mb * 1024 * 1024


class LinkPayload(BaseModel):
    url: str


class LinkResponse(BaseModel):
    url: str
    title: str
    description: str
    favicon: str


@router.post("/file")
async def upload_file(file: UploadFile = File(...)) -> dict[str, Any]:
    if file.content_type and file.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {file.content_type}")
    ext = Path(file.filename or "image.png").suffix or ".png"
    filename = f"{uuid.uuid4().hex}{ext}"
    dest = UPLOAD_DIR / filename
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail=f"File exceeds {settings.max_upload_size_mb}MB limit")
    dest.write_bytes(content)
    url = f"/uploads/{filename}"
    logger.info("File uploaded", filename=filename, size=len(content), type=file.content_type)
    return {"url": url, "filename": filename, "size": len(content), "content_type": file.content_type}


@router.post("/link")
async def upload_link(payload: LinkPayload) -> LinkResponse:
    import httpx
    from bs4 import BeautifulSoup

    url = payload.url.strip()
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    try:
        async with httpx.AsyncClient(timeout=10, follow_redirects=True) as client:
            resp = await client.get(url, headers={"User-Agent": "SyzygyBot/1.0"})
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")
            title = str(soup.title.string).strip() if soup.title and soup.title.string else url
            meta_desc = soup.find("meta", attrs={"name": "description"})
            desc_tag = meta_desc or soup.find("meta", attrs={"property": "og:description"})
            description = str(desc_tag.get("content", "")).strip() if desc_tag else ""
            favicon_tag = soup.find("link", rel=lambda v: v and "icon" in v.lower()) if hasattr(soup, "find") else None
            favicon = ""
            if favicon_tag and favicon_tag.get("href"):
                favicon_href = favicon_tag["href"]
                if isinstance(favicon_href, str):
                    favicon = favicon_href
                    if favicon.startswith("/"):
                        from urllib.parse import urlparse
                        parsed = urlparse(url)
                        favicon = f"{parsed.scheme}://{parsed.netloc}{favicon}"
        logger.info("Link processed", url=url, title=title)
        return LinkResponse(url=url, title=title, description=description, favicon=favicon)
    except Exception as e:
        logger.error("Link fetch failed", url=url, error=str(e))
        return LinkResponse(url=url, title=url, description="", favicon="")
