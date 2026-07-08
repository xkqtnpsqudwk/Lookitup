# Lookitup

**Having a doubt? Just Lookitup.**

Lookitup is a 48-hour hackathon MVP for journalists. It proves one workflow:

> A journalist selects a preset source pack, enters a text claim, searches only inside trusted sources, and receives Evidence Cards before publishing.

## Core Message

Google searches the open web. Lookitup searches your trusted world.

Lookitup is not an AI truth machine. It helps journalists search faster inside sources they already trust.

## Technical Flow

```text
Preset Trusted Source Pack
  -> URL / RSS / local sample ingestion
  -> text extraction
  -> chunking
  -> SQLite FTS5 search index
  -> claim or keyword search
  -> Evidence Card ranking
  -> mismatch / not-found state
  -> breaking-news evidence grouping
```

## Features

- Preset source packs:
  - France Official Sources Pack
  - International Breaking News Pack
  - Wire Services Pack
  - Local Authorities Pack
- URL, RSS, PDF, and local sample text ingestion.
- Local sample corpus for demo reliability without network access.
- SQLite FTS5 / BM25-style retrieval over chunked trusted text.
- Evidence Cards with source name, source type, matched quote, date, URL, ranking score, and trust label.
- Result states:
  - Evidence Found
  - Mismatch: `Trusted sources say X. Claim says Y.`
  - Not Found: `Not found in trusted sources.`
- Breaking-news evidence grouping by source and time.
- Optional evidence-grounded summary using only retrieved Evidence Cards.
- Basic image EXIF review retained as a secondary demo utility.

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

Legacy Streamlit prototype:


```bash
python -m streamlit run app.py
```

The app runs locally and stores added sources in `data/trusted_sources.json`.

## Backend API

```text
GET  /health
GET  /source-packs
POST /source-packs
GET  /sources
POST /sources/url
POST /sources/rss
POST /sources/local
POST /search
POST /evidence/group
POST /evidence/summary
```

Example search request:

```bash
curl -X POST http://localhost:8000/search ^
  -H "Content-Type: application/json" ^
  -d "{\"query\":\"Iran Israel rockets\",\"source_pack_id\":\"international-breaking-news\"}"
```

OpenAPI docs are available at:

```text
http://localhost:8000/docs
```

## Demo Queries

Use the `International Breaking News Pack`.

Evidence found:

```text
Iran Israel rockets
```

Mismatch demo:

```text
Iran Israel drones
```

Not-found demo:

```text
quantum banana treaty
```

## Optional LLM Summary

The P0 product works without generation. If `OPENAI_API_KEY` and a compatible OpenAI client are available, Lookitup can generate a constrained summary from retrieved Evidence Cards only.

If no key is available, Lookitup falls back to an extractive summary with Evidence Card citations.

## Limitations

- This branch keeps the existing Streamlit app instead of rebuilding the frontend in Next.js.
- The SQLite FTS5 index is built locally from the selected pack corpus at runtime.
- Mismatch detection is deterministic and lightweight for the demo case.
- Website extraction may fail on pages that block requests or render content with JavaScript.
- PDF extraction works best with text-based PDFs.
- No login, accounts, payments, production crawler, or fake-image detection.

## Technical Claim

The technical value is a controlled retrieval pipeline that makes evidence visible before publication.
