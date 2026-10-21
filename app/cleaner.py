"""Utilities for normalizing extracted records before export."""

from __future__ import annotations

import re
from typing import Any
from urllib.parse import urlparse


_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _normalise_whitespace(value: Any) -> Any:
    if isinstance(value, str):
        return re.sub(r"\s+", " ", value).strip()
    return value


def _safe_string(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    return str(value)


def _build_record_key(record: dict[str, Any], duplicate_fields: list[str] | None) -> tuple[str, ...]:
    if not duplicate_fields:
        return tuple(sorted(str(record.get(key, "")).strip() for key in record))
    return tuple(str(record.get(field, "")).strip() for field in duplicate_fields)


def clean_record(record: dict[str, Any]) -> dict[str, Any]:
    """Strip strings and normalize empty values for export-friendly records."""
    cleaned: dict[str, Any] = {}

    for key, value in record.items():
        value = _normalise_whitespace(value)
        if value is None:
            cleaned[key] = ""
        elif isinstance(value, str):
            cleaned[key] = value.strip()
        else:
            cleaned[key] = value

    return cleaned


def clean_records(
    records: list[dict[str, Any]],
    duplicate_fields: list[str] | None = None,
    missing_action: str = "flag",
) -> dict[str, Any]:
    """Clean records and apply duplicate removal according to configured rules."""
    cleaned_records: list[dict[str, Any]] = []
    seen: set[tuple[str, ...]] = set()
    duplicates_removed = 0
    flagged = 0

    for record in records:
        cleaned = clean_record(record)
        if duplicate_fields is not None and duplicate_fields:
            key = _build_record_key(cleaned, duplicate_fields)
            if key in seen:
                duplicates_removed += 1
                continue
            seen.add(key)

        missing_required = any((value is None or str(value).strip() == "") for value in cleaned.values())
        if missing_action == "exclude" and missing_required:
            flagged += 1
            continue
        if missing_action == "flag" and missing_required:
            flagged += 1

        cleaned_records.append(cleaned)

    stats = {
        "records_processed": len(records),
        "records_cleaned": len(cleaned_records),
        "duplicates_removed": duplicates_removed,
        "flagged": flagged,
        "removed": len(records) - len(cleaned_records) - duplicates_removed,
    }

    return {"records": cleaned_records, "stats": stats}


def validate_records(
    records: list[dict[str, Any]],
    required_fields: set[str] | None = None,
    email_fields: set[str] | None = None,
    url_fields: set[str] | None = None,
) -> dict[str, Any]:
    """Validate records and return any suspicious or invalid values without altering source records."""
    flags: list[dict[str, Any]] = []
    validated: list[dict[str, Any]] = []

    required_fields = required_fields or set()
    email_fields = email_fields or set()
    url_fields = url_fields or set()

    for index, record in enumerate(records):
        normalised = clean_record(record)
        validated.append(normalised)

        for field_name in sorted(required_fields):
            value = normalised.get(field_name, "")
            if value is None or str(value).strip() == "":
                flags.append({"index": index, "field_name": field_name, "flag_type": "missing_required"})

        for field_name in sorted(email_fields):
            value = str(normalised.get(field_name, "")).strip()
            if value and not _EMAIL_RE.match(value):
                flags.append({"index": index, "field_name": field_name, "flag_type": "invalid_email"})

        for field_name in sorted(url_fields):
            value = str(normalised.get(field_name, "")).strip()
            if value:
                parsed = urlparse(value)
                if parsed.scheme not in {"http", "https"} or not parsed.netloc:
                    flags.append({"index": index, "field_name": field_name, "flag_type": "invalid_url"})

    return {"records": validated, "flags": flags}
