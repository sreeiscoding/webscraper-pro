from __future__ import annotations

import io
from pathlib import Path

import openpyxl
import pytest
from streamlit.testing.v1 import AppTest

from app.storage import ProjectStore
from app.ui import build_extraction_config, prepare_download_bytes, run_extraction_job

APP_PATH = str(Path(__file__).resolve().parents[1] / "app" / "main.py")


def test_extraction_records_the_job_in_history(monkeypatch, tmp_path) -> None:
    """A completed extraction must be written to the local job history."""

    def fake_process_urls(urls, config, pagination_config=None, fetcher=None):
        return {
            "records": [{"title": "Alpha", "price": "£10.00"}],
            "total_records": 1,
            "pages_processed": 1,
            "repeated_page_detected": False,
            "limit_reached": False,
            "stop_reason": "completed",
            "failed_pages": [],
        }

    monkeypatch.setattr("app.ui.process_urls", fake_process_urls)

    at = AppTest.from_file(APP_PATH, default_timeout=90)
    at.run()

    store = ProjectStore(tmp_path / "history.db")
    at.session_state["project_store"] = store

    at.radio[0].set_value("New Extraction").run()
    next(t for t in at.text_input if t.label == "Website URL").set_value("https://books.toscrape.com/").run()

    start = next(b for b in at.button if b.label == "Start extraction")
    start.click().run()

    assert not at.exception, [e.value for e in at.exception]

    history = store.list_job_history(limit=10)
    assert len(history) == 1
    assert history[0].url == "https://books.toscrape.com/"
    assert history[0].record_count == 1
    assert history[0].status == "completed"


def test_navigation_sections_render_without_exceptions() -> None:
    """Every navigation destination must render cleanly."""

    at = AppTest.from_file(APP_PATH, default_timeout=90)
    at.run()

    assert at.radio[0].value == "Overview"
    for section in ("New Extraction", "Results", "History", "Settings", "Overview"):
        at.radio[0].set_value(section).run()
        assert not at.exception, f"{section}: {[e.value for e in at.exception]}"


def test_hero_calls_to_action_switch_sections() -> None:
    """The hero buttons must move the workspace to the matching section."""

    at = AppTest.from_file(APP_PATH, default_timeout=90)
    at.run()

    at.button(key="hero_start_extraction").click().run()
    assert at.radio[0].value == "New Extraction"
    assert any(button.label == "Start extraction" for button in at.button)

    at2 = AppTest.from_file(APP_PATH, default_timeout=90)
    at2.run()
    at2.button(key="hero_view_results").click().run()
    assert at2.radio[0].value == "Results"


def test_extraction_form_state_survives_navigation() -> None:
    """Switching sections must not discard the submitted extraction setup."""

    at = AppTest.from_file(APP_PATH, default_timeout=90)
    at.run()

    at.radio[0].set_value("New Extraction").run()
    next(t for t in at.text_input if t.label == "Website URL").set_value("https://books.toscrape.com/").run()

    at.radio[0].set_value("Overview").run()
    at.radio[0].set_value("New Extraction").run()

    assert next(t for t in at.text_input if t.label == "Website URL").value == "https://books.toscrape.com/"


def test_build_extraction_config_rejects_private_or_local_urls() -> None:
    try:
        build_extraction_config("http://localhost:8000", "books", {})
        assert False, "Expected a validation error for localhost URLs"
    except ValueError:
        pass


def test_run_extraction_job_uses_existing_engine(monkeypatch) -> None:
    captured: dict[str, object] = {}

    def fake_process_urls(urls, config, pagination_config=None, fetcher=None):
        captured["urls"] = urls
        return {
            "records": [{"title": "Alpha", "price": "£10.00"}],
            "total_records": 1,
            "pages_processed": 1,
            "repeated_page_detected": False,
            "limit_reached": False,
            "stop_reason": "completed",
            "failed_pages": [],
        }

    monkeypatch.setattr("app.ui.process_urls", fake_process_urls)

    result = run_extraction_job(
        "https://books.toscrape.com/",
        "books",
        field_overrides={"title": {"selector": "article h3 a"}},
        pagination_config={"max_pages": 2, "max_records": 50, "request_delay": 0.1, "next_page_selector": "a.next"},
    )

    assert captured["urls"] == ["https://books.toscrape.com/"]
    assert result["records"][0]["title"] == "Alpha"
    assert result["total_records"] == 1


def test_prepare_download_bytes_returns_valid_csv_and_excel() -> None:
    records = [{"title": "Alpha", "price": "£10.00"}]

    csv_bytes = prepare_download_bytes(records, "csv", ["title", "price"])
    excel_bytes = prepare_download_bytes(records, "excel", ["title", "price"])

    assert csv_bytes.removeprefix(b"\xef\xbb\xbf").startswith(b"title,price")
    assert excel_bytes

    workbook = openpyxl.load_workbook(io.BytesIO(excel_bytes))
    assert workbook.active["A1"].value == "title"
