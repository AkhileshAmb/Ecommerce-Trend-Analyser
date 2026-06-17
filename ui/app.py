"""
Streamlit UI for TrendScanner AI — guided workflow and tabbed insights.
"""

import hashlib
import json
import os
import sys
import tempfile
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

# Load .env so SMTP, Gemini, SerpAPI keys are available to the UI
try:
    from dotenv import load_dotenv

    _env_alt = project_root / "!.env"
    if _env_alt.exists():
        load_dotenv(_env_alt, override=False)
    else:
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
def cached_read_csv(file_path: str, upload_signature: str):
    """upload_signature busts cache when the user uploads a different file."""
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

current_upload_id = None
if uploaded_file is not None:
    current_upload_id = f"{uploaded_file.name}:{uploaded_file.size}"

if current_upload_id and st.session_state.get("_upload_id") != current_upload_id:
    st.session_state["_upload_id"] = current_upload_id
    st.session_state.pop("analysis_results", None)
    for _sk in list(st.session_state.keys()):
        if str(_sk).startswith("_mal_"):
            del st.session_state[_sk]

step = 1
if uploaded_file is not None:
    step = 2
if st.session_state.get("analysis_results"):
    step = 3

render_step_row(step)

temp_path = None

if uploaded_file is None:
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
        debug_log("ui/app.py", "Creating temp file", {"cwd": str(Path.cwd())}, "A")
        upload_sig = current_upload_id or "none"
        file_hash = hashlib.md5(upload_sig.encode("utf-8"), usedforsecurity=False).hexdigest()[:16]
        temp_path = Path(tempfile.gettempdir()) / f"mal_upload_{file_hash}.csv"
        with open(temp_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        debug_log(
            "ui/app.py",
            "Temp file written",
            {"temp_path": str(temp_path), "size": temp_path.stat().st_size},
            "A",
        )

        with st.spinner("Reading CSV…"):
            df = cached_read_csv(str(temp_path), upload_sig)

        st.success(f"Loaded **{len(df):,}** rows · **{len(df.columns)}** columns")

        workspace = render_workspace_sidebar(df, uploaded_file.name)
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
    finally:
        if temp_path and temp_path.exists():
            try:
                temp_path.unlink()
            except OSError:
                pass
