from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any


def parse_timestamp(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def display_date(value: str | None) -> str:
    parsed = parse_timestamp(value)
    if parsed:
        return parsed.strftime("%Y-%m-%d %H:%M UTC")
    return value or "No date"


def recency_label_and_boost(value: str | None) -> tuple[str, float]:
    parsed = parse_timestamp(value)
    if not parsed:
        return "No date", 0.0
    age_days = (datetime.now(timezone.utc) - parsed).days
    if age_days <= 30:
        return "Recent", 5.0
    if age_days <= 365:
        return "Older", 2.0
    return "Older", 0.0


def _terms(query: str) -> list[str]:
    return [term for term in re.findall(r"[A-Za-z0-9]+", query.lower()) if len(term) > 1]


def _count_term(text: str, term: str) -> int:
    return len(re.findall(rf"\b{re.escape(term)}\b", text, flags=re.IGNORECASE))


def _first_match_index(text_lower: str, query_lower: str, terms: list[str]) -> int:
    phrase_index = text_lower.find(query_lower)
    if phrase_index >= 0:
        return phrase_index
    indexes = [text_lower.find(term) for term in terms if text_lower.find(term) >= 0]
    return min(indexes) if indexes else 0


def build_excerpt(text: str, query: str, radius: int = 170) -> str:
    clean = re.sub(r"\s+", " ", text or "").strip()
    if not clean:
        return ""
    text_lower = clean.lower()
    query_lower = query.lower().strip()
    terms = _terms(query)
    index = _first_match_index(text_lower, query_lower, terms)
    start = max(index - radius, 0)
    end = min(index + len(query) + radius, len(clean))
    excerpt = clean[start:end].strip()
    if start > 0:
        excerpt = f"... {excerpt}"
    if end < len(clean):
        excerpt = f"{excerpt} ..."
    return excerpt


def search_sources(
    query: str,
    sources: list[dict[str, Any]],
    sort_by: str = "relevance",
) -> list[dict[str, Any]]:
    clean_query = query.strip()
    if not clean_query:
        return []

    query_lower = clean_query.lower()
    terms = _terms(clean_query)
    results: list[dict[str, Any]] = []
    for source in sources:
        searchable_text = " ".join(
            [
                str(source.get("title", "")),
                str(source.get("source_name", "")),
                str(source.get("text", "")),
            ]
        )
        text_lower = searchable_text.lower()
        exact_count = text_lower.count(query_lower)
        term_counts = {term: _count_term(searchable_text, term) for term in terms}
        total_term_matches = sum(term_counts.values())
        if exact_count == 0 and total_term_matches == 0:
            continue

        recency_label, recency_boost = recency_label_and_boost(source.get("timestamp"))
        all_terms_bonus = 4.0 if terms and all(term_counts.values()) else 0.0
        score = exact_count * 10.0 + total_term_matches + recency_boost + all_terms_bonus
        explanation = "Keyword found in this source."
        if exact_count:
            explanation = "Exact keyword or phrase found in this source."

        result = dict(source)
        result.update(
            {
                "excerpt": build_excerpt(str(source.get("text", "")), clean_query),
                "match_count": exact_count if exact_count else total_term_matches,
                "exact_match_count": exact_count,
                "term_match_count": total_term_matches,
                "score": round(score, 2),
                "recency": recency_label,
                "date_display": display_date(source.get("timestamp")),
                "explanation": explanation,
            }
        )
        results.append(result)

    if sort_by == "newest first":
        return sorted(
            results,
            key=lambda item: parse_timestamp(item.get("timestamp")) or datetime.min.replace(tzinfo=timezone.utc),
            reverse=True,
        )
    return sorted(results, key=lambda item: item.get("score", 0), reverse=True)
