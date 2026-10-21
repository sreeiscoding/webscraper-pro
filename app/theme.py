"""Centralised visual design system for the WebScraper Pro interface.

The palette, spacing scale and stylesheet live here so that every screen shares
one visual language and the rules are not duplicated across rendering modules.
The palette is a restrained near-black scheme with a single teal accent; the
type stacks resolve to fonts already present on the machine, so the interface
stays readable when the webfonts cannot be fetched.
"""

from __future__ import annotations

import streamlit as st


PALETTE = {
    "background": "#08090A",
    "charcoal": "#0E1011",
    "elevated": "#141618",
    "workspace": "#08090A",
    "card": "#0E1011",
    "text": "#F5F5F5",
    "text_on_dark": "#F5F5F5",
    "text_muted": "#92949A",
    "accent": "#14807A",
    "accent_hover": "#1B9189",
    "accent_soft": "#0F2321",
    "dark_border": "#242528",
    "border": "#242528",
    "success": "#21865B",
    "error": "#C64747",
    "warning": "#B07C2E",
}

FONT_STACKS = {
    # The interface typeface: a monospaced face that gives the product its
    # precise, terminal-inspired identity.
    "ui": '"Inconsolata", ui-monospace, "SFMono-Regular", Consolas, monospace',
    # Dense tabular content (prices, counts, identifiers) uses the platform
    # monospace so columns align and figures scan cleanly.
    "mono": 'ui-monospace, "SFMono-Regular", Menlo, Monaco, Consolas, monospace',
    # A restrained secondary face, used only where a button benefits from
    # typographic contrast against the monospaced interface.
    "accent": '"Noto Sans", sans-serif',
}

FONT_IMPORT = (
    "https://fonts.googleapis.com/css2?"
    "family=Inconsolata:wght@400;500;600;700&"
    "family=Noto+Sans:wght@400;500;600&display=swap"
)


def nav_slug(section: str) -> str:
    """Return the stable key fragment used for a navigation destination."""
    return section.lower().replace(" ", "_")



def nav_slug(section: str) -> str:
    """Return the stable key fragment used for a navigation destination."""
    return section.lower().replace(" ", "_")


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
    --wsp-success: {PALETTE['success']};
    --wsp-error: {PALETTE['error']};
    --wsp-warning: {PALETTE['warning']};
    --wsp-gutter: 2.2rem;
    --wsp-font-ui: {FONT_STACKS['ui']};
    --wsp-font-mono: {FONT_STACKS['mono']};
    --wsp-font-accent: {FONT_STACKS['accent']};
    --wsp-radius: 10px;
    --wsp-shadow: 0 1px 2px rgba(0, 0, 0, 0.4), 0 12px 32px rgba(0, 0, 0, 0.35);
}}

html, body, [data-testid="stApp"] {{
    background: var(--wsp-workspace);
    font-family: var(--wsp-font-ui);
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
    font-family: var(--wsp-font-ui);
}}

[data-testid="stApp"] [data-testid="stMarkdownContainer"] :is(
    p, h1, h2, h3, h4, h5, h6, span, a, li, ul, ol, strong, em, div, label
) {{
    font-family: var(--wsp-font-ui);
}}

/* Technical values and code keep the mono face. The extra scope puts this
   rule above the markdown override above. */
[data-testid="stApp"] [data-testid="stMarkdownContainer"] .wsp-mono,
[data-testid="stApp"] code,
[data-testid="stApp"] pre {{
    font-family: var(--wsp-font-mono);
}}

/* CSS selectors are technical values, so they are set in the mono face. */
[data-testid="stApp"] [class*="st-key-selector_"] input {{
    font-family: var(--wsp-font-mono);
}}

.block-container, [data-testid="stMainBlockContainer"] {{
    padding-top: 1.3rem;
    padding-bottom: 3rem;
    padding-left: var(--wsp-gutter);
    padding-right: var(--wsp-gutter);
    max-width: 1180px;
}}

[data-testid="stHeader"] {{
    background: transparent;
}}

/* Streamlit's default gradient bar is reduced to a single hairline. */
[data-testid="stDecoration"] {{
    background: var(--wsp-border);
    height: 1px;
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
    border: none;
    border-bottom: 1px solid var(--wsp-border);
    border-radius: 0;
    margin-left: calc(-1 * var(--wsp-gutter));
    margin-right: calc(-1 * var(--wsp-gutter));
    padding: 1.05rem var(--wsp-gutter) 0.9rem;
    margin-bottom: 3.4rem;
    position: sticky;
    top: 0;
    z-index: 20;
}}

