from __future__ import annotations

import html
from collections import Counter
from typing import Any

import streamlit as st
from PIL import Image

from utils.exif_tools import extract_exif
from utils.search_index import (
    build_evidence_index_stats,
    evaluate_search_state,
    group_evidence_cards,
    search_evidence_cards,
)
from utils.source_loader import load_pdf, load_rss_feed, load_website, make_source_record
from utils.storage import (
    add_sources,
    clear_saved_sources,
    ensure_data_files,
    get_sources_for_pack,
    load_saved_sources,
    load_source_packs,
)
from utils.summarizer import generate_summary


IMPORTANT_TEXT = "Lookitup is not an AI truth machine. It helps journalists search faster inside sources they already trust."
CORE_MESSAGE = "Google searches the open web. Lookitup searches your trusted world."
AI_SCOPE_TEXT = "AI summaries are generated only from retrieved Evidence Cards shown on this page."
NOT_FOUND_TEXT = "Not found in trusted sources."
IMAGE_FLAG_TEXT = "Image flagging does not prove an image is fake. It only marks it as needing additional verification."


def initialize_state() -> None:
    ensure_data_files()
    st.session_state.setdefault("include_sample_sources", True)
    st.session_state.setdefault("selected_pack_id", "international-breaking-news")
    st.session_state.setdefault("last_claim", "Iran Israel rockets")
    st.session_state.setdefault("last_sort", "BM25 relevance")
    st.session_state.setdefault("last_pack_id", "international-breaking-news")
    st.session_state.setdefault("last_cards", [])
    st.session_state.setdefault("last_state", None)
    st.session_state.setdefault("last_summary", None)
    st.session_state.setdefault("image_flagged", False)
    st.session_state.setdefault("current_image_name", "")


