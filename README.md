# Lookitup

**Having a doubt? Just Lookitup.**

Lookitup is a 48-hour hackathon MVP for journalists. The MVP proves one workflow:

> A journalist selects trusted sources, searches a topic, and reviews Trusted Result Cards before publishing.

## Core Message

Google searches the open web. Lookitup searches your trusted world.

Lookitup is not an AI truth machine. It helps journalists search faster inside sources they already trust.

Search first. AI only when useful. Trusted sources only. Journalists decide.

## Technical Flow

```text
Trusted source list
  -> user selects source ids
  -> URL / RSS / local sample ingestion
  -> text extraction
  -> chunking
  -> SQLite FTS5 search index
  -> topic or keyword search
  -> Trusted Result Card ranking
  -> result review
```

## Features

- Direct trusted source selection. No hidden preset grouping layer.
- URL, RSS, PDF, and local sample text ingestion.
- Local sample corpus for demo reliability without network access.
- SQLite FTS5 / BM25-style retrieval over chunked trusted text.
- Topic search inside only the selected trusted sources.
- Trusted Result Cards with source name, source format, matched quote, timestamp, recency label, URL, match count, score, and explanation.
- Clear no-result state:
  - `No result found does not mean the claim is false. It only means Lookitup could not find it inside your selected trusted sources.`

## Installation

```bash
cd lookitup
pip install -r requirements.txt
```

## Run

Backend API first:

```bash
python -m uvicorn backend.main:app --reload --port 8000
```

React + Vite frontend:

```bash
cd frontend
npm install
npm run dev
```

Open:

```text
http://localhost:5173
```

The React app calls the FastAPI backend at `http://127.0.0.1:8000`.

The app runs locally and stores added sources in `data/trusted_sources.json`.

## Backend API

```text
GET  /health
GET  /sources
POST /sources/url
POST /sources/rss
POST /sources/local
POST /search
POST /evidence/group
POST /evidence/summary
```

The React MVP uses `/sources` and `/search` for the main demo flow.
The group and summary endpoints remain available for follow-up work, but they are not required for the core MVP path.

Example search request:

```bash
curl -X POST http://localhost:8000/search ^
  -H "Content-Type: application/json" ^
  -d "{\"query\":\"Iran Israel rockets\",\"source_ids\":[\"sample-iran-rockets-1\",\"sample-iran-rockets-2\",\"sample-iran-rockets-3\"]}"
```

OpenAPI docs are available at:

```text
http://localhost:8000/docs
```

## Demo Queries

In the React app, use the demo query chips or manually select trusted sources and search:

```text
Iran Israel rockets
```

Expected result: multiple Trusted Result Cards with timestamps and matched excerpts.

No-result demo:

```text
quantum banana treaty
```

## MVP Scope

- Main flow: source selection -> topic search -> result review.
- Search is keyword-based and does not require AI.
- No saved presets, login, auth, crawler, or production database.

## Limitations

- This branch uses React + Vite instead of the originally recommended Next.js frontend.
- The SQLite FTS5 index is built locally from the selected sources at runtime.
- Website extraction may fail on pages that block requests or render content with JavaScript.
- PDF extraction works best with text-based PDFs.
- No login, accounts, payments, production crawler, or fake-image detection.

## Technical Claim

The technical value is a controlled retrieval pipeline that makes trusted-source results visible before publication.
