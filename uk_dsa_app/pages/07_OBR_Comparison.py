import streamlit as st
import pandas as pd
from dsa.io import load_obr_csv
from dsa.plotting import line_chart

def page():
    st.title("OBR Comparison")
    st.write("Upload OBR projections (CSV) and map to app metrics to compare paths. Use the provided sample mapping CSV to align fields.")
    file = st.file_uploader("Upload OBR CSV", type=["csv"])
    if file is None:
        st.info("Provide OBR projections CSV. You can build it from OBR's EFO tables and adapt columns to: metric_id, year, value.")
        return
    df = load_obr_csv(file.read())
    st.dataframe(df.head(10))
    # Expect columns metric_id, year, value
    if not {"metric_id", "year", "value"}.issubset(df.columns):
        st.warning("CSV must include columns: metric_id, year, value.")
        return
    # Example: metric_id values: 'debt_ratio', 'deficit_ratio', 'interest_ratio'
    st.subheader("Select metric to compare")
    metric_choice = st.selectbox("Metric", options=sorted(df["metric_id"].unique()))
    dfm = df[df["metric_id"] == metric_choice].copy()
    dfm["period"] = pd.PeriodIndex(dfm["year"].astype(int), freq="Y")
    s_obr = pd.Series(dfm["value"].values, index=dfm["period"].values, name="OBR")
    # Compare to our baseline or MC median if available
    s_app = None
    ms = st.session_state.get("model_setup", {})
    if metric_choice == "debt_ratio":
        b_hist = ms.get("b_ratio", pd.Series(dtype=float))
        b_proj = None
        # Not stored explicitly; reconstruct baseline from last page? We'll just show hist if not present
        s_app = b_hist
    # If Monte Carlo median available
    if "mc_qdfs" in ms and metric_choice == "debt_ratio":
        qdf = ms["mc_qdfs"]["debt_ratio"]
        s_med = qdf["50"]
        s_med.name = "MC median"
        st.plotly_chart(line_chart({"OBR": s_obr, "MC median": s_med}, "OBR vs App (debt ratio)", "ratio"), use_container_width=True)
    else:
        st.plotly_chart(line_chart({"OBR": s_obr, "App": s_app}, "OBR vs App", "value"), use_container_width=True)

if __name__ == "__main__":
    page()