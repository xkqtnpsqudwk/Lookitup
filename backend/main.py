from __future__ import annotations

import uuid
from datetime import datetime, timezone
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
    get_sources_for_pack,
    load_source_packs,
    save_source_packs,
)
from utils.summarizer import generate_summary


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


class SourcePackCreate(BaseModel):
    id: str | None = Field(default=None, description="Optional stable source pack id.")
    name: str
    description: str = ""
    created_by: str = "Lookitup API"


class UrlSourceCreate(BaseModel):
    pack_id: str
    url: str
    source_name: str = ""
    trust_label: str = "Trusted source"


class RssSourceCreate(BaseModel):
    pack_id: str
    url: str
    source_name: str = ""
    trust_label: str = "Trusted source"
    limit: int = Field(default=8, ge=1, le=20)


class LocalTextSourceCreate(BaseModel):
    pack_id: str
    source_name: str
    title: str = ""
    text: str
    url: str = ""
    timestamp: str | None = None
    trust_label: str = "Trusted source"


class SearchRequest(BaseModel):
    query: str
    source_pack_id: str
    include_samples: bool = True
    limit: int = Field(default=10, ge=1, le=50)
    sort_by: Literal["BM25 relevance", "newest first"] = "BM25 relevance"


class SummaryRequest(SearchRequest):
    style: Literal["short paragraph", "bullet points", "timeline"] = "short paragraph"


app = FastAPI(
    title="Lookitup Backend",
    version="0.1.0",
    description="Controlled retrieval API for preset source packs and Trusted Result Cards.",
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


def require_pack(pack_id: str) -> dict[str, Any]:
    for pack in load_source_packs():
        if pack.get("id") == pack_id:
            return pack
    raise HTTPException(status_code=404, detail=f"Unknown source pack: {pack_id}")


def stamp_sources(records: list[dict[str, Any]], pack_id: str, trust_label: str) -> list[dict[str, Any]]:
    stamped = []
    for record in records:
        source = dict(record)
        source["pack_id"] = pack_id
        source["trust_label"] = trust_label.strip() or "Trusted source"
        stamped.append(source)
    return stamped


def build_search_response(request: SearchRequest) -> dict[str, Any]:
    require_pack(request.source_pack_id)
    sources = get_sources_for_pack(request.source_pack_id, request.include_samples)
    cards = search_evidence_cards(request.query, sources, limit=request.limit, sort_by=request.sort_by)
    state = evaluate_search_state(request.query, cards)
    return {
        "query": request.query,
        "source_pack": require_pack(request.source_pack_id),
        "status": state,
        "index_stats": build_evidence_index_stats(sources),
        "cards": cards,
    }


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/source-packs")
def list_source_packs() -> list[dict[str, Any]]:
    return load_source_packs()


@app.post("/source-packs", status_code=201)
def create_source_pack(payload: SourcePackCreate) -> dict[str, Any]:
    packs = load_source_packs()
    pack_id = payload.id or str(uuid.uuid4())
    if any(pack.get("id") == pack_id for pack in packs):
        raise HTTPException(status_code=409, detail=f"Source pack already exists: {pack_id}")

    pack = {
        "id": pack_id,
        "name": payload.name,
        "description": payload.description,
        "created_by": payload.created_by,
        "created_at": utc_now_iso(),
    }
    packs.append(pack)
    save_source_packs(packs)
    return pack


@app.get("/sources")
def list_sources(
    pack_id: str | None = Query(default=None),
    include_samples: bool = Query(default=True),
) -> dict[str, Any]:
    if pack_id:
        require_pack(pack_id)
        sources = get_sources_for_pack(pack_id, include_samples)
    else:
        sources = get_all_sources(include_samples)
    return {
        "count": len(sources),
        "sources": sources,
    }


@app.post("/sources/url", status_code=201)
def add_url_source(payload: UrlSourceCreate) -> dict[str, Any]:
    require_pack(payload.pack_id)
    try:
        record = load_website(payload.url, payload.source_name)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    stamped = stamp_sources([record], payload.pack_id, payload.trust_label)
    add_sources(stamped)
    return {"added": 1, "source": stamped[0]}


@app.post("/sources/rss", status_code=201)
def add_rss_source(payload: RssSourceCreate) -> dict[str, Any]:
    require_pack(payload.pack_id)
    try:
        records = load_rss_feed(payload.url, payload.source_name, payload.limit)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    stamped = stamp_sources(records, payload.pack_id, payload.trust_label)
    add_sources(stamped)
    return {"added": len(stamped), "sources": stamped}


@app.post("/sources/local", status_code=201)
def add_local_text_source(payload: LocalTextSourceCreate) -> dict[str, Any]:
    require_pack(payload.pack_id)
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
    stamped = stamp_sources([record], payload.pack_id, payload.trust_label)
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
    response["grouping_message"] = "Evidence grouped by source and time."
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
                "notice": "No retrieved Evidence Cards were available.",
            },
        }

    summary = generate_summary(payload.query, response["cards"][:5], payload.style)
    return {
        **response,
        "summary": summary,
    }
