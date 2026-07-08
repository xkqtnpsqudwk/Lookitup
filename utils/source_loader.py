from __future__ import annotations

import re
import uuid
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import Any

import feedparser
import fitz
import requests
from bs4 import BeautifulSoup


REQUEST_HEADERS = {
    "User-Agent": "Lookitup hackathon MVP/0.1 (+https://example.com/lookitup)"
}


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def clean_text(value: str) -> str:
    text = re.sub(r"\s+", " ", value or "").strip()
    return text


def html_to_text(html: str) -> str:
    soup = BeautifulSoup(html or "", "html.parser")
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    return clean_text(soup.get_text(" "))


def normalize_timestamp(value: Any) -> str | None:
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
    return parsed.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def make_source_record(
    *,
    source_name: str,
    source_type: str,
    text: str,
    title: str = "",
    source_url: str = "",
    file_name: str = "",
    timestamp: str | None = None,
) -> dict[str, Any]:
    return {
        "id": str(uuid.uuid4()),
        "source_name": source_name.strip() or "Untitled source",
        "source_type": source_type,
        "source_url": source_url.strip(),
        "file_name": file_name.strip(),
        "title": title.strip() or source_name.strip() or "Untitled source",
        "timestamp": normalize_timestamp(timestamp),
        "text": clean_text(text),
        "created_at": utc_now_iso(),
    }


def load_rss_feed(url: str, source_name: str = "", limit: int = 10) -> list[dict[str, Any]]:
    feed = feedparser.parse(url)
    if getattr(feed, "bozo", False) and not feed.entries:
        raise ValueError("Could not read this RSS feed. Check that the URL is a valid RSS or Atom feed.")
    if not feed.entries:
        raise ValueError("No entries found in this RSS feed.")

    feed_title = clean_text(feed.feed.get("title", "")) if getattr(feed, "feed", None) else ""
    display_name = source_name.strip() or feed_title or url
    records: list[dict[str, Any]] = []
    for entry in feed.entries[:limit]:
        title = html_to_text(entry.get("title", "Untitled RSS item"))
        summary_parts = [
            entry.get("summary", ""),
            entry.get("description", ""),
        ]
        if entry.get("content"):
            summary_parts.extend(item.get("value", "") for item in entry.get("content", []))
        text = html_to_text(" ".join(summary_parts)) or title
        published = entry.get("published") or entry.get("updated") or entry.get("created")
        link = entry.get("link", url)
        records.append(
            make_source_record(
                source_name=display_name,
                source_type="RSS feed",
                source_url=link,
                title=title,
                timestamp=published,
                text=f"{title}. {text}",
            )
        )
    return records


def load_website(url: str, source_name: str = "") -> dict[str, Any]:
    try:
        response = requests.get(url, headers=REQUEST_HEADERS, timeout=12)
        response.raise_for_status()
    except requests.RequestException as exc:
        raise ValueError(f"Website request failed: {exc}") from exc

    soup = BeautifulSoup(response.text, "html.parser")
    for tag in soup(["script", "style", "noscript", "svg"]):
        tag.decompose()
    title = clean_text(soup.title.get_text(" ")) if soup.title else url
    text = clean_text(soup.get_text(" "))
    if len(text) < 50:
        raise ValueError("This page did not contain enough readable text for the library.")
    return make_source_record(
        source_name=source_name.strip() or title,
        source_type="Website",
        source_url=url,
        title=title,
        text=text,
    )


def load_pdf(file_bytes: bytes, file_name: str, source_name: str = "") -> dict[str, Any]:
    try:
        with fitz.open(stream=file_bytes, filetype="pdf") as document:
            page_text = [page.get_text("text") for page in document]
    except Exception as exc:
        raise ValueError(f"PDF extraction failed: {exc}") from exc

    text = clean_text("\n".join(page_text))
    if not text:
        raise ValueError("No readable text was found in this PDF.")
    return make_source_record(
        source_name=source_name.strip() or file_name,
        source_type="PDF",
        file_name=file_name,
        title=file_name,
        text=text,
    )
