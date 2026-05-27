"""
Results UI — modern panel layout, visual hierarchy, and cohesive charts.

Uses design tokens from ui.components and avoids spamming disk writes.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any, Dict

import pandas as pd
import plotly.express as px
import streamlit as st

from llm.summarizer import summarize_agent_results
from core.currency import format_inr
from ui.components import (
    COLOR_PRIMARY,
    create_brand_pie_chart,
    create_dashboard_summary,
    create_feature_bar_chart,
    create_gap_visualization,
    create_price_boxplot,
    create_price_histogram,
    finalize_chart,
    results_panel,
)

from ui.export_utils import (
    export_to_csv,
    export_to_excel,
    export_to_json,
    export_to_pdf,
)


def _format_run_time(ts: str) -> str:
    if not ts:
        return "—"
    try:
        dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        return dt.strftime("%Y-%m-%d %H:%M")
    except ValueError:
        return ts[:19] if len(ts) >= 19 else ts


def _brand_bar_figure(brands_df: pd.DataFrame):
    fig = px.bar(
        brands_df,
        x="brand",
        y="count",
        title="Volume by brand",
        labels={"brand": "", "count": "Products"},
        color_discrete_sequence=[COLOR_PRIMARY],
    )
    fig.update_xaxes(tickangle=45)
    fig.update_traces(marker_line_width=0)
    return finalize_chart(fig, height=380)


def _results_hero(results: Dict[str, Any]) -> None:
    ts = results.get("timestamp", "")
    n = results.get("total_records", 0)
    ts_disp = _format_run_time(ts)
    st.markdown(
        f"""
        <div class="mal-rv-hero">
            <div>
                <p class="mal-rv-hero-title">Analysis ready</p>
                <p class="mal-rv-hero-meta">
                    Run · {ts_disp} · pure Python/Pandas agents · explore by tab
                </p>
            </div>
            <div>
                <span class="mal-rv-pill">{n:,} rows</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _gap_badge_class(score: float):
    if score <= -0.7:
        return "mal-badge-critical", "Major opportunity"
    if score <= -0.6:
        return "mal-badge-strong", "Strong signal"
    return "mal-badge-watch", "Worth reviewing"


