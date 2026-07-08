# Lookitup

**Having a doubt? Just Lookitup.**

Lookitup is a 48-hour hackathon MVP for journalists. It works like a search engine, but searches only inside sources the journalist selected.

## Problem Statement

Journalists often need to search quickly across sources they already trust. Open web search is broad, noisy, and optimized for the public web. Lookitup narrows the search area to a trusted source library so reporters can find relevant material faster.

## Core Message

Google searches the open web. Lookitup searches your trusted world.

Lookitup is not an AI truth machine. It helps journalists search faster inside sources they already trust.

## Features

- Trusted Source Library for RSS feeds, website URLs, PDFs, and manual text.
- Keyword search limited to trusted sources.
- Google-style Trusted Result Cards with source name, type, link, date, excerpt, match count, score, and recency indicator.
- Optional summary generation from the trusted results already shown.
- Fallback extractive summary when no LLM API key is available.
- Image tab for previewing images, reading EXIF metadata, detecting GPS metadata, showing timestamp and camera model, and flagging images for review.
- About / Roadmap section with future extension ideas.

## Installation

```bash
cd lookitup
pip install -r requirements.txt
```

## Run

```bash
streamlit run app.py
```

The app runs locally and stores added sources in `data/trusted_sources.json`.

## Demo Query

Sample sources are included by default, so the app can be demonstrated without internet access.

Try:

```text
Iran Israel rockets
```

Expected result: multiple Trusted Result Cards with timestamps, relevant excerpts, and an optional summary generated only from those displayed results.

## Optional LLM Summary

The core app works without an LLM. If you install a compatible OpenAI Python client and set `OPENAI_API_KEY`, Lookitup will try to use it for summaries. Otherwise it falls back to an extractive summary from top result excerpts.

AI summaries are generated only from the trusted results shown on the page.

## Limitations

- Search is keyword-based, not semantic.
- No login or shared accounts.
- Storage is a local JSON file, not a production database.
- Website extraction may fail on pages that block requests or render content with JavaScript.
- PDF extraction works best with text-based PDFs.
- Image flagging does not prove an image is fake. It only marks it as needing additional verification.
- No fake SynthID detection is implemented.

## Future Extensions

- archive.org article version comparison
- C2PA provenance checks
- SynthID-related checks if detection access becomes available
- reverse image search
- claim breakdown
- source diversity indicator
