"""HTML parsing helpers for turning page content into structured data."""

from __future__ import annotations

from bs4 import BeautifulSoup


def parse_html_page(html: str) -> dict[str, str]:
    """Extract a minimal set of fields from a page.

    This is intentionally lightweight and keeps the project ready for future scraping logic.
    """
    soup = BeautifulSoup(html, "html.parser")

    title = soup.title.get_text(strip=True) if soup.title else ""
    heading = soup.h1.get_text(strip=True) if soup.h1 else ""
    text = " ".join(soup.stripped_strings)[:5000]

    return {
        "title": title,
        "heading": heading,
        "text_preview": text,
    }
