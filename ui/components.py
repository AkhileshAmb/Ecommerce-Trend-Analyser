"""
UI Component Library for TrendScanner AI

Reusable components for visualizations, metrics, and UI elements.
"""

import streamlit as st
import pandas as pd

from core.currency import format_inr
import plotly.express as px
import plotly.graph_objects as go
from typing import Any, Dict, List, Optional, Tuple, TypedDict


class WorkspaceSidebarSettings(TypedDict):
    column_mapping: Dict[str, str]
    price_mode: str
    cleaning_strategy: str
    analysis_params: Dict[str, Any]
    export_options: Dict[str, bool]
    enable_llm: bool

# Harmonized sky / teal palette (matches home theme)
COLOR_PRIMARY = "#0284c7"
COLOR_ACCENT = "#0d9488"
COLOR_SECONDARY = "#0369a1"
COLOR_MUTED = "#64748b"
CHART_COLORWAY = ["#0284c7", "#0d9488", "#0369a1", "#14b8a6", "#0ea5e9", "#475569", "#059669"]

CHART_TEMPLATE = "plotly_white"
DEFAULT_CHART_HEIGHT = 440


def finalize_chart(fig: go.Figure, height: int = DEFAULT_CHART_HEIGHT) -> go.Figure:
    """Rich charts: extra margins prevent title overlap; vivid palette."""
    fig.update_layout(
        template=CHART_TEMPLATE,
        height=height,
        margin=dict(l=52, r=40, t=72, b=56),
        font=dict(family="'Segoe UI', system-ui, sans-serif", size=13),
        title_font_size=17,
        title_font_color="#0c4a6e",
        title=dict(x=0.02, xanchor="left"),
        hovermode="closest",
        paper_bgcolor="rgba(255,255,255,0.85)",
        plot_bgcolor="rgba(240, 249, 255, 0.5)",
        colorway=CHART_COLORWAY,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.08,
            xanchor="right",
            x=1,
            bgcolor="rgba(255,255,255,0.7)",
        ),
        font_color="#334155",
    )
    fig.update_xaxes(
        gridcolor="rgba(148, 163, 184, 0.28)",
        zeroline=False,
        tickfont=dict(color="#475569"),
        title_font=dict(color="#134e4a"),
    )
    fig.update_yaxes(
        gridcolor="rgba(148, 163, 184, 0.28)",
        zeroline=False,
        tickfont=dict(color="#475569"),
        title_font=dict(color="#134e4a"),
    )
    return fig


