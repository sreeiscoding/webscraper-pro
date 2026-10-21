from __future__ import annotations

import pytest
import requests

from app.config import ExtractionConfig, FieldSpec, PaginationConfig
from app.network import fetch_html
from app.pagination import process_urls


HTML_PAGE_1 = """
<html><body>
  <article class="product-card"><h3><a href="/books/1">Alpha</a></h3><p class="price">£10.00</p></article>
  <article class="product-card"><h3><a href="/books/2">Beta</a></h3><p class="price">£12.00</p></article>
  <a class="next-page" href="page-2">Next</a>
</body></html>
"""

HTML_PAGE_2 = """
<html><body>
  <article class="product-card"><h3><a href="/books/3">Gamma</a></h3><p class="price">£15.00</p></article>
  <a class="next-page" href="page-3">Next</a>
</body></html>
"""

HTML_PAGE_3 = """
<html><body>
  <article class="product-card"><h3><a href="/books/4">Delta</a></h3><p class="price">£18.00</p></article>
</body></html>
"""


@pytest.fixture
def extraction_config() -> ExtractionConfig:
    return ExtractionConfig(
        base_url="https://example.com/catalog/",
        record_selector="article.product-card",
        fields={
            "title": FieldSpec(name="title", selector="h3 a", extraction_type="text", required=True),
            "price": FieldSpec(name="price", selector="p.price", extraction_type="text", required=True),
        },
    )


def test_process_urls_handles_normal_pagination(extraction_config: ExtractionConfig) -> None:
    pages = {
        "https://example.com/catalog/": HTML_PAGE_1,
        "https://example.com/catalog/page-2": HTML_PAGE_2,
        "https://example.com/catalog/page-3": HTML_PAGE_3,
    }

    def fake_fetcher(url: str, **kwargs):
        if url not in pages:
            raise AssertionError(f"Unexpected URL requested: {url}")
        return pages[url]

    result = process_urls(
        ["https://example.com/catalog/"],
        extraction_config,
        PaginationConfig(max_pages=5, max_records=10, next_page_selector="a.next-page", request_delay=0.0),
        fetcher=fake_fetcher,
    )

    assert result["total_records"] == 4
    assert result["records"][0]["title"] == "Alpha"
    assert result["pages_processed"] == 3


def test_process_urls_stops_without_next_page_link(extraction_config: ExtractionConfig) -> None:
    html = "<html><body><article class='product-card'><h3><a href='/books/1'>Single</a></h3><p class='price'>£9.00</p></article></body></html>"

    result = process_urls(
        ["https://example.com/catalog/"],
        extraction_config,
        PaginationConfig(max_pages=5, max_records=10, next_page_selector="a.next-page", request_delay=0.0),
        fetcher=lambda url, **kwargs: html,
    )

    assert result["total_records"] == 1
    assert result["pages_processed"] == 1


def test_process_urls_detects_repeated_page(extraction_config: ExtractionConfig) -> None:
    pages = {
        "https://example.com/catalog/": "<html><body><article class='product-card'><h3><a href='/books/1'>Alpha</a></h3><p class='price'>£10.00</p></article><a class='next-page' href='page-2'>Next</a></body></html>",
        "https://example.com/catalog/page-2": "<html><body><article class='product-card'><h3><a href='/books/2'>Beta</a></h3><p class='price'>£12.00</p></article><a class='next-page' href='../catalog/'>Next</a></body></html>",
    }

    result = process_urls(
        ["https://example.com/catalog/"],
        extraction_config,
        PaginationConfig(max_pages=5, max_records=10, next_page_selector="a.next-page", request_delay=0.0),
        fetcher=lambda url, **kwargs: pages[url],
    )

    assert result["repeated_page_detected"] is True
    assert result["pages_processed"] == 2


def test_process_urls_respects_limits(extraction_config: ExtractionConfig) -> None:
    html = "<html><body><article class='product-card'><h3><a href='/books/1'>Alpha</a></h3><p class='price'>£10.00</p></article><a class='next-page' href='/page-2'>Next</a></body></html>"

    result = process_urls(
        ["https://example.com/catalog/"],
        extraction_config,
        PaginationConfig(max_pages=1, max_records=2, next_page_selector="a.next-page", request_delay=0.0),
        fetcher=lambda url, **kwargs: html,
    )

    assert result["limit_reached"] is True
    assert result["pages_processed"] == 1


def test_fetch_html_retries_transient_failures(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeResponse:
        status_code = 200
        headers = {"Content-Type": "text/html; charset=utf-8"}
        url = "https://example.com"
        text = "<html><body>ok</body></html>"
        content = text.encode("utf-8")

    calls = {"count": 0}

    def fake_get(*args, **kwargs):
        calls["count"] += 1
        if calls["count"] == 1:
            raise requests.exceptions.Timeout("temporary")
        return FakeResponse()

    monkeypatch.setattr("app.network.requests.get", fake_get)
    result = fetch_html("https://example.com", max_retries=1, retry_backoff=0.0)

    assert result == "<html><body>ok</body></html>"


def test_request_delay_is_used(monkeypatch: pytest.MonkeyPatch, extraction_config: ExtractionConfig) -> None:
    calls: list[float] = []

    def fake_sleep(delay: float) -> None:
        calls.append(delay)

    html = "<html><body><article class='product-card'><h3><a href='/books/1'>Alpha</a></h3><p class='price'>£10.00</p></article></body></html>"
    monkeypatch.setattr("app.pagination.time.sleep", fake_sleep)

    result = process_urls(
        ["https://example.com/catalog/"],
        extraction_config,
        PaginationConfig(max_pages=1, max_records=10, next_page_selector="a.next-page", request_delay=0.25),
        fetcher=lambda url, **kwargs: html,
    )

    assert result["records"]
    assert calls == [0.25]
