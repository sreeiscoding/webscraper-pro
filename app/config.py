"""Application configuration and shared validation helpers."""

from __future__ import annotations

import ipaddress
import json
import socket
from dataclasses import dataclass, field
from urllib.parse import urljoin, urlparse

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

from app.exceptions import (
    ConfigurationError,
    InvalidSelectorError,
    UnsupportedExtractionTypeError,
)


@dataclass(frozen=True)
class AppSettings:
    """Base settings for the local scraping application."""

    app_name: str = "WebScraper Pro"
    default_timeout: int = 15
    default_user_agent: str = "WebScraperPro/0.1"
    export_directory: str = "exports"


@dataclass(frozen=True)
class FieldSpec:
    """Describes how a single HTML field should be extracted."""

    name: str | None = None
    selector: str = ""
    extraction_type: str = "text"
    required: bool = True
    attribute_name: str | None = None
    normalize_whitespace: bool = True
    default: str = ""
    field_type: str | None = None

    def __post_init__(self) -> None:
        if self.field_type is not None:
            object.__setattr__(self, "extraction_type", self.field_type)

        if self.extraction_type in {"absolute_url", "url"}:
            object.__setattr__(self, "extraction_type", "url")

        if self.name is None:
            object.__setattr__(self, "name", (self.selector or "").strip())
        elif not self.name:
            object.__setattr__(self, "name", "")

    def validate(self) -> None:
        """Validate a field definition before use."""
        if not self.name or not self.name.strip():
            raise ConfigurationError("Field names must not be empty.")

        if not self.selector or not self.selector.strip():
            raise ConfigurationError(f"Field '{self.name}' must define a CSS selector.")

        extraction_type = self.extraction_type.lower()
        if extraction_type in {"absolute_url"}:
            extraction_type = "url"

        supported = {"text", "attribute", "url", "html"}
        if extraction_type not in supported:
            raise UnsupportedExtractionTypeError(
                f"Unsupported extraction type '{self.extraction_type}' for field '{self.name}'."
            )

        if extraction_type in {"attribute", "url"} and not self.attribute_name:
            object.__setattr__(self, "attribute_name", "href")

        try:
            BeautifulSoup("<html><body></body></html>", "html.parser").select(self.selector)
        except SelectorSyntaxError as exc:
            raise InvalidSelectorError(f"Selector '{self.selector}' is invalid for field '{self.name}'.") from exc

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-safe dictionary representation of the field."""
        return {
            "name": self.name,
            "selector": self.selector,
            "extraction_type": self.extraction_type,
            "attribute_name": self.attribute_name,
            "required": self.required,
            "normalize_whitespace": self.normalize_whitespace,
            "default": self.default,
        }

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> "FieldSpec":
        """Create a FieldSpec instance from a dictionary definition."""
        if not isinstance(data, dict):
            raise ConfigurationError("Field definitions must be provided as a dictionary.")

        payload = dict(data)
        name = payload.pop("name", None)
        known_keys = set(cls.__dataclass_fields__)
        kwargs = {key: value for key, value in payload.items() if key in known_keys}
        return cls(name=str(name) if name is not None else None, **kwargs)


@dataclass(frozen=True)
class ExtractionConfig:
    """Reusable configuration for extracting a set of fields from a page."""

    base_url: str
    fields: dict[str, FieldSpec] = field(default_factory=dict)
    record_selector: str = ""

    def validate(self) -> None:
        """Validate the configuration before extraction begins."""
        if not self.base_url or not validate_url(self.base_url):
            raise ConfigurationError("Base URL is required and must be a valid public HTTP(S) URL.")

        if not self.fields:
            raise ConfigurationError("At least one field must be configured for extraction.")

        for field_key, field_spec in self.fields.items():
            if not isinstance(field_spec, FieldSpec):
                raise ConfigurationError(f"Field '{field_key}' is not a valid FieldSpec instance.")
            field_spec.validate()

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-safe dictionary representation of the configuration."""
        return {
            "base_url": self.base_url,
            "record_selector": self.record_selector,
            "fields": {name: spec.to_dict() for name, spec in self.fields.items()},
        }

    def to_json(self) -> str:
        """Serialize the configuration to JSON."""
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> "ExtractionConfig":
        """Create an ExtractionConfig instance from a dictionary definition."""
        if not isinstance(data, dict):
            raise ConfigurationError("Extraction configuration must be provided as a dictionary.")

        raw_fields = data.get("fields", {}) or {}
        if not isinstance(raw_fields, dict):
            raise ConfigurationError("Extraction fields must be provided as a dictionary.")

        fields: dict[str, FieldSpec] = {}
        for field_name, field_value in raw_fields.items():
            if isinstance(field_value, FieldSpec):
                fields[str(field_name)] = field_value
            elif isinstance(field_value, dict):
                fields[str(field_name)] = FieldSpec.from_dict(field_value)
            else:
                raise ConfigurationError(f"Field '{field_name}' is not a valid field definition.")

        return cls(
            base_url=str(data.get("base_url", "")),
            fields=fields,
            record_selector=str(data.get("record_selector", "")),
        )

    @classmethod
    def from_json(cls, payload: str) -> "ExtractionConfig":
        """Load an ExtractionConfig instance from JSON."""
        return cls.from_dict(json.loads(payload))