.st-key-wsp_topnav [data-testid="stHorizontalBlock"] {{
    justify-content: space-between;
    align-items: center;
    flex-wrap: nowrap;
    gap: 1.5rem;
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
    gap: 10px;
}}

.wsp-brand__mark {{
    width: 26px;
    height: 26px;
    flex: 0 0 26px;
    border-radius: 6px;
    background: var(--wsp-accent);
    color: #FFFFFF;
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 0.04em;
    display: flex;
    align-items: center;
    justify-content: center;
}}

.wsp-brand__name {{
    font-size: 0.95rem;
    font-weight: 600;
    color: var(--wsp-text);
    line-height: 1.2;
    letter-spacing: -0.01em;
}}

/* Navigation reads as plain text links rather than buttons. */
.st-key-wsp_topnav [data-testid="stButton"] button {{
    background: transparent;
    border: none;
    color: var(--wsp-muted);
    font-size: 0.9rem;
    font-weight: 500;
    padding: 0.3rem 0.1rem;
    border-radius: 0;
    min-height: auto;
    white-space: nowrap;
    transition: color 130ms ease, box-shadow 130ms ease;
}}

.st-key-wsp_topnav [data-testid="stButton"] button:hover {{
    background: transparent;
    color: var(--wsp-text);
}}

.st-key-wsp_topnav [data-testid="stButton"] button:focus-visible {{
    outline: 2px solid var(--wsp-accent);
    outline-offset: 3px;
}}

/* The active destination is marked with a single hairline underline. */
.st-key-wsp_topnav .st-key-wsp_nav_active [data-testid="stButton"] button,
.st-key-wsp_topnav .st-key-wsp_nav_active button {{
    background: transparent;
    border: none;
    color: var(--wsp-text);
    font-weight: 600;
    box-shadow: inset 0 -1px 0 var(--wsp-accent);
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
        margin-bottom: 2.2rem;
    }}
}}

/* ------------------------------ Hero ----------------------------- */

.st-key-wsp_hero {{
    position: relative;
    padding-top: 0.6rem;
    margin-bottom: 2.6rem;
}}

/* The hero copy must be able to shrink inside the content container, which
   keeps the supporting paragraph from overflowing on narrow screens. */
.st-key-wsp_hero [data-testid="stMarkdownContainer"] {{
    min-width: 0;
}}

.wsp-hero__eyebrow {{
    display: inline-block;
    font-size: 0.72rem;
    font-weight: 600;
    letter-spacing: 0.18em;
    text-transform: uppercase;
    color: var(--wsp-muted);
    margin: 0 0 1.5rem;
}}

/* The headline is the interface typeface at display size. The scope keeps it
   above the markdown override that forces the UI face on other elements. */
[data-testid="stApp"] [data-testid="stMarkdownContainer"] .wsp-hero__title {{
    font-family: var(--wsp-font-ui);
    font-size: clamp(2.5rem, 6vw, 4.9rem);
    line-height: 1.04;
    font-weight: 600;
    letter-spacing: -0.035em;
    color: var(--wsp-text);
    margin: 0 0 1.5rem;
    max-width: 17ch;
}}

.wsp-hero__lead {{
    font-family: var(--wsp-font-ui);
    font-size: 1.06rem;
    line-height: 1.65;
    color: var(--wsp-muted);
    margin: 0 0 2.1rem;
    /* The monospaced face needs a slightly wider measure to keep the
       supporting copy to two comfortable lines. */
    max-width: 64ch;
}}

/* The two calls to action sit together under the supporting copy. */
.st-key-wsp_hero_ctas {{
    margin-bottom: 3.4rem;
}}

.st-key-wsp_hero_ctas [data-testid="stHorizontalBlock"] {{
    gap: 1.6rem;
    flex-wrap: wrap;
    align-items: center;
}}

.st-key-wsp_hero_ctas [data-testid="stHorizontalBlock"] > [data-testid="stColumn"] {{
    flex: 0 0 auto;
    width: auto;
}}

.st-key-wsp_hero_ctas [data-testid="stButton"] {{
    width: auto;
}}

.st-key-wsp_hero_ctas [data-testid="stButton"] button {{
    border-radius: 8px;
    font-family: var(--wsp-font-ui);
    font-size: 0.95rem;
    font-weight: 500;
    padding: 0.72rem 1.5rem;
    min-height: 3rem;
    border: 1px solid transparent;
    white-space: nowrap;
    transition: background-color 130ms ease, border-color 130ms ease, color 130ms ease;
}}

/* The primary action is a light surface with dark text. */
.st-key-wsp_hero_ctas [data-testid="stButton"] button[kind="primary"] {{
    background: #EDEDED;
    border-color: #EDEDED;
    color: #101113;
    font-weight: 600;
}}

