import streamlit as st
import pandas as pd
from dsa.metrics import all_metrics_definition
from dsa.timeseries import DataManager
from dsa.validation import check_missing, check_outliers_zscore, plausible_bounds_check, compute_sfa
from dsa.plotting import line_chart

def init_session():
    if "metrics_def" not in st.session_state:
        st.session_state.metrics_def = all_metrics_definition()
    if "dm" not in st.session_state:
        st.session_state.dm = DataManager(st.session_state.metrics_def)

def page():
    init_session()
    st.title("Data Quality Assurance")
    st.write("Inspect missing values, outliers, and stock-flow reconciliation residuals.")

    metrics_def = st.session_state.metrics_def
    dm = st.session_state.dm

    # Required checks
    missing = dm.missing_required()
    if missing:
        st.warning(f"Missing required metrics: {', '.join(missing)}")

    # Show each available series QA
    for mid in dm.available_metrics():
        s = dm.get_series(mid)
        if s.empty:
            continue
        with st.expander(f"QA: {metrics_def[mid].display_name}"):
            st.write("Last 10 observations")
            st.dataframe(s.to_frame(name=metrics_def[mid].display_name).tail(10))
            # Missing and outliers
            mi = check_missing(s)
            oi = check_outliers_zscore(s)
            pi = plausible_bounds_check(s, mid)
            if mi:
                st.warning(f"Missing values at positions: {mi}")
            if oi:
                st.warning(f"Potential outliers (z-score>4): {oi}")
            if pi:
                st.warning(f"Values outside plausible bounds: {pi}")
            st.plotly_chart(line_chart({metrics_def[mid].display_name: s}, "Series preview", metrics_def[mid].unit), use_container_width=True)

    # SFA residual check
    if not dm.get_series("psnd_ex").empty and not dm.get_series("psnb_ex").empty:
        psnd_y = dm.resample_series(dm.get_series("psnd_ex"), target_freq="yearly", how="mean")
        psnb_y = dm.resample_series(dm.get_series("psnb_ex"), target_freq="yearly", how="mean")
        sfa = compute_sfa(psnd_y, psnb_y)
        st.subheader("Stock-Flow Adjustment (bn)")
        st.dataframe(sfa.to_frame().tail(15))
        st.plotly_chart(line_chart({"SFA (bn)": sfa}, "SFA residual (ΔDebt - PSNB)", "bn_gbp"), use_container_width=True)

    st.success("QA complete. Proceed to Model Setup.")

if __name__ == "__main__":
    page()