def render_analysis_results(
    results: Dict[str, Any],
    cleaned_df: pd.DataFrame,
    column_mapping: Dict[str, str],
    export_options: Dict[str, Any],
    project_root: Path,
    enable_llm: bool,
) -> Dict[str, Any]:
    """
    Render analysis with modern panels: hero strip, bordered sections, badges, chart sync.
    """

    tab_ov, tab_br, tab_pr, tab_ft, tab_gp, tab_ai, tab_dl = st.tabs(
        [
            "Overview",
            "Brand analysis",
            "Pricing analysis",
            "Feature analysis",
            "Gap analysis",
            "AI summary",
            "Export",
        ]
    )

    brand_result = results["agents"]["brand"]
    pricing_result = results["agents"]["pricing"]
    feature_result = results["agents"]["feature"]
    gap_result = results["agents"]["gap"]

    # --- Overview ---
    with tab_ov:
        _results_hero(results)
        with results_panel():
            create_dashboard_summary(results, compact_title=True, short_labels=True)
        st.caption(
            "Each tab below matches **one agent** (or Overview / AI / Export). "
            "Open only the section you need."
        )

    # --- Brands ---
    with tab_br:
        st.markdown('<p class="mal-rv-section-label">Share & concentration</p>', unsafe_allow_html=True)
        st.markdown("##### Brand landscape")
        st.caption("Row share (**confidence**) approximates how much each brand occupies this extract.")

        brand_data = brand_result["results"]["top_brands"]
        brands_df = pd.DataFrame(brand_data)

        hint_l, hint_r = st.columns([2, 1])
        with hint_l:
            with st.expander("How to read", expanded=False):
                st.markdown(
                    """
                    - **Count** — listings per brand after cleaning.  
                    - **Confidence** — count ÷ total rows (share of file).  
                    Bar = volume; donut = proportional mix.
                    """
                )
        with hint_r:
            ub = brand_result["results"].get("total_unique_brands", "—")
            st.metric("Distinct brands", f"{ub}")

        with results_panel():
            try:
                view_cols = ["brand", "count", "confidence"]
                st.dataframe(
                    brands_df[view_cols],
                    use_container_width=True,
                    hide_index=True,
                )
            except KeyError:
                st.dataframe(brands_df, use_container_width=True)

        st.divider()

        ch1, ch2 = st.columns([1.15, 1])
        with ch1:
            with results_panel():
                st.plotly_chart(_brand_bar_figure(brands_df), use_container_width=True)
        with ch2:
            with results_panel():
                st.plotly_chart(create_brand_pie_chart(brands_df), use_container_width=True)

    # --- Pricing ---
    with tab_pr:
        st.markdown('<p class="mal-rv-section-label">Distribution</p>', unsafe_allow_html=True)
        st.markdown("##### Price intelligence")
        st.caption(
            "Values are shown in INR; central tendency and spread reflect whatever range is in your file — "
            "histogram shows clustering; box shows spread/outliers."
        )

        stats = pricing_result["results"]["price_statistics"]
        optimal = pricing_result["results"]["optimal_price_range"]

        with results_panel():
            r1 = st.columns(4)
            r1[0].metric("Min", format_inr(stats["min_price"]))
            r1[1].metric("Max", format_inr(stats["max_price"]))
            r1[2].metric("Mean", format_inr(stats["mean_price"]))
            r1[3].metric("Median", format_inr(stats["median_price"]))
            r2 = st.columns(2)
            r2[0].metric(
                "IQR band (Q1–Q3)",
                f"{format_inr(optimal['optimal_range_min'])} – {format_inr(optimal['optimal_range_max'])}",
                help="IQR band in INR — where most prices fall",
            )
            r2[1].metric("σ (std dev)", format_inr(stats.get("std_price", 0)))

        st.divider()

        try:
            price_column = column_mapping["price"]
            prices = cleaned_df[price_column].dropna().tolist()
            p1, p2 = st.columns(2)
            with p1:
                with results_panel():
                    st.plotly_chart(
                        create_price_histogram(prices, "Price histogram"),
                        use_container_width=True,
                    )
            with p2:
                with results_panel():
                    st.plotly_chart(
                        create_price_boxplot(prices, "Price box plot"),
                        use_container_width=True,
                    )
        except Exception as e:
            st.warning(f"Price charts unavailable: {e}")

    # --- Features ---
    with tab_ft:
        st.markdown('<p class="mal-rv-section-label">Demand signals</p>', unsafe_allow_html=True)
        st.markdown("##### Feature demand")
        st.caption("Most frequent attributes in your feature column — higher **confidence** = more rows.")

        features = feature_result["results"]["top_features"]
        features_df = pd.DataFrame(features)

        top_row = st.columns([3, 1])
        with top_row[0]:
            with results_panel():
                try:
                    st.dataframe(
                        features_df[["feature", "count", "confidence"]],
                        use_container_width=True,
                        hide_index=True,
                    )
                except KeyError:
                    st.dataframe(features_df, use_container_width=True)
        with top_row[1]:
            uf = feature_result["results"].get("total_unique_features", "—")
            st.metric("Unique features", f"{uf}")

        st.divider()

        with results_panel():
            st.plotly_chart(
                create_feature_bar_chart(features_df, horizontal=True),
                use_container_width=True,
            )

    # --- Gaps ---
    with tab_gp:
        st.markdown('<p class="mal-rv-section-label">Opportunity scan</p>', unsafe_allow_html=True)
        st.markdown("##### Market gaps")
        st.caption(
            "Underrepresented brand × feature mixes vs expectation — negative **gap score** = opportunity."
        )

        gaps = gap_result["results"]["top_gaps"]
        total_combinations = gap_result["results"]["total_combinations"]
        gaps_count = gap_result["results"]["identified_gaps_count"]
        confidence = gap_result.get("confidence", 0.0)
        threshold = gap_result["results"].get("gap_threshold", -0.5)

        with results_panel():
            g1, g2, g3 = st.columns(3)
            g1.metric("Pairs scanned", f"{total_combinations}")
            g2.metric("Below cutoff", f"{gaps_count}", help=f"Score ≤ {threshold}")
            g3.metric("Agent confidence", f"{confidence * 100:.1f}%")

        with st.expander("Interpreting scores", expanded=False):
            st.markdown(
                f"""
                **Gap score** ≈ (observed − expected) ÷ expected.  
                **≤ {threshold}** → flagged. More negative = deeper hole vs expectation.
                """
            )

        if gaps:
            gap_viz = create_gap_visualization(gaps, top_n=10)
            if gap_viz:
                with results_panel():
                    st.plotly_chart(gap_viz, use_container_width=True)

            for i, gap in enumerate(gaps, 1):
                gap_pct = abs(gap["gap_score"] * 100)
                badge_cls, badge_lbl = _gap_badge_class(gap["gap_score"])
                opp = max(1, int(gap["expected_count"] - gap["observed_count"]))
                st.markdown(
                    f"""
                    <div class="mal-gap-card">
                        <span class="mal-badge {badge_cls}">{badge_lbl}</span>
                        &nbsp;&nbsp;<strong>#{i}</strong>
                        &nbsp;·&nbsp; <code>{gap["brand"]}</code>
                        &nbsp;×&nbsp; <code>{gap["feature"]}</code>
                        <p class="mal-gap-line">
                            Score <strong>{gap["gap_score"]:.4f}</strong>
                            (~{gap_pct:.0f}% below expected) ·
                            observed <strong>{gap["observed_count"]}</strong>,
                            expected <strong>{gap["expected_count"]:.1f}</strong>
                        </p>
                        <p class="mal-gap-note">
                            Rough fill-in target: ~{opp} listing(s) in this slice.
                        </p>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
        else:
            st.success(
                "No pairs crossed your cutoff — distribution looks balanced for this model's assumptions."
            )

    # --- AI summary (its own tab) ---
    with tab_ai:
        st.markdown('<p class="mal-rv-section-label">Large language model</p>', unsafe_allow_html=True)
        st.markdown("##### AI summary")
        st.caption(
            "Optional Gemini narrative — one call per generation. Numbers always come from the agent tabs."
        )

        cached = results.get("llm_summary")
        with results_panel():
            if enable_llm:
                if cached and cached.get("status") == "success":
                    st.success("Summary cached for this run.")
                    st.markdown(cached["summary"])
                    if st.button("Regenerate summary", key="rv_llm_regen"):
                        results["llm_summary"] = None
                        st.rerun()
                else:
                    if st.button("Generate summary", type="primary", key="rv_llm_gen"):
                        with st.spinner("Calling Gemini…"):
                            try:
                                agent_outputs = [
                                    results["agents"]["brand"],
                                    results["agents"]["pricing"],
                                    results["agents"]["feature"],
                                    results["agents"]["gap"],
                                ]
                                summary_result = summarize_agent_results(agent_outputs)
                                if summary_result.get("status") == "success":
                                    st.markdown(summary_result["summary"])
                                    results["llm_summary"] = summary_result
                                else:
                                    st.warning(summary_result.get("error", "Error")[:320])
                                    results["llm_summary"] = None
                            except Exception as e:
                                st.error(str(e)[:220])
                                results["llm_summary"] = None
            else:
                if cached and cached.get("status") == "success":
                    st.info(
                        "Turn on **Generate AI executive summary** under **AI summary** in Workspace to view or regenerate."
                    )
                else:
                    st.info(
                        "Enable **AI summary** in Workspace, then use **Generate summary** here."
                    )

    # --- Export only ---
    with tab_dl:
        st.markdown('<p class="mal-rv-section-label">Download</p>', unsafe_allow_html=True)
        st.markdown(
            '<p class="mal-export-heading">Export files</p>',
            unsafe_allow_html=True,
        )
        st.markdown(
            '<p class="mal-export-blurb">Pull structured outputs. '
            "<strong>Embed charts in Excel & PDF</strong> under <strong>Export & reports</strong> in Workspace affects Excel and PDF.</p>",
            unsafe_allow_html=True,
        )

        base_filename = f"market_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        include_llm = bool(results.get("llm_summary"))
        incl_charts = export_options.get("include_charts", False)

        json_payload = export_to_json(results, include_llm=include_llm)
        csv_payload = export_to_csv(results)

        with results_panel():
            er1, er2 = st.columns(2)
            er3, er4 = st.columns(2)
            try:
                excel_data = export_to_excel(results, include_charts=incl_charts)
                pdf_data = export_to_pdf(results, include_charts=incl_charts)
                with er1:
                    st.download_button(
                        "JSON — full structure",
                        json_payload,
                        file_name=f"{base_filename}.json",
                        mime="application/json",
                        use_container_width=True,
                        key="rv_dl_json",
                    )
                with er2:
                    st.download_button(
                        "CSV — flat tables",
                        csv_payload,
                        file_name=f"{base_filename}.csv",
                        mime="text/csv",
                        use_container_width=True,
                        key="rv_dl_csv",
                    )
                with er3:
                    st.download_button(
                        "Excel — workbook",
                        excel_data,
                        file_name=f"{base_filename}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True,
                        key="rv_dl_xlsx",
                    )
                with er4:
                    st.download_button(
                        "PDF — report",
                        pdf_data,
                        file_name=f"{base_filename}.pdf",
                        mime="application/pdf",
                        use_container_width=True,
                        key="rv_dl_pdf",
                    )
            except ImportError as e:
                st.error(f"Missing dependency: {e}")
                st.info("`pip install openpyxl reportlab`")
            except Exception as e:
                st.error(f"Export failed: {e}")

        st.markdown('<div class="ts-export-save-section"></div>', unsafe_allow_html=True)
        st.caption("Optional — save a copy into the project `reports/` folder on this machine.")
        _sp_l, _sp_c, _sp_r = st.columns([1, 1.4, 1])
        with _sp_c:
            report_stub = f"market_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            if st.button(
                "Save JSON to reports",
                key="rv_save_reports",
                type="secondary",
                use_container_width=True,
                help="Writes the full JSON payload into the reports/ directory.",
            ):
                reports_dir = project_root / "reports"
                reports_dir.mkdir(exist_ok=True)
                report_path = reports_dir / report_stub
                try:
                    report_path.write_text(
                        export_to_json(results, include_llm=include_llm),
                        encoding="utf-8",
                    )
                    st.success(f"Saved to `{report_path}`")
                except Exception as err:
                    st.warning(str(err))

    st.session_state["analysis_results"] = results
    return results
