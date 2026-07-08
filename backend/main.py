"""Lookitup backend — trusted-source search for journalists.

Run with::

    cd backend
    pip install -r requirements.txt
    uvicorn main:app --reload
"""

from __future__ import annotations

from fastapi import FastAPI, File, Form, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from models.schemas import (
    SearchResponse,
    SortOption,
    SourceCreate,
    SourceOut,
)
from services import search_service, source_service

app = FastAPI(
    title="Lookitup Backend",
    version="1.0.0",
    description="Search only inside sources the journalist trusts. Never the open web.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:4173",
        "http://127.0.0.1:4173",
    ],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/sources", response_model=list[SourceOut])
def get_sources() -> list[dict]:
    return source_service.list_sources()


@app.post("/sources", response_model=SourceOut, status_code=201)
def add_source(payload: SourceCreate) -> SourceOut:
    try:
        return source_service.add_source(payload)
    except source_service.SourceError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/sources/pdf", response_model=SourceOut, status_code=201)
async def add_pdf_source(
    file: UploadFile = File(...),
    name: str = Form(default=""),
) -> SourceOut:
    if file.content_type not in ("application/pdf", "application/octet-stream") and not (
        file.filename or ""
    ).lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Please upload a PDF file.")
    file_bytes = await file.read()
    try:
        return source_service.add_pdf_source(file_bytes, file.filename or "document.pdf", name)
    except source_service.SourceError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.delete("/sources")
def delete_sources() -> dict[str, int | str]:
    removed = source_service.delete_all_sources()
    return {"status": "cleared", "removed": removed}


@app.post("/sources/load-samples")
def load_samples() -> dict[str, object]:
    added = source_service.load_samples()
    return {"added": len(added), "sources": added}


@app.get("/search", response_model=SearchResponse)
def search(
    q: str = Query(default="", description="Search query."),
    sort: SortOption = Query(default="relevance"),
) -> SearchResponse:
    if not q.strip():
        raise HTTPException(status_code=400, detail="Search query cannot be empty.")
    results = search_service.search(q, sort)
    return SearchResponse(query=q, count=len(results), results=results)
