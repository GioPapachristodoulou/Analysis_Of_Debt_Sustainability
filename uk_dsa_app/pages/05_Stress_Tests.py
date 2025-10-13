import streamlit as st
import pandas as pd
from dsa.engine.dsa_math import debt_stress_response
from dsa.engine.scenarios import DEFAULT_SCENARIOS
from dsa.plotting import line_chart

def init_session():
    if "model_setup" not in st.session_state:
        st.session_state.model_setup = {}

def page():
    init_session()
    st.title("Deterministic Stress Tests")
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

    last_year = int(b_hist.index.max().start_time.year) if not b_hist.empty else 2024
    proj_years = list(range(last_year+1, horizon_end+1))
    proj_idx = pd.period_range(start=str(proj_years[0]), end=str(proj_years[-1]), freq="Y") if proj_years else pd.PeriodIndex([], freq="Y")

    r_proj = pd.Series(r_hist.iloc[-1] if not r_hist.empty else 0.03, index=proj_idx, name="effective_r")
    g_proj = pd.Series(g_hist.iloc[-1] if not g_hist.empty else 0.04, index=proj_idx, name="nominal_g")
    pb_proj = pd.Series(pb_hist.iloc[-1] if not pb_hist.empty else 0.0, index=proj_idx, name="pb_ratio")
    sfa_proj = pd.Series(0.0, index=proj_idx, name="sfa_ratio")

    b0 = float(b_hist.iloc[-1]) if not b_hist.empty else 0.85

    st.subheader("Select scenario")
    names = [sc.name for sc in DEFAULT_SCENARIOS] + ["Custom"]
    choice = st.selectbox("Scenario", options=names)
    if choice == "Custom":
        r_pp = st.number_input("Shock to effective r (pp)", value=0.0, step=0.25)/100.0
        g_pp = st.number_input("Shock to nominal g (pp)", value=0.0, step=0.25)/100.0
        pb_pp = st.number_input("Shock to PB (% GDP)", value=0.0, step=0.1)/100.0
        sfa_pp = st.number_input("Shock to SFA ratio (% GDP)", value=0.0, step=0.1)/100.0
        shocks = {"r_pp": r_pp, "g_pp": g_pp, "pb_pp": pb_pp, "sfa_ratio_pp": sfa_pp}
    else:
        sc = [s for s in DEFAULT_SCENARIOS if s.name == choice][0]
        shocks = {"r_pp": sc.r_pp, "g_pp": sc.g_pp, "pb_pp": sc.pb_pp, "sfa_ratio_pp": sc.sfa_ratio_pp}

    b_stress = debt_stress_response(b0=b0, r=r_proj, g=g_proj, pb=pb_proj, sfa=sfa_proj, shocks=shocks)
    st.plotly_chart(line_chart({"Baseline": pd.concat([b_hist, b_stress*0+pd.NA]).dropna(), "Stressed": pd.concat([b_hist.iloc[-1:]*0+pd.NA, b_stress]).dropna()}, f"Debt-to-GDP under {choice}", "ratio"), use_container_width=True)

    st.success("Stress test completed. Proceed to Monte Carlo.")

if __name__ == "__main__":
    page()