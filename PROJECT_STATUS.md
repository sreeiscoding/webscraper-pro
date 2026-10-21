# WebScraper Pro - Project Status

Last updated: 2026-10-20 (premium UI/UX redesign pass)

## Project structure summary

```
Phase2/
├── .streamlit/config.toml      # Base theme (palette, font stack) for the interface
├── app/
│   ├── __init__.py
│   ├── main.py                 # Streamlit entry point (calls render_app())
│   ├── ui.py                   # Streamlit interface: sidebar navigation + five sections
│   ├── theme.py                # NEW: centralised palette, icons and stylesheet
│   ├── config.py               # Settings, FieldSpec/ExtractionConfig/PaginationConfig, URL validation
│   ├── network.py              # HTTP fetching (static + optional Playwright), retries, timeouts
│   ├── extractor.py            # HTML field/record extraction (engine layer, no Streamlit)
│   ├── pagination.py           # Multi-page orchestration, limits, repeat detection
│   ├── cleaner.py              # Whitespace normalisation, duplicate detection, validation flags
│   ├── exporter.py             # CSV / formatted Excel export with formula-injection sanitisation
│   ├── storage.py              # Local SQLite project + job history storage
│   ├── exceptions.py           # Domain exceptions
│   ├── demo_configurations.py  # Preset extraction configurations
│   └── demo_books_to_scrape.py # Books to Scrape preset
├── tests/                      # pytest suite (47 tests)
├── data/webscraper_pro.db      # Local SQLite database
├── exports/                    # Local export output (gitignored)
├── requirements.txt
├── README.md
└── PROJECT_STATUS.md
```

Layering is preserved: the extraction engine (`config`, `network`, `extractor`, `pagination`,
`cleaner`, `exporter`) contains no Streamlit imports. `ui.py` is the only Streamlit-aware module,
and `theme.py` only injects presentation.

## Premium UI/UX redesign

### Visual design system

The palette, spacing scale, icon set and the whole stylesheet live in **one** module,
`app/theme.py`, so no rule is duplicated across rendering code. `.streamlit/config.toml` supplies
the base light theme (workspace `#F5F7F8`, cards `#FFFFFF`, text `#172126`, accent `#14807A`,
system font stack — no web fonts, so the app works offline).

| Area | Treatment |
|---|---|
| Sidebar | Dark `#172126` surface, gold accent on the brand tagline, muted secondary text |
| Workspace | Light `#F5F7F8` background, white cards with a 1px `#E1E7E9` border and a restrained shadow |
| Accent | Teal `#14807A` for primary actions, active navigation, links and focus rings |
| Gold `#C5A46D` | Used only for the brand tagline, the hero eyebrow and the preview badge |
| Typography | One sans-serif stack; page title 1.6rem, section titles 1.08rem, labels 0.7rem uppercase |
| Controls | 8px radii, shared focus ring, consistent borders across inputs, selects, expanders, buttons |
| Status | Success `#21865B`, error `#C64747`, warning tones from Streamlit's own alert styling |

### Sidebar navigation

Implemented in `app/ui.py` with a `st.radio` bound to `st.session_state.nav_section`, so the
selection is a real, keyboard-accessible widget and its state survives reruns.

- Items: **Overview**, **New Extraction**, **Results**, **History**, **Settings**
- The active item is marked with a teal left border and a teal-tinted background
  (`label:has(input:checked)`), with the label text turned white and bold
- Each item has an inline SVG icon (no icon font, no network request) rendered through a CSS
  `mask-image` so the glyph inherits the item's colour
- The native radio marker is hidden while the input stays in the accessibility tree
- A brand block and a footer with the local database/export paths sit above and below the list
- Navigation is a section switch inside the single existing app: no second application, no second
  copy of the extraction form, and the scraping logic is untouched

### Hero and product-preview panel

`_render_hero()` renders a dark charcoal surface that complements the sidebar:

- Eyebrow `WEB DATA EXTRACTION WORKSPACE` (gold), headline **Turn the web into _structured data_.**
  with the accent words in teal, and the required description
- Primary CTA **Start an extraction →** opens the existing New Extraction section;
  secondary CTA **View recent results** opens the existing Results section
- The right-hand panel is a miniature spreadsheet preview built from the app's own data model
  (title, price, availability, product URL). It shows the **real records of the most recent run**
  when results exist — labelled `Latest run` — and a clearly marked `Sample` preview otherwise.
  No metrics, progress bars or success claims are invented.

### Sections

