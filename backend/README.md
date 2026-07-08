# Lookitup Backend

FastAPI service that stores trusted sources locally and searches **only** inside
them. It never queries the open web at search time.

## Run

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

- API base: `http://localhost:8000`
- Interactive docs: `http://localhost:8000/docs`

## Endpoints

| Method | Path                    | Purpose                                        |
| ------ | ----------------------- | ---------------------------------------------- |
| GET    | `/health`               | Liveness check → `{"status": "ok"}`            |
| GET    | `/sources`              | List all stored trusted sources                |
| POST   | `/sources`              | Add an `rss`, `website`, or `manual` source    |
| POST   | `/sources/pdf`          | Add a `pdf` source (multipart file upload)     |
| DELETE | `/sources`              | Clear all sources (reset demo data)            |
| POST   | `/sources/load-samples` | Load bundled `data/sample_sources.json`        |
| GET    | `/search`               | Search stored sources (`?q=` and `?sort=`)     |
| GET    | `/summarize`            | Optional AI summary of results (`?q=&sort=&style=`) |

### Add a source

```jsonc
// rss / website
{ "name": "BBC RSS", "type": "rss", "url": "https://example.com/rss" }

// manual
{ "name": "Reporter note", "type": "manual", "content": "Text to search..." }
```

PDF sources use a multipart upload instead of JSON:

```bash
curl -X POST http://localhost:8000/sources/pdf \
  -F "file=@report.pdf;type=application/pdf" \
  -F "name=Newsroom report"
```

### Search

```text
GET /search?q=Iran%20Israel%20rockets&sort=relevance
```

`sort` is `relevance` (default) or `newest`.

### AI summary (optional)

`GET /summarize?q=...&sort=...&style=paragraph|bullets` runs the same search and
then asks OpenAI to summarize **only the returned trusted excerpts** (no open web,
no outside knowledge). It requires an OpenAI key:

```bash
export OPENAI_API_KEY="sk-..."          # Windows PowerShell: $env:OPENAI_API_KEY="sk-..."
# optional: export OPENAI_SUMMARY_MODEL="gpt-4o-mini"   (default)
```

Without a key the endpoint returns `503` with a clear message; the rest of the app
keeps working. Summarization is opt-in per query — Lookitup searches first, AI only
when the journalist asks.

## Structure

```text
backend/
├─ main.py                     FastAPI app + endpoints
├─ requirements.txt
├─ models/
│  └─ schemas.py               Pydantic request/response models
├─ services/
│  ├─ storage_service.py       JSON read/write
│  ├─ extractor_service.py     RSS / website / manual / PDF → searchable items
│  ├─ source_service.py        add / list / delete / load-samples
│  ├─ search_service.py        keyword search, scoring, excerpts
│  └─ summary_service.py       optional OpenAI summary of trusted results
└─ data/
   ├─ trusted_sources.json     saved sources (starts empty)
   └─ sample_sources.json      demo corpus
```

## Storage model

Each source owns a list of searchable `items`:

```jsonc
{
  "id": "source_ab12cd34",
  "name": "Middle East Security Monitor",
  "type": "rss",
  "url": "https://example.com/rss",
  "created_at": "2026-07-08T09:30:00",
  "items": [
    { "title": "...", "url": "...", "timestamp": "...", "content": "..." }
  ]
}
```

## Scoring

Each item is scored per query:

- exact phrase match — largest weight
- individual keyword matches — additive
- all keywords present — small bonus
- recency (`Recent` / `Older` / `No date`) — small boost

Scores are capped at 99 and results are sorted by score (or timestamp when
`sort=newest`).
