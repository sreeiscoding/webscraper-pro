from __future__ import annotations

import pytest
import requests

from app.config import ExtractionConfig, FieldSpec
from app.exceptions import InvalidSelectorError, MissingFieldError, NetworkRequestError
from app.extractor import extract_fields
from app.network import fetch_html


HTML_FIXTURE = """
<html>
  <head><title>Demo Store</title></head>
  <body>
    <h1>Example Product</h1>
    <p class="price">$9.99</p>
    <p class="stock">In stock</p>
    <a class="product-link" href="/books/1">View details</a>
  </body>
</html>
"""


def test_extract_fields_supports_text_and_absolute_urls() -> None:
    config = ExtractionConfig(
        base_url="https://example.com/catalog/",
        fields={
            "title": FieldSpec(selector="h1", field_type="text", required=True),
            "price": FieldSpec(selector="p.price", field_type="text", required=True),
            "availability": FieldSpec(selector="p.stock", field_type="text", required=True),
            "product_url": FieldSpec(
                selector="a.product-link",
                field_type="absolute_url",
                attribute_name="href",
                required=True,
            ),
        },
    )

    result = extract_fields(HTML_FIXTURE, config)

    assert result == {
        "title": "Example Product",
        "price": "$9.99",
        "availability": "In stock",
        "product_url": "https://example.com/books/1",
    }


def test_extract_fields_raises_for_missing_required_field() -> None:
    config = ExtractionConfig(
        base_url="https://example.com/",
        fields={
            "title": FieldSpec(selector="h2", field_type="text", required=True),
        },
    )

    with pytest.raises(MissingFieldError):
        extract_fields(HTML_FIXTURE, config)


def test_extract_fields_raises_for_invalid_selector() -> None:
    config = ExtractionConfig(
        base_url="https://example.com/",
        fields={
            "title": FieldSpec(selector="h1(=", field_type="text", required=True),
        },
    )

    with pytest.raises(InvalidSelectorError):
        extract_fields(HTML_FIXTURE, config)


def test_fetch_html_raises_network_request_error_on_timeout(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_get(*args, **kwargs):
        raise requests.exceptions.Timeout("Request timed out")

    monkeypatch.setattr("app.network.requests.get", fake_get)

    with pytest.raises(NetworkRequestError):
        fetch_html("https://example.com")
