"""Centralised visual design system for the WebScraper Pro interface.

The palette, spacing scale and stylesheet live here so that every screen shares
one design language and the rules are not duplicated across rendering modules.
No external assets or web fonts are required: icons are inline SVG masks and the
font stack resolves to fonts already present on the machine.
"""

from __future__ import annotations

import streamlit as st


PALETTE = {
    "background": "#080A0C",
    "charcoal": "#121719",
    "elevated": "#191F22",
    "workspace": "#F5F7F8",
    "card": "#FFFFFF",
    "text": "#172126",
    "text_on_dark": "#F5F7F8",
    "text_muted": "#A6B0B5",
    "accent": "#14807A",
    "accent_hover": "#106B66",
    "accent_soft": "#E6F1F0",
    "dark_border": "#293236",
    "border": "#E1E7E9",
    "gold": "#C5A46D",
    "success": "#21865B",
    "error": "#C64747",
    "warning": "#B07C2E",
}

FONT_STACKS = {
    "sans": '"IBM Plex Sans", "Segoe UI", system-ui, -apple-system, "Helvetica Neue", Arial, sans-serif',
    "serif": '"Instrument Serif", "Iowan Old Style", "Palatino Linotype", Palatino, Georgia, "Times New Roman", serif',
    "mono": '"IBM Plex Mono", "SFMono-Regular", Consolas, "Liberation Mono", Menlo, monospace',
}

FONT_IMPORT = (
    "https://fonts.googleapis.com/css2?"
    "family=IBM+Plex+Mono:wght@400;500&"
    "family=IBM+Plex+Sans:wght@400;500;600&"
    "family=Instrument+Serif:ital@0;1&display=swap"
)

_ICON_SVG = {
    "overview": (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" '
        'stroke="black" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">'
        '<rect x="3" y="3" width="7" height="9" rx="1.5"/><rect x="14" y="3" width="7" height="5" rx="1.5"/>'
        '<rect x="14" y="12" width="7" height="9" rx="1.5"/><rect x="3" y="16" width="7" height="5" rx="1.5"/></svg>'
    ),
    "extraction": (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" '
        'stroke="black" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">'
        '<circle cx="11" cy="11" r="7"/><path d="M20 20l-3.6-3.6"/></svg>'
    ),
    "results": (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" '
        'stroke="black" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">'
        '<rect x="3" y="4" width="18" height="16" rx="2"/><path d="M3 9h18M9 9v11"/></svg>'
    ),
    "history": (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" '
        'stroke="black" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">'
        '<circle cx="12" cy="12" r="8.5"/><path d="M12 7.5V12l3 2"/></svg>'
    ),
    "settings": (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" '
        'stroke="black" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">'
        '<circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.6 1.6 0 00.3 1.8l.1.1a2 2 0 11-2.8 2.8l-.1-.1a1.6 1.6 0 00-1.8-.3 1.6 1.6 0 00-1 1.5V21a2 2 0 11-4 0v-.1A1.6 1.6 0 008 19.4a1.6 1.6 0 00-1.8.3l-.1.1a2 2 0 11-2.8-2.8l.1-.1a1.6 1.6 0 00.3-1.8 1.6 1.6 0 00-1.5-1H2a2 2 0 110-4h.1A1.6 1.6 0 003.6 8a1.6 1.6 0 00-.3-1.8l-.1-.1a2 2 0 112.8-2.8l.1.1a1.6 1.6 0 001.8.3H8a1.6 1.6 0 001-1.5V2a2 2 0 114 0v.1a1.6 1.6 0 001 1.5 1.6 1.6 0 001.8-.3l.1-.1a2 2 0 112.8 2.8l-.1.1a1.6 1.6 0 00-.3 1.8V8a1.6 1.6 0 001.5 1H22a2 2 0 110 4h-.1a1.6 1.6 0 00-1.5 1z"/></svg>'
    ),
}


NAV_ICONS = {
    "Overview": "overview",
    "New Extraction": "extraction",
    "Results": "results",
    "History": "history",
    "Settings": "settings",
}


def nav_slug(section: str) -> str:
    """Return the stable key fragment used for a navigation destination."""
    return section.lower().replace(" ", "_")


def _icon_mask(name: str) -> str:
    """Return a CSS mask value for a bundled inline SVG icon."""
    svg = _ICON_SVG[name].replace('"', "'").replace("<svg", "<svg width='16' height='16'")
    return f"url(\"data:image/svg+xml,{svg}\")"