.st-key-wsp_hero_ctas [data-testid="stButton"] button[kind="primary"]:hover {{
    background: #FFFFFF;
    border-color: #FFFFFF;
    color: #101113;
}}

/* The secondary action reads as a plain text link. */
.st-key-wsp_hero_ctas [data-testid="stButton"] button[kind="secondary"] {{
    background: transparent;
    border-color: transparent;
    color: var(--wsp-muted);
    padding-left: 0;
    padding-right: 0;
    min-height: auto;
    box-shadow: none;
}}

.st-key-wsp_hero_ctas [data-testid="stButton"] button[kind="secondary"]:hover {{
    background: transparent;
    border-color: transparent;
    color: var(--wsp-text);
}}

.st-key-wsp_hero_ctas [data-testid="stButton"] button:focus-visible {{
    outline: 2px solid var(--wsp-accent);
    outline-offset: 3px;
}}

/* ---------------------- Product interface visual ------------------ */

.wsp-visual {{
    border: 1px solid var(--wsp-border);
    border-radius: 12px;
    overflow: hidden;
    background: var(--wsp-charcoal);
    box-shadow: var(--wsp-shadow);
}}

.wsp-visual__bar {{
    display: flex;
    align-items: center;
    gap: 0.75rem;
    padding: 0.6rem 0.95rem;
    border-bottom: 1px solid var(--wsp-border);
    background: rgba(255, 255, 255, 0.014);
}}

.wsp-visual__url {{
    font-size: 0.72rem;
    color: var(--wsp-muted);
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    min-width: 0;
}}

.wsp-visual__badge {{
    margin-left: auto;
    flex: 0 0 auto;
    display: inline-flex;
    align-items: center;
    gap: 0.4rem;
    font-size: 0.68rem;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    color: var(--wsp-muted);
    border: 1px solid var(--wsp-border);
    border-radius: 999px;
    padding: 2px 9px;
}}

.wsp-visual__dot {{
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background: var(--wsp-accent);
    display: block;
}}

.wsp-visual__body {{
    display: grid;
    grid-template-columns: 216px minmax(0, 1fr);
}}

.wsp-visual__rail {{
    border-right: 1px solid var(--wsp-border);
    padding: 0.95rem 1rem;
    min-width: 0;
}}

.wsp-visual__rail-title {{
    font-size: 0.64rem;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    color: var(--wsp-muted);
    margin: 0 0 0.45rem;
}}

.wsp-visual__rail-title + .wsp-visual__rail-title {{
    margin-top: 1.1rem;
}}

.wsp-visual__rail-value {{
    font-size: 0.72rem;
    color: var(--wsp-text);
    word-break: normal;
    overflow-wrap: anywhere;
    line-height: 1.5;
}}

.wsp-visual__rail-value--muted {{
    color: var(--wsp-muted);
}}

.wsp-visual__main {{
    min-width: 0;
}}

.wsp-visual__scroll {{
    overflow-x: auto;
    max-width: 100%;
}}

.wsp-visual table {{
    width: 100%;
    border-collapse: collapse;
    font-size: 0.78rem;
}}

.wsp-visual th {{
    text-align: left;
    font-size: 0.64rem;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: var(--wsp-muted);
    font-weight: 600;
    padding: 0.62rem 0.85rem;
    border-bottom: 1px solid var(--wsp-border);
    white-space: nowrap;
}}

.wsp-visual td {{
    padding: 0.58rem 0.85rem;
    color: var(--wsp-text);
    border-bottom: 1px solid rgba(36, 37, 40, 0.8);
    white-space: nowrap;
}}

.wsp-visual tr:last-child td {{
    border-bottom: none;
}}

.wsp-visual td.wsp-visual__mono {{
    font-family: var(--wsp-font-mono);
    font-size: 0.74rem;
    color: var(--wsp-muted);
}}

.wsp-visual__foot {{
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 1.3rem;
    padding: 0.62rem 0.95rem;
    border-top: 1px solid var(--wsp-border);
    background: rgba(255, 255, 255, 0.012);
}}

.wsp-visual__meta {{
    font-size: 0.68rem;
    color: var(--wsp-muted);
}}

