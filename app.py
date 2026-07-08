from __future__ import annotations

import html
from collections import Counter
from typing import Any

import streamlit as st
from PIL import Image

from utils.exif_tools import extract_exif
from utils.search import search_sources
from utils.source_loader import load_pdf, load_rss_feed, load_website, make_source_record
from utils.storage import add_sources, clear_saved_sources, ensure_data_files, get_all_sources, load_saved_sources
from utils.summarizer import generate_summary


IMPORTANT_TEXT = "Lookitup is not an AI truth machine. It helps journalists search faster inside sources they already trust."
CORE_MESSAGE = "Google searches the open web. Lookitup searches your trusted world."
AI_SCOPE_TEXT = "AI summaries are generated only from the trusted results shown on this page."
NO_RESULTS_TEXT = "No result found does not mean the claim is false. It only means Lookitup could not find it inside your selected trusted sources."
IMAGE_FLAG_TEXT = "Image flagging does not prove an image is fake. It only marks it as needing additional verification."


def initialize_state() -> None:
    ensure_data_files()
    st.session_state.setdefault("include_sample_sources", True)
    st.session_state.setdefault("last_query", "Iran Israel rockets")
    st.session_state.setdefault("last_sort", "relevance")
    st.session_state.setdefault("last_results", [])
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
        div[data-testid="stMarkdownContainer"] h5,
        div[data-testid="stMarkdownContainer"] h6,
        div[data-testid="stMarkdownContainer"] p,
        div[data-testid="stWidgetLabel"] *,
        label,
        input,
        textarea {
            color: #111827;
        }
        div[data-testid="stCaptionContainer"],
        div[data-testid="stCaptionContainer"] * {
            color: #475569;
        }
        div[data-testid="stTextInput"] input,
        div[data-testid="stTextArea"] textarea {
            background: #ffffff;
            border-color: #cbd5e1;
            color: #111827;
        }
        div[data-testid="stFileUploader"] {
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
        div[data-testid="stMetric"] {
            background: #ffffff;
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            padding: 0.75rem 0.85rem;
        }
        div[data-testid="stMetric"] * { color: #111827; }
        .lookitup-hero {
            background: #ffffff;
            border: 1px solid #dbe4ee;
            border-left: 5px solid #0f766e;
            border-radius: 8px;
            padding: 0.85rem 1rem;
            margin-bottom: 0.65rem;
            margin-top: 0.15rem;
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
            max-width: 760px;
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
        .flow-copy {
            color: #475569;
            font-size: 0.84rem;
            margin-top: 0.18rem;
            line-height: 1.32;
            display: none;
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
        .section-note {
            background: #ecfdf5;
            border: 1px solid #bbf7d0;
            color: #14532d;
            border-radius: 8px;
            padding: 0.75rem 0.9rem;
            margin-bottom: 0.8rem;
        }
        .result-card {
            border: 1px solid #dbe4ee;
            border-left: 4px solid #0f766e;
            border-radius: 8px;
            padding: 1rem 1.05rem;
            margin: 0.85rem 0;
            background: #ffffff;
        }
        .result-topline {
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
        .badge-trusted { color: #115e59; background: #ccfbf1; border-color: #99f6e4; }
        .badge-warning { color: #854d0e; background: #fef3c7; border-color: #fde68a; }
        .result-title {
            font-size: 1.12rem;
            font-weight: 760;
            color: #111827;
            margin: 0.2rem 0 0.35rem 0;
        }
        .result-meta {
            color: #475569;
            font-size: 0.9rem;
            line-height: 1.45;
            margin-bottom: 0.65rem;
        }
        .result-excerpt {
            color: #1f2937;
            line-height: 1.55;
            background: #f8fafc;
            border-radius: 8px;
            padding: 0.75rem 0.85rem;
        }
        .result-footer {
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
        .mini-title {
            color: #111827;
            font-weight: 720;
            margin-bottom: 0.2rem;
        }
        .mini-copy {
            color: #475569;
            font-size: 0.9rem;
            line-height: 1.4;
        }
        @media (max-width: 800px) {
            .flow-grid { grid-template-columns: 1fr; }
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
          <div class="hero-kicker">Trusted-source search for journalists</div>
          <div class="lookitup-title">Lookitup</div>
          <div class="lookitup-tagline">
            Having a doubt? Just Lookitup. {html.escape(CORE_MESSAGE)}
          </div>
        </div>
        <div class="flow-grid">
          <div class="flow-card">
            <div class="flow-step">Step 1</div>
            <div class="flow-title">Add trusted sources</div>
            <div class="flow-copy">Import RSS, websites, PDFs, or manual notes into one searchable library.</div>
          </div>
          <div class="flow-card">
            <div class="flow-step">Step 2</div>
            <div class="flow-title">Search only that library</div>
            <div class="flow-copy">Keyword search stays fast and does not scan the open web.</div>
          </div>
          <div class="flow-card">
            <div class="flow-step">Step 3</div>
            <div class="flow-title">Summarize if useful</div>
            <div class="flow-copy">AI is optional and uses only the trusted results already shown.</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_section_note(text: str) -> None:
    st.markdown(f'<div class="section-note">{html.escape(text)}</div>', unsafe_allow_html=True)


def source_summary_rows(sources: list[dict[str, Any]]) -> list[dict[str, str]]:
    rows = []
    for source in sources:
        rows.append(
            {
                "Name": source.get("source_name", "Untitled source"),
                "Type": source.get("source_type", "Unknown"),
                "Title": source.get("title", ""),
                "Date": source.get("timestamp") or "No date",
                "Library": source.get("library", "saved"),
            }
        )
    return rows


def source_type_text(sources: list[dict[str, Any]]) -> str:
    counts = Counter(source.get("source_type", "Unknown") for source in sources)
    if not counts:
        return "No source types yet"
    return ", ".join(f"{source_type}: {count}" for source_type, count in sorted(counts.items()))


def render_library_metrics(sources: list[dict[str, Any]], saved_sources: list[dict[str, Any]]) -> None:
    sample_count = sum(1 for source in sources if source.get("library") == "sample")
    st.markdown(
        f"""
        <div class="stat-grid">
          <div class="stat-card">
            <div class="stat-label">Searchable records</div>
            <div class="stat-value">{len(sources)}</div>
          </div>
          <div class="stat-card">
            <div class="stat-label">Saved by user</div>
            <div class="stat-value">{len(saved_sources)}</div>
          </div>
          <div class="stat-card">
            <div class="stat-label">Sample records</div>
            <div class="stat-value">{sample_count}</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.caption(source_type_text(sources))


def render_add_source_panel() -> None:
    with st.container(border=True):
        st.markdown("#### Add One Trusted Source")
        st.caption("Choose the source type first, then fill only the fields needed for that type.")
        source_kind = st.radio(
            "Source type",
            ["RSS feed", "Website URL", "PDF upload", "Manual text"],
            horizontal=True,
        )

        with st.form("source_form"):
            source_name = st.text_input("Source name", placeholder="Example: Newsroom archive")

            if source_kind == "RSS feed":
                rss_url = st.text_input("RSS feed URL", placeholder="https://example.com/feed.xml")
                rss_limit = st.slider("Entries to import", min_value=1, max_value=20, value=8)
                submit_label = "Add RSS entries"
            elif source_kind == "Website URL":
                website_url = st.text_input("Website URL", placeholder="https://example.com/article")
                submit_label = "Add website page"
            elif source_kind == "PDF upload":
                pdf_file = st.file_uploader("PDF file", type=["pdf"], key="source_pdf_file")
                submit_label = "Add PDF"
            else:
                manual_title = st.text_input("Title", placeholder="Briefing note title")
                manual_url = st.text_input("Optional source link")
                manual_timestamp = st.text_input("Optional date", placeholder="2026-06-18T09:30:00Z")
                manual_text = st.text_area("Text content", height=190)
                submit_label = "Add manual text"

            submitted = st.form_submit_button(submit_label, type="primary", use_container_width=True)

        if not submitted:
            return

        try:
            if source_kind == "RSS feed":
                if not rss_url.strip():
                    st.error("Add a valid RSS feed URL first.")
                    return
                records = load_rss_feed(rss_url.strip(), source_name, rss_limit)
                count = add_sources(records)
                st.success(f"Added {count} RSS entries to trusted sources.")
            elif source_kind == "Website URL":
                if not website_url.strip():
                    st.error("Add a valid website URL first.")
                    return
                record = load_website(website_url.strip(), source_name)
                add_sources([record])
                st.success("Added website text to trusted sources.")
            elif source_kind == "PDF upload":
                if not pdf_file:
                    st.error("Upload a PDF first.")
                    return
                record = load_pdf(pdf_file.getvalue(), pdf_file.name, source_name)
                add_sources([record])
                st.success("Added PDF text to trusted sources.")
            else:
                if not manual_text.strip():
                    st.error("Add text content first.")
                    return
                record = make_source_record(
                    source_name=source_name or manual_title or "Manual source",
                    source_type="Manual text",
                    source_url=manual_url,
                    title=manual_title or source_name or "Manual text source",
                    timestamp=manual_timestamp,
                    text=manual_text,
                )
                add_sources([record])
                st.success("Added manual text to trusted sources.")
        except ValueError as exc:
            st.error(str(exc))


def render_library_control_panel(sources: list[dict[str, Any]], saved_sources: list[dict[str, Any]]) -> None:
    with st.container(border=True):
        st.markdown("#### Library Status")
        render_library_metrics(sources, saved_sources)
        st.divider()
        st.checkbox(
            "Include sample demo sources",
            key="include_sample_sources",
            help="Keep this on for a reliable offline demo.",
        )
        st.caption("Demo query: Iran Israel rockets")
        if st.button("Clear saved sources", type="secondary", use_container_width=True):
            clear_saved_sources()
            st.success("Saved trusted sources cleared. Sample demo sources were left unchanged.")
            st.rerun()


def render_source_list(sources: list[dict[str, Any]]) -> None:
    st.markdown("#### Trusted Source List")
    if not sources:
        st.warning("Your trusted source library is empty. Add a source or enable sample demo sources.")
        return

    type_options = sorted({source.get("source_type", "Unknown") for source in sources})
    selected_types = st.multiselect("Filter by source type", type_options, default=type_options)
    filtered_sources = [
        source for source in sources if source.get("source_type", "Unknown") in selected_types
    ]
    if not filtered_sources:
        st.info("No sources match the selected filters.")
        return
    st.dataframe(source_summary_rows(filtered_sources), use_container_width=True, hide_index=True)


def render_source_setup_tab() -> None:
    st.subheader("Source Setup")
    render_section_note(IMPORTANT_TEXT)

    sources = get_all_sources(st.session_state.include_sample_sources)
    saved_sources = load_saved_sources()
    add_col, status_col = st.columns([1.35, 0.9], gap="large")
    with add_col:
        render_add_source_panel()
    with status_col:
        render_library_control_panel(sources, saved_sources)

    render_source_list(get_all_sources(st.session_state.include_sample_sources))


def result_card(result: dict[str, Any]) -> None:
    source_name = html.escape(result.get("source_name", "Untitled source"))
    source_type = html.escape(result.get("source_type", "Unknown type"))
    title = html.escape(result.get("title") or result.get("source_name", "Untitled source"))
    date_display = html.escape(result.get("date_display", "No date"))
    recency = html.escape(result.get("recency", "No date"))
    excerpt = html.escape(result.get("excerpt") or "No excerpt available.")
    explanation = html.escape(result.get("explanation", "Keyword found in this source."))
    source_url = result.get("source_url", "")
    score = html.escape(str(result.get("score", 0)))
    match_count = html.escape(str(result.get("match_count", 0)))
    exact_count = html.escape(str(result.get("exact_match_count", 0)))
    term_count = html.escape(str(result.get("term_match_count", 0)))
    recency_class = "badge-trusted" if result.get("recency") == "Recent" else "badge-warning"
    link_html = (
        f'<a href="{html.escape(source_url)}" target="_blank" rel="noreferrer">Open source</a>'
        if source_url
        else "No source link"
    )

    st.markdown(
        f"""
        <div class="result-card">
          <div class="result-topline">
            <span class="badge badge-trusted">Trusted Result Card</span>
            <span class="badge">{source_type}</span>
            <span class="badge {recency_class}">{recency}</span>
          </div>
          <div class="result-title">{title}</div>
          <div class="result-meta">
            {source_name} - {date_display} - {link_html}
          </div>
          <div class="result-excerpt">{excerpt}</div>
          <div class="result-footer">
            Matches: {match_count} - Exact phrase: {exact_count} - Keyword hits: {term_count} - Score: {score}
            <br>{explanation}
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def run_search(query: str, sort_by: str) -> list[dict[str, Any]]:
    sources = get_all_sources(st.session_state.include_sample_sources)
    results = search_sources(query, sources, sort_by)
    st.session_state.last_query = query
    st.session_state.last_sort = sort_by
    st.session_state.last_results = results
    st.session_state.last_summary = None
    return results


def render_search_toolbar() -> tuple[str, str, bool]:
    with st.container(border=True):
        st.markdown("#### Search Workspace")
        st.caption("This search scans only the trusted source library. It does not search the open web.")
        query_col, sort_col = st.columns([3, 1])
        with query_col:
            query = st.text_input(
                "Keyword or topic",
                value=st.session_state.last_query,
                placeholder="Iran Israel rockets",
            )
        with sort_col:
            sort_by = st.selectbox(
                "Sort",
                ["relevance", "newest first"],
                index=0 if st.session_state.last_sort == "relevance" else 1,
            )
        search_clicked = st.button("Search trusted sources", type="primary", use_container_width=True)
    return query, sort_by, search_clicked


def render_results_overview(query: str, results: list[dict[str, Any]]) -> None:
    source_count = len({result.get("source_name") for result in results})
    recent_count = sum(1 for result in results if result.get("recency") == "Recent")
    top_score = max((result.get("score", 0) for result in results), default=0)

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Results", len(results))
    col2.metric("Sources", source_count)
    col3.metric("Recent", recent_count)
    col4.metric("Top score", top_score)

    action_col, note_col = st.columns([1.1, 2])
    with action_col:
        if st.button("Generate AI Summary from Trusted Results", use_container_width=True):
            summary = generate_summary(query, results, "short paragraph")
            st.session_state.last_summary = summary
            st.success(summary["mode"])
            st.write(summary["summary"])
    with note_col:
        st.caption(AI_SCOPE_TEXT)
        st.caption("Main search is keyword-based. AI runs only when you click the summary button.")


def render_search_tab() -> None:
    st.subheader("Search")
    render_section_note(CORE_MESSAGE)
    sources = get_all_sources(st.session_state.include_sample_sources)
    if not sources:
        st.warning("Your source library is empty. Add sources in Source Setup first.")
        return

    query, sort_by, search_clicked = render_search_toolbar()
    should_search = (
        search_clicked
        or query != st.session_state.last_query
        or sort_by != st.session_state.last_sort
        or not st.session_state.last_results
    )
    results = run_search(query, sort_by) if should_search else st.session_state.last_results

    if not query.strip():
        st.info("Enter a keyword or topic to search inside trusted sources.")
        return
    if not results:
        st.warning(NO_RESULTS_TEXT)
        return

    st.markdown(f"#### Results for `{query}`")
    render_results_overview(query, results)
    for result in results:
        result_card(result)


def render_result_mini_card(index: int, result: dict[str, Any]) -> None:
    title = html.escape(result.get("title") or result.get("source_name", "Trusted source"))
    source = html.escape(result.get("source_name", "Trusted source"))
    date = html.escape(result.get("date_display") or result.get("timestamp") or "No date")
    excerpt = html.escape(result.get("excerpt") or "")
    st.markdown(
        f"""
        <div class="mini-card">
          <div class="mini-title">{index}. {title}</div>
          <div class="mini-copy">{source} - {date}</div>
          <div class="mini-copy">{excerpt}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_ai_summary_tab() -> None:
    st.subheader("AI Summary")
    render_section_note(AI_SCOPE_TEXT)
    query = st.session_state.get("last_query", "")
    results = st.session_state.get("last_results", [])
    if not query or not results:
        with st.container(border=True):
            st.warning("Run a search first. The summary can only use trusted results already shown in Search.")
            st.caption("Recommended demo query: Iran Israel rockets")
        return

    top_results = results[:5]
    control_col, context_col = st.columns([0.9, 1.2], gap="large")
    with control_col:
        with st.container(border=True):
            st.markdown("#### Summary Controls")
            st.caption(f"Current query: {query}")
            st.metric("Trusted results used", len(top_results))
            style = st.radio("Summary format", ["short paragraph", "bullet points", "timeline"])
            if st.button("Generate summary", type="primary", use_container_width=True):
                summary = generate_summary(query, top_results, style)
                st.session_state.last_summary = summary
                st.success(summary["mode"])
            st.caption("No outside web content is added to this summary.")

        if st.session_state.last_summary:
            with st.container(border=True):
                st.markdown("#### Generated Summary")
                st.write(st.session_state.last_summary["summary"])
                st.caption(st.session_state.last_summary["notice"])

    with context_col:
        st.markdown("#### Trusted Results Used")
        for index, result in enumerate(top_results, start=1):
            render_result_mini_card(index, result)


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
    render_section_note("For this MVP, Lookitup reads local image metadata. It does not implement SynthID detection.")

    upload_col, review_col = st.columns([1.05, 1], gap="large")
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

            image_bytes = uploaded_image.getvalue()
            details = extract_exif(image_bytes)
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
    st.subheader("About / Roadmap")
    purpose_col, roadmap_col = st.columns(2, gap="large")

    with purpose_col:
        with st.container(border=True):
            st.markdown("#### What Lookitup Is")
            st.write(IMPORTANT_TEXT)
            st.write(CORE_MESSAGE)
            st.write("Lookitup is not a Google replacement and it is not an AI truth machine.")
            st.write("It searches only inside sources selected by the journalist. Journalists make the final decision.")

        with st.container(border=True):
            st.markdown("#### Limitations")
            st.write(
                "- Search is simple keyword matching.\n"
                "- Website extraction depends on page structure and access.\n"
                "- PDF extraction works best for text-based PDFs, not scanned documents.\n"
                "- Image flagging is a workflow marker, not proof of manipulation."
            )

    with roadmap_col:
        with st.container(border=True):
            st.markdown("#### Future Extensions")
            st.write(
                "- archive.org article version comparison\n"
                "- C2PA provenance checks\n"
                "- SynthID-related checks if detection access becomes available\n"
                "- reverse image search\n"
                "- claim breakdown\n"
                "- source diversity indicator"
            )


def main() -> None:
    st.set_page_config(page_title="Lookitup", page_icon="L", layout="wide")
    initialize_state()
    page_styles()
    render_header()

    source_tab, search_tab, summary_tab, images_tab, about_tab = st.tabs(
        ["1 Source Setup", "2 Search", "3 AI Summary", "4 Images", "5 About / Roadmap"]
    )
    with source_tab:
        render_source_setup_tab()
    with search_tab:
        render_search_tab()
    with summary_tab:
        render_ai_summary_tab()
    with images_tab:
        render_images_tab()
    with about_tab:
        render_about_tab()


if __name__ == "__main__":
    main()
