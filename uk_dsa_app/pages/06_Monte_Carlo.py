import streamlit as st
import pandas as pd
import numpy as np
from dsa.engine.calibration import calibrate_var
from dsa.engine.mc import mc_distribution
from dsa.plotting import fan_chart

def init_session():
    if "model_setup" not in st.session_state:
        st.session_state.model_setup = {}

def page():
    init_session()
    st.title("Monte Carlo Simulation")
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

    df_hist = pd.concat([g_hist.rename("nominal_g"), r_hist.rename("effective_r"), pb_hist.rename("pb_ratio")], axis=1).dropna()
    st.write("Historical calibration sample size:", len(df_hist))
    lag = st.slider("VAR lags", min_value=1, max_value=2, value=1, step=1)
    params = calibrate_var(df_hist, lags=lag)
    if not params:
        st.warning("Insufficient data to calibrate VAR. Provide longer series.")
        return

    n_paths = st.number_input("Number of Monte Carlo paths", min_value=500, max_value=100000, value=5000, step=500)
    seed = st.number_input("Random seed", min_value=1, max_value=10_000_000, value=42, step=1)
    if st.button("Run Monte Carlo"):
        qdfs = mc_distribution(b0=float(b_hist.iloc[-1]), dates=proj_idx, var_params=params,
                               map_columns={"nominal_g": params["columns"].index("nominal_g"),
                                            "effective_r": params["columns"].index("effective_r"),
                                            "pb_ratio": params["columns"].index("pb_ratio")},
                               sfa_ratio=sfa_hist.reindex(proj_idx).fillna(0.0),
                               n_paths=int(n_paths), seed=int(seed))
        if qdfs:
            fig = fan_chart({"Debt/GDP": qdfs["debt_ratio"]}, "Debt ratio fan chart (MC)", "ratio")
            st.plotly_chart(fig, use_container_width=True)
            st.session_state.model_setup["mc_qdfs"] = qdfs
            st.success("Monte Carlo completed. Proceed to OBR Comparison.")
        else:
            st.warning("Simulation failed (parameter mapping).")

if __name__ == "__main__":
    page()