from __future__ import annotations

import re
import sqlite3
from datetime import datetime, timezone
from typing import Any

from utils.search import build_excerpt, display_date, parse_timestamp, recency_label_and_boost


EVENT_TERMS = {
    "rocket": "rockets",
    "rockets": "rockets",
    "missile": "missiles",
    "missiles": "missiles",
    "drone": "drones",
    "drones": "drones",
    "copyright": "copyright",
    "regulation": "regulation",
    "image": "image",
    "fake": "fake image",
}

CONTRAST_PAIRS = {
    ("rockets", "missiles"),
    ("rockets", "drones"),
    ("missiles", "rockets"),
    ("drones", "rockets"),
    ("regulation", "copyright"),
    ("copyright", "regulation"),
}


def tokenize_query(query: str) -> list[str]:
    return [token.lower() for token in re.findall(r"[A-Za-z0-9]+", query) if len(token) > 1]


def make_fts_query(query: str) -> str:
    tokens = tokenize_query(query)
    return " OR ".join(f'"{token}"' for token in tokens)


def chunk_text(text: str, chunk_size: int = 700, overlap: int = 120) -> list[str]:
    clean = re.sub(r"\s+", " ", text or "").strip()
    if not clean:
        return []
    if len(clean) <= chunk_size:
        return [clean]

    chunks = []
    start = 0
    while start < len(clean):
        end = min(start + chunk_size, len(clean))
        chunk = clean[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end == len(clean):
            break
        start = max(end - overlap, start + 1)
    return chunks


def _connection_with_index(sources: list[dict[str, Any]]) -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.execute(
        """
        CREATE TABLE chunks (
            id INTEGER PRIMARY KEY,
            document_id TEXT,
            source_name TEXT,
            source_type TEXT,
            title TEXT,
            url TEXT,
            timestamp TEXT,
            trust_label TEXT,
            chunk_index INTEGER,
            text TEXT
        )
        """
    )
    conn.execute(
        """
        CREATE VIRTUAL TABLE chunks_fts
        USING fts5(title, source_name, text, content='chunks', content_rowid='id', tokenize='unicode61')
        """
    )

    chunk_id = 1
    for source in sources:
        text = str(source.get("text", ""))
        for chunk_index, chunk in enumerate(chunk_text(text), start=1):
            conn.execute(
                """
                INSERT INTO chunks (
                    id, document_id, source_name, source_type, title, url, timestamp,
                    trust_label, chunk_index, text
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    chunk_id,
                    source.get("id", ""),
                    source.get("source_name", "Untitled source"),
                    source.get("source_type", "Unknown"),
                    source.get("title", ""),
                    source.get("source_url", ""),
                    source.get("timestamp"),
                    source.get("trust_label", "Trusted source"),
                    chunk_index,
                    chunk,
                ),
            )
            conn.execute(
                "INSERT INTO chunks_fts(rowid, title, source_name, text) VALUES (?, ?, ?, ?)",
                (
                    chunk_id,
                    source.get("title", ""),
                    source.get("source_name", "Untitled source"),
                    chunk,
                ),
            )
            chunk_id += 1
    return conn


def build_evidence_index_stats(sources: list[dict[str, Any]]) -> dict[str, int]:
    chunk_count = sum(len(chunk_text(str(source.get("text", "")))) for source in sources)
    return {
        "documents": len(sources),
        "chunks": chunk_count,
    }


def _match_count(query: str, text: str) -> int:
    terms = tokenize_query(query)
    return sum(len(re.findall(rf"\b{re.escape(term)}\b", text, flags=re.IGNORECASE)) for term in terms)


def _exact_match_count(query: str, text: str) -> int:
    clean_query = query.strip()
    if not clean_query:
        return 0
    return text.lower().count(clean_query.lower())


def _source_format(source_type: str) -> str:
    normalized = source_type.lower()
    if "rss" in normalized:
        return "RSS"
    if "website" in normalized or "url" in normalized:
        return "Website"
    if "pdf" in normalized:
        return "PDF"
    return "Manual text"


def search_evidence_cards(
    query: str,
    sources: list[dict[str, Any]],
    limit: int = 10,
    sort_by: str = "BM25 relevance",
) -> list[dict[str, Any]]:
    fts_query = make_fts_query(query)
    if not fts_query or not sources:
        return []

    try:
        conn = _connection_with_index(sources)
        rows = conn.execute(
            """
            SELECT
                chunks.*,
                bm25(chunks_fts) AS rank
            FROM chunks_fts
            JOIN chunks ON chunks_fts.rowid = chunks.id
            WHERE chunks_fts MATCH ?
            ORDER BY rank
            LIMIT ?
            """,
            (fts_query, limit),
        ).fetchall()
    except sqlite3.OperationalError:
        return []
    finally:
        try:
            conn.close()
        except UnboundLocalError:
            pass

    cards = []
    for row in rows:
        row_dict = dict(row)
        text = row_dict.get("text", "")
        searchable_text = " ".join([row_dict.get("title", ""), row_dict.get("source_name", ""), text])
        matches = _match_count(query, searchable_text)
        exact_matches = _exact_match_count(query, searchable_text)
        rank = float(row_dict.get("rank") or 0)
        recency, recency_boost = recency_label_and_boost(row_dict["timestamp"])
        score = round(100 / (1 + abs(rank)) + matches + (exact_matches * 4) + recency_boost, 2)
        explanation = "Keyword found in this trusted source."
        if exact_matches:
            explanation = "Exact keyword or phrase found in this trusted source."
        cards.append(
            {
                "chunk_id": row_dict["id"],
                "document_id": row_dict["document_id"],
                "source_name": row_dict["source_name"],
                "source_type": row_dict["source_type"],
                "title": row_dict["title"] or row_dict["source_name"],
                "matched_quote": build_excerpt(text, query, radius=190) or text[:380],
                "excerpt": build_excerpt(text, query, radius=190) or text[:380],
                "url": row_dict["url"],
                "source_url": row_dict["url"],
                "timestamp": row_dict["timestamp"],
                "date_display": display_date(row_dict["timestamp"]),
                "recency": recency,
                "source_format": _source_format(row_dict["source_type"]),
                "trust_label": row_dict["trust_label"],
                "chunk_index": row_dict["chunk_index"],
                "score": score,
                "rank": rank,
                "match_count": matches,
                "exact_match_count": exact_matches,
                "explanation": explanation,
                "text": text,
            }
        )

    if sort_by == "newest first":
        return sorted(
            cards,
            key=lambda item: parse_timestamp(item.get("timestamp")) or datetime.min.replace(tzinfo=timezone.utc),
            reverse=True,
        )
    return cards


def _event_terms_in(value: str) -> set[str]:
    tokens = tokenize_query(value)
    return {EVENT_TERMS[token] for token in tokens if token in EVENT_TERMS}


def evaluate_search_state(query: str, cards: list[dict[str, Any]]) -> dict[str, str]:
    if not cards:
        return {
            "status": "not_found",
            "label": "Not Found",
            "message": "Not found in trusted sources.",
        }

    query_terms = _event_terms_in(query)
    evidence_terms = _event_terms_in(" ".join(card.get("matched_quote", "") for card in cards[:3]))
    for evidence_term, claim_term in CONTRAST_PAIRS:
        if claim_term in query_terms and evidence_term in evidence_terms and claim_term not in evidence_terms:
            return {
                "status": "mismatch",
                "label": "Mismatch",
                "message": f"Trusted sources say {evidence_term}. Claim says {claim_term}.",
            }

    return {
        "status": "evidence_found",
        "label": "Evidence Found",
        "message": "Matching Evidence Cards found in the selected trusted source pack.",
    }


def group_evidence_cards(cards: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for card in cards:
        timestamp = card.get("timestamp") or ""
        date_key = timestamp[:10] if timestamp else "No date"
        key = (card.get("source_name", "Unknown source"), date_key)
        groups.setdefault(key, []).append(card)

    grouped = []
    for (source_name, date_key), group_cards in groups.items():
        grouped.append(
            {
                "source_name": source_name,
                "date": date_key,
                "count": len(group_cards),
                "top_score": max(card.get("score", 0) for card in group_cards),
                "cards": sorted(group_cards, key=lambda item: item.get("score", 0), reverse=True),
            }
        )
    return sorted(grouped, key=lambda item: (item["date"], item["top_score"]), reverse=True)