def page_styles() -> None:
    st.markdown(
        """
        <style>
        .stApp { background: #f8fafc; }
        .block-container { padding-top: 2.4rem; max-width: 1180px; }
        div[data-testid="stMarkdownContainer"] h1,
        div[data-testid="stMarkdownContainer"] h2,
        div[data-testid="stMarkdownContainer"] h3,
        div[data-testid="stMarkdownContainer"] h4,
        div[data-testid="stMarkdownContainer"] p,
        div[data-testid="stWidgetLabel"] *,
        label,
        input,
        textarea { color: #111827; }
        div[data-testid="stCaptionContainer"], div[data-testid="stCaptionContainer"] * { color: #475569; }
        div[data-testid="stTextInput"] input,
        div[data-testid="stTextArea"] textarea {
            background: #ffffff;
            border-color: #cbd5e1;
            color: #111827;
        }
        div[data-baseweb="select"] div {
            background: #ffffff !important;
            border-color: #cbd5e1 !important;
            color: #111827 !important;
        }
        div[data-baseweb="select"] span,
        div[data-baseweb="select"] svg {
            color: #111827 !important;
            fill: #111827 !important;
        }
        div[data-baseweb="tag"] {
            background: #ccfbf1 !important;
            border-color: #99f6e4 !important;
        }
        div[data-baseweb="tag"] * {
            color: #115e59 !important;
            fill: #115e59 !important;
        }
        div[data-testid="stTabs"] button { font-weight: 650; }
        div[data-testid="stTabs"] button p { color: #334155; }
        div[data-testid="stTabs"] button[aria-selected="true"] p { color: #0f766e; }
        div[data-testid="stButton"] button[kind="primary"] {
            background: #0f766e;
            border-color: #0f766e;
            color: #ffffff;
        }
        div[data-testid="stButton"] button[kind="primary"] * { color: #ffffff; }
        div[data-testid="stButton"] button[kind="secondary"] {
            background: #ffffff;
            border-color: #cbd5e1;
            color: #111827;
        }
        div[data-testid="stButton"] button[kind="secondary"] * { color: #111827; }
        .lookitup-hero {
            background: #ffffff;
            border: 1px solid #dbe4ee;
            border-left: 5px solid #0f766e;
            border-radius: 8px;
            padding: 0.85rem 1rem;
            margin: 0.15rem 0 0.65rem 0;
        }
        .hero-kicker {
            color: #0f766e;
            font-size: 0.78rem;
            font-weight: 760;
            letter-spacing: 0.06em;
            text-transform: uppercase;
            margin-bottom: 0.2rem;
        }
        .lookitup-title {
            color: #111827;
            font-size: 1.85rem;
            font-weight: 780;
            line-height: 1.1;
            margin: 0;
        }
        .lookitup-tagline {
            color: #334155;
            font-size: 0.98rem;
            margin-top: 0.35rem;
            max-width: 850px;
        }
        .flow-grid {
            display: grid;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            gap: 0.6rem;
            margin: 0.5rem 0 0.7rem 0;
        }
        .flow-card {
            background: #ffffff;
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            padding: 0.62rem 0.72rem;
        }
        .flow-step {
            color: #0f766e;
            font-weight: 760;
            font-size: 0.78rem;
            text-transform: uppercase;
            letter-spacing: 0.04em;
        }
        .flow-title {
            color: #111827;
            font-weight: 720;
            margin-top: 0.1rem;
        }
        .section-note {
            background: #ecfdf5;
            border: 1px solid #bbf7d0;
            color: #14532d;
            border-radius: 8px;
            padding: 0.75rem 0.9rem;
            margin-bottom: 0.8rem;
        }
        .stat-grid {
            display: grid;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            gap: 0.55rem;
            margin-bottom: 0.55rem;
        }
        .stat-card {
            background: #ffffff;
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            padding: 0.62rem 0.65rem;
        }
        .stat-label {
            color: #475569;
            font-size: 0.74rem;
            line-height: 1.2;
        }
        .stat-value {
            color: #111827;
            font-size: 1.45rem;
            font-weight: 760;
            margin-top: 0.15rem;
        }
        .evidence-card {
            border: 1px solid #dbe4ee;
            border-left: 4px solid #0f766e;
            border-radius: 8px;
            padding: 1rem 1.05rem;
            margin: 0.85rem 0;
            background: #ffffff;
        }
        .card-topline {
            display: flex;
            flex-wrap: wrap;
            gap: 0.4rem;
            align-items: center;
            margin-bottom: 0.45rem;
        }
        .badge {
            display: inline-block;
            font-size: 0.74rem;
            font-weight: 730;
            color: #334155;
            background: #f1f5f9;
            border: 1px solid #e2e8f0;
            padding: 0.16rem 0.48rem;
            border-radius: 999px;
        }
        .badge-evidence { color: #115e59; background: #ccfbf1; border-color: #99f6e4; }
        .badge-state { color: #854d0e; background: #fef3c7; border-color: #fde68a; }
        .card-title {
            color: #111827;
            font-size: 1.12rem;
            font-weight: 760;
            margin: 0.2rem 0 0.35rem 0;
        }
        .card-meta {
            color: #475569;
            font-size: 0.9rem;
            line-height: 1.45;
            margin-bottom: 0.65rem;
        }
        .quote-box {
            color: #1f2937;
            line-height: 1.55;
            background: #f8fafc;
            border-radius: 8px;
            padding: 0.75rem 0.85rem;
        }
        .card-footer {
            color: #475569;
            font-size: 0.86rem;
            margin-top: 0.65rem;
        }
        .mini-card {
            background: #ffffff;
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            padding: 0.75rem 0.85rem;
            margin-bottom: 0.6rem;
        }
        .mini-title { color: #111827; font-weight: 720; margin-bottom: 0.2rem; }
        .mini-copy { color: #475569; font-size: 0.9rem; line-height: 1.4; }
        @media (max-width: 800px) {
            .flow-grid, .stat-grid { grid-template-columns: 1fr; }
            .lookitup-title { font-size: 1.65rem; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_header() -> None:
    st.markdown(
        f"""
        <div class="lookitup-hero">
          <div class="hero-kicker">Controlled retrieval before publication</div>
          <div class="lookitup-title">Lookitup</div>
          <div class="lookitup-tagline">
            Having a doubt? Just Lookitup. {html.escape(CORE_MESSAGE)}
          </div>
        </div>
        <div class="flow-grid">
          <div class="flow-card">
            <div class="flow-step">Step 1</div>
            <div class="flow-title">Select source pack</div>
          </div>
          <div class="flow-card">
            <div class="flow-step">Step 2</div>
            <div class="flow-title">Search a claim</div>
          </div>
          <div class="flow-card">
            <div class="flow-step">Step 3</div>
            <div class="flow-title">Review Evidence Cards</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_section_note(text: str) -> None:
    st.markdown(f'<div class="section-note">{html.escape(text)}</div>', unsafe_allow_html=True)


def source_pack_map() -> dict[str, dict[str, Any]]:
    return {pack["id"]: pack for pack in load_source_packs()}


def pack_name(pack_id: str) -> str:
    pack = source_pack_map().get(pack_id, {})
    return pack.get("name", pack_id)


def pack_selector(label: str, key: str) -> str:
    packs = load_source_packs()
    if not packs:
        st.warning("No preset source packs are configured.")
        return ""
    pack_ids = [pack["id"] for pack in packs]
    current = st.session_state.selected_pack_id
    index = pack_ids.index(current) if current in pack_ids else 0
    selected = st.selectbox(
        label,
        pack_ids,
        index=index,
        format_func=lambda pack_id: source_pack_map()[pack_id]["name"],
        key=key,
    )
    st.session_state.selected_pack_id = selected
    return selected


def selected_pack_sources(pack_id: str) -> list[dict[str, Any]]:
    return get_sources_for_pack(pack_id, st.session_state.include_sample_sources)


def stamp_sources(records: list[dict[str, Any]], pack_id: str, trust_label: str) -> list[dict[str, Any]]:
    stamped = []
    for record in records:
        source = dict(record)
        source["pack_id"] = pack_id
        source["trust_label"] = trust_label.strip() or "Trusted source"
        stamped.append(source)
    return stamped


def source_summary_rows(sources: list[dict[str, Any]]) -> list[dict[str, str]]:
    rows = []
    for source in sources:
        rows.append(
            {
                "Source": source.get("source_name", "Untitled source"),
                "Pack": pack_name(source.get("pack_id", "")),
                "Type": source.get("source_type", "Unknown"),
                "Trust label": source.get("trust_label", "Trusted source"),
                "Date": source.get("timestamp") or "No date",
                "Title": source.get("title", ""),
            }
        )
    return rows


def render_pack_stats(sources: list[dict[str, Any]]) -> None:
    stats = build_evidence_index_stats(sources)
    type_counts = Counter(source.get("source_type", "Unknown") for source in sources)
    st.markdown(
        f"""
        <div class="stat-grid">
          <div class="stat-card">
            <div class="stat-label">Documents</div>
            <div class="stat-value">{stats["documents"]}</div>
          </div>
          <div class="stat-card">
            <div class="stat-label">Text chunks</div>
            <div class="stat-value">{stats["chunks"]}</div>
          </div>
          <div class="stat-card">
            <div class="stat-label">Source types</div>
            <div class="stat-value">{len(type_counts)}</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if type_counts:
        st.caption(", ".join(f"{name}: {count}" for name, count in sorted(type_counts.items())))


def render_add_source_form(pack_id: str) -> None:
    with st.container(border=True):
        st.markdown("#### Add Trusted Source to Pack")
        st.caption("Live URL/RSS ingestion is useful for demos; local sample text keeps the fallback reliable.")
        source_kind = st.radio(
            "Source type",
            ["URL", "RSS", "Local sample text", "PDF"],
            horizontal=True,
        )

        with st.form("source_form"):
            source_name = st.text_input("Source name", placeholder="Example: Ministry page or trusted wire")
            trust_label = st.text_input("Trust label", value="Trusted source")
            url = ""
            rss_limit = 8
            pdf_file = None
            title = ""
            timestamp = ""
            text = ""

            if source_kind == "URL":
                url = st.text_input("Article or official page URL", placeholder="https://example.com/article")
                submit_label = "Add URL source"
            elif source_kind == "RSS":
                url = st.text_input("RSS feed URL", placeholder="https://example.com/feed.xml")
                rss_limit = st.slider("Entries to import", min_value=1, max_value=20, value=8)
                submit_label = "Add RSS entries"
            elif source_kind == "PDF":
                pdf_file = st.file_uploader("PDF file", type=["pdf"], key="source_pdf_file")
                submit_label = "Add PDF source"
            else:
                title = st.text_input("Title", placeholder="Local fallback sample title")
                url = st.text_input("Optional URL")
                timestamp = st.text_input("Optional date", placeholder="2026-06-18T09:30:00Z")
                text = st.text_area("Text content", height=170)
                submit_label = "Add local sample text"

            submitted = st.form_submit_button(submit_label, type="primary", use_container_width=True)

        if not submitted:
            return

        try:
            if source_kind == "URL":
                if not url.strip():
                    st.error("Add a valid URL first.")
                    return
                records = [load_website(url.strip(), source_name)]
            elif source_kind == "RSS":
                if not url.strip():
                    st.error("Add a valid RSS URL first.")
                    return
                records = load_rss_feed(url.strip(), source_name, rss_limit)
            elif source_kind == "PDF":
                if not pdf_file:
                    st.error("Upload a PDF first.")
                    return
                records = [load_pdf(pdf_file.getvalue(), pdf_file.name, source_name)]
            else:
                if not text.strip():
                    st.error("Add local sample text first.")
                    return
                records = [
                    make_source_record(
                        source_name=source_name or title or "Local sample text",
                        source_type="Local sample text",
                        source_url=url,
                        title=title or source_name or "Local sample text",
                        timestamp=timestamp,
                        text=text,
                    )
                ]
            count = add_sources(stamp_sources(records, pack_id, trust_label))
            st.success(f"Added {count} source record(s) to {pack_name(pack_id)}.")
        except ValueError as exc:
            st.error(str(exc))


def render_source_packs_tab() -> None:
    st.subheader("Source Packs")
    render_section_note("A journalist starts by selecting a preset source pack, so setup time stays out of the pitch.")

    pack_col, add_col = st.columns([0.9, 1.15], gap="large")
    with pack_col:
        with st.container(border=True):
            st.markdown("#### Preset Source Pack")
            pack_id = pack_selector("Pack", "setup_pack_selector")
            pack = source_pack_map().get(pack_id, {})
            st.write(pack.get("description", "No description."))
            st.checkbox(
                "Include local sample fallback corpus",
                key="include_sample_sources",
                help="Keeps the demo reliable without network access.",
            )
            sources = selected_pack_sources(pack_id)
            render_pack_stats(sources)
            if st.button("Clear saved sources", type="secondary", use_container_width=True):
                clear_saved_sources()
                st.success("Saved sources cleared. Sample pack data was left unchanged.")
                st.rerun()
        render_add_source_form(pack_id)

    with add_col:
        st.markdown("#### Pack Corpus")
        sources = selected_pack_sources(st.session_state.selected_pack_id)
        if not sources:
            st.warning("This source pack has no corpus yet. Add a URL/RSS/local source or enable sample fallback.")
        else:
            st.dataframe(source_summary_rows(sources), use_container_width=True, hide_index=True)
        saved_count = len(load_saved_sources())
        st.caption(f"{saved_count} saved source records across all packs.")


def run_claim_search(claim: str, pack_id: str, sort_by: str) -> tuple[list[dict[str, Any]], dict[str, str]]:
    sources = selected_pack_sources(pack_id)
    cards = search_evidence_cards(claim, sources, limit=12, sort_by=sort_by)
    state = evaluate_search_state(claim, cards)
    st.session_state.last_claim = claim
    st.session_state.last_sort = sort_by
    st.session_state.selected_pack_id = pack_id
    st.session_state.last_pack_id = pack_id
    st.session_state.last_cards = cards
    st.session_state.last_state = state
    st.session_state.last_summary = None
    return cards, state


def render_state_message(state: dict[str, str]) -> None:
    if state["status"] == "evidence_found":
        st.success(state["message"])
    elif state["status"] == "mismatch":
        st.warning(state["message"])
    else:
        st.error(state["message"])
        st.caption("This means the selected trusted source pack currently lacks support for the claim.")


def render_evidence_card(card: dict[str, Any], index: int) -> None:
    source_name = html.escape(card.get("source_name", "Untitled source"))
    source_type = html.escape(card.get("source_type", "Unknown type"))
    title = html.escape(card.get("title", source_name))
    date_display = html.escape(card.get("date_display", "No date"))
    trust_label = html.escape(card.get("trust_label", "Trusted source"))
    matched_quote = html.escape(card.get("matched_quote", ""))
    score = html.escape(str(card.get("score", 0)))
    match_count = html.escape(str(card.get("match_count", 0)))
    url = card.get("url", "")
    link_html = (
        f'<a href="{html.escape(url)}" target="_blank" rel="noreferrer">Open source</a>'
        if url
        else "No URL"
    )
    st.markdown(
        f"""
        <div class="evidence-card">
          <div class="card-topline">
            <span class="badge badge-evidence">Evidence Card {index}</span>
            <span class="badge">{source_type}</span>
            <span class="badge">{trust_label}</span>
          </div>
          <div class="card-title">{title}</div>
          <div class="card-meta">{source_name} - {date_display} - {link_html}</div>
          <div class="quote-box">{matched_quote}</div>
          <div class="card-footer">Ranking score: {score} - Keyword hits: {match_count} - Chunk #{card.get("chunk_index", 1)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_grouped_evidence(cards: list[dict[str, Any]]) -> None:
    groups = group_evidence_cards(cards)
    st.info("Evidence grouped by source and time.")
    for group in groups:
        with st.expander(f"{group['source_name']} - {group['date']} - {group['count']} card(s)", expanded=False):
            for card in group["cards"]:
                st.write(f"Score {card.get('score', 0)}: {card.get('title', '')}")
                st.caption(card.get("matched_quote", ""))


def render_claim_search_tab() -> None:
    st.subheader("Claim Search")
    render_section_note("Search a text claim only inside the selected trusted source pack. Results are Evidence Cards, not final truth labels.")

    packs = load_source_packs()
    if not packs:
        st.warning("No preset source packs are configured.")
        return

    with st.container(border=True):
        pack_col, sort_col = st.columns([2, 1], gap="large")
        with pack_col:
            pack_id = pack_selector("Preset source pack", "search_pack_selector")
        with sort_col:
            sort_by = st.selectbox("Sort", ["BM25 relevance", "newest first"], key="search_sort")

        claim = st.text_area(
            "Text claim or keyword query",
            value=st.session_state.last_claim,
            height=90,
            placeholder="Iran Israel rockets",
        )
        group_breaking_news = st.checkbox("Group breaking-news evidence by source and time")
        search_clicked = st.button("Search selected source pack", type="primary", use_container_width=True)

    should_search = (
        search_clicked
        or claim != st.session_state.last_claim
        or sort_by != st.session_state.last_sort
        or pack_id != st.session_state.last_pack_id
        or not st.session_state.last_state
    )
    cards, state = run_claim_search(claim, pack_id, sort_by) if should_search else (st.session_state.last_cards, st.session_state.last_state)

    if not claim.strip():
        st.info("Enter a claim or keyword query first.")
        return

    stats = build_evidence_index_stats(selected_pack_sources(pack_id))
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Evidence Cards", len(cards))
    col2.metric("Indexed documents", stats["documents"])
    col3.metric("Indexed chunks", stats["chunks"])
    col4.metric("State", state["label"])

    render_state_message(state)

    if state["status"] == "not_found":
        return

    if group_breaking_news:
        render_grouped_evidence(cards)

    for index, card in enumerate(cards, start=1):
        render_evidence_card(card, index)


def render_result_mini_card(index: int, card: dict[str, Any]) -> None:
    title = html.escape(card.get("title") or card.get("source_name", "Evidence"))
    source = html.escape(card.get("source_name", "Trusted source"))
    date = html.escape(card.get("date_display") or card.get("timestamp") or "No date")
    quote = html.escape(card.get("matched_quote") or "")
    st.markdown(
        f"""
        <div class="mini-card">
          <div class="mini-title">[{index}] {title}</div>
          <div class="mini-copy">{source} - {date}</div>
          <div class="mini-copy">{quote}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_evidence_summary_tab() -> None:
    st.subheader("Evidence Summary")
    render_section_note(AI_SCOPE_TEXT)

    claim = st.session_state.get("last_claim", "")
    cards = st.session_state.get("last_cards", [])
    state = st.session_state.get("last_state")
    if not claim or not state:
        with st.container(border=True):
            st.warning("Run a claim search first.")
            st.caption("Recommended demo query: Iran Israel rockets")
        return

    if state["status"] == "not_found" or not cards:
        st.error(NOT_FOUND_TEXT)
        st.caption("The summary is blocked because no retrieved Evidence Cards are available.")
        return

    top_cards = cards[:5]
    control_col, context_col = st.columns([0.9, 1.2], gap="large")
    with control_col:
        with st.container(border=True):
            st.markdown("#### Summary Controls")
            st.caption(f"Claim: {claim}")
            st.metric("Evidence Cards used", len(top_cards))
            style = st.radio("Summary format", ["short paragraph", "bullet points", "timeline"])
            if st.button("Generate evidence-grounded summary", type="primary", use_container_width=True):
                summary = generate_summary(claim, top_cards, style)
                st.session_state.last_summary = summary
                st.success(summary["mode"])
            st.caption("Outside knowledge and invented facts are blocked by prompt and fallback design.")

        if st.session_state.last_summary:
            with st.container(border=True):
                st.markdown("#### Generated Summary")
                st.write(st.session_state.last_summary["summary"])
                st.caption(st.session_state.last_summary["notice"])

    with context_col:
        st.markdown("#### Evidence Cards Used")
        for index, card in enumerate(top_cards, start=1):
            render_result_mini_card(index, card)


def render_image_quick_checks(details: dict[str, Any]) -> None:
    gps_status = "Found" if details["gps"] else "Not found"
    timestamp_status = "Found" if details["timestamp"] else "Not found"
    camera_status = "Found" if details["camera_model"] else "Not found"
    col1, col2, col3 = st.columns(3)
    col1.metric("GPS", gps_status)
    col2.metric("Timestamp", timestamp_status)
    col3.metric("Camera", camera_status)

    if details["gps"]:
        st.caption(f"GPS coordinates: {details['gps']['latitude']}, {details['gps']['longitude']}")
    if details["timestamp"]:
        st.caption(f"Timestamp: {details['timestamp']}")
    if details["camera_model"]:
        st.caption(f"Camera model: {details['camera_model']}")


def render_images_tab() -> None:
    st.subheader("Images")
    render_section_note("Image provenance is later scope for this technical branch. This MVP only reads local EXIF metadata.")

    upload_col, review_col = st.columns([1.05, 1], gap="large")
    uploaded_image = None
    with upload_col:
        with st.container(border=True):
            st.markdown("#### Upload and Preview")
            uploaded_image = st.file_uploader("Image file", type=["jpg", "jpeg", "png", "tiff", "webp"])
            if uploaded_image:
                if st.session_state.current_image_name != uploaded_image.name:
                    st.session_state.current_image_name = uploaded_image.name
                    st.session_state.image_flagged = False
                try:
                    image = Image.open(uploaded_image)
                    st.image(image, caption=uploaded_image.name, use_container_width=True)
                except Exception as exc:
                    st.error(f"Could not preview image: {exc}")
            else:
                st.info("Upload an image to inspect EXIF metadata.")

    with review_col:
        with st.container(border=True):
            st.markdown("#### Metadata Review")
            if not uploaded_image:
                st.caption("Waiting for an image.")
                return

            details = extract_exif(uploaded_image.getvalue())
            render_image_quick_checks(details)

            if details["warnings"]:
                for warning in details["warnings"]:
                    st.warning(warning)
            else:
                st.success("No GPS, camera model, or timestamp metadata was detected.")

            if st.button("Flag as suspicious", use_container_width=True):
                st.session_state.image_flagged = True

            if st.session_state.image_flagged:
                st.error("Status: Needs review - Flagged by user.")
            else:
                st.info("Status: Not flagged.")
            st.caption(IMAGE_FLAG_TEXT)

    if uploaded_image:
        details = extract_exif(uploaded_image.getvalue())
        st.markdown("#### EXIF Metadata Table")
        if details["metadata"]:
            st.dataframe(details["metadata"], use_container_width=True, hide_index=True)
        else:
            st.warning("No EXIF metadata found.")


def render_about_tab() -> None:
    st.subheader("About")
    with st.container(border=True):
        st.markdown("#### What Lookitup Is")
        st.write(IMPORTANT_TEXT)
        st.write(CORE_MESSAGE)
        st.write("Lookitup is a controlled retrieval pipeline: preset source packs are ingested, chunked, indexed with SQLite FTS5, and searched before publication.")
        st.write("It returns Evidence Cards, mismatch or not-found states, and grouped breaking-news evidence. Journalists make the final decision.")


def main() -> None:
    st.set_page_config(page_title="Lookitup", page_icon="L", layout="wide")
    initialize_state()
    page_styles()
    render_header()

    source_tab, search_tab, summary_tab, images_tab, about_tab = st.tabs(
        ["1 Source Packs", "2 Claim Search", "3 Evidence Summary", "4 Images", "5 About"]
    )
    with source_tab:
        render_source_packs_tab()
    with search_tab:
        render_claim_search_tab()
    with summary_tab:
        render_evidence_summary_tab()
    with images_tab:
        render_images_tab()
    with about_tab:
        render_about_tab()


if __name__ == "__main__":
    main()
