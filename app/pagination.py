"""Multi-page extraction orchestration with guardrails and pagination tracking."""

from __future__ import annotations

import time

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

from app.config import ExtractionConfig, PaginationConfig, resolve_url, validate_url
from app.exceptions import ConfigurationError, InvalidSelectorError, MissingFieldError, NetworkRequestError
from app.extractor import extract_records
from app.network import fetch_html


def _extract_next_page_url(page_html: str, page_url: str, next_page_selector: str) -> str | None:
    """Return the next page URL if a valid pagination link is present."""
    if not next_page_selector:
        return None

    soup = BeautifulSoup(page_html, "html.parser")
    try:
        link = soup.select_one(next_page_selector)
    except SelectorSyntaxError as exc:
        raise InvalidSelectorError(f"Pagination selector '{next_page_selector}' is invalid.") from exc

    if not link:
        return None

    href = link.get("href")
    if not href:
        return None

    resolved = resolve_url(page_url, href)
    if not validate_url(resolved):
        return None
    return resolved


def process_urls(
    urls: list[str],
    config: ExtractionConfig,
    pagination_config: PaginationConfig | None = None,
    fetcher=None,
) -> dict[str, object]:
    """Process a list of permitted URLs, following pagination within configured limits."""
    if not urls:
        raise ConfigurationError("At least one URL is required for processing.")

    if pagination_config is None:
        pagination_config = PaginationConfig()
    pagination_config.validate()

    fetch_fn = fetcher or fetch_html

    queue = []
    for url in urls:
        if not validate_url(url):
            raise ConfigurationError(f"Unsupported URL '{url}' for processing.")
        queue.append(url)

    seen_pages: set[str] = set()
    records: list[dict[str, str]] = []
    processed_pages = 0
    repeated_page_detected = False
    limit_reached = False
    stop_reason = "completed"

    while queue:
        current_url = queue.pop(0)

        if current_url in seen_pages:
            repeated_page_detected = True
            stop_reason = "repeated_page"
            break
        seen_pages.add(current_url)

        time.sleep(pagination_config.request_delay)

        try:
            page_html = fetch_fn(current_url, max_retries=pagination_config.max_retries, retry_backoff=pagination_config.retry_backoff)
        except NetworkRequestError:
            stop_reason = "fatal_network_error"
            break

        processed_pages += 1

        try:
            page_records = extract_records(page_html, config, base_url=current_url)
        except MissingFieldError:
            page_records = []

        if page_records:
            for record in page_records:
                if len(records) >= pagination_config.max_records:
                    limit_reached = True
                    stop_reason = "max_records_reached"
                    break
                records.append(record)
            if limit_reached:
                break

        if processed_pages >= pagination_config.max_pages:
            limit_reached = True
            stop_reason = "max_pages_reached"
            break

        if len(records) >= pagination_config.max_records:
            limit_reached = True
            stop_reason = "max_records_reached"
            break

        next_page = _extract_next_page_url(page_html, current_url, pagination_config.next_page_selector)
        if not next_page:
            stop_reason = "no_next_page"
            break

        if next_page not in seen_pages and next_page not in {item for item in queue}:
            queue.append(next_page)
        else:
            repeated_page_detected = True
            stop_reason = "repeated_page"
            break

    return {
        "records": records,
        "total_records": len(records),
        "pages_processed": processed_pages,
        "repeated_page_detected": repeated_page_detected,
        "limit_reached": limit_reached,
        "stop_reason": stop_reason,
    }
