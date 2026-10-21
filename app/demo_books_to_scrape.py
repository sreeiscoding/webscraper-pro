"""Demonstration extraction configuration for Books to Scrape."""

from __future__ import annotations

from app.config import ExtractionConfig, FieldSpec


BOOKS_TO_SCRAPE_CONFIG = ExtractionConfig(
    base_url="https://books.toscrape.com/",
    fields={
        "title": FieldSpec(
            name="title",
            selector="article.product_pod h3 a",
            extraction_type="text",
            required=True,
        ),
        "price": FieldSpec(
            name="price",
            selector="article.product_pod p.price_color",
            extraction_type="text",
            required=True,
        ),
        "availability": FieldSpec(
            name="availability",
            selector="article.product_pod p.instock.availability",
            extraction_type="text",
            required=True,
        ),
        "product_url": FieldSpec(
            name="product_url",
            selector="article.product_pod h3 a",
            extraction_type="url",
            attribute_name="href",
            required=True,
        ),
    },
)
