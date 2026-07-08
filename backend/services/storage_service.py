"""Local JSON file storage for trusted sources.

Sources are stored in ignored ``backend/data/trusted_sources.local.json`` as a
list of source objects, each shaped like the sample data
(see ``sample_sources.json``)::

    {
        "id": "source_...",
        "name": "AFP RSS",
        "type": "rss",
        "url": "https://example.com/rss",
        "created_at": "2026-07-08T12:00:00",
        "items": [{"title": ..., "url": ..., "timestamp": ..., "content": ...}]
    }
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

DATA_DIR = Path(__file__).resolve().parents[1] / "data"
TRUSTED_SOURCES_SEED_PATH = DATA_DIR / "trusted_sources.json"
TRUSTED_SOURCES_PATH = DATA_DIR / "trusted_sources.local.json"
SAMPLE_SOURCES_PATH = DATA_DIR / "sample_sources.json"


def _ensure_files() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not TRUSTED_SOURCES_PATH.exists():
        seed_sources = _read_json_list(TRUSTED_SOURCES_SEED_PATH)
        TRUSTED_SOURCES_PATH.write_text(
            json.dumps(seed_sources, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )


def _read_json_list(path: Path) -> list[dict[str, Any]]:
    """Read a JSON list, tolerating a missing file or malformed JSON."""
    try:
        raw = path.read_text(encoding="utf-8").strip()
        data = json.loads(raw or "[]")
    except (OSError, json.JSONDecodeError):
        return []
    return data if isinstance(data, list) else []


def load_sources() -> list[dict[str, Any]]:
    """Return all stored trusted sources."""
    _ensure_files()
    return _read_json_list(TRUSTED_SOURCES_PATH)


def save_sources(sources: list[dict[str, Any]]) -> None:
    _ensure_files()
    TRUSTED_SOURCES_PATH.write_text(
        json.dumps(sources, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def load_sample_sources() -> list[dict[str, Any]]:
    """Return the bundled demo sources from ``sample_sources.json``."""
    return _read_json_list(SAMPLE_SOURCES_PATH)
