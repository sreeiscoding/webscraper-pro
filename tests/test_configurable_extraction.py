from __future__ import annotations

import json

import pytest

from app.config import ExtractionConfig, FieldSpec
from app.exceptions import ConfigurationError, InvalidSelectorError, MissingFieldError, UnsupportedExtractionTypeError
from app.extractor import extract_fields, extract_records


HTML_FIXTURE = """
<html>
  <body>
    <article class="product-card">
      <h3><a href="/books/1">Alpha</a></h3>
      <p class="price">£10.00</p>
      <p class="stock">In stock</p>
    </article>
    <article class="product-card">
      <h3><a href="/books/2">Beta</a></h3>
      <p class="price">£12.50</p>
      <p class="stock">Out of stock</p>
    </article>
  </body>
</html>
"""


def test_extract_fields_supports_text_attribute_and_url() -> None:
    config = ExtractionConfig(
        base_url="https://example.com/catalog/",
        fields={
            "title": FieldSpec(name="title", selector="h3 a", extraction_type="text", required=True),
            "href": FieldSpec(name="href", selector="h3 a", extraction_type="attribute", attribute_name="href", required=True),
            "product_url": FieldSpec(
                name="product_url",
                selector="h3 a",
                extraction_type="url",
                attribute_name="href",
                required=True,
            ),
        },
    )

    result = extract_fields(HTML_FIXTURE, config)

    assert result["title"] == "Alpha"
    assert result["href"] == "/books/1"
    assert result["product_url"] == "https://example.com/books/1"


def test_extract_records_supports_repeated_elements() -> None:
    config = ExtractionConfig(
        base_url="https://example.com/catalog/",
        record_selector="article.product-card",
        fields={
            "title": FieldSpec(name="title", selector="h3 a", extraction_type="text", required=True),
            "price": FieldSpec(name="price", selector="p.price", extraction_type="text", required=True),
            "availability": FieldSpec(name="availability", selector="p.stock", extraction_type="text", required=True),
            "product_url": FieldSpec(
                name="product_url",
                selector="h3 a",
                extraction_type="url",
                attribute_name="href",
                required=True,
            ),
        },
    )

    result = extract_records(HTML_FIXTURE, config)

    assert len(result) == 2
    assert result[0]["title"] == "Alpha"
    assert result[1]["title"] == "Beta"
    assert result[0]["product_url"] == "https://example.com/books/1"
    assert result[1]["product_url"] == "https://example.com/books/2"


def test_configuration_validation_rejects_bad_values() -> None:
    with pytest.raises(ConfigurationError):
        FieldSpec(name="", selector="h1", extraction_type="text").validate()

    with pytest.raises(InvalidSelectorError):
        FieldSpec(name="title", selector="h1(=", extraction_type="text").validate()

    with pytest.raises(UnsupportedExtractionTypeError):
        FieldSpec(name="title", selector="h1", extraction_type="image").validate()

    with pytest.raises(ConfigurationError):
        ExtractionConfig(base_url="https://example.com", fields={}).validate()


def test_json_round_trip_for_config() -> None:
    config = ExtractionConfig(
        base_url="https://example.com/catalog/",
        record_selector="article.product-card",
        fields={
            "title": FieldSpec(name="title", selector="h3 a", extraction_type="text", required=True),
            "price": FieldSpec(name="price", selector="p.price", extraction_type="text", required=True),
        },
    )

    payload = json.loads(config.to_json())
    restored = ExtractionConfig.from_json(json.dumps(payload))

    assert restored.base_url == "https://example.com/catalog/"
    assert restored.record_selector == "article.product-card"
    assert restored.fields["title"].selector == "h3 a"
    assert restored.fields["price"].extraction_type == "text"


def test_missing_required_selectors_raise_error() -> None:
    config = ExtractionConfig(
        base_url="https://example.com/catalog/",
        fields={
            "title": FieldSpec(name="title", selector="h2", extraction_type="text", required=True),
        },
    )

    with pytest.raises(MissingFieldError):
        extract_fields(HTML_FIXTURE, config)
