# WebScraper Pro

WebScraper Pro is a local Python application for extracting publicly accessible website data, transforming it into structured records, and exporting professional CSV and Excel files. It is designed for local, permission-aware use and emphasises safe configuration, transparent validation, and export-ready data quality.

## Purpose

This project is intended to:

- fetch public HTML content from permitted sources
- extract repeated fields into structured records
- validate and clean extracted values before export
- export results as CSV and Excel files
- provide a local Streamlit interface for configuration and review

## Supported methods

- Static HTML extraction: default and recommended for most public pages
- Optional Playwright rendering: useful for JavaScript-heavy pages when explicitly enabled

The application does not support login-based scraping, bypassing access controls, or hidden bot-like navigation.

## Prerequisites

- Python 3.10 or 3.12 recommended
- Windows 10 or 11
- Git
- A virtual environment is recommended

> Python 3.14 is not recommended for this project because the pandas stack can be unstable in that environment on Windows.

## Installation

From the project root:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Optional Playwright support:

```powershell
python -m pip install playwright
python -m playwright install chromium
```

## Launch the application

Start the app from the project root:

```powershell
streamlit run app/main.py
```

If you want to force a specific local port:

```powershell
streamlit run app/main.py --server.headless true --server.port 8501
```

## Run tests

```powershell
python -m pytest -q
```

## Configuration example

```json
{
  "base_url": "https://example.com/products",
  "record_selector": "article.product-card",
  "fields": {
    "title": {"selector": "h3 a", "extraction_type": "text", "required": true},
    "price": {"selector": "p.price", "extraction_type": "text", "required": true}
  },
  "pagination": {
    "max_pages": 3,
    "max_records": 200,
    "next_page_selector": "a.next-page",
    "request_delay": 0.5,
    "max_retries": 1,
    "retry_backoff": 0.5
  }
}
```

## Data handling and responsible use

- Only scrape public websites that allow access and are permitted for extraction.
- Respect robots.txt, rate limits, and website terms.
- Do not bypass login walls, CAPTCHAs, anti-bot protections, or paywalls.
- Do not submit forms, click through arbitrary UI flows, or perform account actions.
- Keep extraction bounded with page and record limits.
- Prefer the static engine by default; use Playwright only for explicitly permitted JavaScript-heavy pages.
- Exported CSV and Excel files should be reviewed before sharing or publishing.

## Troubleshooting

### Streamlit fails to start

- Check that port 8501 is not already in use.
- Re-run the app on a free port.
- Ensure the virtual environment is activated.

### URL validation errors

- Use a full URL with `http://` or `https://`.
- Avoid localhost, private IPs, or blocked network destinations.
- Check that the hostname resolves to a public address.

### Selector issues

- Confirm the selector is valid CSS and matches the target page structure.
- Use a browser inspector to validate the selector before running a job.

### Empty or incomplete results

- Reduce the page count or record cap if a site is rate-limiting or paginating unexpectedly.
- Confirm the page is public and not protected by JavaScript or access barriers.
- Check the extraction settings and required-field configuration.

## Known limitations

- This is a local desktop project, not a distributed cloud scraper.
- It is intended for permitted public websites and does not automate authenticated workflows.
- Browser rendering is still opt-in and should be used carefully.
- Some complex JavaScript-heavy sites may still require site-specific selectors or manual review.
- Database files and exported files remain local to the project directory.

## Release status

This release is a verified local application build for a safe, controlled workflow. It is suitable for local use and manual review, but it is not a general-purpose production scraper for unrestricted web automation.