| Section | Content | Source of truth |
|---|---|---|
| Overview | Hero, live metric cards, recent session activity, three-step explainer | Real session state and database counts |
| New Extraction | Source configuration, preset, field enable/selector grid, advanced settings expander, Test selectors + Start extraction | The existing form and callbacks, unchanged in behaviour |
| Results | Success notice, metric cards, validation warnings, failed pages, data preview, cleaning controls, export controls | The existing `last_result` / `last_cleaned` state |
| History | Stored job history table plus the current session's jobs | `store.list_job_history()` and `st.session_state.jobs` |
| Settings | Application configuration, environment, local storage paths, responsible-use note, saved-project management | `SETTINGS`, `platform`/`sys`, `DEFAULT_DB_PATH`, existing project store |

### Responsive behaviour (verified in headless Chrome)

| Viewport | Sidebar | Hero | Horizontal overflow |
|---|---|---|---|
| 1440 × 900 (desktop) | 336px, persistent | Two columns | None |
| 834 × 1112 (tablet) | 272px | Stacked to one column | None |
| 390 × 844 (mobile) | Collapses to Streamlit's own drawer | Stacked, full-width CTAs | None |

Measured `documentElement.scrollWidth === clientWidth` at all three widths. The hero preview table
scrolls inside its own container (`overflow-x: auto`) and its URL column wraps on mobile, so no
element forces the page to overflow. Streamlit columns are explicitly stacked below 768px, and
the field-mapping column headers are hidden once the fields stack.

## Files changed and why

| File | Change | Reason |
|---|---|---|
| `app/theme.py` | **New.** Palette, inline SVG icon set, the complete stylesheet and `inject_theme()` | Centralised design system; no duplicated CSS; no new dependencies |
| `.streamlit/config.toml` | **New.** Light base theme with the specified palette and a system font stack | Applies the workspace/background/text colours natively, without CSS overrides |
| `app/ui.py` | Split the monolithic `render_app()` into `_render_overview`, `_render_extraction`, `_render_results`, `_render_history`, `_render_settings` plus `_render_sidebar`, `_render_hero`, `_stat_cards`, `_preview_table_html` | Single-page app with sidebar navigation; the engine and the form behaviour are unchanged |
| `app/ui.py` | Removed a duplicated `test_selectors_for_url` / `_preview_value` block that had been copied into the file | Dead code left by the previous agent's interrupted edit |
| `app/ui.py` | The URL stays inside the form; the preset moved outside it; every form widget gained a stable key and a draft-backed default | The URL is always submitted atomically with the form; switching preset updates the field list immediately; the last submitted setup is restored after navigating away |
| `app/ui.py` | `store` is now resolved inside `_render_extraction` | Fixes a defect introduced during the restructure where job-history writes failed silently |
| `tests/test_ui.py` | Four new interface tests: job history is written, every section renders, the hero CTAs switch sections, form state survives navigation | Guards the behaviour that the redesign could have broken |

The extraction engine (`config`, `network`, `extractor`, `pagination`, `cleaner`, `exporter`) and the
scraping behaviour were **not** modified by this pass.

## Commands executed and actual results

| Command | Result |
|---|---|
| `.venv\Scripts\python.exe -m compileall -q app` | **OK** (exit 0) |
| `.venv\Scripts\python.exe -m pytest -q` | **47 passed** (43 before this pass, plus 4 new interface tests) |
| `streamlit.testing.v1.AppTest` interface sweep | 0 exceptions for Overview / New Extraction / Results / History / Settings; both hero CTAs switch sections; form state preserved across navigation |
| Headless Chrome (CDP, `Emulation.setDeviceMetricsOverride`) at 1440×900, 834×1112, 390×844 | Sidebar `#172126`, workspace `#F5F7F8`, card `#FFFFFF`, teal accent, gold eyebrow; active nav item teal-tinted with a 2px teal border; icons render; **no horizontal overflow at any width** |
| Headless Chrome, real extraction | Typed the URL, clicked Start extraction: 1 record captured, job written to `job_history`, Results section showed 4 metric cards, 3 tables and the `Download CSV` button, no exceptions |
| `streamlit run app\main.py` | Server running, `HTTP 200` from `http://localhost:8501` |

## Test results

`47 passed` — full suite green, no skips, no errors.

New interface tests in `tests/test_ui.py`:

- `test_extraction_records_the_job_in_history` — a completed extraction must be written to the
  local job history (this test covers the silent `store` defect found during the redesign)
- `test_navigation_sections_render_without_exceptions` — every navigation destination renders cleanly
- `test_hero_calls_to_action_switch_sections` — the hero buttons move the workspace to the matching section
- `test_extraction_form_state_survives_navigation` — switching sections does not discard the setup