def render_home_hero() -> None:
    """
    Single HTML hero — Streamlit widgets cannot nest inside raw divs, so we embed title + subtitle here.
    Guarantees white text on the dark gradient strip (high contrast).
    """
    st.markdown(
        """
        <div class="mal-title-strip">
            <h1 class="mal-hero-title" style="color:#ffffff;margin:0 0 0.65rem 0;font-weight:800;">
                TrendScanner AI
            </h1>
            <p class="mal-hero-caption" style="color:rgba(255,255,255,0.94);margin:0;">
                Upload a CSV → open <strong style="color:#ffffff;">Workspace</strong> in the sidebar → <strong style="color:#ffffff;">Run full analysis</strong> → explore result tabs.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def apply_results_view_styles() -> None:
    """Reserved — full theme loads once from apply_app_styles() in app."""
    pass


def results_panel():
    """Bordered panel when supported (Streamlit ≥1.29)."""
    try:
        return st.container(border=True)
    except TypeError:
        return st.container()


def apply_app_styles() -> None:
    """
    Flash dashboard theme: mesh gradients, chrome tabs, spacing guards against overlaps.
    Light theme with high-contrast text; fixes dark click/focus surfaces on tabs & expanders.
    """
    st.markdown(
        """
        <style>
          /* --- Shell: flat light canvas so grey Streamlit text reads clearly --- */
          .stApp {
            color-scheme: light;
            --text-color: #1e293b;
            --heading-color: #0f172a;
            background: #f1f5f9 !important;
          }
          .main .block-container {
            padding-top: 1.25rem;
            padding-bottom: 3rem;
            max-width: 1240px;
            color: #1e293b !important;
          }

          /* --- Readable copy: force dark slate on Streamlit defaults --- */
          .main {
            color: #1e293b !important;
          }
          .main [data-testid="element-container"] {
            color: #1e293b;
          }
          .main [data-testid="stMarkdownContainer"] p:not(.mal-hero-caption):not(.mal-rv-hero-title):not(.mal-rv-hero-meta):not(.mal-rv-section-label):not(.mal-gap-line):not(.mal-gap-note):not(.mal-dashboard-title):not(.mal-export-heading):not(.mal-export-blurb),
          .main [data-testid="stMarkdownContainer"] li,
          .main [data-testid="stMarkdownContainer"] td {
            color: #1e293b !important;
          }
          .main [data-testid="stMarkdownContainer"] th {
            color: #0f172a !important;
          }
          .main [data-testid="stMarkdownContainer"] strong {
            color: #0f172a !important;
          }
          .main [data-testid="stMarkdownContainer"] a {
            color: #0369a1 !important;
          }
          .main [data-testid="stMarkdownContainer"] h1:not(.mal-hero-title),
          .main [data-testid="stMarkdownContainer"] h2,
          .main [data-testid="stMarkdownContainer"] h3,
          .main [data-testid="stMarkdownContainer"] h4,
          .main [data-testid="stMarkdownContainer"] h5 {
            color: #0f172a !important;
            -webkit-text-fill-color: #0f172a !important;
            background: none !important;
            -webkit-background-clip: border-box !important;
            background-clip: border-box !important;
          }
          /* header / subheader / title widgets (not only markdown) */
          .main [data-testid="stHeader"],
          .main [data-testid="stHeader"] *,
          .main [data-testid="stHeading"],
          .main [data-testid="stHeading"] * {
            color: #0f172a !important;
            -webkit-text-fill-color: #0f172a !important;
          }
          /* Catch-all headings inside main (covers nested wrappers) */
          .main .block-container h1:not(.mal-hero-title),
          .main .block-container h2,
          .main .block-container h3,
          .main .block-container h4,
          .main .block-container h5 {
            color: #0f172a !important;
            -webkit-text-fill-color: #0f172a !important;
          }

          /*
           * Streamlit ≥1.33 often renders ### / titles via .stHeading + inner spans.
           * Theme CSS can paint these white on our light canvas — force dark slate everywhere
           * except the hero strip (white text on gradient).
           */
          [data-testid="stMain"],
          [data-testid="stMain"] .block-container {
            --text-color: #1e293b !important;
            --heading-color: #0f172a !important;
          }
          .main .stMarkdown h1,
          .main .stMarkdown h2,
          .main .stMarkdown h3,
          .main .stMarkdown h4,
          .main .stMarkdown h5,
          .main .stMarkdown h6 {
            color: #0f172a !important;
            -webkit-text-fill-color: #0f172a !important;
          }
          .main .stHeading,
          .main .stHeading *,
          .main [data-testid="stHeading"],
          .main [data-testid="stHeading"] * {
            color: #0f172a !important;
            -webkit-text-fill-color: #0f172a !important;
            background-image: none !important;
          }
          /* Heading permalink / chain icon (SVG) — must not stay white */
          .main .stHeading svg,
          .main .stMarkdown h3 svg,
          .main [data-testid="stMarkdownContainer"] [data-testid="stHeading"] svg,
          .main [data-testid="stMarkdownContainer"] h3 a svg {
            fill: #0f172a !important;
            color: #0f172a !important;
            opacity: 1 !important;
          }
          .main .stHeading a svg,
          .main [data-testid="stMarkdownContainer"] h3 a svg {
            fill: #0369a1 !important;
          }
          .main .stHeading a,
          .main [data-testid="stMarkdownContainer"] h2 a,
          .main [data-testid="stMarkdownContainer"] h3 a,
          .main [data-testid="stMarkdownContainer"] h4 a {
            color: #0369a1 !important;
            -webkit-text-fill-color: #0369a1 !important;
          }
          /* Nested spans inside markdown headings (Streamlit emotion wrappers) */
          .main [data-testid="stMarkdownContainer"] h1 span,
          .main [data-testid="stMarkdownContainer"] h2 span,
          .main [data-testid="stMarkdownContainer"] h3 span,
          .main [data-testid="stMarkdownContainer"] h4 span,
          .main [data-testid="stMarkdownContainer"] h5 span {
            color: #0f172a !important;
            -webkit-text-fill-color: #0f172a !important;
          }
          /* Same headings repeated inside tab panels */
          .main [role="tabpanel"] .stMarkdown h1,
          .main [role="tabpanel"] .stMarkdown h2,
          .main [role="tabpanel"] .stMarkdown h3,
          .main [role="tabpanel"] .stMarkdown h4,
          .main [role="tabpanel"] .stMarkdown h5,
          .main [role="tabpanel"] .stHeading,
          .main [role="tabpanel"] .stHeading * {
            color: #0f172a !important;
            -webkit-text-fill-color: #0f172a !important;
          }

          /*
           * Do NOT blanket-style all markdown spans — that paints dark text on Streamlit's
           * dark tab/expander/radio focus backgrounds. Scope to body copy + known components.
           */
          .stApp [data-testid="stAppViewContainer"] {
            --text-color: #1e293b !important;
            --heading-color: #0f172a !important;
          }
          .main [data-testid="stMarkdownContainer"] a span {
            color: #0369a1 !important;
            -webkit-text-fill-color: #0369a1 !important;
          }
          /* Coloured chips/badges inside raw HTML markdown */
          .main [data-testid="stMarkdownContainer"] span.mal-rv-pill,
          .main [data-testid="stMarkdownContainer"] .mal-rv-pill {
            color: #f8fafc !important;
            -webkit-text-fill-color: #f8fafc !important;
          }
          .main [data-testid="stMarkdownContainer"] .mal-badge-critical,
          .main [data-testid="stMarkdownContainer"] .mal-badge-strong {
            color: #ffffff !important;
            -webkit-text-fill-color: #ffffff !important;
          }
          .main [data-testid="stMarkdownContainer"] .mal-badge-watch {
            color: #422006 !important;
            -webkit-text-fill-color: #422006 !important;
          }
          /* Uppercase section ribbons — often wrapped in inner spans */
          .main [data-testid="stMarkdownContainer"] p.mal-rv-section-label,
          .main [data-testid="stMarkdownContainer"] .mal-rv-section-label span {
            color: #0369a1 !important;
            -webkit-text-fill-color: #0369a1 !important;
          }
          .main [data-testid="stMarkdownContainer"] .mal-title-strip span,
          .main [data-testid="stMarkdownContainer"] .mal-title-strip strong,
          .main [data-testid="stMarkdownContainer"] .mal-title-strip * {
            color: #ffffff !important;
            -webkit-text-fill-color: #ffffff !important;
          }
          .main [data-testid="stMarkdownContainer"] .mal-title-strip .mal-hero-caption {
            color: rgba(255, 255, 255, 0.94) !important;
          }

          /* Alerts: tint backgrounds stay, body text must stay dark */
          div[data-testid="stAlert"],
          div[data-testid="stAlert"] [data-testid="stMarkdownContainer"],
          div[data-testid="stAlert"] [data-testid="stMarkdownContainer"] p,
          div[data-testid="stAlert"] [data-testid="stMarkdownContainer"] span,
          div[data-testid="stAlert"] [data-testid="stMarkdownContainer"] li {
            color: #0f172a !important;
            -webkit-text-fill-color: #0f172a !important;
          }

          /* File drop zone — light surface + dark helper text (not dark-on-dark) */
          [data-testid="stFileUploader"] section {
            background: #f8fafc !important;
            border: 2px dashed #94a3b8 !important;
          }
          [data-testid="stFileUploader"] section,
          [data-testid="stFileUploader"] section span,
          [data-testid="stFileUploader"] section small,
          [data-testid="stFileUploader"] section p,
          [data-testid="stFileUploader"] [data-baseweb="label"],
          [data-testid="stFileUploader"] .uploadedFile {
            color: #334155 !important;
            -webkit-text-fill-color: #334155 !important;
          }
          [data-testid="stFileUploader"] section button {
            color: #0f172a !important;
            background: #ffffff !important;
            border: 1px solid #cbd5e1 !important;
          }

          /* Slider / number-input helper rows */
          [data-testid="stSlider"] label,
          [data-testid="stNumberInput"] label {
            color: #1e293b !important;
          }

          [data-testid="stCaptionContainer"] {
            color: #334155 !important;
          }
          [data-testid="stCaptionContainer"] p,
          [data-testid="stCaptionContainer"] span {
            color: #334155 !important;
          }
          [data-testid="stWidgetLabel"] label,
          [data-testid="stWidgetLabel"] p,
          [data-testid="stWidgetLabel"] span {
            color: #1e293b !important;
          }
          [data-testid="stExpander"] summary,
          [data-testid="stExpander"] details summary {
            color: #0f172a !important;
            background-color: #ffffff !important;
            -webkit-text-fill-color: #0f172a !important;
          }
          [data-testid="stExpander"] [data-testid="stMarkdownContainer"] p,
          [data-testid="stExpander"] [data-testid="stMarkdownContainer"] li {
            color: #1e293b !important;
          }
          .stRadio label span,
          .stCheckbox label span,
          .stMultiSelect label span {
            color: #1e293b !important;
          }
          /* Alerts: keep body text dark on tinted backgrounds */
          div[data-testid="stAlert"] [data-testid="stMarkdownContainer"] p,
          div[data-testid="stAlert"] [data-testid="stMarkdownContainer"] li,
          div[data-testid="stAlert"] [data-testid="stMarkdownContainer"] strong {
            color: #0f172a !important;
          }
          /*
           * Selectbox / multiselect closed control — Streamlit theme often paints a
           * black trigger while our rules only set dark text → invisible labels.
           */
          [data-testid="stSelectbox"] [data-baseweb="select"],
          [data-testid="stSelectbox"] [data-baseweb="select"] > div,
          [data-testid="stSelectbox"] [data-baseweb="select"] > div > div,
          [data-testid="stSelectbox"] [data-baseweb="select"] span,
          [data-testid="stSelectbox"] [data-baseweb="select"] p,
          [data-testid="stMultiSelect"] [data-baseweb="select"],
          [data-testid="stMultiSelect"] [data-baseweb="select"] > div,
          [data-testid="stMultiSelect"] [data-baseweb="select"] span {
            background-color: #ffffff !important;
            background: #ffffff !important;
            color: #0f172a !important;
            -webkit-text-fill-color: #0f172a !important;
          }
          [data-testid="stSelectbox"] [data-baseweb="select"] > div,
          [data-testid="stMultiSelect"] [data-baseweb="select"] > div {
            border: 1px solid #cbd5e1 !important;
            border-radius: 8px !important;
          }
          [data-testid="stSelectbox"] [data-baseweb="select"] svg,
          [data-testid="stMultiSelect"] [data-baseweb="select"] svg {
            fill: #475569 !important;
            color: #475569 !important;
          }
          [data-testid="stSidebar"] [data-testid="stSelectbox"] [data-baseweb="select"] > div,
          [data-testid="stSidebar"] [data-testid="stMultiSelect"] [data-baseweb="select"] > div {
            background: #ffffff !important;
            background-color: #ffffff !important;
          }
          /* Value text inside closed select (e.g. "Drop rows with…") */
          [data-testid="stSelectbox"] [data-baseweb="select"] > div:first-child,
          [data-testid="stSelectbox"] [data-baseweb="select"] > div:first-child *,
          [data-testid="stSelectbox"] [role="combobox"],
          [data-testid="stSelectbox"] [role="combobox"] * {
            color: #0f172a !important;
            -webkit-text-fill-color: #0f172a !important;
          }
          [data-testid="stSelectbox"] [data-baseweb="select"] > div:first-child {
            background-color: #ffffff !important;
            background: #ffffff !important;
          }
          [data-testid="stSelectbox"] [data-baseweb="select"] > div:first-child *:not(svg):not(path) {
            background-color: transparent !important;
          }
          .stApp [data-baseweb="input"] input,
          .stApp [data-baseweb="textarea"] textarea {
            color: #0f172a !important;
            background-color: #ffffff !important;
          }
          [data-testid="stDataFrame"] {
            color: #0f172a !important;
          }

          /* --- Hero: all content lives INSIDE this div (do not use st.title alongside wrapper divs) --- */
          .mal-title-strip {
            margin-bottom: 1.35rem;
            padding: 1.5rem 1.65rem 1.45rem;
            border-radius: 18px;
            background: linear-gradient(118deg, #0f172a 0%, #134e4a 42%, #0e7490 100%);
            box-shadow: 0 14px 38px rgba(15, 23, 42, 0.28), inset 0 1px 0 rgba(255,255,255,0.12);
            border: 1px solid rgba(148, 163, 184, 0.35);
          }
          .mal-title-strip .mal-hero-title {
            margin: 0 0 0.65rem 0;
            padding: 0;
            font-size: clamp(1.55rem, 3.5vw, 2.05rem);
            font-weight: 800;
            letter-spacing: -0.03em;
            color: #ffffff !important;
            text-shadow: 0 2px 14px rgba(0, 0, 0, 0.45);
            line-height: 1.2;
          }
          .mal-title-strip .mal-hero-caption {
            margin: 0;
            padding: 0;
            font-size: 1rem;
            line-height: 1.6;
            font-weight: 500;
            color: rgba(255, 255, 255, 0.94) !important;
          }
          .mal-title-strip .mal-hero-caption strong {
            color: #ffffff !important;
            font-weight: 700;
          }
          /* Beat Streamlit default heading / markdown colours on raw HTML */
          [data-testid="stMarkdownContainer"] .mal-title-strip .mal-hero-title,
          .main [data-testid="stMarkdownContainer"] h1.mal-hero-title {
            color: #ffffff !important;
            -webkit-text-fill-color: #ffffff !important;
          }
          [data-testid="stMarkdownContainer"] .mal-title-strip .mal-hero-caption {
            color: rgba(255, 255, 255, 0.94) !important;
          }
          .mal-steps-row {
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            margin: 0 0 1.25rem 0;
          }
          .mal-step-chip {
            flex: 1;
            min-width: 140px;
            padding: 10px 14px;
            border-radius: 14px;
            font-size: 0.82rem;
            font-weight: 600;
            border: 2px solid #e2e8f0;
            background: #ffffff;
            backdrop-filter: blur(6px);
            box-shadow: 0 2px 12px rgba(15, 23, 42, 0.06);
            color: #1e293b;
          }
          .mal-step-chip.done {
            border-color: rgba(16, 185, 129, 0.55);
            background: linear-gradient(135deg, rgba(209, 250, 229, 0.95), rgba(255, 255, 255, 0.92));
            color: #065f46;
          }
          .mal-step-chip.active {
            border-color: rgba(14, 165, 233, 0.65);
            background: linear-gradient(135deg, rgba(224, 242, 254, 0.98), rgba(240, 253, 250, 0.95));
            box-shadow: 0 6px 20px rgba(14, 165, 233, 0.22);
            color: #0c4a6e;
          }
          .mal-step-chip.pending {
            opacity: 1;
            color: #334155;
          }

          /* --- Sidebar --- */
          [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #f8fafc 0%, #f0fdfa 55%, #f8fafc 100%) !important;
            border-right: 3px solid #99f6e4 !important;
            box-shadow: inset -6px 0 20px rgba(13, 148, 136, 0.06);
            color: #1e293b !important;
          }
          [data-testid="stSidebar"] .block-container {
            padding-top: 1.5rem;
            padding-bottom: 2rem;
          }
          [data-testid="stSidebar"] h3,
          [data-testid="stSidebar"] h4,
          [data-testid="stSidebar"] label span,
          [data-testid="stSidebar"] [data-testid="stHeader"],
          [data-testid="stSidebar"] [data-testid="stHeader"] *,
          [data-testid="stSidebar"] [data-testid="stHeading"],
          [data-testid="stSidebar"] [data-testid="stHeading"] * {
            color: #0f172a !important;
            -webkit-text-fill-color: #0f172a !important;
          }
          [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
          [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] li {
            color: #1e293b !important;
          }
          [data-testid="stSidebar"] [data-testid="stCaptionContainer"],
          [data-testid="stSidebar"] [data-testid="stCaptionContainer"] p,
          [data-testid="stSidebar"] [data-testid="stCaptionContainer"] span {
            color: #334155 !important;
          }
          /* Sidebar markdown headings / titles */
          [data-testid="stSidebar"] .stMarkdown h1,
          [data-testid="stSidebar"] .stMarkdown h2,
          [data-testid="stSidebar"] .stMarkdown h3,
          [data-testid="stSidebar"] .stHeading,
          [data-testid="stSidebar"] .stHeading * {
            color: #0f172a !important;
            -webkit-text-fill-color: #0f172a !important;
          }

          .mal-sidebar-card {
            border: 1px solid #cbd5e1;
            border-radius: 14px;
            padding: 0.85rem 1rem 1rem;
            margin-bottom: 0.75rem;
            background: rgba(255, 255, 255, 0.9);
            box-shadow: 0 4px 18px rgba(15, 23, 42, 0.06);
            color: #1e293b;
          }
          .mal-sidebar-card p {
            color: #1e293b !important;
          }
          .mal-sidebar-hint {
            font-size: 0.78rem;
            color: #334155 !important;
            line-height: 1.45;
            margin-top: 0.35rem;
          }

          /* --- Settings workspace (sidebar) --- */
          .ts-settings-hero {
            margin: 0 0 1rem 0;
            padding: 1rem 1.05rem 1.05rem;
            border-radius: 14px;
            background: linear-gradient(125deg, #0f172a 0%, #134e4a 48%, #0e7490 100%);
            border: 1px solid rgba(148, 163, 184, 0.35);
            box-shadow: 0 8px 24px rgba(15, 23, 42, 0.18);
          }
          .ts-settings-kicker {
            margin: 0;
            font-size: 0.68rem;
            font-weight: 700;
            letter-spacing: 0.12em;
            text-transform: uppercase;
            color: rgba(167, 243, 208, 0.95) !important;
          }
          .ts-settings-title {
            margin: 0.25rem 0 0;
            font-size: 1.2rem;
            font-weight: 800;
            color: #ffffff !important;
            letter-spacing: -0.02em;
          }
          .ts-settings-sub {
            margin: 0.4rem 0 0;
            font-size: 0.8rem;
            line-height: 1.45;
            color: rgba(255, 255, 255, 0.88) !important;
          }
          [data-testid="stSidebar"] .ts-settings-hero,
          [data-testid="stSidebar"] .ts-settings-hero * {
            -webkit-text-fill-color: unset;
          }
          [data-testid="stSidebar"] .ts-settings-hero .ts-settings-kicker {
            color: #a7f3d0 !important;
            -webkit-text-fill-color: #a7f3d0 !important;
          }
          [data-testid="stSidebar"] .ts-settings-hero .ts-settings-title {
            color: #ffffff !important;
            -webkit-text-fill-color: #ffffff !important;
          }
          [data-testid="stSidebar"] .ts-settings-hero .ts-settings-sub,
          [data-testid="stSidebar"] .ts-settings-hero .ts-settings-sub strong {
            color: rgba(255, 255, 255, 0.92) !important;
            -webkit-text-fill-color: rgba(255, 255, 255, 0.92) !important;
          }
          [data-testid="stSidebar"] .ts-section-lead,
          [data-testid="stSidebar"] .ts-section-lead strong {
            color: #475569 !important;
            -webkit-text-fill-color: #475569 !important;
          }
          [data-testid="stSidebar"] .ts-section-lead strong {
            color: #0f172a !important;
            -webkit-text-fill-color: #0f172a !important;
          }
          [data-testid="stSidebar"] .ts-pill,
          [data-testid="stSidebar"] .ts-pill span {
            -webkit-text-fill-color: currentColor !important;
          }
          .ts-settings-footer {
            margin-top: 0.5rem;
            padding: 0.65rem 0.75rem;
            border-radius: 10px;
            background: #e2e8f0;
            border: 1px dashed #94a3b8;
            font-size: 0.75rem;
            color: #334155 !important;
            line-height: 1.4;
          }
          .ts-settings-footer strong {
            color: #0f172a !important;
          }
          [data-testid="stSidebar"] [data-testid="stExpander"] {
            border: 1px solid #e2e8f0;
            border-radius: 12px;
            background: #ffffff !important;
            margin-bottom: 0.55rem;
            box-shadow: 0 2px 10px rgba(15, 23, 42, 0.04);
            overflow: hidden;
          }
          [data-testid="stSidebar"] [data-testid="stExpander"] details,
          [data-testid="stSidebar"] [data-testid="stExpander"] details[open] {
            background: #ffffff !important;
          }
          [data-testid="stSidebar"] [data-testid="stExpander"] summary {
            font-weight: 650 !important;
            font-size: 0.88rem !important;
            color: #0f172a !important;
            -webkit-text-fill-color: #0f172a !important;
            background: #ffffff !important;
            padding: 0.5rem 0.35rem;
          }
          [data-testid="stSidebar"] [data-testid="stExpander"] details[open] > summary {
            background: #f0fdfa !important;
            color: #0f766e !important;
            -webkit-text-fill-color: #0f766e !important;
          }
          [data-testid="stSidebar"] [data-testid="stExpander"] summary:hover {
            background: #f8fafc !important;
            color: #0e7490 !important;
            -webkit-text-fill-color: #0e7490 !important;
          }
          [data-testid="stSidebar"] [data-testid="stExpander"] summary span,
          [data-testid="stSidebar"] [data-testid="stExpander"] summary p,
          [data-testid="stSidebar"] [data-testid="stExpander"] summary svg {
            color: inherit !important;
            -webkit-text-fill-color: inherit !important;
            fill: currentColor !important;
          }
          .ts-section-lead {
            font-size: 0.8rem;
            color: #475569 !important;
            line-height: 1.5;
            margin: 0 0 0.65rem 0;
          }
          .ts-pill-row {
            display: flex;
            flex-wrap: wrap;
            gap: 6px;
            margin: 0.35rem 0 0.5rem 0;
          }
          .ts-pill {
            font-size: 0.72rem;
            font-weight: 600;
            padding: 4px 10px;
            border-radius: 999px;
            background: #ecfdf5;
            color: #065f46 !important;
            border: 1px solid #a7f3d0;
          }
          .ts-pill.price { background: #f0f9ff; color: #0c4a6e !important; border-color: #bae6fd; }
          .ts-pill.feature { background: #f5f3ff; color: #5b21b6 !important; border-color: #ddd6fe; }

          .stTabs [data-baseweb="tab-list"] {
            gap: 10px;
            flex-wrap: wrap;
            background: #ffffff;
            padding: 12px 14px 6px !important;
            border-radius: 16px;
            box-shadow: 0 4px 24px rgba(15, 23, 42, 0.07);
            border: 1px solid #e2e8f0;
            margin-bottom: 8px;
          }
          .stTabs [data-baseweb="tab"] {
            border-radius: 12px 12px 0 0 !important;
            padding: 10px 16px !important;
            font-weight: 700 !important;
            font-size: 0.88rem !important;
            color: #475569 !important;
            background-color: transparent !important;
            background: transparent !important;
            -webkit-text-fill-color: #475569 !important;
          }
          .stTabs [data-baseweb="tab"]:hover {
            background: #f8fafc !important;
            color: #0f172a !important;
            -webkit-text-fill-color: #0f172a !important;
          }
          .stTabs [data-baseweb="tab"][aria-selected="true"],
          .stTabs [aria-selected="true"] {
            background: #ffffff !important;
            background-color: #ffffff !important;
            color: #0369a1 !important;
            -webkit-text-fill-color: #0369a1 !important;
            box-shadow: 0 -2px 12px rgba(14, 165, 233, 0.12);
            border-bottom: 3px solid #0284c7 !important;
          }
          .stTabs [data-baseweb="tab"] span,
          .stTabs [data-baseweb="tab"] p,
          .stTabs [data-baseweb="tab"] div {
            color: inherit !important;
            -webkit-text-fill-color: inherit !important;
            background: transparent !important;
          }

          /* --- Anti-overlap: charts & captions --- */
          [data-testid="stPlotlyChart"] {
            margin-bottom: 2rem !important;
            margin-top: 0.5rem !important;
            min-height: 360px;
          }
          .js-plotly-plot .plotly .main-svg {
            border-radius: 12px;
          }
          [data-testid="stVerticalBlock"] > div [data-testid="element-container"] {
            margin-bottom: 0.5rem;
          }
          [data-testid="stCaptionContainer"] {
            margin-bottom: 1.1rem !important;
            margin-top: 0.25rem !important;
          }
          h4, h5, [data-testid="stHeader"] { letter-spacing: -0.02em; }

          /* --- Metrics strip --- */
          [data-testid="stMetricValue"] {
            color: #0369a1 !important;
            font-weight: 800 !important;
          }
          [data-testid="stMetricLabel"] {
            color: #334155 !important;
          }

          /* --- Results hero --- */
          .mal-rv-hero {
            display: flex;
            flex-wrap: wrap;
            align-items: center;
            justify-content: space-between;
            gap: 14px;
            padding: 18px 22px;
            margin-bottom: 20px;
            border-radius: 18px;
            background: #ffffff;
            border: 1px solid #cbd5e1;
            box-shadow: 0 8px 28px rgba(15, 23, 42, 0.08);
          }
          .mal-rv-hero-title {
            margin: 0;
            font-size: 1.2rem;
            font-weight: 800;
            letter-spacing: -0.02em;
            color: #0f172a !important;
            -webkit-text-fill-color: #0f172a !important;
          }
          .mal-rv-hero-meta {
            margin: 6px 0 0;
            font-size: 0.88rem;
            color: #1e293b !important;
            font-weight: 500;
          }
          .mal-rv-pill {
            display: inline-block;
            padding: 10px 18px;
            border-radius: 999px;
            font-size: 0.85rem;
            font-weight: 800;
            background: linear-gradient(135deg, #0284c7, #0d9488);
            color: #f8fafc !important;
            box-shadow: 0 6px 18px rgba(2, 132, 199, 0.35);
            border: none;
          }
          .mal-rv-section-label {
            font-size: 0.72rem;
            text-transform: uppercase;
            letter-spacing: 0.14em;
            font-weight: 800;
            color: #0369a1 !important;
            -webkit-text-fill-color: #0369a1 !important;
            margin-bottom: 10px;
          }

          .mal-badge-critical { background: linear-gradient(135deg,#dc2626,#b91c1c); color: #fff !important; padding: 5px 12px; border-radius: 8px; }
          .mal-badge-strong { background: linear-gradient(135deg,#ea580c,#c2410c); color: #fff !important; padding: 5px 12px; border-radius: 8px; }
          .mal-badge-watch { background: linear-gradient(135deg,#eab308,#ca8a04); color: #422006 !important; padding: 5px 12px; border-radius: 8px; }

          .mal-gap-card {
            padding: 16px 18px;
            margin-bottom: 14px;
            border-radius: 16px;
            border: 1px solid #e2e8f0;
            background: rgba(255, 255, 255, 0.92);
            box-shadow: 0 6px 22px rgba(15, 23, 42, 0.06);
          }
          .mal-gap-card p.mal-gap-line {
            margin: 12px 0 8px;
            font-size: 0.9rem;
            color: #1e293b !important;
            line-height: 1.45;
          }
          .mal-gap-card p.mal-gap-note {
            margin: 0;
            font-size: 0.8rem;
            color: #475569 !important;
          }
          .mal-gap-card code {
            color: #0c4a6e !important;
            background: #f1f5f9;
            padding: 3px 8px;
            border-radius: 6px;
            border: 1px solid #cbd5e1;
          }

          /* Buttons — dark label on secondary so Streamlit grey never fades out */
          .stButton > button[kind="secondary"],
          .stButton > button:not([kind="primary"]) {
            color: #0f172a !important;
          }
          /* Primary button — sky → teal */
          .stButton > button[kind="primary"] {
            background: linear-gradient(135deg, #0284c7 0%, #0d9488 100%) !important;
            border: none !important;
            color: #ffffff !important;
            font-weight: 800 !important;
            letter-spacing: 0.02em;
            box-shadow: 0 8px 22px rgba(2, 132, 199, 0.35);
            border-radius: 14px !important;
          }
          /*
           * Download buttons: Streamlit often uses a dark primary fill — our old rule forced
           * dark text (#0f172a) on dark bg. Force a light chrome + dark label so labels stay readable.
           */
          .stDownloadButton > button {
            border-radius: 12px !important;
            font-weight: 700 !important;
            color: #0f172a !important;
            -webkit-text-fill-color: #0f172a !important;
            background: linear-gradient(180deg, #ffffff 0%, #f1f5f9 100%) !important;
            border: 2px solid rgba(14, 165, 233, 0.45) !important;
            box-shadow: 0 2px 10px rgba(15, 23, 42, 0.07) !important;
          }
          .stDownloadButton > button:hover {
            border-color: #0284c7 !important;
            background: #ffffff !important;
          }
          .stDownloadButton > button span,
          .stDownloadButton > button p {
            color: #0f172a !important;
            -webkit-text-fill-color: #0f172a !important;
          }

          /* Export tab — explicit headings/blurbs (avoid ##### / caption washing out) */
          .mal-export-heading {
            font-size: 1.12rem;
            font-weight: 800;
            letter-spacing: -0.02em;
            color: #0f172a !important;
            -webkit-text-fill-color: #0f172a !important;
            margin: 0.15rem 0 0.65rem 0;
            line-height: 1.3;
          }
          .main [data-testid="stMarkdownContainer"] p.mal-export-heading {
            color: #0f172a !important;
            -webkit-text-fill-color: #0f172a !important;
          }
          .mal-export-blurb {
            font-size: 0.92rem;
            line-height: 1.55;
            color: #475569 !important;
            margin: 0 0 1.15rem 0;
          }
          .main [data-testid="stMarkdownContainer"] p.mal-export-blurb {
            color: #475569 !important;
          }
          .mal-export-blurb strong {
            color: #0f172a !important;
          }

          /* Info / success boxes spacing */
          div[data-testid="stAlert"] {
            margin-bottom: 1rem !important;
          }

          .mal-upload-callout {
            padding: 1.6rem 1.75rem;
            border-radius: 18px;
            text-align: center;
            background: #ffffff;
            border: 2px dashed rgba(14, 165, 233, 0.45);
            color: #0f172a !important;
            font-weight: 500;
            margin-bottom: 1.25rem;
            box-shadow: 0 8px 28px rgba(15, 23, 42, 0.06);
            line-height: 1.55;
          }
          .mal-upload-callout strong {
            color: #0f172a !important;
          }
          .mal-upload-callout span {
            color: #1e293b !important;
            opacity: 1 !important;
          }

          /* Explicit dashboard title (avoids Streamlit ### sometimes rendering pale/white) */
          .mal-dashboard-title {
            font-size: clamp(1.2rem, 2.4vw, 1.42rem);
            font-weight: 800;
            color: #0f172a !important;
            -webkit-text-fill-color: #0f172a !important;
            margin: 0.35rem 0 0.85rem 0;
            letter-spacing: -0.02em;
            line-height: 1.25;
          }
          .main [data-testid="stMarkdownContainer"] p.mal-dashboard-title {
            color: #0f172a !important;
            -webkit-text-fill-color: #0f172a !important;
          }

          .main h1:not(.mal-hero-title),
          .main h2,
          .main h3,
          .main h4,
          .main h5 {
            color: #0f172a !important;
            -webkit-text-fill-color: #0f172a !important;
            font-weight: 800 !important;
            margin-top: 0.75rem !important;
          }

          @keyframes mal-shimmer {
            0% { background-position: 0% 50%; }
            100% { background-position: 100% 50%; }
          }

          /* ===== Contrast guard: interactive surfaces stay LIGHT with DARK text ===== */

          /* Main-area expanders (results tabs, "How to read", etc.) */
          .main [data-testid="stExpander"],
          [data-testid="stMain"] [data-testid="stExpander"] {
            background: #ffffff !important;
            border: 1px solid #e2e8f0 !important;
            border-radius: 12px !important;
          }
          .main [data-testid="stExpander"] details,
          .main [data-testid="stExpander"] details[open] {
            background: #ffffff !important;
          }
          .main [data-testid="stExpander"] summary,
          .main [data-testid="stExpander"] details[open] > summary {
            background: #ffffff !important;
            color: #0f172a !important;
            -webkit-text-fill-color: #0f172a !important;
          }
          .main [data-testid="stExpander"] details[open] > summary {
            background: #f8fafc !important;
            border-bottom: 1px solid #e2e8f0;
          }
          .main [data-testid="stExpander"] summary:hover,
          .main [data-testid="stExpander"] summary:focus,
          .main [data-testid="stExpander"] summary:active {
            background: #f1f5f9 !important;
            color: #0f172a !important;
            -webkit-text-fill-color: #0f172a !important;
          }
          .main [data-testid="stExpander"] summary span,
          .main [data-testid="stExpander"] summary p {
            color: inherit !important;
            -webkit-text-fill-color: inherit !important;
          }

          /* Radio / checkbox — never dark label on dark row */
          .stRadio [role="radiogroup"] label,
          .stRadio [role="radiogroup"] label span,
          .stRadio [role="radiogroup"] label p,
          .stCheckbox label,
          .stCheckbox label span {
            color: #1e293b !important;
            -webkit-text-fill-color: #1e293b !important;
            background-color: transparent !important;
          }
          .stRadio [role="radiogroup"] label:has(input:checked),
          .stRadio label[data-checked="true"] {
            background-color: #e0f2fe !important;
            border-radius: 8px;
          }
          .stRadio [role="radiogroup"] label:has(input:checked) span,
          .stRadio label[data-checked="true"] span {
            color: #0c4a6e !important;
            -webkit-text-fill-color: #0c4a6e !important;
          }

          /* Select / multiselect — labels + open dropdown list */
          [data-testid="stSelectbox"] label,
          [data-testid="stMultiSelect"] label {
            color: #1e293b !important;
          }
          [data-baseweb="popover"],
          [data-baseweb="popover"] ul,
          [data-baseweb="menu"],
          [data-baseweb="menu"] ul {
            background: #ffffff !important;
            background-color: #ffffff !important;
          }
          [data-baseweb="popover"] li,
          [data-baseweb="menu"] li,
          ul[role="listbox"] li,
          [role="listbox"] [role="option"] {
            color: #0f172a !important;
            -webkit-text-fill-color: #0f172a !important;
            background: #ffffff !important;
            background-color: #ffffff !important;
          }
          ul[role="listbox"] li[aria-selected="true"],
          [role="listbox"] [role="option"][aria-selected="true"],
          [data-baseweb="popover"] li[aria-selected="true"],
          [data-baseweb="menu"] li[aria-selected="true"] {
            background: #e0f2fe !important;
            background-color: #e0f2fe !important;
            color: #0c4a6e !important;
            -webkit-text-fill-color: #0c4a6e !important;
          }
          [data-baseweb="popover"] li span,
          [data-baseweb="menu"] li span,
          ul[role="listbox"] li span {
            color: inherit !important;
            -webkit-text-fill-color: inherit !important;
            background: transparent !important;
          }

          /* Sidebar widgets — same rules inside Workspace */
          [data-testid="stSidebar"] .stRadio [role="radiogroup"] label,
          [data-testid="stSidebar"] .stRadio [role="radiogroup"] label span,
          [data-testid="stSidebar"] .stCheckbox label span,
          [data-testid="stSidebar"] [data-testid="stWidgetLabel"] label,
          [data-testid="stSidebar"] [data-testid="stWidgetLabel"] span,
          [data-testid="stSidebar"] [data-testid="stSlider"] label,
          [data-testid="stSidebar"] [data-testid="stSlider"] span {
            color: #1e293b !important;
            -webkit-text-fill-color: #1e293b !important;
          }
          [data-testid="stSidebar"] .stRadio [role="radiogroup"] label:has(input:checked) {
            background-color: #ccfbf1 !important;
          }

          /* Sidebar nested expander (manual column override) */
          [data-testid="stSidebar"] [data-testid="stExpander"] [data-testid="stExpander"] {
            background: #f8fafc !important;
          }

          /* Branded HTML blocks — explicit contrast (beats Streamlit emotion wrappers) */
          .mal-rv-hero,
          .mal-rv-hero .mal-rv-hero-title,
          .mal-rv-hero .mal-rv-hero-meta {
            color: #0f172a !important;
            -webkit-text-fill-color: #0f172a !important;
          }
          .mal-rv-hero .mal-rv-hero-meta {
            color: #334155 !important;
            -webkit-text-fill-color: #334155 !important;
          }
          .mal-rv-pill,
          .mal-rv-pill span {
            color: #f8fafc !important;
            -webkit-text-fill-color: #f8fafc !important;
          }
          .mal-rv-section-label,
          .mal-rv-section-label span {
            color: #0369a1 !important;
            -webkit-text-fill-color: #0369a1 !important;
          }
          .mal-step-chip span {
            color: #1e293b !important;
            -webkit-text-fill-color: #1e293b !important;
          }
          .mal-step-chip.done span { color: #065f46 !important; -webkit-text-fill-color: #065f46 !important; }
          .mal-step-chip.active span { color: #0c4a6e !important; -webkit-text-fill-color: #0c4a6e !important; }

          /* Primary / secondary buttons — keep label readable on click */
          .stButton > button[kind="primary"],
          .stButton > button[kind="primary"] span,
          .stButton > button[kind="primary"] p {
            color: #ffffff !important;
            -webkit-text-fill-color: #ffffff !important;
          }
          .stButton > button[kind="primary"]:hover,
          .stButton > button[kind="primary"]:active,
          .stButton > button[kind="primary"]:focus {
            color: #ffffff !important;
            -webkit-text-fill-color: #ffffff !important;
          }
          .stButton > button[kind="secondary"]:hover,
          .stButton > button:not([kind="primary"]):hover {
            background: #f1f5f9 !important;
            color: #0f172a !important;
            -webkit-text-fill-color: #0f172a !important;
          }

          /* Tab panels — headings inside results */
          .main [role="tabpanel"] [data-testid="stMarkdownContainer"] p,
          .main [role="tabpanel"] [data-testid="stCaptionContainer"] p {
            color: #334155 !important;
          }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_step_row(step: int, labels: Optional[List[str]] = None) -> None:
    """Flash step chips — clear states, no cramped caption line."""
    labels = labels or [
        "Upload CSV",
        "Configure & run",
        "Explore results",
    ]
    chips = []
    for i, lab in enumerate(labels, start=1):
        if i < step:
            cls = "mal-step-chip done"
        elif i == step:
            cls = "mal-step-chip active"
        else:
            cls = "mal-step-chip pending"
        chips.append(
            f'<div class="{cls}"><strong>Step {i}</strong><br/>'
            f'<span style="font-weight:600;color:#1e293b">{lab}</span></div>'
        )
    st.markdown(
        f'<div class="mal-steps-row">{"".join(chips)}</div>',
        unsafe_allow_html=True,
    )


def create_kpi_card(title: str, value: str, delta: Optional[str] = None, 
                    delta_color: str = "normal", help_text: Optional[str] = None):
    """Create a KPI metric card with optional delta and help text."""
    col = st.columns(1)[0]
    with col:
        if help_text:
            st.metric(title, value, delta, delta_color=delta_color, help=help_text)
        else:
            st.metric(title, value, delta, delta_color=delta_color)


def create_dashboard_summary(
    results: Dict, *, compact_title: bool = False, short_labels: bool = False
) -> None:
    """Create a dashboard summary section with key metrics."""
    if compact_title:
        st.markdown('<p class="mal-rv-section-label">Performance snapshot</p>', unsafe_allow_html=True)
        st.markdown("##### At a glance")
        st.caption("Deterministic outputs from all four agents on your cleaned file.")
    else:
        st.header("📊 Executive Dashboard")

    brand_result = results["agents"]["brand"]
    pricing_result = results["agents"]["pricing"]
    feature_result = results["agents"]["feature"]
    gap_result = results["agents"]["gap"]

    total_records = results.get("total_records", 0)
    top_brand = (
        brand_result["results"]["top_brands"][0] if brand_result["results"]["top_brands"] else None
    )
    pricing_stats = pricing_result["results"]["price_statistics"]
    gaps_count = gap_result["results"]["identified_gaps_count"]

    if short_labels:
        r_lbl = "Rows analyzed"
        lead_lbl = "Top brand"
        price_lbl = "Avg price"
        gap_lbl = "Gap signals"
        ub_lbl = "Brands"
        uf_lbl = "Features"
        pr_lbl = "Price span"
    else:
        r_lbl = "Total Records Analyzed"
        lead_lbl = "Market Leader"
        price_lbl = "Average Price"
        gap_lbl = "Market Gaps Identified"
        ub_lbl = "Unique Brands"
        uf_lbl = "Unique Features"
        pr_lbl = "Price Range"

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(r_lbl, f"{total_records:,}", help="Rows used after cleaning")

    with col2:
        market_leader = top_brand["brand"] if top_brand else "N/A"
        market_share = f"{top_brand['confidence']*100:.1f}% share" if top_brand else "—"
        st.metric(
            lead_lbl,
            market_leader,
            delta=market_share,
            delta_color="off",
            help="Highest row-share brand in this extract",
        )

    with col3:
        avg_price = pricing_stats.get("mean_price", 0)
        st.metric(price_lbl, format_inr(avg_price), help="Mean price (INR)")

    with col4:
        st.metric(gap_lbl, f"{gaps_count}", help="Brand×feature pairs below your gap cutoff")

    col5, col6, col7 = st.columns(3)

    with col5:
        unique_brands = brand_result["results"]["total_unique_brands"]
        st.metric(ub_lbl, f"{unique_brands}", help="Distinct brand values")

    with col6:
        unique_features = feature_result["results"]["total_unique_features"]
        st.metric(uf_lbl, f"{unique_features}", help="Distinct feature strings")

    with col7:
        price_range = pricing_stats["max_price"] - pricing_stats["min_price"]
        st.metric(pr_lbl, format_inr(price_range), help="Max − min price (INR)")


def create_brand_pie_chart(brands_df: pd.DataFrame) -> go.Figure:
    """Create a pie chart for brand distribution."""
    fig = px.pie(
        brands_df,
        values="count",
        names="brand",
        title="Share of rows by brand",
        hole=0.45,
        color_discrete_sequence=CHART_COLORWAY,
    )
    fig.update_traces(textposition='inside', textinfo='percent+label')
    return finalize_chart(fig, height=400)


def create_price_histogram(prices: List[float], title: str = "Price Distribution") -> go.Figure:
    """Create a histogram for price distribution."""
    fig = px.histogram(
        x=prices,
        nbins=30,
        title=title,
        labels={"x": "Price (₹)", "y": "Frequency"}
    )
    fig.update_layout(showlegend=False)
    return finalize_chart(fig)


def create_price_boxplot(prices: List[float], title: str = "Price Distribution Box Plot") -> go.Figure:
    """Create a box plot for price distribution."""
    fig = go.Figure()
    fig.add_trace(go.Box(y=prices, name="Prices", boxmean='sd'))
    fig.update_layout(title=title, yaxis_title="Price (₹)", showlegend=False)
    return finalize_chart(fig)


def create_feature_bar_chart(features_df: pd.DataFrame, horizontal: bool = True) -> go.Figure:
    """Create a bar chart for features."""
    if horizontal:
        fig = px.bar(
            features_df,
            x="count",
            y="feature",
            orientation='h',
            title="Top Features by Count",
            labels={"count": "Count", "feature": "Feature"}
        )
    else:
        fig = px.bar(
            features_df,
            x="feature",
            y="count",
            title="Top Features by Count",
            labels={"count": "Count", "feature": "Feature"}
        )
    fig.update_layout(showlegend=False)
    return finalize_chart(fig)


def create_gap_visualization(gaps: List[Dict], top_n: int = 10) -> Optional[go.Figure]:
    """Create visualization for market gaps."""
    if not gaps:
        return None
    
    # Get top N gaps
    top_gaps = sorted(gaps, key=lambda x: x['gap_score'])[:top_n]
    
    gap_df = pd.DataFrame(top_gaps)
    
    fig = px.bar(
        gap_df,
        x="gap_score",
        y="brand",
        color="gap_score",
        color_continuous_scale=[
            [0, "#dbeafe"],
            [0.5, "#f97316"],
            [1, "#991b1b"],
        ],
        orientation='h',
        title="Strongest gap signals (most negative scores)",
        labels={"gap_score": "Gap score", "brand": "Brand"},
        hover_data=["feature", "observed_count", "expected_count"]
    )
    fig.update_layout(showlegend=False)
    return finalize_chart(fig, height=460)


def create_data_quality_metrics(df: pd.DataFrame) -> Dict:
    """Calculate and return data quality metrics."""
    total_rows = len(df)
    total_cols = len(df.columns)
    missing_values = df.isnull().sum().sum()
    missing_percentage = (missing_values / (total_rows * total_cols)) * 100
    duplicate_rows = df.duplicated().sum()
    duplicate_percentage = (duplicate_rows / total_rows) * 100 if total_rows > 0 else 0
    
    quality_score = 100 - (missing_percentage + duplicate_percentage)
    quality_score = max(0, min(100, quality_score))
    
    return {
        "total_rows": total_rows,
        "total_cols": total_cols,
        "missing_values": missing_values,
        "missing_percentage": missing_percentage,
        "duplicate_rows": duplicate_rows,
        "duplicate_percentage": duplicate_percentage,
        "quality_score": quality_score
    }


def display_data_quality_metrics(df: pd.DataFrame, cleaned_df: pd.DataFrame) -> None:
    """Display data quality metrics before and after cleaning."""
    with st.expander("📈 Data Quality Metrics", expanded=False):
        before_metrics = create_data_quality_metrics(df)
        after_metrics = create_data_quality_metrics(cleaned_df)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📥 Before Cleaning")
            st.metric(
                "Total Rows", 
                f"{before_metrics['total_rows']:,}",
                help="Total number of rows in the dataset"
            )
            
            # Missing values - lower is better
            missing_delta = f"{before_metrics['missing_percentage']:.1f}%"
            missing_color = "normal" if before_metrics['missing_percentage'] == 0 else "inverse"
            st.metric(
                "Missing Values", 
                f"{before_metrics['missing_values']:,}", 
                delta=missing_delta,
                delta_color=missing_color,
                help="Number and percentage of missing values"
            )
            
            # Duplicate rows - lower is better
            dup_delta = f"{before_metrics['duplicate_percentage']:.1f}%"
            dup_color = "normal" if before_metrics['duplicate_rows'] == 0 else "inverse"
            st.metric(
                "Duplicate Rows",
                f"{before_metrics['duplicate_rows']:,}",
                delta=dup_delta,
                delta_color=dup_color,
                help="Number and percentage of duplicate rows"
            )
            
            # Quality score - higher is better
            quality_delta = f"{before_metrics['quality_score']:.1f}/100"
            quality_color = "normal" if before_metrics['quality_score'] >= 90 else ("off" if before_metrics['quality_score'] >= 70 else "inverse")
            st.metric(
                "Quality Score",
                f"{before_metrics['quality_score']:.1f}/100",
                help="Overall data quality score (0-100)"
            )
        
        with col2:
            st.subheader("✨ After Cleaning")
            rows_removed = before_metrics['total_rows'] - after_metrics['total_rows']
            rows_delta = f"-{rows_removed}" if rows_removed > 0 else None
            st.metric(
                "Total Rows",
                f"{after_metrics['total_rows']:,}",
                delta=rows_delta,
                delta_color="inverse" if rows_removed > 0 else "off",
                help="Total number of rows after cleaning"
            )
            
            # Missing values after cleaning
            missing_after_delta = f"{after_metrics['missing_percentage']:.1f}%"
            missing_after_color = "normal" if after_metrics['missing_percentage'] == 0 else "inverse"
            st.metric(
                "Missing Values",
                f"{after_metrics['missing_values']:,}",
                delta=missing_after_delta,
                delta_color=missing_after_color,
                help="Number and percentage of missing values after cleaning"
            )
            
            # Duplicate rows after cleaning
            dup_after_delta = f"{after_metrics['duplicate_percentage']:.1f}%"
            dup_after_color = "normal" if after_metrics['duplicate_rows'] == 0 else "inverse"
            st.metric(
                "Duplicate Rows",
                f"{after_metrics['duplicate_rows']:,}",
                delta=dup_after_delta,
                delta_color=dup_after_color,
                help="Number and percentage of duplicate rows after cleaning"
            )
            
            # Quality score after cleaning
            quality_improvement = after_metrics['quality_score'] - before_metrics['quality_score']
            quality_delta_str = f"+{quality_improvement:.1f}" if quality_improvement > 0 else None
            quality_after_color = "normal" if quality_improvement > 0 else "off"
            st.metric(
                "Quality Score",
                f"{after_metrics['quality_score']:.1f}/100",
                delta=quality_delta_str,
                delta_color=quality_after_color,
                help="Overall data quality score after cleaning"
            )


PRICE_MODE_LABELS: Dict[str, str] = {
    "uploaded": "Keep uploaded amounts (reports use your min/max)",
    "scale_usd_to_inr": "Scale dollar-like values → INR (USD_TO_INR_RATE)",
    "live_shopping": "Live retail hints via SerpAPI (optional key)",
}


def _detect_column_mapping(
    df: pd.DataFrame,
) -> Tuple[Dict[str, str], bool, Optional[str], Optional[str], Optional[str]]:
    """Return mapping, whether auto-detected, and optional column names for manual UI."""
    columns = list(df.columns)
    brand_keywords = ["brand", "manufacturer", "company", "maker", "vendor"]
    price_keywords = [
        "price", "cost", "amount", "usd", "dollar", "retail",
        "inr", "rupee", "rs", "rs.", "mrp",
    ]
    feature_keywords = ["feature", "spec", "attribute", "specification", "property"]

    brand_col = next((c for c in columns if any(kw in c.lower() for kw in brand_keywords)), None)
    price_col = next((c for c in columns if any(kw in c.lower() for kw in price_keywords)), None)
    feature_col = next((c for c in columns if any(kw in c.lower() for kw in feature_keywords)), None)

    if {"brand", "price", "feature"}.issubset(set(columns)):
        return {"brand": "brand", "price": "price", "feature": "feature"}, True, None, None, None

    if brand_col and price_col and feature_col:
        return (
            {"brand": brand_col, "price": price_col, "feature": feature_col},
            True,
            brand_col,
            price_col,
            feature_col,
        )

    return (
        {
            "brand": brand_col or columns[0],
            "price": price_col or (columns[1] if len(columns) > 1 else columns[0]),
            "feature": feature_col or (columns[2] if len(columns) > 2 else columns[0]),
        },
        False,
        brand_col,
        price_col,
        feature_col,
    )


def _column_mapping_widgets(df: pd.DataFrame) -> Dict[str, str]:
    """Column mapping UI (use inside sidebar expander)."""
    columns = list(df.columns)
    mapping, auto_ok, brand_col, price_col, feature_col = _detect_column_mapping(df)

    st.markdown(
        '<p class="ts-section-lead">Link your CSV to <strong>brand</strong>, '
        "<strong>price (INR)</strong>, and <strong>feature</strong> fields.</p>",
        unsafe_allow_html=True,
    )

    if auto_ok:
        b, p, f = mapping["brand"], mapping["price"], mapping["feature"]
        st.markdown(
            f"""
            <div class="ts-pill-row">
              <span class="ts-pill">Brand · {b}</span>
              <span class="ts-pill price">Price · {p}</span>
              <span class="ts-pill feature">Feature · {f}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.caption("Auto-matched from column names. Open manual picks below if this looks wrong.")
        with st.expander("Manual column override", expanded=False):
            brand_column = st.selectbox(
                "Brand column",
                columns,
                index=columns.index(b),
                help="Manufacturer or product line (e.g. Samsung, Nike).",
            )
            price_column = st.selectbox(
                "Price column",
                columns,
                index=columns.index(p),
                help="Numeric amounts in INR (e.g. 1299.00).",
            )
            feature_column = st.selectbox(
                "Feature column",
                columns,
                index=columns.index(f),
                help="Specs or attributes (e.g. 5G+OLED, waterproof).",
            )
        return {"brand": brand_column, "price": price_column, "feature": feature_column}

    st.warning("We could not match all three columns automatically.")
    brand_column = st.selectbox(
        "Brand column",
        columns,
        index=columns.index(brand_col) if brand_col in columns else 0,
        help="Manufacturer or product line.",
    )
    price_column = st.selectbox(
        "Price column",
        columns,
        index=columns.index(price_col) if price_col in columns else 0,
        help="Numeric INR amounts.",
    )
    feature_column = st.selectbox(
        "Feature column",
        columns,
        index=columns.index(feature_col) if feature_col in columns else 0,
        help="Product features or specs.",
    )
    return {"brand": brand_column, "price": price_column, "feature": feature_column}


def create_column_mapping_sidebar(df: pd.DataFrame) -> Dict[str, str]:
    """Legacy entry — prefer render_workspace_sidebar."""
    return _column_mapping_widgets(df)


# Presets: (top_n_brands, top_n_features, gap_threshold)
ANALYSIS_PROFILES: Dict[str, Optional[tuple]] = {
    "Balanced": (10, 15, -0.5),
    "Wide coverage": (20, 30, -0.45),
    "Strict gaps only": (10, 12, -0.75),
    "Manual (sliders)": None,
}


def _analysis_parameters_widgets() -> Dict[str, Any]:
    """Analysis presets + sliders (use inside sidebar expander)."""
    st.markdown(
        '<p class="ts-section-lead">Control how many leaders appear in charts and '
        "how aggressively we flag under-served brand–feature pairs.</p>",
        unsafe_allow_html=True,
    )

    profile_labels = list(ANALYSIS_PROFILES.keys())
    profile = st.selectbox(
        "Insight profile",
        profile_labels,
        index=0,
        help="Preset bundles brands, features, and gap strictness. Choose Manual to tune freely.",
    )

    prev = st.session_state.get("_mal_prev_profile")
    if prev is None:
        st.session_state["_mal_prev_profile"] = profile
        prev = profile

    if profile != prev:
        preset = ANALYSIS_PROFILES[profile]
        if preset is not None:
            st.session_state["_mal_br"] = preset[0]
            st.session_state["_mal_ft"] = preset[1]
            st.session_state["_mal_gap"] = preset[2]
        st.session_state["_mal_prev_profile"] = profile

    if "_mal_br" not in st.session_state:
        st.session_state["_mal_br"] = 10
        st.session_state["_mal_ft"] = 15
        st.session_state["_mal_gap"] = -0.5

    st.markdown("**Chart depth**")
    col_a, col_b = st.columns(2)
    with col_a:
        st.slider(
            "Top brands",
            min_value=5,
            max_value=20,
            key="_mal_br",
            help="Brands shown in ranking charts.",
        )
    with col_b:
        st.slider(
            "Top features",
            min_value=5,
            max_value=30,
            key="_mal_ft",
            help="Feature strings ranked in charts.",
        )

    st.markdown("**Gap sensitivity**")
    st.slider(
        "Gap score cutoff",
        min_value=-1.0,
        max_value=0.0,
        step=0.05,
        key="_mal_gap",
        help="Pairs at or below this score surface as market gaps. More negative = stricter.",
    )

    gt = float(st.session_state["_mal_gap"])
    if gt <= -0.65:
        severity_note = "Strict — only deep underrepresentation."
    elif gt <= -0.5:
        severity_note = "Balanced — recommended default."
    else:
        severity_note = "Sensitive — surfaces more potential gaps."

    st.caption(
        f"Cutoff **{gt:.2f}** · {severity_note} Formula: (observed − expected) ÷ expected."
    )

    return {
        "top_n_brands": int(st.session_state["_mal_br"]),
        "top_n_features": int(st.session_state["_mal_ft"]),
        "gap_threshold": float(st.session_state["_mal_gap"]),
    }


def create_analysis_parameters_sidebar() -> Dict[str, Any]:
    """Legacy entry — prefer render_workspace_sidebar."""
    return _analysis_parameters_widgets()


def _export_options_widgets() -> Dict[str, bool]:
    st.markdown(
        '<p class="ts-section-lead">Configure report downloads on the '
        "<strong>Export</strong> tab after analysis completes.</p>",
        unsafe_allow_html=True,
    )
    include_charts = st.checkbox(
        "Embed charts in Excel & PDF",
        value=False,
        help="Adds chart images to exports (larger files).",
    )
    st.caption("CSV export is always available from the Export tab.")
    return {"include_charts": include_charts}


def create_export_options_sidebar() -> Dict[str, bool]:
    """Legacy entry — prefer render_workspace_sidebar."""
    return _export_options_widgets()


def _render_workspace_sidebar_header() -> None:
    st.sidebar.markdown(
        """
        <div class="ts-settings-hero">
          <p class="ts-settings-kicker">TrendScanner AI</p>
          <p class="ts-settings-title">Workspace</p>
          <p class="ts-settings-sub">Configure your run, then press <strong>Run full analysis</strong>.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def append_price_enrichment_notes(notes: List[str]) -> None:
    """Show post-enrichment messages under the price section."""
    if not notes:
        return
    with st.sidebar.expander("Price enrichment log", expanded=False):
        for note in notes:
            st.caption(note)


def render_workspace_sidebar(df: pd.DataFrame, uploaded_filename: str) -> WorkspaceSidebarSettings:
    """
    Branded, sectioned sidebar: columns → prices → cleaning → analysis → export → AI.
    """
    _render_workspace_sidebar_header()

    column_mapping: Dict[str, str]
    try:
        with st.sidebar.expander("① Data columns", expanded=True):
            column_mapping = _column_mapping_widgets(df.head(1))
    except Exception as e:
        st.sidebar.warning(f"Column detection issue: {e}")
        column_mapping, _, _, _, _ = _detect_column_mapping(df.head(1))

    with st.sidebar.expander("② Prices & INR", expanded=False):
        st.markdown(
            '<p class="ts-section-lead">How prices are interpreted before charts and '
            "gap scoring. Reports always respect your numeric range after transforms.</p>",
            unsafe_allow_html=True,
        )
        price_mode = st.radio(
            "Price handling",
            list(PRICE_MODE_LABELS.keys()),
            index=0,
            format_func=lambda k: PRICE_MODE_LABELS[k],
            key="_mal_price_mode",
            help="USD scale uses USD_TO_INR_RATE (default 83). Live mode needs SERPAPI_API_KEY in .env or secrets.",
        )
        if price_mode == "live_shopping":
            st.info("Optional: set **SERPAPI_API_KEY** for Google Shopping India hints.")

    with st.sidebar.expander("③ Data cleaning", expanded=False):
        st.markdown(
            '<p class="ts-section-lead">Applied immediately before agents run. '
            "Duplicate rows are always removed.</p>",
            unsafe_allow_html=True,
        )
        cleaning_strategy = st.selectbox(
            "Missing values",
            ["drop_rows", "drop_columns", "keep"],
            index=0,
            format_func=lambda x: {
                "drop_rows": "Drop rows with any missing cell",
                "drop_columns": "Drop columns that are mostly empty",
                "keep": "Keep all rows (may reduce quality)",
            }[x],
            help="Choose how sparse cells are handled in the pipeline.",
        )

    with st.sidebar.expander("④ Analysis engine", expanded=True):
        analysis_params = _analysis_parameters_widgets()

    with st.sidebar.expander("⑤ Export & reports", expanded=False):
        export_options = _export_options_widgets()

    with st.sidebar.expander("⑥ AI summary", expanded=False):
        st.markdown(
            '<p class="ts-section-lead">Optional narrative from Gemini on the '
            "<strong>AI summary</strong> tab. Requires GEMINI_API_KEY.</p>",
            unsafe_allow_html=True,
        )
        enable_llm = st.checkbox(
            "Generate AI executive summary",
            value=False,
            help="Off by default — enable when your API key is configured.",
        )

    st.sidebar.markdown(
        f"""
        <div class="ts-settings-footer">
          <strong>Active file</strong><br/>
          {uploaded_filename}
        </div>
        """,
        unsafe_allow_html=True,
    )

    return WorkspaceSidebarSettings(
        column_mapping=column_mapping,
        price_mode=price_mode,
        cleaning_strategy=cleaning_strategy,
        analysis_params=analysis_params,
        export_options=export_options,
        enable_llm=enable_llm,
    )
