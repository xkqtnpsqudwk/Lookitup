# Lookitup

**Having a doubt? Just Lookitup.**

A trusted-source search engine for journalists. Lookitup works like a search
engine, but instead of searching the entire open web, it searches **only inside
sources the journalist has chosen to trust**.

## Problem

When a story breaks, journalists are flooded with claims from the open web,
where anything can rank. Verifying against sources they already trust is slow and
manual. Lookitup makes that fast: add trusted sources once, then search inside
only those sources.

## Core message

> Google searches the open web. Lookitup searches your trusted world.
>
> Search first. AI only when useful. Trusted sources only. Journalists decide.

## MVP scope

The minimum flow, and the whole point of this MVP:

1. **Add trusted sources** — RSS feed, website, manual text, or PDF upload.
2. **Search inside those trusted sources** — keyword search, never the open web.
3. **Show trusted results** — as Trusted Result Cards.

No login, no accounts, no crawler, no universal fact-checker, no AI-for-every-query.

## Tech stack

- **Frontend:** React, Vite, TypeScript, plain CSS.
- **Backend:** FastAPI, Python, Uvicorn, Pydantic.
- **Storage:** local JSON files (`backend/data/`).
- **Extraction:** `feedparser` (RSS), `requests` + `BeautifulSoup` (websites),
  `PyMuPDF` (PDF text).

## Project structure

```text
lookitup/
├─ frontend/          React + Vite + TS app
│  └─ src/
│     ├─ api/         backend client
│     ├─ components/  Header, SourceForm, SourceList, SearchBar, ResultCard
│     ├─ pages/       HomePage, AboutPage
│     ├─ types/       shared TS types
│     └─ styles/      global.css
└─ backend/           FastAPI app
   ├─ main.py         API endpoints
   ├─ models/         Pydantic schemas
   ├─ services/       source, search, extractor, storage
   └─ data/           trusted_sources.json, sample_sources.json
```

## Install & run

**Backend:**

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

The API runs at `http://localhost:8000` (OpenAPI docs at `/docs`).

**Frontend:**

```bash
cd frontend
npm install
npm run dev
```

The app runs at `http://localhost:5173` and calls the backend at
`http://localhost:8000`. Override with a `VITE_API_BASE_URL` env var if needed.

## Demo query

1. Click **Load sample sources**.
2. Search **`Iran Israel rockets`**.

Expected result: multiple Trusted Result Cards with timestamps, matched
excerpts, match counts, and relevance scores.

## API endpoints

```text
GET    /health                 → {"status": "ok"}
GET    /sources                → list of trusted sources
POST   /sources                → add an rss / website / manual source (JSON)
POST   /sources/pdf            → add a PDF source (multipart file upload)
DELETE /sources                → clear all sources (reset demo)
POST   /sources/load-samples   → load backend/data/sample_sources.json
GET    /search?q=...&sort=...  → search (sort: relevance | newest)
GET    /summarize?q=...&style=  → optional AI summary of results (needs OPENAI_API_KEY)
```

## Limitations

- **Lookitup is not a universal truth engine.**
- **The quality of results depends on the quality of the trusted sources selected
  by the journalist.**
- **No result found does not mean the claim is false.**
- **Lookitup does not search the open web by default.**
- Website extraction may fail on pages that block requests or render with JavaScript.
- PDF extraction reads text-based PDFs only; scanned/image-only PDFs would need OCR (out of scope).
- Search is keyword-based; it does not understand meaning or synonyms.

## Future extensions

Beyond the core MVP, Lookitup now also has an **optional AI summary** (OpenAI,
generated only from the trusted results). Set `OPENAI_API_KEY` to enable it; without
a key the app still works and the summary button shows a clear message.

Still on the roadmap:

- Image EXIF metadata tab and image flagging.
- C2PA provenance/signature verification for uploaded images.
- Archive.org article-version comparison.
- OCR for scanned/image-only PDFs.
- Source diversity indicator.
- C2PA / SynthID-related checks if reliable tooling becomes available.
