"""Source lifecycle: add, list, delete, load samples.

A "source" is a trusted collection (an RSS feed, a website, or a manual note)
that owns one or more searchable items.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from models.schemas import SourceCreate, SourceOut
from services import extractor_service, storage_service


class SourceError(ValueError):
    """A user-facing problem while adding a source (bad input, duplicate, etc.)."""


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _new_id() -> str:
    return f"source_{uuid.uuid4().hex[:8]}"


def _to_out(source: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": source.get("id", ""),
        "name": source.get("name", "Untitled source"),
        "type": source.get("type", "manual"),
        "url": source.get("url", ""),
        "created_at": source.get("created_at", ""),
        "item_count": len(source.get("items", [])),
    }


def list_sources() -> list[dict[str, Any]]:
    return [_to_out(source) for source in storage_service.load_sources()]


def _existing_names() -> set[str]:
    return {str(source.get("name", "")).strip().lower() for source in storage_service.load_sources()}


def add_source(payload: SourceCreate) -> SourceOut:
    name = payload.name.strip()
    if not name:
        # Fall back to the URL for RSS/website; manual sources must be named.
        name = payload.url.strip() if payload.type in ("rss", "website") else ""
    if not name:
        raise SourceError("A source name is required.")

    if name.lower() in _existing_names():
        raise SourceError(f'A source named "{name}" already exists.')

    try:
        if payload.type == "rss":
            items = extractor_service.extract_rss(payload.url)
        elif payload.type == "website":
            items = extractor_service.extract_website(payload.url)
        elif payload.type == "manual":
            items = extractor_service.build_manual(payload.content, name, payload.url)
        else:  # pragma: no cover - guarded by pydantic Literal
            raise SourceError(f"Unsupported source type: {payload.type}")
    except extractor_service.ExtractionError as exc:
        raise SourceError(str(exc)) from exc

    record = {
        "id": _new_id(),
        "name": name,
        "type": payload.type,
        "url": payload.url.strip(),
        "created_at": _now_iso(),
        "items": items,
    }
    sources = storage_service.load_sources()
    sources.append(record)
    storage_service.save_sources(sources)
    return SourceOut(**_to_out(record))


def add_pdf_source(file_bytes: bytes, file_name: str, name: str = "") -> SourceOut:
    display_name = name.strip() or file_name.strip()
    if not display_name:
        raise SourceError("A PDF source needs a name or file name.")
    if display_name.lower() in _existing_names():
        raise SourceError(f'A source named "{display_name}" already exists.')

    try:
        # Let the item title come from the PDF's own metadata / file name,
        # while ``display_name`` stays the source (outlet) name.
        items = extractor_service.extract_pdf(file_bytes, file_name)
    except extractor_service.ExtractionError as exc:
        raise SourceError(str(exc)) from exc

    record = {
        "id": _new_id(),
        "name": display_name,
        "type": "pdf",
        "url": "",
        "created_at": _now_iso(),
        "items": items,
    }
    sources = storage_service.load_sources()
    sources.append(record)
    storage_service.save_sources(sources)
    return SourceOut(**_to_out(record))


def delete_all_sources() -> int:
    removed = len(storage_service.load_sources())
    storage_service.save_sources([])
    return removed


def load_samples() -> list[dict[str, Any]]:
    """Append bundled sample sources, skipping any whose name already exists."""
    stored = storage_service.load_sources()
    existing = {str(source.get("name", "")).strip().lower() for source in stored}

    added: list[dict[str, Any]] = []
    for sample in storage_service.load_sample_sources():
        name = str(sample.get("name", "")).strip()
        if not name or name.lower() in existing:
            continue
        record = {
            "id": sample.get("id") or _new_id(),
            "name": name,
            "type": sample.get("type", "manual"),
            "url": sample.get("url", ""),
            "created_at": sample.get("created_at") or _now_iso(),
            "items": sample.get("items", []),
        }
        stored.append(record)
        existing.add(name.lower())
        added.append(_to_out(record))

    storage_service.save_sources(stored)
    return added
