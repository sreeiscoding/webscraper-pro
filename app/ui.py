"""Streamlit user interface for the local scraper application."""

from __future__ import annotations

import html
import json
import logging
import platform
import sys
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any

import pandas as pd
import streamlit as st
from bs4 import BeautifulSoup

try:
    from bs4 import SelectorSyntaxError
except ImportError:  # pragma: no cover - newer bs4/soupsieve compatibility
    try:
        from soupsieve.util import SelectorSyntaxError
    except ImportError:  # pragma: no cover - final fallback
        class SelectorSyntaxError(ValueError):
            """Fallback selector syntax error for compatible bs4 imports."""

            pass

from app.cleaner import clean_records, validate_records
from app.config import SETTINGS, ExtractionConfig, FieldSpec, PaginationConfig, resolve_url, validate_url
from app.demo_configurations import BOOKS_TO_SCRAPE_CONFIG, LOCAL_PRODUCT_LIST_CONFIG
from app.exporter import export_csv, export_excel
from app.network import fetch_html
from app.pagination import process_urls
from app.storage import DEFAULT_DB_PATH, ProjectStore
from app.theme import PALETTE, inject_theme, nav_slug

LOGGER = logging.getLogger(__name__)

_PRESETS = {
    "books": BOOKS_TO_SCRAPE_CONFIG,
    "product_list": LOCAL_PRODUCT_LIST_CONFIG,
}

SECTIONS = ("Overview", "New Extraction", "Results", "History", "Settings")
DEFAULT_SECTION = "Overview"

_DRAFT_KEY = "extraction_draft"

_ADVANCED_WIDGET_KEYS = (
    "extraction_engine",
    "extraction_wait_for",
    "extraction_wait_until",
    "extraction_wait_timeout",
    "extraction_page_load_timeout",
    "extraction_max_pages",
    "extraction_max_records",
    "extraction_next_page_selector",
    "extraction_request_delay",
    "extraction_max_retries",
    "extraction_retry_backoff",
)



def _preset_options() -> list[str]:
    return list(_PRESETS.keys())


def build_extraction_config(
    url: str,
    preset_name: str,
    field_overrides: dict[str, dict[str, Any]] | None = None,
) -> ExtractionConfig:
    """Build a validated ExtractionConfig from a public URL and preset configuration."""
    if not url or not url.strip():
        raise ValueError("A website URL is required before starting an extraction.")
    if not validate_url(url):
        raise ValueError("Only public HTTP(S) websites are permitted. Localhost and private addresses are blocked.")

    preset = _PRESETS.get(preset_name, BOOKS_TO_SCRAPE_CONFIG)
    field_overrides = field_overrides or {}

    field_map: dict[str, FieldSpec] = {}
    for field_name, field_spec in preset.fields.items():
        details = field_spec.to_dict()
        override = field_overrides.get(field_name, {})
        if override:
            details.update(override)
        details.setdefault("name", field_name)
        field_map[field_name] = FieldSpec(**details)

    return ExtractionConfig(
        base_url=url,
        record_selector=preset.record_selector,
        fields=field_map,
    )


