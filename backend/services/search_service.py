"""Keyword search across the items stored inside trusted sources.

The search never touches the open web: it only reads what has already been
extracted and stored locally.
"""

from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any

from services import storage_service

# Scoring weights (tuned so an exact phrase match dominates keyword matches).
EXACT_PHRASE_WEIGHT = 40
KEYWORD_MATCH_WEIGHT = 8
ALL_KEYWORDS_BONUS = 6
RECENCY_BOOST = {"Recent": 8, "Older": 3, "No date": 0}
MAX_SCORE = 99


def _terms(query: str) -> list[str]:
    return [term for term in re.findall(r"[A-Za-z0-9]+", query.lower()) if len(term) > 1]


def _count_term(text: str, term: str) -> int:
    return len(re.findall(rf"\b{re.escape(term)}\b", text, flags=re.IGNORECASE))


def _parse_timestamp(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _recency(value: str | None) -> str:
    parsed = _parse_timestamp(value)
    if not parsed:
        return "No date"
    age_days = (datetime.now(timezone.utc) - parsed).days
    return "Recent" if age_days <= 30 else "Older"


def _build_excerpt(text: str, query: str, terms: list[str], radius: int = 160) -> str:
    clean = re.sub(r"\s+", " ", text or "").strip()
    if not clean:
        return ""
    lowered = clean.lower()
    query_lower = query.lower().strip()

    index = lowered.find(query_lower)
    if index < 0:
        candidates = [lowered.find(term) for term in terms if lowered.find(term) >= 0]
        index = min(candidates) if candidates else 0

    start = max(index - radius, 0)
    end = min(index + len(query_lower) + radius, len(clean))
    excerpt = clean[start:end].strip()
    if start > 0:
        excerpt = f"... {excerpt}"
    if end < len(clean):
        excerpt = f"{excerpt} ..."
    return excerpt


def search(query: str, sort: str = "relevance") -> list[dict[str, Any]]:
    clean_query = query.strip()
    if not clean_query:
        return []

    query_lower = clean_query.lower()
    terms = _terms(clean_query)
    sources = storage_service.load_sources()

    results: list[dict[str, Any]] = []
    for source in sources:
        source_id = source.get("id", "")
        source_name = source.get("name", "Untitled source")
        source_type = source.get("type", "manual")

        for item in source.get("items", []):
            title = str(item.get("title", ""))
            content = str(item.get("content", ""))
            searchable = f"{title} {content}"
            lowered = searchable.lower()

            exact_count = lowered.count(query_lower)
            term_counts = {term: _count_term(searchable, term) for term in terms}
            total_matches = sum(term_counts.values())
            if exact_count == 0 and total_matches == 0:
                continue

            timestamp = item.get("timestamp")
            recency = _recency(timestamp)
            all_terms_hit = bool(terms) and all(term_counts.values())

            raw_score = (
                exact_count * EXACT_PHRASE_WEIGHT
                + total_matches * KEYWORD_MATCH_WEIGHT
                + (ALL_KEYWORDS_BONUS if all_terms_hit else 0)
                + RECENCY_BOOST[recency]
            )
            score = min(MAX_SCORE, raw_score)

            explanation = "Keyword found in this trusted source."
            if exact_count:
                explanation = "Exact phrase found in this trusted source."
            elif all_terms_hit:
                explanation = "All keywords found in this trusted source."

            results.append(
                {
                    "source_id": source_id,
                    "source_name": source_name,
                    "source_type": source_type,
                    "title": title or source_name,
                    "url": item.get("url", ""),
                    "timestamp": timestamp,
                    "excerpt": _build_excerpt(content or title, clean_query, terms),
                    "match_count": exact_count if exact_count else total_matches,
                    "score": score,
                    "recency": recency,
                    "explanation": explanation,
                    "_sort_time": _parse_timestamp(timestamp),
                }
            )

    if sort == "newest":
        results.sort(
            key=lambda r: r["_sort_time"] or datetime.min.replace(tzinfo=timezone.utc),
            reverse=True,
        )
    else:
        results.sort(key=lambda r: r["score"], reverse=True)

    for index, result in enumerate(results, start=1):
        result["id"] = f"result_{index:03d}"
        result.pop("_sort_time", None)

    return results
