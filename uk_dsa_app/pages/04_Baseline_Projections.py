import streamlit as st
import pandas as pd
from dsa.engine.dsa_math import debt_dynamics, stabilize_primary_balance, fiscal_gap, interest_to_gdp
from dsa.plotting import line_chart

def init_session():
    if "model_setup" not in st.session_state:
        st.session_state.model_setup = {}

def page():
    init_session()
    st.title("Baseline Projections")
    ms = st.session_state.model_setup
    if not {"b_ratio", "effective_r", "nominal_g", "pb_ratio", "sfa_ratio", "horizon_end"}.issubset(ms.keys()):
        st.warning("Please complete Model Setup first.")
        return

    b_hist = ms["b_ratio"].dropna()
    r_hist = ms["effective_r"].dropna()
    g_hist = ms["nominal_g"].dropna()
    pb_hist = ms["pb_ratio"].dropna()
    sfa_hist = ms["sfa_ratio"].dropna()
    horizon_end = int(ms["horizon_end"])

    # Prepare projection dates: yearly beyond last hist year
    last_year = int(b_hist.index.max().start_time.year) if not b_hist.empty else 2024
    proj_years = list(range(last_year+1, horizon_end+1))
    proj_idx = pd.period_range(start=str(proj_years[0]), end=str(proj_years[-1]), freq="Y") if proj_years else pd.PeriodIndex([], freq="Y")

    # Baseline assumptions: hold last observed r,g,pb,sfa constant
    r_proj = pd.Series(r_hist.iloc[-1] if not r_hist.empty else 0.03, index=proj_idx, name="effective_r")
    g_proj = pd.Series(g_hist.iloc[-1] if not g_hist.empty else 0.04, index=proj_idx, name="nominal_g")
    pb_proj = pd.Series(pb_hist.iloc[-1] if not pb_hist.empty else 0.0, index=proj_idx, name="pb_ratio")
    sfa_proj = pd.Series(0.0, index=proj_idx, name="sfa_ratio")

    b0 = float(b_hist.iloc[-1]) if not b_hist.empty else 0.85
    b_baseline = debt_dynamics(b0=b0, r=r_proj, g=g_proj, pb=pb_proj, sfa=sfa_proj)

    # Combine historical and baseline for charting
    b_all = pd.concat([b_hist, b_baseline])
    st.plotly_chart(line_chart({"Debt/GDP": b_all}, "Debt-to-GDP ratio baseline", "ratio"), use_container_width=True)

    # Debt-stabilizing PB
    pb_star_hist = stabilize_primary_balance(b_hist, r_hist, g_hist).dropna()
    pb_star_proj = stabilize_primary_balance(b_baseline, r_proj, g_proj)
    st.plotly_chart(line_chart({"PB* (hist)": pb_star_hist, "PB* (proj)": pb_star_proj}, "Debt-stabilizing primary balance", "ratio"), use_container_width=True)

    # Fiscal gap latest
    latest_gap = (pb_hist.iloc[-1] - pb_star_hist.iloc[-1]) if not pb_star_hist.empty and not pb_hist.empty else float("nan")
    st.metric("Latest fiscal gap (pb - pb*)", f"{latest_gap:.2%}" if pd.notna(latest_gap) else "N/A")

    st.success("Baseline projections completed. Proceed to Stress Tests.")

if __name__ == "__main__":
    page()