"""HTTP request helpers for fetching remote pages safely."""

from __future__ import annotations

import re
import time
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import Any

import requests

from app.config import SETTINGS, validate_url
from app.exceptions import NetworkRequestError, UnexpectedContentTypeError

_HEADER_CHARSET_PATTERN = re.compile(r"charset\s*=\s*[\"']?\s*([A-Za-z0-9_.:+-]+)", re.IGNORECASE)
_META_CHARSET_PATTERN = re.compile(rb"<meta[^>]*?charset\s*=\s*[\"']?\s*([A-Za-z0-9_.:+-]+)", re.IGNORECASE)


def _detect_html_encoding(response: requests.Response) -> str:
    """Determine the character encoding declared for an HTML response.

    ``requests`` assumes ISO-8859-1 for ``text/*`` responses that omit a charset,
    which silently corrupts UTF-8 documents such as pages that use the pound sign.
    The charset is therefore taken from the response header, then from the
    document's own ``<meta charset>`` declaration, and finally from statistical
    detection of the raw bytes.
    """
    header_match = _HEADER_CHARSET_PATTERN.search(response.headers.get("Content-Type", ""))
    if header_match:
        return header_match.group(1)

    meta_match = _META_CHARSET_PATTERN.search(response.content[:8192])
    if meta_match:
        declared = meta_match.group(1).decode("ascii", errors="ignore").strip()
        if declared:
            return declared

    return response.apparent_encoding or "utf-8"


def _decode_html(response: requests.Response) -> str:
    """Decode an HTML response body using the detected character encoding."""
    encoding = _detect_html_encoding(response)
    try:
        return response.content.decode(encoding)
    except (LookupError, UnicodeDecodeError):
        return response.content.decode("utf-8", errors="replace")


def _retry_delay_from_headers(headers: dict[str, str]) -> float | None:
    """Return a delay value from the Retry-After header when present."""
    retry_after = headers.get("Retry-After")
    if not retry_after:
        return None

    try:
        return max(0.0, float(retry_after))
    except ValueError:
        try:
            retry_at = parsedate_to_datetime(retry_after)
            delta = (retry_at - datetime.now(timezone.utc)).total_seconds()
            return max(0.0, delta)
        except (TypeError, ValueError, OverflowError):
            return None


def _fetch_with_playwright(
    url: str,
    user_agent: str | None = None,
    render_config: dict[str, Any] | None = None,
) -> str:
    """Fetch rendered HTML by launching a temporary browser session for JavaScript-heavy pages."""
    config = render_config or {}
    wait_for = str(config.get("wait_for", "body"))
    wait_timeout = int(config.get("wait_timeout", 30000))
    page_load_timeout = int(config.get("page_load_timeout", 30000))
    wait_until = str(config.get("wait_until", "domcontentloaded"))

    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:  # pragma: no cover - optional dependency path
        raise NetworkRequestError(
            "Playwright is not installed. Install it with 'python -m pip install playwright' and 'python -m playwright install chromium'."
        ) from exc

    browser = None
    context = None
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            context_options: dict[str, Any] = {}
            if user_agent:
                context_options["user_agent"] = user_agent
            context = browser.new_context(**context_options)
            page = context.new_page()
            page.goto(url, wait_until=wait_until, timeout=page_load_timeout)
            if wait_for:
                page.wait_for_selector(wait_for, timeout=wait_timeout)
            final_url = page.url
            if not validate_url(final_url):
                raise NetworkRequestError(f"The final URL '{final_url}' is not a permitted public destination.")
            return page.content()
    except Exception as exc:
        if isinstance(exc, NetworkRequestError):
            raise
        raise NetworkRequestError(f"Browser rendering failed for '{url}'.") from exc
    finally:
        if context is not None:
            try:
                context.close()
            except Exception:  # pragma: no cover - best effort cleanup
                pass
        if browser is not None:
            try:
                browser.close()
            except Exception:  # pragma: no cover - best effort cleanup
                pass


def fetch_html(
    url: str,
    timeout: int | None = None,
    user_agent: str | None = None,
    max_retries: int = 0,
    retry_backoff: float = 0.5,
    engine: str = "static",
    render_config: dict[str, Any] | None = None,
) -> str:
    """Fetch HTML from a public URL using either static HTTP requests or optional browser rendering."""
    if not url or not url.strip():
        raise ValueError("A URL is required.")

    if not validate_url(url):
        raise ValueError("Only public HTTP(S) URLs are allowed.")

    if engine.lower() == "playwright":
        return _fetch_with_playwright(url, user_agent=user_agent, render_config=render_config)

    timeout_value = timeout if timeout is not None else SETTINGS.default_timeout
    headers = {"User-Agent": user_agent or SETTINGS.default_user_agent}

    response = None
    for attempt in range(max_retries + 1):
        try:
            response = requests.get(url, timeout=timeout_value, headers=headers, allow_redirects=True)
            break
        except requests.exceptions.Timeout as exc:
            if attempt >= max_retries:
                raise NetworkRequestError(f"Request to '{url}' timed out.") from exc
        except requests.exceptions.ConnectionError as exc:
            if attempt >= max_retries:
                raise NetworkRequestError(f"Connection failed while requesting '{url}'.") from exc
        except requests.exceptions.RequestException as exc:
            if attempt >= max_retries:
                raise NetworkRequestError(f"The request to '{url}' failed unexpectedly.") from exc

        delay = retry_backoff * (2**attempt)
        retry_after = _retry_delay_from_headers(headers)
        if retry_after is not None:
            delay = max(delay, retry_after)
        time.sleep(delay)

    if response is None:
        raise NetworkRequestError(f"The request to '{url}' failed unexpectedly.")

    if response.status_code in {429, 500, 502, 503, 504}:
        if max_retries > 0:
            if response.status_code == 429:
                delay = _retry_delay_from_headers(response.headers) or retry_backoff
            else:
                delay = _retry_delay_from_headers(response.headers) or retry_backoff
            time.sleep(delay)
            return fetch_html(url, timeout=timeout_value, user_agent=user_agent, max_retries=max_retries - 1, retry_backoff=retry_backoff, engine=engine, render_config=render_config)
        raise NetworkRequestError(
            f"The server responded with HTTP {response.status_code} for '{url}'."
        )

    if response.status_code >= 400:
        raise NetworkRequestError(
            f"The server responded with HTTP {response.status_code} for '{url}'."
        )

    content_type = response.headers.get("Content-Type", "").lower()
    if content_type and "text/html" not in content_type and "application/xhtml+xml" not in content_type:
        raise UnexpectedContentTypeError(
            f"Unexpected content type '{content_type}' for '{url}'. Expected HTML."
        )

    final_url = response.url
    if not validate_url(final_url):
        raise NetworkRequestError(f"The final URL '{final_url}' is not a permitted public destination.")

    return _decode_html(response)
