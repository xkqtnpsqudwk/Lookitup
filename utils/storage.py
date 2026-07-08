import json
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
SAMPLE_SOURCES_PATH = DATA_DIR / "sample_sources.json"
TRUSTED_SOURCES_PATH = DATA_DIR / "trusted_sources.json"
SOURCE_PACKS_PATH = DATA_DIR / "source_packs.json"


def ensure_data_files() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not TRUSTED_SOURCES_PATH.exists():
        TRUSTED_SOURCES_PATH.write_text("[]", encoding="utf-8")
    if not SAMPLE_SOURCES_PATH.exists():
        SAMPLE_SOURCES_PATH.write_text("[]", encoding="utf-8")
    if not SOURCE_PACKS_PATH.exists():
        SOURCE_PACKS_PATH.write_text("[]", encoding="utf-8")


def _read_json_list(path: Path) -> list[dict[str, Any]]:
    ensure_data_files()
    try:
        raw = path.read_text(encoding="utf-8").strip()
        data = json.loads(raw or "[]")
    except (OSError, json.JSONDecodeError):
        return []
    return data if isinstance(data, list) else []


def load_sample_sources() -> list[dict[str, Any]]:
    return _read_json_list(SAMPLE_SOURCES_PATH)


def load_saved_sources() -> list[dict[str, Any]]:
    return _read_json_list(TRUSTED_SOURCES_PATH)


def load_source_packs() -> list[dict[str, Any]]:
    return _read_json_list(SOURCE_PACKS_PATH)


def save_sources(sources: list[dict[str, Any]]) -> None:
    ensure_data_files()
    TRUSTED_SOURCES_PATH.write_text(
        json.dumps(sources, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def add_sources(new_sources: list[dict[str, Any]]) -> int:
    saved_sources = load_saved_sources()
    stamped_sources = []
    for source in new_sources:
        source_copy = dict(source)
        source_copy["library"] = "saved"
        stamped_sources.append(source_copy)
    save_sources(saved_sources + stamped_sources)
    return len(stamped_sources)


def clear_saved_sources() -> None:
    save_sources([])


def get_all_sources(include_samples: bool = True) -> list[dict[str, Any]]:
    sources: list[dict[str, Any]] = []
    if include_samples:
        sources.extend(load_sample_sources())
    sources.extend(load_saved_sources())
    return sources


def get_sources_for_pack(pack_id: str, include_samples: bool = True) -> list[dict[str, Any]]:
    sources = get_all_sources(include_samples)
    return [source for source in sources if source.get("pack_id") == pack_id]
