from __future__ import annotations

from typing import Any, Literal

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from utils.search_index import (
    build_evidence_index_stats,
    evaluate_search_state,
    group_evidence_cards,
    search_evidence_cards,
)
from utils.source_loader import load_rss_feed, load_website, make_source_record
from utils.storage import (
    add_sources,
    get_all_sources,
)
from utils.summarizer import generate_summary


class UrlSourceCreate(BaseModel):
    url: str
    source_name: str = ""
    trust_label: str = "Trusted source"


class RssSourceCreate(BaseModel):
    url: str
    source_name: str = ""
    trust_label: str = "Trusted source"
    limit: int = Field(default=8, ge=1, le=20)


class LocalTextSourceCreate(BaseModel):
    source_name: str
    title: str = ""
    text: str
    url: str = ""
    timestamp: str | None = None
    trust_label: str = "Trusted source"


class SearchRequest(BaseModel):
    query: str
    source_ids: list[str] = Field(default_factory=list)
    include_samples: bool = True
    limit: int = Field(default=10, ge=1, le=50)
    sort_by: Literal["BM25 relevance", "newest first"] = "BM25 relevance"


class SummaryRequest(SearchRequest):
    style: Literal["short paragraph", "bullet points", "timeline"] = "short paragraph"


app = FastAPI(
    title="Lookitup Backend",
    version="0.1.0",
    description="Controlled retrieval API for selected trusted sources and Trusted Result Cards.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
        "http://localhost:4173",
        "http://127.0.0.1:4173",
    ],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


def stamp_sources(records: list[dict[str, Any]], trust_label: str) -> list[dict[str, Any]]:
    stamped = []
    for record in records:
        source = dict(record)
        source["trust_label"] = trust_label.strip() or "Trusted source"
        stamped.append(source)
    return stamped


def get_selected_sources(source_ids: list[str], include_samples: bool) -> list[dict[str, Any]]:
    selected_ids = list(dict.fromkeys(source_id.strip() for source_id in source_ids if source_id.strip()))
    if not selected_ids:
        raise HTTPException(status_code=400, detail="Select at least one trusted source.")

    available_sources = get_all_sources(include_samples)
    sources_by_id = {str(source.get("id", "")): source for source in available_sources}
    missing_ids = [source_id for source_id in selected_ids if source_id not in sources_by_id]
    if missing_ids:
        raise HTTPException(status_code=404, detail=f"Unknown source id(s): {', '.join(missing_ids)}")

    return [sources_by_id[source_id] for source_id in selected_ids]


def source_summary(source: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": source.get("id"),
        "source_name": source.get("source_name"),
        "source_type": source.get("source_type"),
        "source_url": source.get("source_url"),
        "title": source.get("title"),
        "timestamp": source.get("timestamp"),
        "trust_label": source.get("trust_label"),
    }


def build_search_response(request: SearchRequest) -> dict[str, Any]:
    sources = get_selected_sources(request.source_ids, request.include_samples)
    cards = search_evidence_cards(request.query, sources, limit=request.limit, sort_by=request.sort_by)
    state = evaluate_search_state(request.query, cards)
    return {
        "query": request.query,
        "selected_sources": [source_summary(source) for source in sources],
        "status": state,
        "index_stats": build_evidence_index_stats(sources),
        "cards": cards,
    }


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/sources")
def list_sources(
    include_samples: bool = Query(default=True),
) -> dict[str, Any]:
    sources = get_all_sources(include_samples)
    return {
        "count": len(sources),
        "sources": sources,
    }


@app.post("/sources/url", status_code=201)
def add_url_source(payload: UrlSourceCreate) -> dict[str, Any]:
    try:
        record = load_website(payload.url, payload.source_name)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    stamped = stamp_sources([record], payload.trust_label)
    add_sources(stamped)
    return {"added": 1, "source": stamped[0]}


@app.post("/sources/rss", status_code=201)
def add_rss_source(payload: RssSourceCreate) -> dict[str, Any]:
    try:
        records = load_rss_feed(payload.url, payload.source_name, payload.limit)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    stamped = stamp_sources(records, payload.trust_label)
    add_sources(stamped)
    return {"added": len(stamped), "sources": stamped}


@app.post("/sources/local", status_code=201)
def add_local_text_source(payload: LocalTextSourceCreate) -> dict[str, Any]:
    if not payload.text.strip():
        raise HTTPException(status_code=400, detail="Local text cannot be empty.")
    record = make_source_record(
        source_name=payload.source_name,
        source_type="Local sample text",
        source_url=payload.url,
        title=payload.title or payload.source_name,
        timestamp=payload.timestamp,
        text=payload.text,
    )
    stamped = stamp_sources([record], payload.trust_label)
    add_sources(stamped)
    return {"added": 1, "source": stamped[0]}


@app.post("/search")
def search(payload: SearchRequest) -> dict[str, Any]:
    if not payload.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty.")
    return build_search_response(payload)


@app.post("/evidence/group")
def group_evidence(payload: SearchRequest) -> dict[str, Any]:
    response = build_search_response(payload)
    response["grouping_message"] = "Trusted results grouped by source and time."
    response["groups"] = group_evidence_cards(response["cards"])
    return response


@app.post("/evidence/summary")
def summarize_evidence(payload: SummaryRequest) -> dict[str, Any]:
    response = build_search_response(payload)
    if response["status"]["status"] == "not_found":
        return {
            **response,
            "summary": {
                "mode": "Blocked",
                "summary": "Not found in trusted sources.",
                "notice": "No retrieved Trusted Result Cards were available.",
            },
        }

    summary = generate_summary(payload.query, response["cards"][:5], payload.style)
    return {
        **response,
        "summary": summary,
    }