.wsp-visual__meta b {{
    color: var(--wsp-text);
    font-weight: 500;
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

/* ------------------------- Typography accents ---------------------- */

/* A restrained secondary face is reserved for the buttons that carry the
   primary action. Everything else - navigation, links, labels, controls -
   stays in the monospaced interface face. The label is styled as well as the
   button itself, because Streamlit renders the label inside its own markdown
   container, which would otherwise keep the interface face. */
.st-key-wsp_hero_ctas [data-testid="stButton"] button[kind="primary"],
[data-testid="stFormSubmitButton"] button[kind="primary"],
[data-testid="stDownloadButton"] button {{
    font-family: var(--wsp-font-accent);
}}

[data-testid="stApp"] .st-key-wsp_hero_ctas [data-testid="stButton"] button[kind="primary"] [data-testid="stMarkdownContainer"] p,
[data-testid="stApp"] [data-testid="stFormSubmitButton"] button[kind="primary"] [data-testid="stMarkdownContainer"] p,
[data-testid="stApp"] [data-testid="stDownloadButton"] button [data-testid="stMarkdownContainer"] p {{
    font-family: var(--wsp-font-accent);
}}

/* The primary action keeps a stable width whether the webfont loads or the
   fallback is used. */
.st-key-wsp_hero_ctas [data-testid="stButton"] button[kind="primary"] {{
    min-width: 9.5rem;
}}

/* Dense tabular content - prices, counts, identifiers and technical
   metadata - uses the platform monospace so figures align and scan cleanly.
   These rules carry the same extra scope as the interface override above, so
   they win over it without !important. */
[data-testid="stApp"] [data-testid="stMarkdownContainer"] .wsp-mono,
[data-testid="stApp"] [data-testid="stMarkdownContainer"] .wsp-stat__value,
[data-testid="stApp"] [data-testid="stMarkdownContainer"] .wsp-visual__url,
[data-testid="stApp"] [data-testid="stMarkdownContainer"] .wsp-visual__rail-value,
[data-testid="stApp"] [data-testid="stMarkdownContainer"] .wsp-visual__meta {{
    font-family: var(--wsp-font-mono);
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
    background: transparent;
    border-color: var(--wsp-border);
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
    border-color: #2A2C2F;
    color: var(--wsp-text);
    background: var(--wsp-elevated);
}}

[data-testid="stTextInput"] input:focus,
[data-testid="stNumberInput"] input:focus,
[data-testid="stTextArea"] textarea:focus {{
    border-color: var(--wsp-accent);
    box-shadow: 0 0 0 1px var(--wsp-accent);
}}

[data-testid="stTextInput"] input::placeholder,
[data-testid="stTextArea"] textarea::placeholder {{
    color: #6B7075;
}}

[data-testid="stExpander"] {{
    border: 1px solid var(--wsp-border);
    border-radius: var(--wsp-radius);
    background: #0B0C0D;
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

    .wsp-visual__body {{
        grid-template-columns: 180px minmax(0, 1fr);
    }}
}}

@media (max-width: 640px) {{
    :root {{
        --wsp-gutter: 1rem;
    }}

    .block-container, [data-testid="stMainBlockContainer"] {{
        padding-top: 0.8rem;
        padding-left: 1rem;
        padding-right: 1rem;
    }}

    .st-key-wsp_hero {{
        padding-top: 0.2rem;
        margin-bottom: 1.8rem;
    }}

    .wsp-hero__eyebrow {{
        margin-bottom: 0.9rem;
        font-size: 0.64rem;
        letter-spacing: 0.14em;
    }}

    .wsp-hero__title {{
        font-size: clamp(2rem, 9.5vw, 2.6rem);
        line-height: 1.1;
        margin-bottom: 1rem;
        max-width: 100%;
    }}

    .wsp-hero__lead {{
        font-size: 0.95rem;
        line-height: 1.6;
        margin-bottom: 1.6rem;
        max-width: 100%;
    }}

    /* The calls to action stack on a narrow screen. */
    .st-key-wsp_hero_ctas {{
        margin-bottom: 2.4rem;
    }}

    .st-key-wsp_hero_ctas [data-testid="stHorizontalBlock"] {{
        flex-direction: column;
        align-items: flex-start;
        gap: 1rem;
    }}

    .st-key-wsp_hero_ctas [data-testid="stHorizontalBlock"] > [data-testid="stColumn"] {{
        flex: 0 0 auto;
        width: auto;
    }}

    /* The configuration rail is dropped so the data table keeps the width. */
    .wsp-visual__body {{
        grid-template-columns: minmax(0, 1fr);
    }}

    .wsp-visual__rail {{
        display: none;
    }}

    .wsp-visual__foot {{
        gap: 0.9rem;
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

    /* The navigation keeps its own single row: the brand on the left and the
       menu trigger on the right. */
    .st-key-wsp_topnav [data-testid="stHorizontalBlock"] > [data-testid="stColumn"] {{
        flex: 0 1 auto !important;
        width: auto !important;
        min-width: 0;
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


def inject_theme() -> None:
    """Apply the design system stylesheet to the running Streamlit app."""
    st.markdown(
        f"<style>{THEME_CSS}</style>",
        unsafe_allow_html=True,
    )
