"""
Streamlit UI for TrendScanner AI — guided workflow and tabbed insights.
"""

import io
import json
import os
import sys
from contextlib import nullcontext
from datetime import datetime
from pathlib import Path

import pandas as pd
import streamlit as st

# #region agent log
DEBUG_LOG_PATH = Path(__file__).parent.parent / ".cursor" / "debug.log"


def debug_log(location, message, data=None, hypothesis_id=None):
    try:
        log_entry = {
            "timestamp": datetime.now().timestamp() * 1000,
            "location": location,
            "message": message,
            "data": data or {},
            "sessionId": "debug-session",
            "runId": "run1",
            "hypothesisId": hypothesis_id,
        }
        DEBUG_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(DEBUG_LOG_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry) + "\n")
    except Exception:
        pass


# #endregion

project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Load .env so SMTP, Groq, SerpAPI keys are available to the UI
try:
    from dotenv import load_dotenv

    _env_alt = project_root / "!.env"
    if _env_alt.exists():
        load_dotenv(_env_alt, override=False)
    load_dotenv(project_root / ".env", override=False)
except ImportError:
    pass

from core.ingestion import read_csv_file
from core.validator import validate_and_clean
from core.orchestrator import run_all_agents
from core.price_enrichment import apply_price_enrichment

from ui.components import (
    apply_app_styles,
    append_price_enrichment_notes,
    display_data_quality_metrics,
    render_home_hero,
    render_step_row,
    render_workspace_sidebar,
)
from ui.views import render_analysis_results

# Cache expensive IO / transforms
@st.cache_data
def cached_read_csv_bytes(file_bytes: bytes, upload_signature: str):
    """Read uploaded CSV bytes; upload_signature busts cache when the file changes."""
    df = pd.read_csv(io.BytesIO(file_bytes), encoding="utf-8")
    if df.empty:
        raise pd.errors.EmptyDataError("CSV file is empty")
    return df


def _persist_upload(uploaded_file) -> str:
    """Store upload in session so reruns (buttons, downloads) keep the dataset."""
    sig = f"{uploaded_file.name}:{uploaded_file.size}"
    if st.session_state.get("_upload_id") != sig:
        st.session_state["_upload_id"] = sig
        st.session_state.pop("analysis_results", None)
        for _sk in list(st.session_state.keys()):
            if str(_sk).startswith("_mal_"):
                del st.session_state[_sk]
    st.session_state["uploaded_csv_bytes"] = uploaded_file.getvalue()
    st.session_state["uploaded_csv_name"] = uploaded_file.name
    return sig


def _active_upload() -> tuple[bytes | None, str | None, str | None]:
    """Return (bytes, filename, signature) for the current session upload."""
    data = st.session_state.get("uploaded_csv_bytes")
    if not data:
        return None, None, None
    return (
        data,
        st.session_state.get("uploaded_csv_name", "upload.csv"),
        st.session_state.get("_upload_id"),
    )


@st.cache_data
def cached_read_csv(file_path: str, upload_signature: str):
    """Legacy path-based reader (kept for compatibility)."""
    return read_csv_file(file_path)


@st.cache_data
def cached_validate_and_clean(
    df: pd.DataFrame,
    cleaning_strategy: str,
    remove_dupes: bool,
    upload_signature: str,
    pipeline_variant: str = "",
):
    return validate_and_clean(df, cleaning_strategy=cleaning_strategy, remove_dupes=remove_dupes)


st.set_page_config(
    page_title="TrendScanner AI",
    layout="wide",
    initial_sidebar_state="expanded",
)

apply_app_styles()

# Session defaults
if "column_mapping" not in st.session_state:
    st.session_state.column_mapping = {"brand": "brand", "price": "price", "feature": "feature"}
if "analysis_params" not in st.session_state:
    st.session_state.analysis_params = {"top_n_brands": 10, "top_n_features": 15, "gap_threshold": -0.5}
if "export_options" not in st.session_state:
    st.session_state.export_options = {"include_charts": False}

# --- Header (single HTML block = title sits ON the gradient, always readable) ---
render_home_hero()

uploaded_file = st.file_uploader(
    "CSV file",
    type=["csv"],
    help="Include columns for brand name, numeric price in INR, and feature text.",
)

if uploaded_file is not None:
    _persist_upload(uploaded_file)

csv_bytes, csv_name, upload_sig = _active_upload()

if upload_sig and st.session_state.get("analysis_results"):
    step = 3
elif upload_sig:
    step = 2
else:
    step = 1

render_step_row(step)

if not upload_sig:
    st.markdown(
        """
        <div class="mal-upload-callout">
          <strong style="font-size:1.1rem;">Drop your CSV here</strong><br/>
          <span>Brand · price · feature columns — open <strong>Workspace</strong> in the sidebar → run analysis.</span>
        </div>
        """,
        unsafe_allow_html=True,
    )