def run_extraction_job(
    url: str,
    preset_name: str,
    field_overrides: dict[str, dict[str, Any]] | None = None,
    pagination_config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Run the reusable extraction engine using the UI-specified configuration."""
    config = build_extraction_config(url, preset_name, field_overrides)
    config.validate()

    page_settings = pagination_config or {}
    pagination = PaginationConfig(
        max_pages=int(page_settings.get("max_pages", 5)),
        max_records=int(page_settings.get("max_records", 200)),
        next_page_selector=str(page_settings.get("next_page_selector", "")),
        request_delay=float(page_settings.get("request_delay", 0.5)),
        max_retries=int(page_settings.get("max_retries", 1)),
        retry_backoff=float(page_settings.get("retry_backoff", 0.5)),
    )
    pagination.validate()

    def fetcher_with_engine(current_url: str, **kwargs):
        return fetch_html(
            current_url,
            engine=str(page_settings.get("engine", "static")).lower(),
            render_config={
                "wait_for": page_settings.get("wait_for", "body"),
                "wait_timeout": int(page_settings.get("wait_timeout", 30000)),
                "page_load_timeout": int(page_settings.get("page_load_timeout", 30000)),
                "wait_until": page_settings.get("wait_until", "domcontentloaded"),
            },
            **kwargs,
        )

    result = process_urls([url], config, pagination, fetcher=fetcher_with_engine)
    result["records"] = result.get("records", [])
    result["failed_pages"] = result.get("failed_pages", [])
    result["config"] = config
    result["pagination_config"] = pagination
    result["validation"] = validate_records(
        result["records"],
        required_fields={field_name for field_name, field in config.fields.items() if field.required},
    )
    return result


def prepare_download_bytes(
    records: list[dict[str, Any]],
    export_format: str,
    columns: list[str] | None = None,
) -> bytes:
    """Prepare valid CSV or Excel bytes for download while reusing the app export modules."""
    if not records:
        if export_format.lower() == "csv":
            return b""
        return b""

    frame = pd.DataFrame(records)
    selected_columns = columns or list(frame.columns)
    selected_columns = [column for column in selected_columns if column in frame.columns]
    if not selected_columns:
        selected_columns = list(frame.columns)
    frame = frame[selected_columns]

    with NamedTemporaryFile(suffix=f".{export_format.lower()}", delete=False) as temp_file:
        temp_path = Path(temp_file.name)

    if export_format.lower() == "csv":
        export_csv(frame.to_dict(orient="records"), temp_path)
    else:
        export_excel(frame.to_dict(orient="records"), temp_path, summary_stats={"rows": len(frame)})

    data = temp_path.read_bytes()
    temp_path.unlink(missing_ok=True)
    return data


def _preview_value(value: Any, limit: int = 120) -> str:
    """Return a compact preview of a value without exposing excessive output."""
    if value is None:
        return ""
    text = str(value).strip()
    if len(text) > limit:
        text = text[: limit - 3] + "..."
    return text


def test_selectors_for_url(
    url: str,
    preset_name: str,
    field_overrides: dict[str, dict[str, Any]],
    pagination_config: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Validate selectors against a single permitted target page and return preview data without running a full extraction job."""
    if not url or not url.strip():
        raise ValueError("A website URL is required before testing selectors.")
    if not validate_url(url):
        raise ValueError("Only public HTTP(S) URLs are permitted. Localhost and private addresses are blocked.")

    page_settings = pagination_config or {}
    engine = str(page_settings.get("engine", "static")).lower()
    timeout = int(page_settings.get("timeout", SETTINGS.default_timeout))
    max_retries = int(page_settings.get("max_retries", 1))
    retry_backoff = float(page_settings.get("retry_backoff", 0.5))
    render_config = {
        "wait_for": page_settings.get("wait_for", "body"),
        "wait_timeout": int(page_settings.get("wait_timeout", 30000)),
        "page_load_timeout": int(page_settings.get("page_load_timeout", 30000)),
        "wait_until": page_settings.get("wait_until", "domcontentloaded"),
    }

    html = fetch_html(
        url,
        timeout=timeout,
        max_retries=max_retries,
        retry_backoff=retry_backoff,
        engine=engine,
        render_config=render_config,
    )
    soup = BeautifulSoup(html, "html.parser")

    preset = _PRESETS.get(preset_name, BOOKS_TO_SCRAPE_CONFIG)
    results: list[dict[str, Any]] = []

    for field_name, field_spec in preset.fields.items():
        if field_name not in field_overrides:
            continue

        selector = str(field_overrides.get(field_name, {}).get("selector", field_spec.selector) or field_spec.selector)
        extraction_type = str(getattr(field_spec, "extraction_type", "text") or "text").lower()
        attribute_name = str(
            field_overrides.get(field_name, {}).get("attribute_name")
            or getattr(field_spec, "attribute_name", None)
            or ("href" if extraction_type in {"attribute", "url"} else "")
        )

        try:
            matches = soup.select(selector)
        except SelectorSyntaxError as exc:
            results.append(
                {
                    "field": field_name,
                    "status": "invalid_selector",
                    "match_count": 0,
                    "sample": [],
                    "message": f"Invalid CSS selector for '{field_name}': {exc}",
                }
            )
            continue

        if not matches:
            results.append(
                {
                    "field": field_name,
                    "status": "no_matches",
                    "match_count": 0,
                    "sample": [],
                    "message": f"Selector '{selector}' matched no elements on this page.",
                }
            )
            continue

        sample_values: list[str] = []
        for match in matches[:5]:
            if extraction_type in {"text", "html"}:
                value = match.get_text(" ", strip=True) if extraction_type == "text" else match.decode_contents()
                sample_values.append(_preview_value(value))
            elif extraction_type in {"attribute", "url"}:
                raw_value = match.get(attribute_name)
                if raw_value is None:
                    sample_values.append("attribute missing")
                    continue
                if extraction_type == "url":
                    resolved = resolve_url(url, raw_value)
                    sample_values.append(_preview_value(resolved))
                else:
                    sample_values.append(_preview_value(raw_value))

        results.append(
            {
                "field": field_name,
                "status": "valid_matches",
                "match_count": len(matches),
                "sample": sample_values[:5],
                "message": f"Selector matched {len(matches)} element(s).",
                "selector": selector,
                "attribute_name": attribute_name,
            }
        )

    return results


# ---------------------------------------------------------------------------
# Navigation and session state
# ---------------------------------------------------------------------------


def _init_session_state() -> None:
    """Prepare session state and apply any queued navigation request."""
    defaults: dict[str, Any] = {
        "jobs": [],
        "last_result": None,
        "last_cleaned": [],
        "last_notice": None,
        "selector_test_results": [],
        "scrape_in_progress": False,
        "nav_section": DEFAULT_SECTION,
        _DRAFT_KEY: {},
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

    if "project_store" not in st.session_state:
        st.session_state.project_store = ProjectStore(DEFAULT_DB_PATH)

    requested = st.session_state.pop("nav_request", None)
    if requested in SECTIONS:
        st.session_state.nav_section = requested


def _extraction_widget_keys(preset_name: str) -> list[str]:
    """Return the session-state keys that belong to the extraction form."""
    preset = _PRESETS.get(preset_name, BOOKS_TO_SCRAPE_CONFIG)
    keys = ["extraction_url", "extraction_preset", *list(_ADVANCED_WIDGET_KEYS)]
    for field_name in preset.fields:
        keys.append(f"field_enabled_{field_name}")
        keys.append(f"selector_{field_name}")
    return keys


def _capture_extraction_draft(preset_name: str) -> None:
    """Store the current form values so they survive navigation.

    The values are used as the default value of the form widgets the next time
    the extraction section is opened, so navigating away and back does not
    discard the setup the user already submitted.
    """
    draft = dict(st.session_state.get(_DRAFT_KEY) or {})
    for key in _extraction_widget_keys(preset_name):
        if key in st.session_state:
            draft[key] = st.session_state[key]
    st.session_state[_DRAFT_KEY] = draft


def _request_navigation(section: str) -> None:
    """Queue a navigation change that is applied at the start of the next run."""
    st.session_state.nav_request = section


def _render_topnav() -> str:
    """Render the top navigation and return the active section.

    The active section is kept in ``st.session_state.nav_section`` and every
    control reuses the existing ``_request_navigation`` mechanism, so the
    navigation behaviour is unchanged from the previous sidebar implementation.
    """
    active = st.session_state.get("nav_section", DEFAULT_SECTION)

    with st.container(key="wsp_topnav"):
        with st.container(key="wsp_topnav_desktop"):
            left, right = st.columns([1, 1], gap="medium")
            with left:
                st.markdown(
                    """
                    <div class="wsp-brand">
                      <div class="wsp-brand__mark">WS</div>
                      <div>
                        <div class="wsp-brand__name">WebScraper Pro</div>
                        <div class="wsp-brand__tag">Extraction Suite</div>
                      </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            with right:
                # The extra room accounts for the navigation icon and the
                # button padding, so the labels never wrap.
                nav_columns = st.columns(
                    [max(len(section) + 9, 12) for section in SECTIONS],
                    gap="small",
                )
                for column, section in zip(nav_columns, SECTIONS):
                    with column:
                        is_active = section == active
                        container_key = "wsp_nav_active" if is_active else f"wsp_nav_{nav_slug(section)}"
                        with st.container(key=container_key):
                            st.button(
                                section,
                                key=f"nav_{nav_slug(section)}",
                                on_click=_request_navigation,
                                args=(section,),
                                use_container_width=True,
                            )

        with st.container(key="wsp_topnav_mobile"):
            brand_col, menu_col = st.columns([1, 1], gap="small")
            with brand_col:
                st.markdown(
                    """
                    <div class="wsp-brand">
                      <div class="wsp-brand__mark">WS</div>
                      <div>
                        <div class="wsp-brand__name">WebScraper Pro</div>
                        <div class="wsp-brand__tag">Extraction Suite</div>
                      </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            with menu_col:
                with st.popover("Menu", use_container_width=True):
                    for section in SECTIONS:
                        st.button(
                            section,
                            key=f"navm_{nav_slug(section)}",
                            on_click=_request_navigation,
                            args=(section,),
                            use_container_width=True,
                        )

    return active


# ---------------------------------------------------------------------------
# Shared building blocks
# ---------------------------------------------------------------------------


def _page_header(title: str, lead: str) -> None:
    """Render a consistent page title and supporting description."""
    st.markdown(f'<h1 class="wsp-page-title">{html.escape(title)}</h1>', unsafe_allow_html=True)
    st.markdown(f'<p class="wsp-page-lead">{html.escape(lead)}</p>', unsafe_allow_html=True)


def _stat_cards(stats: list[tuple[str, str, str]], mono_labels: set[str] | None = None) -> None:
    """Render a responsive grid of metric cards computed from real application state.

    ``mono_labels`` names the cards whose value is a technical string such as a
    file path, a version or a user agent, so that value is set in the
    monospace face while the rest of the interface stays in the UI typeface.
    """
    technical = mono_labels or set()
    cards = []
    for label, value, hint in stats:
        value_class = "wsp-stat__value wsp-stat__value--long" if len(value) > 24 else "wsp-stat__value"
        if label in technical:
            value_class += " wsp-mono"
        cards.append(
            f"""
        <div class="wsp-stat">
          <div class="wsp-stat__label">{html.escape(label)}</div>
          <div class="{value_class}">{html.escape(value)}</div>
          <div class="wsp-stat__hint">{html.escape(hint)}</div>
        </div>"""
        )
    st.markdown(f'<div class="wsp-stat-grid">{"".join(cards)}</div>', unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Overview
# ---------------------------------------------------------------------------


def _render_hero() -> None:
    """Render the immersive Overview hero with its calls to action."""
    with st.container(key="wsp_hero"):
        st.markdown(
            '<div class="wsp-hero__eyebrow">Web data extraction workspace</div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            '<h2 class="wsp-hero__title">Turn the web into<br />structured data.</h2>',
            unsafe_allow_html=True,
        )
        st.markdown(
            '<p class="wsp-hero__lead">Extract, organise, and export valuable information from '
            "websites into clean, usable datasets.</p>",
            unsafe_allow_html=True,
        )
        primary_col, secondary_col = st.columns([1, 1])
        with primary_col:
            st.button(
                "Start an extraction \u2192",
                type="primary",
                use_container_width=True,
                on_click=_request_navigation,
                args=("New Extraction",),
                key="hero_start_extraction",
            )
        with secondary_col:
            st.button(
                "View results",
                use_container_width=True,
                on_click=_request_navigation,
                args=("Results",),
                key="hero_view_results",
            )


def _render_overview() -> None:
    """Render the landing section: hero, live metrics and recent activity."""
    _render_hero()

    store: ProjectStore = st.session_state.project_store
    last_result = st.session_state.get("last_result") or {}
    jobs = st.session_state.get("jobs") or []

    try:
        saved_projects = len(store.list_projects())
        recorded_jobs = len(store.list_job_history(limit=200))
    except Exception as exc:  # pragma: no cover - UI guard for storage issues
        LOGGER.warning("Unable to read stored project counts: %s", exc)
        saved_projects = 0
        recorded_jobs = 0

    _stat_cards(
        [
            ("Extractions this session", str(len(jobs)), "Runs completed in this browser session"),
            ("Records in latest run", str(last_result.get("total_records", 0)), "From the most recent extraction"),
            ("Saved projects", str(saved_projects), "Reusable configurations on this machine"),
            ("Jobs recorded", str(recorded_jobs), "Extraction history stored locally"),
        ]
    )

    left, right = st.columns([1.35, 1], gap="large")

    with left:
        st.markdown(
            '<h3 class="wsp-section-title">Recent activity</h3>'
            '<p class="wsp-section-hint">The most recent jobs run in this session.</p>',
            unsafe_allow_html=True,
        )
        if jobs:
            job_frame = pd.DataFrame(
                [
                    {
                        "URL": job.get("url", ""),
                        "Records": job.get("records", 0),
                        "Status": job.get("status", ""),
                    }
                    for job in jobs[-6:]
                ]
            )
            st.dataframe(job_frame, use_container_width=True, hide_index=True)
        else:
            st.info("No extractions have been run in this session yet. Start one from the New Extraction section.")

    with right:
        st.markdown(
            '<h3 class="wsp-section-title">How it works</h3>'
            '<p class="wsp-section-hint">The same three steps for every source.</p>',
            unsafe_allow_html=True,
        )
        st.markdown(
            """
            <div class="wsp-card">
              <div class="wsp-stat__label">01 &middot; Source</div>
              <div class="wsp-stat__hint">Enter a public website URL and choose an extraction preset.</div>
              <div class="wsp-stat__label" style="margin-top:0.9rem;">02 &middot; Fields</div>
              <div class="wsp-stat__hint">Enable the fields you need and tune the CSS selectors.</div>
              <div class="wsp-stat__label" style="margin-top:0.9rem;">03 &middot; Export</div>
              <div class="wsp-stat__hint">Clean the dataset and download it as CSV or Excel.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


# ---------------------------------------------------------------------------
# New extraction
# ---------------------------------------------------------------------------


def _render_extraction() -> None:
    """Render the existing extraction workspace with refined organisation."""
    _page_header(
        "New Extraction",
        "Configure your source, select the fields you need, and extract structured data.",
    )

    if "scrape_in_progress" not in st.session_state:
        st.session_state.scrape_in_progress = False

    store: ProjectStore = st.session_state.project_store

    draft = st.session_state.get(_DRAFT_KEY) or {}
    draft_preset = str(draft.get("extraction_preset") or _preset_options()[0])
    if draft_preset not in _preset_options():
        draft_preset = _preset_options()[0]

    # The preset sits outside the form so switching it updates the field list
    # immediately. The URL stays inside the form so it is always submitted
    # together with the extraction request.
    with st.container(key="wsp_source"):
        st.markdown(
            '<div class="wsp-label">Extraction configuration</div>'
            '<h3 class="wsp-section-title">Preset and field mapping</h3>',
            unsafe_allow_html=True,
        )
        preset_name = st.selectbox(
            "Extraction configuration",
            options=_preset_options(),
            index=_preset_options().index(draft_preset),
            key="extraction_preset",
        )

    with st.form("scrape_form", clear_on_submit=False):
        with st.container(key="wsp_source_url"):
            st.markdown(
                '<div class="wsp-label">Source configuration</div>'
                '<h3 class="wsp-section-title">Target website</h3>',
                unsafe_allow_html=True,
            )
            url = st.text_input(
                "Website URL",
                value=str(draft.get("extraction_url") or ""),
                placeholder="https://books.toscrape.com/",
                help="Use a public HTTP(S) URL only.",
                key="extraction_url",
            )

        preset = _PRESETS.get(preset_name, BOOKS_TO_SCRAPE_CONFIG)
        field_overrides: dict[str, dict[str, Any]] = {}

        if preset.fields:
            with st.container(key="wsp_field_headers"):
                headers = st.columns([0.7, 1.8, 3.4])
                with headers[0]:
                    st.caption("Enable")
                with headers[1]:
                    st.caption("Field")
                with headers[2]:
                    st.caption("CSS selector")

        for field_name, field_spec in preset.fields.items():
            col_enable, col_name, col_selector = st.columns([0.7, 1.8, 3.4])
            with col_enable:
                enabled = st.checkbox(
                    "",
                    value=bool(draft.get(f"field_enabled_{field_name}", True)),
                    key=f"field_enabled_{field_name}",
                    help=f"Include field '{field_name}' in the extraction.",
                )
            with col_name:
                st.markdown(f"**{field_name}**")
            with col_selector:
                selector = st.text_input(
                    "",
                    value=str(draft.get(f"selector_{field_name}", field_spec.selector)),
                    key=f"selector_{field_name}",
                    help="CSS selector used to locate the field in each record.",
                    label_visibility="collapsed",
                    placeholder="CSS selector",
                )
            if enabled:
                field_overrides[field_name] = {"selector": selector, "required": field_spec.required}

        with st.expander("Advanced settings — pagination and requests", expanded=False):
            st.caption("Tune extraction behaviour while keeping requests bounded and safe.")
            engine = st.selectbox("Rendering engine", options=["static", "playwright"], index=["static", "playwright"].index(str(draft.get("extraction_engine", "static"))), key="extraction_engine")
            wait_for = st.text_input(
                "Wait for selector (optional)",
                value=str(draft.get("extraction_wait_for", "body")),
                help="Use a CSS selector to wait for content before extracting when rendering JavaScript pages.",
                key="extraction_wait_for",
            )
            wait_until = st.selectbox(
                "Page-load strategy",
                options=["domcontentloaded", "load", "networkidle"],
                index=["domcontentloaded", "load", "networkidle"].index(str(draft.get("extraction_wait_until", "domcontentloaded"))),
                key="extraction_wait_until",
            )
            wait_timeout = st.number_input(
                "Wait timeout (ms)", min_value=1000, max_value=120000, value=int(draft.get("extraction_wait_timeout", 30000)), step=1000, key="extraction_wait_timeout"
            )
            page_load_timeout = st.number_input(
                "Page-load timeout (ms)",
                min_value=1000,
                max_value=120000,
                value=int(draft.get("extraction_page_load_timeout", 30000)),
                step=1000,
                key="extraction_page_load_timeout",
            )
            max_pages = st.number_input("Maximum pages", min_value=1, max_value=100, value=int(draft.get("extraction_max_pages", 5)), key="extraction_max_pages")
            max_records = st.number_input(
                "Maximum records", min_value=1, max_value=10000, value=int(draft.get("extraction_max_records", 200)), key="extraction_max_records"
            )
            next_page_selector = st.text_input(
                "Next-page selector", value=str(draft.get("extraction_next_page_selector", "")), placeholder="a.next", key="extraction_next_page_selector"
            )
            request_delay = st.number_input(
                "Request delay (seconds)", min_value=0.0, max_value=30.0, value=float(draft.get("extraction_request_delay", 0.5)), step=0.1, key="extraction_request_delay"
            )
            max_retries = st.number_input("Retry attempts", min_value=0, max_value=10, value=int(draft.get("extraction_max_retries", 1)), key="extraction_max_retries")
            retry_backoff = st.number_input(
                "Retry backoff (seconds)", min_value=0.0, max_value=30.0, value=float(draft.get("extraction_retry_backoff", 0.5)), step=0.1, key="extraction_retry_backoff"
            )

        action_test, action_start = st.columns([1, 1.5])
        with action_test:
            test_selectors = st.form_submit_button(
                "Test selectors",
                use_container_width=True,
                disabled=st.session_state.scrape_in_progress,
            )
        with action_start:
            button_label = "Running extraction..." if st.session_state.scrape_in_progress else "Start extraction"
            start_job = st.form_submit_button(
                button_label,
                type="primary",
                use_container_width=True,
                disabled=st.session_state.scrape_in_progress,
            )

    _capture_extraction_draft(preset_name)

    if test_selectors:
        try:
            pagination = {
                "engine": engine,
                "wait_for": wait_for,
                "wait_until": wait_until,
                "wait_timeout": int(wait_timeout),
                "page_load_timeout": int(page_load_timeout),
                "max_pages": 1,
                "max_records": 1,
                "next_page_selector": "",
                "request_delay": float(request_delay),
                "max_retries": int(max_retries),
                "retry_backoff": float(retry_backoff),
            }
            results = test_selectors_for_url(url, preset_name, field_overrides, pagination_config=pagination)
            st.session_state.selector_test_results = results

            if results:
                rows = [
                    {
                        "Field": item["field"],
                        "Status": item["status"],
                        "Matches": item["match_count"],
                        "Preview": "; ".join(item["sample"]) if item["sample"] else "-",
                        "Message": item["message"],
                    }
                    for item in results
                ]
                st.markdown(
                    '<h3 class="wsp-section-title" style="margin-top:1.6rem;">Selector test results</h3>',
                    unsafe_allow_html=True,
                )
                st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
            else:
                st.info("No enabled fields were available to test.")
        except ValueError as exc:
            LOGGER.warning("Selector test validation failed: %s", exc)
            st.error(str(exc))
        except Exception as exc:  # pragma: no cover - selector test boundary guard
            LOGGER.exception("Selector testing failed")
            st.error(
                f"Unable to test selectors for '{url}'. Please check the URL, request limits, and target site "
                f"permissions. Details: {exc}"
            )

    if start_job:
        st.session_state.scrape_in_progress = True
        try:
            pagination = {
                "engine": engine,
                "wait_for": wait_for,
                "wait_until": wait_until,
                "wait_timeout": int(wait_timeout),
                "page_load_timeout": int(page_load_timeout),
                "max_pages": int(max_pages),
                "max_records": int(max_records),
                "next_page_selector": next_page_selector,
                "request_delay": float(request_delay),
                "max_retries": int(max_retries),
                "retry_backoff": float(retry_backoff),
            }
            if not url or not url.strip():
                raise ValueError("A website URL is required before starting an extraction.")
            result = run_extraction_job(url, preset_name, field_overrides=field_overrides, pagination_config=pagination)
            st.session_state.last_result = result
            summary = {
                "url": url,
                "records": result.get("total_records", 0),
                "status": result.get("stop_reason", "completed"),
            }
            st.session_state.jobs.append(summary)
            try:
                store.add_job_summary(
                    project_id=None,
                    status=summary["status"],
                    record_count=int(summary["records"]),
                    error_summary=None,
                    engine=str(pagination.get("engine", "static")),
                    url=url,
                )
            except Exception as exc:  # pragma: no cover - storage failure only
                LOGGER.warning("Unable to save job summary: %s", exc)
            st.session_state.last_cleaned = result.get("records", [])
            st.session_state.last_notice = {
                "type": "success",
                "message": f"Extraction completed successfully. {summary['records']} record(s) captured.",
            }
        except ValueError as exc:
            LOGGER.warning("Extraction validation failed: %s", exc)
            st.session_state.last_notice = None
            st.error(str(exc))
        except Exception as exc:  # pragma: no cover - interface-level boundary guard
            LOGGER.exception("Unexpected extraction error")
            st.session_state.last_notice = None
            st.error(
                "The extraction job could not be completed. Please check the URL, site permissions, "
                "and configured selectors."
            )
        finally:
            st.session_state.scrape_in_progress = False


# ---------------------------------------------------------------------------
# Results
# ---------------------------------------------------------------------------


def _render_results() -> None:
    """Render the results, cleaning and export workspace."""
    _page_header(
        "Results",
        "Review the records returned by your last extraction, clean the dataset, and export it.",
    )

    notice = st.session_state.get("last_notice")
    if notice:
        st.success(notice["message"])

    result = st.session_state.get("last_result")
    if not result:
        st.info("No extraction results yet. Run an extraction to populate this section.")
        st.button(
            "Open New Extraction",
            type="primary",
            on_click=_request_navigation,
            args=("New Extraction",),
            key="results_empty_cta",
        )
        return

    records = result.get("records", [])
    validation = result.get("validation", {"flags": []})
    warnings = validation.get("flags", [])
    total_records = result.get("total_records", len(records))

    _stat_cards(
        [
            ("Records extracted", str(total_records), "Rows returned by the last run"),
            ("Pages processed", str(result.get("pages_processed", 0)), "Pages fetched from the source"),
            ("Duplicates removed", str(result.get("duplicates_removed", 0)), "Removed by the cleaning preview"),
            ("Validation warnings", str(len(warnings)), "Records needing attention"),
        ]
    )

    if warnings:
        st.warning("Validation warnings were detected in the extracted data.")
        st.dataframe(pd.DataFrame(warnings), use_container_width=True, hide_index=True)

    failed_pages = result.get("failed_pages", [])
    if failed_pages:
        st.warning("A few pages failed during extraction.")
        st.dataframe(pd.DataFrame(failed_pages), use_container_width=True, hide_index=True)

    st.markdown(
        '<h3 class="wsp-section-title">Data preview</h3>'
        '<p class="wsp-section-hint">The records exactly as they were extracted.</p>',
        unsafe_allow_html=True,
    )
    if records:
        st.dataframe(pd.DataFrame(records), use_container_width=True, hide_index=True)
    else:
        st.info("No records were returned for this job.")

    st.markdown(
        '<h3 class="wsp-section-title" style="margin-top:1.8rem;">Data cleaning</h3>'
        '<p class="wsp-section-hint">Remove duplicates and decide how missing values are handled.</p>',
        unsafe_allow_html=True,
    )
    if records:
        columns = list(records[0].keys())
        duplicate_fields = st.multiselect(
            "Duplicate-removal fields",
            options=columns,
            default=columns[:1] if columns else [],
        )
        missing_rule = st.selectbox("Missing-value rule", options=["flag", "exclude", "keep"], index=1)

        preview = clean_records(records, duplicate_fields=duplicate_fields or None, missing_action=missing_rule)
        st.session_state.last_cleaned = preview["records"]
        st.caption(
            f"Preview includes {preview['stats']['records_cleaned']} cleaned records and "
            f"{preview['stats']['duplicates_removed']} duplicates removed."
        )
        st.dataframe(pd.DataFrame(preview["records"]), use_container_width=True, hide_index=True)
    else:
        st.info("Run an extraction before reviewing cleaning actions.")

    st.markdown(
        '<h3 class="wsp-section-title" style="margin-top:1.8rem;">Export</h3>'
        '<p class="wsp-section-hint">Download the cleaned dataset as a spreadsheet or CSV file.</p>',
        unsafe_allow_html=True,
    )
    export_columns = list(records[0].keys()) if records else []
    selected_export_columns = st.multiselect("Columns to include", options=export_columns, default=export_columns)

    if selected_export_columns:
        export_choice = st.radio("File format", options=["CSV", "Excel"], index=0, horizontal=True)
        export_file = "data.csv" if export_choice == "CSV" else "data.xlsx"
        payload = prepare_download_bytes(
            st.session_state.last_cleaned or records,
            export_choice.lower(),
            selected_export_columns,
        )
        st.download_button(
            label=f"Download {export_choice}",
            data=payload,
            file_name=export_file,
            mime="text/csv" if export_choice == "CSV" else "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        st.dataframe(
            pd.DataFrame(st.session_state.last_cleaned or records)[selected_export_columns],
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("No columns are available to export yet.")


# ---------------------------------------------------------------------------
# History
# ---------------------------------------------------------------------------


def _render_history() -> None:
    """Render the stored extraction history and the current session's jobs."""
    _page_header(
        "History",
        "Every extraction recorded on this machine, with its status and record count.",
    )

    store: ProjectStore = st.session_state.project_store

    st.markdown(
        '<h3 class="wsp-section-title">Recorded jobs</h3>'
        '<p class="wsp-section-hint">Stored locally in the project database.</p>',
        unsafe_allow_html=True,
    )

    try:
        history = store.list_job_history(limit=50)
    except Exception as exc:  # pragma: no cover - UI guard for storage issues
        LOGGER.exception("Job history listing failed")
        st.warning(f"The job history could not be loaded: {exc}")
        history = []

    if history:
        history_frame = pd.DataFrame(
            [
                {
                    "Job": job.job_id,
                    "Started": job.started_at,
                    "Status": job.status,
                    "Records": job.record_count,
                    "Engine": job.engine,
                    "URL": job.url,
                }
                for job in history
            ]
        )
        st.dataframe(history_frame, use_container_width=True, hide_index=True)
    else:
        st.info("No extractions have been recorded yet. Completed runs are stored here automatically.")

    st.markdown(
        '<h3 class="wsp-section-title" style="margin-top:1.8rem;">This session</h3>'
        '<p class="wsp-section-hint">Jobs run in the current browser session.</p>',
        unsafe_allow_html=True,
    )
    jobs = st.session_state.get("jobs") or []
    if jobs:
        session_frame = pd.DataFrame(
            [
                {
                    "URL": job.get("url", ""),
                    "Records": job.get("records", 0),
                    "Status": job.get("status", ""),
                }
                for job in reversed(jobs)
            ]
        )
        st.dataframe(session_frame, use_container_width=True, hide_index=True)
    else:
        st.info("No jobs have been run in this session yet.")


# ---------------------------------------------------------------------------
# Settings
# ---------------------------------------------------------------------------


def _render_saved_projects(store: ProjectStore) -> None:
    """Render the existing saved-project management controls."""
    st.markdown(
        '<h3 class="wsp-section-title">Saved projects</h3>'
        '<p class="wsp-section-hint">Reusable extraction configurations stored on this machine.</p>',
        unsafe_allow_html=True,
    )

    try:
        projects = store.list_projects()
    except Exception as exc:  # pragma: no cover - UI guard for storage issues
        LOGGER.exception("Project listing failed")
        st.warning(f"Saved project data could not be loaded: {exc}")
        projects = []

    if projects:
        project_df = pd.DataFrame(
            [
                {
                    "id": project.project_id,
                    "name": project.name,
                    "url": project.url,
                    "updated": project.updated_at,
                }
                for project in projects
            ]
        )
        st.dataframe(project_df, use_container_width=True, hide_index=True)

        selected_project_id = st.selectbox(
            "Select a project to edit",
            options=[project.project_id for project in projects],
            index=0,
            format_func=lambda project_id: next(
                project.name for project in projects if project.project_id == project_id
            ),
            key="selected_project_id",
        )
        selected_project = next(
            (project for project in projects if project.project_id == selected_project_id),
            None,
        )
        if selected_project is not None:
            with st.form("project_update_form"):
                edited_name = st.text_input("Project name", value=selected_project.name, key="edit_project_name")
                edited_url = st.text_input("Project URL", value=selected_project.url, key="edit_project_url")
                edited_config = st.text_area(
                    "Config JSON",
                    value=json.dumps(selected_project.config, indent=2, sort_keys=True),
                    height=180,
                    key="edit_project_config",
                )
                col_update, col_delete = st.columns([1, 1])
                with col_update:
                    update_project = st.form_submit_button("Update project")
                with col_delete:
                    delete_project = st.form_submit_button("Delete project")

            if update_project:
                try:
                    payload = json.loads(edited_config)
                    project = store.update_project(
                        selected_project_id, name=edited_name, url=edited_url, config=payload
                    )
                    st.success(f"Updated project '{project.name}'.")
                    st.rerun()
                except Exception as exc:
                    LOGGER.exception("Project update failed")
                    st.error(f"The project could not be updated: {exc}")

            if delete_project:
                try:
                    store.delete_project(selected_project_id)
                    st.success(f"Deleted project '{selected_project.name}'.")
                    st.rerun()
                except Exception as exc:
                    LOGGER.exception("Project deletion failed")
                    st.error(f"The project could not be deleted: {exc}")
    else:
        st.info("No projects are saved yet.")

    with st.form("project_form", clear_on_submit=True):
        project_name = st.text_input("Project name", placeholder="My product list")
        project_url = st.text_input("Project URL", placeholder="https://example.com")
        project_config = st.text_area(
            "Config JSON",
            value='{\n  "base_url": "https://example.com",\n  "record_selector": "article",\n'
            '  "fields": {\n    "title": {"selector": "h2", "extraction_type": "text", "required": true}\n  },\n'
            '  "pagination": {"max_pages": 2}\n}',
            height=180,
        )
        submitted_project = st.form_submit_button("Save project")

    if submitted_project:
        try:
            payload = json.loads(project_config)
            project = store.create_project(project_name, project_url, payload)
            st.success(f"Saved project '{project.name}' with ID {project.project_id}.")
            st.rerun()
        except Exception as exc:
            LOGGER.exception("Project save failed")
            st.error(f"The project could not be saved: {exc}")


def _render_settings() -> None:
    """Render genuine application settings and the environment in use."""
    _page_header(
        "Settings",
        "Application configuration, local storage locations, and the environment in use.",
    )

    left, right = st.columns([1, 1], gap="large")

    with left:
        st.markdown(
            '<h3 class="wsp-section-title">Application configuration</h3>'
            '<p class="wsp-section-hint">Default values applied by the extraction engine.</p>',
            unsafe_allow_html=True,
        )
        _stat_cards(
            [
                ("Application", SETTINGS.app_name, "Displayed in the brand and page title"),
                ("Default timeout", f"{SETTINGS.default_timeout}s", "Applied when no override is set"),
                ("Default user agent", SETTINGS.default_user_agent, "Sent with every request"),
                ("Export directory", SETTINGS.export_directory, "Relative to the project root"),
            ],
            mono_labels={"Default user agent"},
        )

        st.markdown(
            '<h3 class="wsp-section-title" style="margin-top:1.6rem;">Responsible use</h3>'
            '<p class="wsp-section-hint">Guardrails that apply to every run.</p>',
            unsafe_allow_html=True,
        )
        st.markdown(
            """
            <div class="wsp-card">
              <div class="wsp-stat__hint">
                Only public HTTP(S) addresses are permitted; localhost and private network ranges are blocked.
                Request counts, page counts and delays are bounded by the advanced settings.
                Extracted content is treated as plain text and is never executed.
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with right:
        st.markdown(
            '<h3 class="wsp-section-title">Environment</h3>'
            '<p class="wsp-section-hint">The interpreter and packages running this workspace.</p>',
            unsafe_allow_html=True,
        )
        try:
            import streamlit

            streamlit_version = streamlit.__version__
        except Exception:  # pragma: no cover - streamlit is always importable at runtime
            streamlit_version = "unavailable"

        _stat_cards(
            [
                ("Python", platform.python_version(), sys.executable),
                ("Streamlit", streamlit_version, "Interface framework"),
                ("Platform", platform.system(), platform.release()),
                ("Working directory", str(Path.cwd()), "Project root"),
            ],
            mono_labels={"Python", "Streamlit", "Working directory"},
        )

        st.markdown(
            '<h3 class="wsp-section-title" style="margin-top:1.6rem;">Local storage</h3>'
            '<p class="wsp-section-hint">Where the workspace keeps its data.</p>',
            unsafe_allow_html=True,
        )
        _stat_cards(
            [
                ("Project database", str(DEFAULT_DB_PATH), "Projects and job history"),
                (
                    "Export folder",
                    str(DEFAULT_DB_PATH.parent.parent / "exports"),
                    "Generated CSV and Excel workbooks",
                ),
            ],
            mono_labels={"Project database", "Export folder"},
        )

    st.markdown("<div style='height:1.4rem'></div>", unsafe_allow_html=True)
    _render_saved_projects(st.session_state.project_store)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def render_app() -> None:
    """Render the complete Streamlit workspace."""
    st.set_page_config(page_title=SETTINGS.app_name, page_icon="📊", layout="wide")
    inject_theme(SECTIONS)

    _init_session_state()
    section = _render_topnav()

    if section == "Overview":
        _render_overview()
    elif section == "New Extraction":
        _render_extraction()
    elif section == "Results":
        _render_results()
    elif section == "History":
        _render_history()
    elif section == "Settings":
        _render_settings()
    else:  # pragma: no cover - defensive fallback for an unknown section
        _render_overview()
