from __future__ import annotations

import pytest
import requests

from app.exceptions import NetworkRequestError, UnexpectedContentTypeError
from app.network import fetch_html


def test_fetch_html_decodes_utf8_when_header_omits_charset(monkeypatch: pytest.MonkeyPatch) -> None:
    """A UTF-8 page must not be decoded as ISO-8859-1 when the header omits a charset."""

    body = (
        "<html><head><meta charset='utf-8'></head>"
        "<body><p class='price_color'>£51.77</p></body></html>"
    ).encode("utf-8")

    class FakeResponse:
        status_code = 200
        headers = {"Content-Type": "text/html"}
        url = "https://example.com"
        content = body
        apparent_encoding = "utf-8"

    monkeypatch.setattr("app.network.requests.get", lambda *args, **kwargs: FakeResponse())

    html = fetch_html("https://example.com")

    assert "£51.77" in html
    assert "Â£" not in html


def test_fetch_html_decodes_utf8_when_only_meta_declares_charset(monkeypatch: pytest.MonkeyPatch) -> None:
    """International text must survive the whole fetch path unchanged."""
    body = "<html><head><meta charset='utf-8'></head><body><p>£51.77 — café</p></body></html>".encode("utf-8")

    class FakeResponse:
        status_code = 200
        headers = {"Content-Type": "text/html"}
        url = "https://example.com"
        content = body
        apparent_encoding = "utf-8"

    monkeypatch.setattr("app.network.requests.get", lambda *args, **kwargs: FakeResponse())

    html = fetch_html("https://example.com")

    assert "£51.77 — café" in html
    assert "Â£" not in html


def test_fetch_html_honours_charset_declared_in_response_header(monkeypatch: pytest.MonkeyPatch) -> None:
    """An explicit charset in the response header takes precedence."""

    class FakeResponse:
        status_code = 200
        headers = {"Content-Type": "text/html; charset=iso-8859-1"}
        url = "https://example.com"
        content = "<html><body>café</body></html>".encode("iso-8859-1")
        apparent_encoding = "utf-8"

    monkeypatch.setattr("app.network.requests.get", lambda *args, **kwargs: FakeResponse())

    html = fetch_html("https://example.com")

    assert "café" in html
    assert "Â£" not in html


def test_fetch_html_raises_for_http_500(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeResponse:
        status_code = 500
        headers = {"Content-Type": "text/html; charset=utf-8"}
        url = "https://example.com"
        text = "<html><body>error</body></html>"
        content = text.encode("utf-8")

    def fake_get(*args, **kwargs):
        return FakeResponse()

    monkeypatch.setattr("app.network.requests.get", fake_get)

    with pytest.raises(NetworkRequestError):
        fetch_html("https://example.com")


def test_fetch_html_raises_for_unexpected_content_type(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeResponse:
        status_code = 200
        headers = {"Content-Type": "application/json"}
        url = "https://example.com"
        text = "{}"
        content = text.encode("utf-8")

    def fake_get(*args, **kwargs):
        return FakeResponse()

    monkeypatch.setattr("app.network.requests.get", fake_get)

    with pytest.raises(UnexpectedContentTypeError):
        fetch_html("https://example.com")