else:
    try:
        if uploaded_file is None:
            st.caption(f"Active file: **{csv_name}** — choose a new CSV above to replace.")

        debug_log("ui/app.py", "Loading CSV from session", {"name": csv_name}, "A")

        with st.spinner("Reading CSV…"):
            df = cached_read_csv_bytes(csv_bytes, upload_sig or "none")

        st.success(f"Loaded **{len(df):,}** rows · **{len(df.columns)}** columns")

        workspace = render_workspace_sidebar(df, csv_name or "upload.csv")
        column_mapping = workspace["column_mapping"]
        price_mode = workspace["price_mode"]
        cleaning_strategy = workspace["cleaning_strategy"]
        analysis_params = workspace["analysis_params"]
        export_options = workspace["export_options"]
        enable_llm = workspace["enable_llm"]
        st.session_state.column_mapping = column_mapping
        st.session_state.analysis_params = analysis_params
        st.session_state.export_options = export_options

        model_col = "model" if "model" in df.columns else None

        def _serpapi_key():
            k = os.environ.get("SERPAPI_API_KEY")
            if k:
                return k
            try:
                return str(st.secrets["SERPAPI_API_KEY"])
            except Exception:
                return None

        if "_mal_serp_price_cache" not in st.session_state:
            st.session_state["_mal_serp_price_cache"] = {}

        enrich_key = (
            f"{upload_sig}|{price_mode}|{column_mapping['brand']}|"
            f"{column_mapping['price']}|{column_mapping['feature']}|{model_col or ''}"
        )
        use_cached_enrichment = (
            price_mode == "live_shopping"
            and st.session_state.get("_mal_enrich_key") == enrich_key
            and st.session_state.get("_mal_enriched_df") is not None
        )

        if use_cached_enrichment:
            df_work = st.session_state["_mal_enriched_df"]
            _price_notes = st.session_state.get("_mal_price_notes", [])
        else:
            enrich_spinner = (
                "Fetching live retail prices (parallel SerpAPI)…"
                if price_mode == "live_shopping"
                else None
            )
            with st.spinner(enrich_spinner) if enrich_spinner else nullcontext():
                df_work, _price_notes = apply_price_enrichment(
                    df,
                    column_mapping["brand"],
                    column_mapping["price"],
                    column_mapping["feature"],
                    mode=price_mode,
                    model_column=model_col,
                    serpapi_key=_serpapi_key(),
                    cache=st.session_state["_mal_serp_price_cache"],
                )
            if price_mode == "live_shopping":
                st.session_state["_mal_enriched_df"] = df_work
                st.session_state["_mal_enrich_key"] = enrich_key
                st.session_state["_mal_price_notes"] = _price_notes
        append_price_enrichment_notes(_price_notes)

        left, right = st.columns([1.6, 1])
        with left:
            st.subheader("Preview")
            st.dataframe(df_work.head(25), use_container_width=True, hide_index=True)
        with right:
            st.subheader("File snapshot")
            st.metric("Rows", f"{len(df_work):,}")
            st.metric("Columns", len(df.columns))
            st.metric(
                "Approx. memory",
                f"{df_work.memory_usage(deep=True).sum() / 1024 ** 2:.2f} MB",
            )

        with st.spinner("Cleaning data…"):
            cleaned_df = cached_validate_and_clean(
                df_work,
                cleaning_strategy=cleaning_strategy,
                remove_dupes=True,
                upload_signature=upload_sig,
                pipeline_variant=f"{price_mode}|{model_col or ''}",
            )

        dropped = len(df_work) - len(cleaned_df)
        st.caption(
            f"After cleaning: **{len(cleaned_df):,}** rows kept · **{dropped:,}** rows removed"
        )

        display_data_quality_metrics(df_work, cleaned_df)

        run = st.button(
            "Run full analysis",
            type="primary",
            use_container_width=True,
            key="mal_run_analysis",
        )

        if run:
            progress = st.progress(0)
            status = st.empty()
            results = None
            try:
                status.text("Running agents…")
                progress.progress(15)
                debug_log(
                    "ui/app.py:run",
                    "Before run_all_agents",
                    {
                        "cleaned_df_rows": len(cleaned_df),
                        "column_mapping": column_mapping,
                        "analysis_params": analysis_params,
                    },
                    "C",
                )
                progress.progress(55)
                results = run_all_agents(
                    cleaned_df,
                    brand_column=column_mapping["brand"],
                    price_column=column_mapping["price"],
                    feature_column=column_mapping["feature"],
                    top_n_brands=analysis_params["top_n_brands"],
                    top_n_features=analysis_params["top_n_features"],
                    gap_threshold=analysis_params["gap_threshold"],
                )
                debug_log(
                    "ui/app.py:run",
                    "After run_all_agents",
                    {"results_keys": list(results.keys())},
                    "C",
                )
                progress.progress(100)
                status.empty()
                progress.empty()
                st.session_state["analysis_results"] = results
                st.success("Analysis finished — open the tabs below.")
            except Exception as e:
                progress.empty()
                status.empty()
                st.error(f"Analysis failed: {e}")
                debug_log("ui/app.py:error", "Analysis error", {"error": str(e)}, "E")

        results = st.session_state.get("analysis_results")
        if results:
            st.markdown(
                '<div id="mal-results-dashboard"></div>',
                unsafe_allow_html=True,
            )
            st.markdown(
                '<p class="mal-rv-section-label" style="margin-top:1.5rem;">Live analytics</p>',
                unsafe_allow_html=True,
            )
            st.markdown(
                '<p class="mal-dashboard-title">Results dashboard</p>',
                unsafe_allow_html=True,
            )
            render_analysis_results(
                results,
                cleaned_df,
                column_mapping,
                export_options,
                project_root,
                enable_llm,
            )

    except Exception as e:
        debug_log(
            "ui/app.py:outer",
            "Exception",
            {"error": str(e), "type": type(e).__name__},
            "E",
        )
        st.error(f"Something went wrong: {e}")