## Feature status

| # | Feature | Status | Evidence |
|---|---|---|---|
| 1 | Application startup | **WORKING** | `compileall` OK, server serves HTTP 200 |
| 2 | Streamlit UI rendering | **WORKING** | AppTest and Chrome: 0 exceptions, 0 Streamlit error elements |
| 3 | Website URL input | **WORKING** | Submitted inside the form, so it is always sent with the request |
| 4 | Extraction configuration and field selection | **WORKING** | Preset switch updates the field list immediately; per-field enable toggles verified live |
| 5 | CSS selector configuration | **WORKING** | Per-field selector inputs, restored after navigation |
| 6 | Start extraction button | **WORKING** | Dominant teal action; verified with a real run in the browser |
| 7 | Scraping and data extraction | **WORKING** | Live run against books.toscrape.com returned title/price/stock/URL |
| 8 | Pagination | **WORKING** | Covered by the existing engine tests; advanced settings unchanged |
| 9 | Error handling | **WORKING** | Validation and failure messages render as alerts, never as tracebacks |
| 10 | Progress and status indicators | **PARTIALLY WORKING** | Button state and result metrics are real; there is still **no per-page progress feedback** during a running job, and none is simulated |
| 11 | Results preview | **WORKING** | Data preview, validation warnings, failed pages and cleaned preview |
| 12 | CSV and Excel export | **WORKING** | Download button renders with real payload bytes; export modules unchanged |
| 13 | Dependency and environment configuration | **WORKING** | No dependency added; `requirements.txt` still matches the venv |
| 14 | Existing tests | **WORKING** | 47/47 pass |
| 15 | Saved projects / job history | **WORKING** | Project management moved to Settings; job history shown in History; write path re-verified |
| 16 | Playwright browser rendering | **NOT VERIFIED** | Code path covered by fakes only; no browser runtime installed |
| 17 | Relative URL resolution | **WORKING** | Page-2 records resolve to `/catalogue/...` correctly |
| 18 | Character encoding | **WORKING** | `£51.77` preserved through fetch → extract → XLSX and CSV |
| 19 | Sidebar navigation | **WORKING** | All five sections reachable by mouse, keyboard and the hero CTAs |
| 20 | Responsive layout | **WORKING** | Measured at three viewports in headless Chrome: no horizontal overflow, hero stacks, tables scroll in place |

## Remaining errors or limitations

1. **No in-job progress feedback.** A running extraction blocks the Streamlit script run, so the
   user sees no page-by-page progress. This remains the main functional gap.
2. **Playwright path unverified end-to-end** (no browser runtime in this environment).
3. **Streamlit accessibility warnings** for the collapsed per-field checkbox/selector inputs
   (empty `label` with `label_visibility="collapsed"`). Cosmetic today.
4. **In-form edits need a submit.** Values inside the extraction form (field toggles, selectors,
   advanced settings) are only sent to the server when the form is submitted, which is Streamlit's
   form semantics. The last submitted values are restored when the section is reopened.
5. **`validate_url` performs a DNS lookup per call** — correct but slow, and it fails closed when
   the machine is offline.
6. `data/webscraper_pro.db` and `exports/` are local-only; no backup or rotation is implemented.

## Exact command to launch the app on Windows

From the project root (`C:\Users\renja\OneDrive\Desktop\Websites\Phase2`):

```powershell
.\.venv\Scripts\python.exe -m streamlit run app\main.py
```

Headless / fixed port variant:

```powershell
.\.venv\Scripts\python.exe -m streamlit run app\main.py --server.headless true --server.port 8501
```

## Localhost URL and port

- **URL to open: http://localhost:8501**
- **The server is currently running** (persistent background process, confirmed listening on
  0.0.0.0:8501 and returning HTTP 200)
- Rendering was verified in headless Chrome at three viewport sizes; it was not confirmed in an
  interactive browser window

## Next recommended development task

Add per-page progress reporting to the extraction job. `process_urls` already returns
`pages_processed`, `total_records` and `stop_reason`; the smallest change is an optional progress
callback in `app/pagination.py` surfaced with `st.progress` / `st.status` in `app/ui.py`, keeping
the engine free of Streamlit imports. This is the one feature still only partially working and the
main usability gap for long multi-page jobs.

---

## Earlier recovery work (retained for reference)

## Original error and verified root cause

Reported symptom:

```
IndentationError: unexpected indent
File: app/ui.py
Line: 351
button_label = "Running extraction..." if st.session_state.scrape_in_progress else "Start extraction"
```

Verified findings:

1. The reported line number did not match the file. The `button_label` statement is at
   `app/ui.py:585` (it was at line 351 in the version that produced the traceback, before later
   edits added code above it). The statement itself was correctly indented inside the
   `with st.form("scrape_form", ...)` block.
2. `app/ui.py` as found contained a **duplicated import block** (lines 17-39): the
   `SelectorSyntaxError` compatibility shim, plus `import streamlit as st` and
   `from bs4 import BeautifulSoup`, appeared twice. This is the residue of the previous agent's
   interrupted edit, and is the construct that produces "unexpected indent" errors when a
   duplicated block is pasted at a different indentation level.
3. The file **compiled cleanly** on the version found (`py_compile` and `compileall` both passed),
   so the syntax error itself was already resolved by the time this pass started.
4. A separate, still-live defect hid behind it: the compatibility shim imported
   `SoupSieveSyntaxError` from `soupsieve`, which does not exist in the installed soupsieve
   version, so the shim silently fell through to a locally defined `class SelectorSyntaxError(ValueError)`.
   The real exception raised by BeautifulSoup is `soupsieve.util.SelectorSyntaxError`, which is
   **not** a `ValueError` subclass. Every `except SelectorSyntaxError` handler in the codebase
   therefore failed to catch malformed selectors, so an invalid CSS selector crashed the app
   instead of being reported as a user-facing validation error.


## Encoding root cause (the `Â£51.77` defect)

The `Â` was introduced **at the HTTP layer**, not during parsing, cleaning, or export.

Measured against the live site:

| Stage | Value | Verdict |
|---|---|---|
| Raw HTTP body | `... \xc2\xa3 51.77 ...` (correct UTF-8) | correct |
| `Content-Type` response header | `text/html` — **no charset parameter** | triggers the fallback |
| `response.encoding` (requests) | `ISO-8859-1` | **root cause** |
| `response.apparent_encoding` | `utf-8` | the truth, but unused by `response.text` |
| HTML `<meta charset>` | `UTF-8` | declared, but requests never consults it |
| `response.text` | `\xc2\xa351.77` | mojibake introduced here |
| BeautifulSoup parse | `\xc2\xa351.77` | faithful, not a cause |
| Extractor / cleaner | `\xc2\xa351.77` | faithful, not a cause |
| pandas DataFrame / openpyxl cell | `\xc2\xa351.77` | faithful, not a cause |

`requests` follows RFC 2616 and assumes `ISO-8859-1` for any `text/*` response whose header omits
a charset. `books.toscrape.com` sends `Content-Type: text/html` with no charset while its body is
UTF-8, so every multi-byte character was decoded as two Latin-1 characters (`£` = U+00A3 became
U+00C2 U+00A3 = `Â£`).

**Fix**: `app/network.py` now decodes `response.content` with a charset resolved in this order:

1. the `charset` parameter of the `Content-Type` response header,
2. the document's own `<meta charset="...">` declaration (searched in the first 8 KB),
3. `response.apparent_encoding` (statistical detection of the raw bytes),
4. `utf-8` as the final fallback.

No encode/decode round-tripping and no global character replacement is used, so valid international
text, currency symbols and other Unicode characters are preserved exactly. Verified live: the price
now arrives as `\xa351.77` (`£51.77`) and the exported cell contains `£51.77`.

### CSV has a separate issue from XLSX

The CSV and the XLSX are produced by different code paths, and they failed for different reasons:

- **XLSX** failed because of the HTTP-layer misdecoding above. The workbook format is UTF-8 XML
  internally, so once the value is correct the file is correct. Fixed by the network change.
- **CSV** never had corrupt bytes — the file contained valid UTF-8. But Excel's *double-click*
  import does not use the file's encoding; it assumes the system's ANSI code page (Windows-1252),
  which turns the UTF-8 bytes `C2 A3` back into `Â£`. The CSV is therefore now written as
  `utf-8-sig` (UTF-8 with a byte order mark), which is the standard way to tell Excel the file is
  UTF-8. `pandas.read_csv` strips the BOM automatically (verified: column names stay `title`,
  `price`), and the raw file is still valid UTF-8.

## Dependency and environment status

- Interpreter used: `.venv\Scripts\python.exe` → Python 3.10.4
- Installed and importable: streamlit 1.39.0, requests, beautifulsoup4, pandas, openpyxl, pytest
- Optional: `playwright` is not installed in the venv; the Playwright path is exercised by
  fakes in `tests/test_rendering.py`, not against a real browser
- The system `python` on PATH is 3.14.0 and does **not** have streamlit; always use the venv
  interpreter, as the README already advises
- No dependencies were added, removed, or reinstalled