@dataclass(frozen=True)
class PaginationConfig:
    """Controls paging behaviour and request pacing for multi-page extraction."""

    max_pages: int = 5
    max_records: int = 200
    next_page_selector: str = ""
    request_delay: float = 0.5
    max_retries: int = 1
    retry_backoff: float = 0.5

    def validate(self) -> None:
        """Validate pagination settings before processing pages."""
        if self.max_pages < 1:
            raise ConfigurationError("The maximum page count must be at least 1.")
        if self.max_records < 1:
            raise ConfigurationError("The maximum record count must be at least 1.")
        if self.request_delay < 0:
            raise ConfigurationError("Request delay cannot be negative.")
        if self.max_retries < 0:
            raise ConfigurationError("Retry count cannot be negative.")
        if self.retry_backoff < 0:
            raise ConfigurationError("Retry backoff cannot be negative.")

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-safe dictionary representation of the configuration."""
        return {
            "max_pages": self.max_pages,
            "max_records": self.max_records,
            "next_page_selector": self.next_page_selector,
            "request_delay": self.request_delay,
            "max_retries": self.max_retries,
            "retry_backoff": self.retry_backoff,
        }

    def to_json(self) -> str:
        """Serialize the configuration to JSON."""
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> "PaginationConfig":
        """Create a PaginationConfig instance from a dictionary."""
        return cls(
            max_pages=int(data.get("max_pages", 5)),
            max_records=int(data.get("max_records", 200)),
            next_page_selector=str(data.get("next_page_selector", "")),
            request_delay=float(data.get("request_delay", 0.5)),
            max_retries=int(data.get("max_retries", 1)),
            retry_backoff=float(data.get("retry_backoff", 0.5)),
        )

    @classmethod
    def from_json(cls, payload: str) -> "PaginationConfig":
        """Load a PaginationConfig instance from JSON."""
        data = json.loads(payload)
        return cls.from_dict(data)


SETTINGS = AppSettings()


def resolve_url(base_url: str, href: str) -> str:
    """Resolve a link found on a page against the base URL of the page it came from.

    Standard URL rules are applied: absolute links are kept as-is, while relative
    links are resolved against the base URL so that the result points at the same
    location a browser would request.
    """
    cleaned = (href or "").strip()
    if not cleaned:
        return base_url
    return urljoin(base_url, cleaned)


def _resolve_ip_addresses(hostname: str) -> list[ipaddress._BaseAddress]:
    """Resolve a hostname to IP addresses for public-network validation."""
    try:
        records = socket.getaddrinfo(hostname, None, type=socket.SOCK_STREAM)
    except socket.gaierror:
        return []

    addresses: list[ipaddress._BaseAddress] = []
    for record in records:
        ip_text = record[4][0]
        try:
            addresses.append(ipaddress.ip_address(ip_text))
        except ValueError:
            continue
    return addresses


def validate_url(url: str) -> bool:
    """Return True only for supported, public HTTP(S) URLs."""
    if not isinstance(url, str):
        return False

    candidate = url.strip()
    if not candidate:
        return False

    parsed = urlparse(candidate)
    if parsed.scheme.lower() not in {"http", "https"}:
        return False

    if not parsed.netloc:
        return False

    hostname = parsed.hostname
    if not hostname:
        return False

    lowered = hostname.lower()
    if lowered == "localhost" or lowered.endswith(".localhost"):
        return False

    try:
        port = parsed.port
        if port is not None and not (1 <= port <= 65535):
            return False
    except ValueError:
        return False

    addresses = _resolve_ip_addresses(hostname)
    if not addresses:
        return False

    return not any(
        address.is_loopback
        or address.is_private
        or address.is_link_local
        or address.is_multicast
        or address.is_reserved
        or address.is_unspecified
        or getattr(address, "is_site_local", False)
        for address in addresses
    )
