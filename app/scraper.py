"""Scraping workflow and page extraction logic."""

from __future__ import annotations

from app.cleaner import clean_record
from app.config import validate_url
from app.network import fetch_html
from app.parser import parse_html_page


def scrape_page_summary(url: str) -> dict[str, str]:
    """Fetch a web page, parse core fields, and normalize the result.

    This function intentionally keeps the logic simple and ready for future extension.
    """
    if not validate_url(url):
        raise ValueError("A valid HTTP or HTTPS URL is required.")

    html = fetch_html(url)
    parsed = parse_html_page(html)
    return clean_record(parsed)
