"""Example extraction configurations for different websites."""

from __future__ import annotations

from app.config import ExtractionConfig, FieldSpec


BOOKS_TO_SCRAPE_CONFIG = ExtractionConfig(
    base_url="https://books.toscrape.com/",
    fields={
        "title": FieldSpec(name="title", selector="article.product_pod h3 a", extraction_type="text", required=True),
        "price": FieldSpec(name="price", selector="article.product_pod p.price_color", extraction_type="text", required=True),
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


LOCAL_PRODUCT_LIST_CONFIG = ExtractionConfig(
    base_url="https://example.com/catalog/",
    record_selector="article.product-card",
    fields={
        "title": FieldSpec(name="title", selector="h3 a", extraction_type="text", required=True),
        "price": FieldSpec(name="price", selector="p.price", extraction_type="text", required=True),
        "stock": FieldSpec(name="stock", selector="p.stock", extraction_type="text", required=True),
        "product_url": FieldSpec(
            name="product_url",
            selector="h3 a",
            extraction_type="url",
            attribute_name="href",
            required=True,
        ),
    },
)
