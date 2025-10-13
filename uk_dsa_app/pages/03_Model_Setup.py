import streamlit as st
import pandas as pd
import numpy as np
from dsa.metrics import all_metrics_definition
from dsa.timeseries import DataManager
from dsa.engine.calibration import compute_effective_r_from_interest_and_debt, implied_pb_ratio
from dsa.engine.dsa_math import stock_flow_adjustment_ratio
from dsa.config import DEFAULT_HORIZON

def init_session():
    if "metrics_def" not in st.session_state:
        st.session_state.metrics_def = all_metrics_definition()
    if "dm" not in st.session_state:
        st.session_state.dm = DataManager(st.session_state.metrics_def)
    if "model_setup" not in st.session_state:
        st.session_state.model_setup = {}

def page():
    init_session()
    st.title("Model Setup")
    st.write("Select modeling horizon and compute derived series for r, g, PB, and SFA ratios.")

    dm = st.session_state.dm
    metrics = st.session_state.metrics_def

    horizon_end = st.number_input("Projection horizon end year", min_value=2026, max_value=2050, value=DEFAULT_HORIZON, step=1)
    st.session_state.model_setup["horizon_end"] = int(horizon_end)

    # Derived baseline series (convert via timestamp then back to periods)
    psnd = dm.resample_series(dm.get_series("psnd_ex"), target_freq="yearly", how="mean")
    gdp = dm.resample_series(dm.get_series("gdp_nominal"), target_freq="yearly", how="mean")
    psnb = dm.resample_series(dm.get_series("psnb_ex"), target_freq="yearly", how="mean")
    di = dm.resample_series(dm.get_series("debt_interest"), target_freq="yearly", how="mean")

    if psnd.empty or gdp.empty or psnb.empty or di.empty:
        st.warning("Required core series missing. Provide PSND ex, GDP nominal, PSNB ex, and Debt Interest.")
        return

    eff_r = compute_effective_r_from_interest_and_debt(di, psnd)
    g = gdp.pct_change().rename("nominal_g")
    pb_ratio = implied_pb_ratio(psnb, di, gdp)
    sfa_ratio = stock_flow_adjustment_ratio(psnd, psnb, gdp)

    # Save to session
    st.session_state.model_setup["effective_r"] = eff_r
    st.session_state.model_setup["nominal_g"] = g
    st.session_state.model_setup["pb_ratio"] = pb_ratio
    st.session_state.model_setup["sfa_ratio"] = sfa_ratio
    st.session_state.model_setup["b_ratio"] = (psnd / gdp).rename("debt_ratio")

    st.subheader("Derived series preview")
    df_prev = pd.concat([st.session_state.model_setup["b_ratio"],
                         eff_r, g, pb_ratio, sfa_ratio], axis=1).dropna()
    st.dataframe(df_prev.tail(10))

    st.success("Model setup computed. Proceed to Baseline Projections.")

if __name__ == "__main__":
    page()