"""HTML extraction utilities for structured field extraction."""

from __future__ import annotations

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

from app.config import ExtractionConfig, FieldSpec, resolve_url, validate_url
from app.exceptions import InvalidSelectorError, MissingFieldError, UnsupportedExtractionTypeError


def _normalise_text(value: str, normalize_whitespace: bool) -> str:
    """Normalise whitespace when configured to do so."""
    if not normalize_whitespace:
        return value
    return " ".join(value.split())


def _extract_from_element(
    element: object,
    field_spec: FieldSpec,
    base_url: str,
) -> str:
    extraction_type = field_spec.extraction_type.lower()

    if extraction_type == "text":
        value = element.get_text(" ", strip=True)
        return _normalise_text(value, field_spec.normalize_whitespace)

    if extraction_type == "html":
        value = element.decode_contents()
        return _normalise_text(value, field_spec.normalize_whitespace)

    attribute_name = field_spec.attribute_name or "href"
    raw_value = element.get(attribute_name)

    if raw_value is None:
        raise MissingFieldError(f"Field '{attribute_name}' was not found in the selected element.")

    raw_value = raw_value.strip()

    if extraction_type == "attribute":
        return _normalise_text(raw_value, field_spec.normalize_whitespace)

    if extraction_type == "url":
        resolved = resolve_url(base_url, raw_value)
        if not validate_url(resolved):
            raise ValueError(f"Resolved URL '{resolved}' is not a valid HTTP(S) URL.")
        return resolved

    raise UnsupportedExtractionTypeError(
        f"Unsupported extraction type '{field_spec.extraction_type}' for field '{field_spec.name}'."
    )


def extract_fields(html: str, config: ExtractionConfig, base_url: str | None = None) -> dict[str, str]:
    """Extract values from HTML using a reusable extraction configuration.

    ``base_url`` overrides the configuration base URL when relative links must be
    resolved against the page the markup was actually loaded from.
    """
    config.validate()
    resolution_base = base_url or config.base_url
    soup = BeautifulSoup(html, "html.parser")
    extracted: dict[str, str] = {}

    for field_name, field_spec in config.fields.items():
        selector = field_spec.selector
        try:
            matches = soup.select(selector)
        except SelectorSyntaxError as exc:  # pragma: no cover - bs4 raises this on malformed selectors
            raise InvalidSelectorError(f"Selector '{selector}' is invalid.") from exc

        if not matches:
            if field_spec.required:
                raise MissingFieldError(f"Required field '{field_name}' was not found using selector '{selector}'.")
            extracted[field_name] = field_spec.default or ""
            continue

        value = _extract_from_element(matches[0], field_spec, resolution_base)
        extracted[field_name] = value

    return extracted


def extract_records(html: str, config: ExtractionConfig, base_url: str | None = None) -> list[dict[str, str]]:
    """Extract repeated records from matching HTML elements using a record selector.

    ``base_url`` overrides the configuration base URL so that relative links are
    resolved against the page the records were loaded from.
    """
    config.validate()
    resolution_base = base_url or config.base_url
    soup = BeautifulSoup(html, "html.parser")

    if config.record_selector:
        containers = soup.select(config.record_selector)
    else:
        containers = [soup]

    if not containers:
        raise MissingFieldError(
            f"No elements were found for record selector '{config.record_selector}'."
        )

    records: list[dict[str, str]] = []

    for container in containers:
        record: dict[str, str] = {}
        for field_name, field_spec in config.fields.items():
            try:
                matches = container.select(field_spec.selector)
            except SelectorSyntaxError as exc:
                raise InvalidSelectorError(f"Selector '{field_spec.selector}' is invalid.") from exc

            if not matches:
                if field_spec.required:
                    raise MissingFieldError(
                        f"Required field '{field_name}' was not found using selector '{field_spec.selector}'."
                    )
                record[field_name] = field_spec.default or ""
                continue

            record[field_name] = _extract_from_element(matches[0], field_spec, resolution_base)
        records.append(record)

    return records
