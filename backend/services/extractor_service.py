"""Turn a raw source (RSS URL, website URL, or manual text) into searchable items.

Each item is a dict: ``{"title", "url", "timestamp", "content"}``.
"""

from __future__ import annotations

import re
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import Any

import feedparser
import fitz  # PyMuPDF
import requests
from bs4 import BeautifulSoup

REQUEST_HEADERS = {
    "User-Agent": "Lookitup hackathon MVP/0.1 (+https://example.com/lookitup)"
}


class ExtractionError(ValueError):
    """Raised when a source cannot be read or contains no usable text."""


def clean_text(value: str) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


def html_to_text(html: str) -> str:
    soup = BeautifulSoup(html or "", "html.parser")
    for tag in soup(["script", "style", "noscript", "svg"]):
        tag.decompose()
    return clean_text(soup.get_text(" "))


def normalize_timestamp(value: Any) -> str | None:
    """Return an ISO-8601 UTC string, or ``None`` when the value is unusable."""
    if not value:
        return None
    if isinstance(value, datetime):
        parsed = value
    else:
        raw = str(value).strip()
        try:
            parsed = parsedate_to_datetime(raw)
        except (TypeError, ValueError, IndexError, OverflowError):
            try:
                parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
            except ValueError:
                return raw
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc).replace(microsecond=0).isoformat()


def extract_rss(url: str, limit: int = 12) -> list[dict[str, Any]]:
    if not url.strip():
        raise ExtractionError("An RSS source needs a feed URL.")
    feed = feedparser.parse(url)
    if getattr(feed, "bozo", False) and not feed.entries:
        raise ExtractionError(
            "Could not read this RSS feed. Check that the URL is a valid RSS or Atom feed."
        )
    if not feed.entries:
        raise ExtractionError("No entries were found in this RSS feed.")

    items: list[dict[str, Any]] = []
    for entry in feed.entries[:limit]:
        title = html_to_text(entry.get("title", "Untitled RSS item")) or "Untitled RSS item"
        parts = [entry.get("summary", ""), entry.get("description", "")]
        for content in entry.get("content", []) or []:
            parts.append(content.get("value", ""))
        body = html_to_text(" ".join(parts))
        published = entry.get("published") or entry.get("updated") or entry.get("created")
        items.append(
            {
                "title": title,
                "url": entry.get("link", url),
                "timestamp": normalize_timestamp(published),
                "content": body or title,
            }
        )
    return items


def extract_website(url: str) -> list[dict[str, Any]]:
    if not url.strip():
        raise ExtractionError("A website source needs a URL.")
    try:
        response = requests.get(url, headers=REQUEST_HEADERS, timeout=12)
        response.raise_for_status()
    except requests.RequestException as exc:
        raise ExtractionError(f"Website request failed: {exc}") from exc

    soup = BeautifulSoup(response.text, "html.parser")
    for tag in soup(["script", "style", "noscript", "svg"]):
        tag.decompose()
    title = clean_text(soup.title.get_text(" ")) if soup.title else url
    text = clean_text(soup.get_text(" "))
    if len(text) < 50:
        raise ExtractionError("This page did not contain enough readable text.")
    return [
        {
            "title": title or url,
            "url": url,
            "timestamp": normalize_timestamp(datetime.now(timezone.utc)),
            "content": text,
        }
    ]


def _parse_pdf_date(raw: str | None) -> str | None:
    """Parse a PDF metadata date like ``D:20240115120000+00'00'`` to ISO UTC."""
    if not raw:
        return None
    match = re.match(r"D?:?(\d{4})(\d{2})?(\d{2})?(\d{2})?(\d{2})?(\d{2})?", raw.strip())
    if not match:
        return None
    year, month, day, hour, minute, second = (
        int(part) if part else default
        for part, default in zip(match.groups(), (0, 1, 1, 0, 0, 0))
    )
    try:
        parsed = datetime(year, month, day, hour, minute, second, tzinfo=timezone.utc)
    except ValueError:
        return None
    return parsed.replace(microsecond=0).isoformat()


def extract_pdf(file_bytes: bytes, file_name: str, name: str = "") -> list[dict[str, Any]]:
    """Extract text from an uploaded PDF into a single searchable item."""
    if not file_bytes:
        raise ExtractionError("The uploaded PDF is empty.")
    try:
        with fitz.open(stream=file_bytes, filetype="pdf") as document:
            pages = [page.get_text("text") for page in document]
            metadata = document.metadata or {}
    except Exception as exc:  # PyMuPDF raises a broad set of errors on bad input
        raise ExtractionError(f"Could not read this PDF: {exc}") from exc

    text = clean_text("\n".join(pages))
    if len(text) < 20:
        raise ExtractionError(
            "This PDF contained no extractable text. Scanned/image-only PDFs need OCR, "
            "which is out of scope for this MVP."
        )

    meta_title = clean_text(metadata.get("title", ""))
    title = name.strip() or meta_title or file_name
    timestamp = _parse_pdf_date(metadata.get("creationDate") or metadata.get("modDate"))
    return [
        {
            "title": title,
            "url": "",
            "timestamp": timestamp,
            "content": text,
        }
    ]


def build_manual(content: str, name: str, url: str = "") -> list[dict[str, Any]]:
    text = clean_text(content)
    if not text:
        raise ExtractionError("Manual text cannot be empty.")
    return [
        {
            "title": name.strip() or "Manual note",
            "url": url.strip(),
            "timestamp": normalize_timestamp(datetime.now(timezone.utc)),
            "content": text,
        }
    ]