def _nav_icon_rules(nav_sections: tuple[str, ...] | list[str]) -> str:
    """Build the icon rules for the top navigation buttons.

    Streamlit renders a keyed widget inside an element container that carries
    the ``st-key-<key>`` class, so each navigation button is addressed by the
    key it was created with rather than by its position in the bar.
    """
    rules = []
    for label in nav_sections:
        icon = NAV_ICONS.get(label)
        if icon is None:
            continue
        mask = _icon_mask(icon)
        for prefix in ("nav", "navm"):
            rules.append(
                f"""
[data-testid="stApp"] .st-key-{prefix}_{nav_slug(label)} button::before {{
    content: "";
    display: inline-block;
    width: 15px;
    height: 15px;
    margin-right: 8px;
    vertical-align: -2px;
    background-color: currentColor;
    -webkit-mask-image: {mask};
    mask-image: {mask};
    -webkit-mask-size: contain;
    mask-size: contain;
    -webkit-mask-repeat: no-repeat;
    mask-repeat: no-repeat;
}}"""
            )
    return "\n".join(rules)


THEME_CSS = f"""
/* ---------------------------------------------------------------
   WebScraper Pro design foundation
   Design tokens, typography and the shared component rules live
   here so every screen renders with one visual language.
   --------------------------------------------------------------- */

@import url('{FONT_IMPORT}');

:root {{
    --wsp-background: {PALETTE['background']};
    --wsp-charcoal: {PALETTE['charcoal']};
    --wsp-elevated: {PALETTE['elevated']};
    --wsp-workspace: {PALETTE['workspace']};
    --wsp-card: {PALETTE['card']};
    --wsp-text: {PALETTE['text']};
    --wsp-text-on-dark: {PALETTE['text_on_dark']};
    --wsp-muted: {PALETTE['text_muted']};
    --wsp-accent: {PALETTE['accent']};
    --wsp-accent-hover: {PALETTE['accent_hover']};
    --wsp-accent-soft: {PALETTE['accent_soft']};
    --wsp-dark-border: {PALETTE['dark_border']};
    --wsp-border: {PALETTE['border']};
    --wsp-gold: {PALETTE['gold']};
    --wsp-success: {PALETTE['success']};
    --wsp-error: {PALETTE['error']};
    --wsp-warning: {PALETTE['warning']};
    --wsp-gutter: 2.2rem;
    --wsp-sans: {FONT_STACKS['sans']};
    --wsp-serif: {FONT_STACKS['serif']};
    --wsp-mono: {FONT_STACKS['mono']};
    --wsp-radius: 10px;
    --wsp-shadow: 0 1px 2px rgba(23, 33, 38, 0.04), 0 8px 24px rgba(23, 33, 38, 0.05);
}}

html, body, [data-testid="stApp"] {{
    background: var(--wsp-workspace);
    font-family: var(--wsp-sans);
    font-size: 15px;
}}

[data-testid="stApp"] input,
[data-testid="stApp"] button,
[data-testid="stApp"] select,
[data-testid="stApp"] textarea {{
    font-family: inherit;
}}

/* Streamlit's markdown container declares its own font-family, which
   overrides the interface typeface for every markdown-rendered element
   (headings, labels and the custom blocks below). Scoping the rules to the
   app container raises specificity above Streamlit's own declarations, so
   the override is reliable without resorting to !important. */
[data-testid="stApp"] [data-testid="stMarkdownContainer"] {{
    font-family: var(--wsp-sans);
}}

[data-testid="stApp"] [data-testid="stMarkdownContainer"] :is(
    p, h1, h2, h3, h4, h5, h6, span, a, li, ul, ol, strong, em, div, label
) {{
    font-family: var(--wsp-sans);
}}

/* Technical values and code keep the mono face. The extra scope puts this
   rule above the markdown override above. */
[data-testid="stApp"] [data-testid="stMarkdownContainer"] .wsp-mono,
[data-testid="stApp"] code,
[data-testid="stApp"] pre {{
    font-family: var(--wsp-mono);
}}

/* CSS selectors are technical values, so they are set in the mono face. */
[data-testid="stApp"] [class*="st-key-selector_"] input {{
    font-family: var(--wsp-mono);
}}

.block-container, [data-testid="stMainBlockContainer"] {{
    padding-top: 1.3rem;
    padding-bottom: 3rem;
    padding-left: var(--wsp-gutter);
    padding-right: var(--wsp-gutter);
    max-width: 1600px;
}}

[data-testid="stHeader"] {{
    background: transparent;
}}

/* Streamlit's default gradient bar is replaced with a restrained accent line. */
[data-testid="stDecoration"] {{
    background: linear-gradient(90deg, var(--wsp-accent) 0%, var(--wsp-gold) 100%);
    height: 2px;
}}

/* Columns must be allowed to shrink so wide tables scroll inside their
   container instead of widening the page. */
[data-testid="stColumn"] {{
    min-width: 0;
}}

[data-testid="stHorizontalBlock"] {{
    min-width: 0;
}}

/* ----------------------------- Top nav ---------------------------- */

.st-key-wsp_topnav {{
    background: var(--wsp-background);
    border: 1px solid var(--wsp-dark-border);
    border-radius: 12px;
    margin-left: calc(-1 * var(--wsp-gutter));
    margin-right: calc(-1 * var(--wsp-gutter));
    padding: 0.7rem var(--wsp-gutter);
    margin-bottom: 1.1rem;
    position: sticky;
    top: 0.5rem;
    z-index: 20;
}}

.st-key-wsp_topnav [data-testid="stHorizontalBlock"] {{
    justify-content: space-between;
    align-items: center;
    flex-wrap: nowrap;
}}

.st-key-wsp_topnav [data-testid="stHorizontalBlock"] > [data-testid="stColumn"] {{
    flex: 0 0 auto;
}}

.st-key-wsp_topnav [data-testid="stHorizontalBlock"] > [data-testid="stColumn"]:first-child {{
    flex: 1 1 auto;
}}

.wsp-brand {{
    display: flex;
    align-items: center;
    gap: 12px;
}}

.wsp-brand__mark {{
    width: 34px;
    height: 34px;
    flex: 0 0 34px;
    border-radius: 8px;
    background: var(--wsp-accent);
    border: 1px solid rgba(197, 164, 109, 0.45);
    color: #FFFFFF;
    font-size: 13px;
    font-weight: 600;
    letter-spacing: 0.06em;
    display: flex;
    align-items: center;
    justify-content: center;
}}

.wsp-brand__name {{
    font-size: 1rem;
    font-weight: 600;
    color: var(--wsp-text-on-dark);
    line-height: 1.2;
    letter-spacing: -0.01em;
}}

.wsp-brand__tag {{
    font-size: 0.66rem;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    color: var(--wsp-gold);
    margin-top: 3px;
}}

.st-key-wsp_topnav [data-testid="stButton"] button {{
    background: transparent;
    border: 1px solid transparent;
    color: var(--wsp-muted);
    font-size: 0.9rem;
    font-weight: 500;
    padding: 0.4rem 0.85rem;
    border-radius: 8px;
    min-height: 2.35rem;
    white-space: nowrap;
    transition: background-color 130ms ease, color 130ms ease, border-color 130ms ease;
}}

.st-key-wsp_topnav [data-testid="stButton"] button:hover {{
    background: rgba(245, 247, 248, 0.06);
    color: var(--wsp-text-on-dark);
}}

.st-key-wsp_topnav [data-testid="stButton"] button:focus-visible {{
    outline: 2px solid var(--wsp-accent);
    outline-offset: 2px;
}}

/* The active destination is marked with a quiet teal highlight. */
.st-key-wsp_topnav .st-key-wsp_nav_active [data-testid="stButton"] button,
.st-key-wsp_topnav .st-key-wsp_nav_active button {{
    background: rgba(20, 128, 122, 0.16);
    border-color: rgba(20, 128, 122, 0.55);
    color: var(--wsp-text-on-dark);
    font-weight: 600;
}}

.st-key-wsp_topnav_mobile {{
    display: none;
}}

@media (max-width: 900px) {{
    .st-key-wsp_topnav_desktop {{
        display: none;
    }}

    .st-key-wsp_topnav_mobile {{
        display: block;
    }}

    .st-key-wsp_topnav {{
        border-radius: 10px;
    }}
}}

/* ------------------------------ Hero ----------------------------- */

.st-key-wsp_hero {{
    position: relative;
    isolation: isolate;
    background-color: var(--wsp-background);
    background-image: radial-gradient(rgba(245, 247, 248, 0.05) 1px, transparent 1px);
    background-size: 24px 24px;
    border: 1px solid var(--wsp-dark-border);
    border-radius: 14px;
    margin-left: calc(-1 * var(--wsp-gutter));
    margin-right: calc(-1 * var(--wsp-gutter));
    padding: 4.4rem 3.4rem 4.6rem;
    margin-bottom: 1.6rem;
    overflow: hidden;
}}

.st-key-wsp_hero::before {{
    content: "";
    position: absolute;
    inset: 0;
    z-index: -1;
    background: radial-gradient(65% 90% at 12% 0%, rgba(20, 128, 122, 0.20), transparent 62%);
    pointer-events: none;
}}

.st-key-wsp_hero::after {{
    content: "";
    position: absolute;
    inset: 0;
    z-index: -1;
    background: radial-gradient(50% 60% at 92% 100%, rgba(197, 164, 109, 0.10), transparent 60%);
    pointer-events: none;
}}

.wsp-hero__eyebrow {{
    display: inline-block;
    font-size: 0.7rem;
    font-weight: 600;
    letter-spacing: 0.18em;
    text-transform: uppercase;
    color: var(--wsp-gold);
    margin-bottom: 1.4rem;
}}

/* The hero headline is the only serif element, so it re-asserts the serif
   face with a specificity above the markdown override above. */
[data-testid="stApp"] [data-testid="stMarkdownContainer"] .wsp-hero__title {{
    font-family: var(--wsp-serif);
    font-size: clamp(2.35rem, 5.4vw, 4.35rem);
    line-height: 1.05;
    font-weight: 400;
    letter-spacing: -0.012em;
    color: var(--wsp-text-on-dark);
    margin: 0 0 1.5rem;
    max-width: 18ch;
}}

.wsp-hero__title em {{
    font-style: italic;
    color: #5CC7C0;
}}

.wsp-hero__lead {{
    font-family: var(--wsp-sans);
    font-size: 1.05rem;
    line-height: 1.7;
    color: var(--wsp-muted);
    margin: 0 0 2.3rem;
    max-width: 52ch;
}}

.wsp-hero__actions {{
    display: flex;
    flex-wrap: wrap;
    gap: 0.8rem;
}}

.wsp-hero__actions [data-testid="stButton"] {{
    width: auto;
}}

.wsp-hero__actions [data-testid="stButton"] button {{
    border-radius: 8px;
    font-family: var(--wsp-sans);
    font-size: 0.95rem;
    font-weight: 500;
    padding: 0.75rem 1.5rem;
    min-height: 3rem;
    border: 1px solid transparent;
    transition: background-color 130ms ease, border-color 130ms ease;
}}

.wsp-hero__actions [data-testid="stButton"] button[kind="primary"] {{
    background: var(--wsp-accent);
    border-color: var(--wsp-accent);
    color: #FFFFFF;
}}

.wsp-hero__actions [data-testid="stButton"] button[kind="primary"]:hover {{
    background: var(--wsp-accent-hover);
    border-color: var(--wsp-accent-hover);
}}

.wsp-hero__actions [data-testid="stButton"] button[kind="secondary"] {{
    background: transparent;
    border-color: var(--wsp-dark-border);
    color: var(--wsp-text-on-dark);
}}

.wsp-hero__actions [data-testid="stButton"] button[kind="secondary"]:hover {{
    border-color: var(--wsp-gold);
    background: rgba(245, 247, 248, 0.04);
}}

.wsp-hero__actions [data-testid="stButton"] button:focus-visible {{
    outline: 2px solid var(--wsp-gold);
    outline-offset: 2px;
}}

/* --------------------------- Typography -------------------------- */

.wsp-page-title {{
    font-size: 1.6rem;
    font-weight: 650;
    letter-spacing: -0.015em;
    color: var(--wsp-text);
    margin: 0 0 0.3rem;
}}

.wsp-page-lead {{
    font-size: 0.95rem;
    color: var(--wsp-muted);
    margin: 0 0 1.35rem;
    line-height: 1.55;
}}

.wsp-section-title {{
    font-size: 1.08rem;
    font-weight: 620;
    color: var(--wsp-text);
    margin: 0 0 0.15rem;
}}

.wsp-section-hint {{
    font-size: 0.86rem;
    color: var(--wsp-muted);
    margin: 0 0 0.95rem;
}}

.wsp-label {{
    font-size: 0.7rem;
    letter-spacing: 0.11em;
    text-transform: uppercase;
    color: var(--wsp-muted);
    font-weight: 600;
    margin-bottom: 0.4rem;
}}

/* ----------------------------- Cards ----------------------------- */

.wsp-card {{
    background: var(--wsp-card);
    border: 1px solid var(--wsp-border);
    border-radius: var(--wsp-radius);
    padding: 1.15rem 1.25rem;
    margin-bottom: 1.1rem;
    box-shadow: var(--wsp-shadow);
}}

.wsp-card > div > div > div > [data-testid="stMarkdownContainer"] p:first-child {{
    margin-top: 0;
}}

.wsp-stat-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(170px, 1fr));
    gap: 0.9rem;
    margin-bottom: 1.35rem;
}}

.wsp-stat {{
    background: var(--wsp-card);
    border: 1px solid var(--wsp-border);
    border-radius: var(--wsp-radius);
    padding: 0.95rem 1.05rem;
    box-shadow: var(--wsp-shadow);
}}

.wsp-stat__label {{
    font-size: 0.72rem;
    letter-spacing: 0.09em;
    text-transform: uppercase;
    color: var(--wsp-muted);
    margin-bottom: 0.3rem;
}}

.wsp-stat__value {{
    font-size: 1.45rem;
    font-weight: 650;
    color: var(--wsp-text);
    font-variant-numeric: tabular-nums;
    line-height: 1.15;
    overflow-wrap: anywhere;
}}

.wsp-stat__value--long {{
    font-size: 0.86rem;
    font-weight: 600;
    line-height: 1.4;
    font-variant-numeric: normal;
}}

.wsp-stat__hint {{
    font-size: 0.76rem;
    color: var(--wsp-muted);
    margin-top: 0.22rem;
    overflow-wrap: anywhere;
}}

/* ----------------------------- Forms ----------------------------- */

[data-testid="stForm"] {{
    background: var(--wsp-card);
    border: 1px solid var(--wsp-border);
    border-radius: var(--wsp-radius);
    padding: 1.2rem 1.3rem;
    box-shadow: var(--wsp-shadow);
}}

[data-testid="stForm"] [data-testid="stFormSubmitButton"] {{
    margin-top: 0.2rem;
}}

[data-testid="stForm"] [data-testid="stFormSubmitButton"] button {{
    border-radius: 8px;
    font-weight: 600;
    padding: 0.62rem 1.1rem;
    min-height: 2.6rem;
}}

[data-testid="stForm"] [data-testid="stFormSubmitButton"] button[kind="primary"] {{
    background: var(--wsp-accent);
    border-color: var(--wsp-accent);
    color: #FFFFFF;
}}

[data-testid="stForm"] [data-testid="stFormSubmitButton"] button[kind="primary"]:hover {{
    background: var(--wsp-accent-hover);
    border-color: var(--wsp-accent-hover);
}}

[data-testid="stForm"] [data-testid="stFormSubmitButton"] button[kind="secondary"] {{
    background: #FFFFFF;
    border-color: #C9D5D9;
    color: var(--wsp-text);
}}

[data-testid="stForm"] [data-testid="stFormSubmitButton"] button[kind="secondary"]:hover {{
    border-color: var(--wsp-accent);
    color: var(--wsp-accent);
}}

[data-testid="stTextInput"] input,
[data-testid="stNumberInput"] input,
[data-testid="stSelectbox"] div[data-baseweb="select"] > div,
[data-testid="stTextArea"] textarea {{
    border-radius: 8px;
    border-color: #D3DDE0;
    color: var(--wsp-text);
}}

[data-testid="stTextInput"] input:focus,
[data-testid="stNumberInput"] input:focus,
[data-testid="stTextArea"] textarea:focus {{
    border-color: var(--wsp-accent);
    box-shadow: 0 0 0 1px var(--wsp-accent);
}}

[data-testid="stTextInput"] input::placeholder,
[data-testid="stTextArea"] textarea::placeholder {{
    color: #A7B4B9;
}}

[data-testid="stExpander"] {{
    border: 1px solid var(--wsp-border);
    border-radius: var(--wsp-radius);
    background: #FBFCFC;
}}

[data-testid="stExpander"] summary {{
    font-weight: 600;
    color: var(--wsp-text);
    font-size: 0.92rem;
}}

/* -------------------------- Data display ------------------------- */

[data-testid="stDataFrame"] {{
    border: 1px solid var(--wsp-border);
    border-radius: var(--wsp-radius);
    overflow: hidden;
    background: var(--wsp-card);
}}

[data-testid="stMetric"] {{
    background: var(--wsp-card);
    border: 1px solid var(--wsp-border);
    border-radius: var(--wsp-radius);
    padding: 0.9rem 1rem;
    box-shadow: var(--wsp-shadow);
}}

[data-testid="stMetricLabel"] p {{
    font-size: 0.74rem;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: var(--wsp-muted);
}}

[data-testid="stMetricValue"] {{
    font-size: 1.5rem;
    font-weight: 650;
    color: var(--wsp-text);
}}

[data-testid="stAlert"] {{
    border-radius: var(--wsp-radius);
    border: 1px solid var(--wsp-border);
}}

[data-testid="stDownloadButton"] button,
[data-testid="stButton"] button {{
    border-radius: 8px;
}}

[data-testid="stDownloadButton"] button {{
    background: var(--wsp-accent);
    border-color: var(--wsp-accent);
    color: #FFFFFF;
    font-weight: 600;
}}

[data-testid="stDownloadButton"] button:hover {{
    background: var(--wsp-accent-hover);
    border-color: var(--wsp-accent-hover);
}}

/* ---------------------------- Responsive -------------------------- */

@media (max-width: 1200px) {{
    .st-key-wsp_hero {{
        padding: 3.6rem 2.6rem 3.8rem;
    }}

    .block-container, [data-testid="stMainBlockContainer"] {{
        padding-left: 1.5rem;
        padding-right: 1.5rem;
    }}

    :root {{
        --wsp-gutter: 1.5rem;
    }}
}}

@media (max-width: 900px) {{
    .st-key-wsp_topnav {{
        position: static;
    }}

    .st-key-wsp_hero {{
        padding: 3rem 1.9rem 3.2rem;
        border-radius: 12px;
    }}

    .wsp-hero__title {{
        max-width: 20ch;
    }}
}}

@media (max-width: 640px) {{
    :root {{
        --wsp-gutter: 1rem;
    }}

    .block-container, [data-testid="stMainBlockContainer"] {{
        padding-top: 1rem;
        padding-left: 1rem;
        padding-right: 1rem;
    }}

    .st-key-wsp_hero {{
        padding: 2.4rem 1.35rem 2.6rem;
        border-radius: 10px;
        margin-bottom: 1.1rem;
    }}

    .wsp-hero__eyebrow {{
        margin-bottom: 1rem;
        font-size: 0.64rem;
        letter-spacing: 0.14em;
    }}

    .wsp-hero__title {{
        font-size: clamp(2rem, 10vw, 2.7rem);
        line-height: 1.08;
        margin-bottom: 1.1rem;
        max-width: 100%;
    }}

    .wsp-hero__lead {{
        font-size: 0.95rem;
        line-height: 1.6;
        margin-bottom: 1.7rem;
    }}

    .wsp-hero__actions {{
        flex-direction: column;
        align-items: stretch;
        gap: 0.7rem;
    }}

    .wsp-hero__actions [data-testid="stButton"] {{
        width: 100%;
    }}

    .wsp-hero__actions [data-testid="stButton"] button {{
        width: 100%;
        min-height: 3rem;
    }}

    .wsp-page-title {{
        font-size: 1.35rem;
    }}

    /* Streamlit keeps columns side by side on small screens, so the layout is
       stacked explicitly to keep every control reachable. */
    [data-testid="stHorizontalBlock"] {{
        flex-wrap: wrap;
    }}

    [data-testid="stHorizontalBlock"] > [data-testid="stColumn"] {{
        flex: 1 1 100% !important;
        width: 100% !important;
        min-width: 100%;
    }}

    /* The field column headers do not apply once the columns stack. */
    .st-key-wsp_field_headers {{
        display: none;
    }}

    .wsp-stat-grid {{
        grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
    }}

    [data-testid="stForm"] {{
        padding: 1rem 0.95rem;
    }}

    [data-testid="stForm"] [data-testid="stFormSubmitButton"] button {{
        width: 100%;
        min-height: 2.9rem;
    }}
}}

@media (prefers-reduced-motion: reduce) {{
    [data-testid="stApp"] *,
    [data-testid="stApp"] *::before,
    [data-testid="stApp"] *::after {{
        animation-duration: 0.001ms !important;
        animation-iteration-count: 1 !important;
        transition-duration: 0.001ms !important;
        scroll-behavior: auto !important;
    }}
}}
"""


def inject_theme(nav_sections: tuple[str, ...] | list[str] = ()) -> None:
    """Apply the design system stylesheet to the running Streamlit app."""
    st.markdown(
        f"<style>{THEME_CSS}{_nav_icon_rules(nav_sections)}</style>",
        unsafe_allow_html=True,
    )
