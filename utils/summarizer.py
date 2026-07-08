from __future__ import annotations

import os
import re
from typing import Any


def _trim(value: str, limit: int = 300) -> str:
    clean = re.sub(r"\s+", " ", value or "").strip()
    if len(clean) <= limit:
        return clean
    return clean[: limit - 3].rsplit(" ", 1)[0] + "..."


def _fallback_summary(query: str, results: list[dict[str, Any]], style: str) -> str:
    top_results = results[:5]
    if not top_results:
        return "Not found in trusted sources."

    if style == "bullet points":
        lines = []
        for index, result in enumerate(top_results, start=1):
            source = result.get("source_name", "Trusted source")
            date = result.get("date_display") or result.get("timestamp") or "No date"
            lines.append(f"- [{index}] {source} ({date}): {_trim(result.get('matched_quote') or result.get('excerpt') or result.get('text', ''), 220)}")
        return "\n".join(lines)

    if style == "timeline":
        dated_results = sorted(top_results, key=lambda item: item.get("timestamp") or "")
        lines = []
        for index, result in enumerate(dated_results, start=1):
            date = result.get("date_display") or result.get("timestamp") or "No date"
            lines.append(f"- {date}: [{index}] {result.get('source_name', 'Trusted source')} reports {_trim(result.get('matched_quote') or result.get('excerpt') or result.get('text', ''), 200)}")
        return "\n".join(lines)

    first = top_results[0]
    source_names = ", ".join(f"[{index}] {result.get('source_name', 'trusted source')}" for index, result in enumerate(top_results[:3], start=1))
    return (
        f"From the Trusted Result Cards shown for \"{query}\", the strongest matches come from {source_names}. "
        f"The top Trusted Result Card says: {_trim(first.get('matched_quote') or first.get('excerpt') or first.get('text', ''), 360)} "
        "This summary is a starting point for review, not a final verification."
    )


def _llm_summary(query: str, results: list[dict[str, Any]], style: str) -> str | None:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None

    try:
        from openai import OpenAI
    except ImportError:
        return None

    context_blocks = []
    for index, result in enumerate(results[:5], start=1):
        context_blocks.append(
            "\n".join(
                [
                    f"Result {index}",
                    f"Source: {result.get('source_name', 'Unknown source')}",
                    f"Type: {result.get('source_type', 'Unknown type')}",
                    f"Date: {result.get('date_display') or result.get('timestamp') or 'No date'}",
                    f"Trusted Result Card citation: [{index}]",
                    f"Matched quote: {_trim(result.get('matched_quote') or result.get('excerpt') or result.get('text', ''), 700)}",
                ]
            )
        )

    prompt = (
        "Summarize the search query using only the Trusted Result Cards below. "
        "Cite supporting Trusted Result Cards with bracketed citation numbers. "
        "Do not add outside facts. If evidence is missing, say Not found in trusted sources. "
        f"Style: {style}. Query: {query}\n\n" + "\n\n".join(context_blocks)
    )

    try:
        client = OpenAI(api_key=api_key)
        response = client.responses.create(
            model=os.getenv("LOOKITUP_LLM_MODEL", "gpt-4o-mini"),
            input=[
                {
                    "role": "system",
                    "content": "You help journalists summarize retrieved Trusted Result Cards without adding outside information or invented facts.",
                },
                {"role": "user", "content": prompt},
            ],
        )
    except Exception:
        return None
    return getattr(response, "output_text", None)


def generate_summary(query: str, results: list[dict[str, Any]], style: str) -> dict[str, Any]:
    llm_output = _llm_summary(query, results, style)
    if llm_output:
        return {
            "summary": llm_output.strip(),
            "mode": "LLM summary",
            "notice": "Generated only from retrieved Trusted Result Cards shown on this page.",
        }
    return {
        "summary": _fallback_summary(query, results, style),
        "mode": "Fallback extractive summary",
        "notice": "No LLM API key or compatible OpenAI client was available, so Lookitup used top Trusted Result Card quotes.",
    }
