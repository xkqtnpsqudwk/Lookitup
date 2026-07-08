"""Optional AI summary generated ONLY from trusted search results.

Uses the OpenAI API. The model is instructed to rely solely on the provided
trusted-source excerpts and never to add outside knowledge, matching Lookitup's
"trusted sources only" principle.
"""

from __future__ import annotations

import os
from typing import Any, Literal

SummaryStyle = Literal["paragraph", "bullets"]

DEFAULT_MODEL = os.environ.get("OPENAI_SUMMARY_MODEL", "gpt-4o-mini")
MAX_CARDS = 6

SYSTEM_PROMPT = (
    "You are a research assistant for journalists using Lookitup. "
    "You summarize ONLY the trusted-source excerpts provided by the user. "
    "Rules:\n"
    "- Use only the given excerpts. Never add outside knowledge or assumptions.\n"
    "- If the excerpts do not answer the query, say so plainly.\n"
    "- Attribute claims to the trusted source name in parentheses.\n"
    "- Be concise, neutral, and factual. Do not speculate.\n"
    "- Never state that a claim is true or false; only report what the sources say."
)


class SummaryUnavailable(RuntimeError):
    """Raised when summarization cannot run (e.g. missing API key)."""


def _build_context(results: list[dict[str, Any]]) -> str:
    lines = []
    for index, card in enumerate(results[:MAX_CARDS], start=1):
        name = card.get("source_name", "Unknown source")
        title = card.get("title", "")
        date = card.get("timestamp") or "no date"
        excerpt = card.get("excerpt", "")
        lines.append(f"[{index}] Source: {name} | {title} ({date})\n{excerpt}")
    return "\n\n".join(lines)


def generate_summary(
    query: str,
    results: list[dict[str, Any]],
    style: SummaryStyle = "paragraph",
) -> dict[str, Any]:
    if not results:
        raise SummaryUnavailable("There are no trusted results to summarize.")

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise SummaryUnavailable(
            "OPENAI_API_KEY is not set. Add your OpenAI key to enable AI summaries."
        )

    try:
        from openai import OpenAI, OpenAIError
    except ImportError as exc:  # pragma: no cover
        raise SummaryUnavailable("The openai package is not installed.") from exc

    shape = (
        "Write 2-4 short bullet points, each starting with '- '."
        if style == "bullets"
        else "Write one tight paragraph (3-5 sentences)."
    )
    user_prompt = (
        f"Journalist query: {query}\n\n"
        f"Trusted-source excerpts:\n{_build_context(results)}\n\n"
        f"Task: Summarize what these trusted sources say about the query. {shape} "
        f"Attribute claims to source names. If the sources do not address the query, say so."
    )

    try:
        client = OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model=DEFAULT_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.2,
            max_tokens=400,
        )
    except OpenAIError as exc:
        raise SummaryUnavailable(f"OpenAI request failed: {exc}") from exc

    text = (response.choices[0].message.content or "").strip()
    used_sources = list(
        dict.fromkeys(card.get("source_name", "") for card in results[:MAX_CARDS])
    )
    return {
        "summary": text,
        "model": DEFAULT_MODEL,
        "style": style,
        "used_sources": [name for name in used_sources if name],
        "based_on": min(len(results), MAX_CARDS),
    }
