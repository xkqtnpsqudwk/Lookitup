from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

# Stored / returned source types. PDF sources exist too, but they are created
# through the file-upload endpoint, not the JSON POST /sources endpoint.
SourceType = Literal["rss", "website", "manual", "pdf"]
CreatableType = Literal["rss", "website", "manual"]
SortOption = Literal["relevance", "newest"]


class SourceCreate(BaseModel):
    """Payload for POST /sources (JSON sources only).

    - rss / website require ``url``.
    - manual requires ``content``.
    PDF sources are added via POST /sources/pdf (multipart file upload).
    """

    name: str = Field(default="", description="Display name for the trusted source.")
    type: CreatableType
    url: str = Field(default="", description="RSS or website URL.")
    content: str = Field(default="", description="Raw text for a manual source.")


class SourceItem(BaseModel):
    title: str
    url: str = ""
    timestamp: str | None = None
    content: str


class SourceOut(BaseModel):
    id: str
    name: str
    type: SourceType
    url: str = ""
    created_at: str
    item_count: int


class SearchResult(BaseModel):
    id: str
    source_id: str
    source_name: str
    source_type: SourceType
    title: str
    url: str = ""
    timestamp: str | None = None
    excerpt: str
    match_count: int
    score: int
    recency: str
    explanation: str


class SearchResponse(BaseModel):
    query: str
    count: int
    results: list[SearchResult]
