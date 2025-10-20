import os
import streamlit as st
import pandas as pd
import numpy as np

from dsa.metrics import all_metrics_definition
from dsa.timeseries import DataManager
from dsa.io import parse_pasted_two_column, read_csv_uploaded, read_excel_uploaded, normalize_index_to_freq, paste_matrix_to_series
from dsa.config import FREQ_DEPENDENCY_RULES, SUPPORTED_FREQS

def init_session():
    if "metrics_def" not in st.session_state:
        st.session_state.metrics_def = all_metrics_definition()
    if "dm" not in st.session_state:
        st.session_state.dm = DataManager(st.session_state.metrics_def)
    if "accepted_disclaimer" not in st.session_state:
        st.session_state.accepted_disclaimer = False

def page():
    init_session()
    st.title("Data Ingestion")
    st.write("Ingest raw series (PSND ex, PSNB ex, Debt Interest, Nominal GDP, etc.) and set each metric's frequency. Derived metrics are computed automatically and do not appear here.")
    st.info("Inputs required: provide PSND ex BoE, Nominal GDP, PSNB ex, and Debt Interest. Optional series (deflator, CPI, maturities) improve outputs. Derived items (Primary Balance, Debt/GDP, Effective rate, Nominal g) are auto-computed and thus not listed here.")

    metrics_def = st.session_state.metrics_def
    dm = st.session_state.dm

    st.subheader("Frequency selection")
    cols = st.columns(3)
    i = 0
    for mid, m in metrics_def.items():
        # Skip derived metrics in frequency selection
        if m.derived:
            continue
        if not m.user_selectable_frequency:
            dm.set_user_freq(mid, m.default_freq)
            continue
        col = cols[i % 3]
        with col:
            freq = st.selectbox(f"{m.display_name} frequency", options=m.allowed_freqs, index=m.allowed_freqs.index(m.default_freq), key=f"freq_{mid}")
            dm.set_user_freq(mid, freq)
        i += 1

    changes = dm.enforce_frequency_dependencies(FREQ_DEPENDENCY_RULES)
    if changes:
        st.info("Adjusted frequencies to respect dependencies: " + ", ".join([f"{k}→{v}" for k, v in changes.items()]))

    st.subheader("Enter data series")
    for mid, m in metrics_def.items():
        # Skip derived metrics in data entry
        if m.derived:
            continue
        with st.expander(f"{m.display_name} [{m.unit}] - {m.description}", expanded=False):
            st.caption(f"Metric ID: {mid}")
            entry_freq = dm.get_user_freq(mid)
            st.write(f"Chosen input frequency: {entry_freq}")
            st.caption("Tip: you can paste an Excel column directly; the app will align dates.")

            mode = st.radio(f"Provide {m.display_name} via", options=["Paste two-column", "Upload CSV", "Upload Excel", "Paste single-column to predefined index"], key=f"mode_{mid}", horizontal=True)
            series = None
            if mode in ("Upload CSV", "Upload Excel"):
                file = st.file_uploader(f"Upload file for {m.display_name}", type=["csv", "xlsx", "xls"], key=f"file_{mid}")
                if file is not None:
                    if file.type.endswith("csv"):
                        s = read_csv_uploaded(file.read())
                    else:
                        s = read_excel_uploaded(file.read())
                    s = normalize_index_to_freq(s, entry_freq)
                    series = s
            elif mode == "Paste two-column":
                txt = st.text_area("Paste two-column data (date, value)", height=150, key=f"paste_{mid}")
                if txt.strip():
                    s = parse_pasted_two_column(txt)
                    s = normalize_index_to_freq(s, entry_freq)
                    series = s
            else:
                if entry_freq == "yearly":
                    y0 = st.number_input("Start Year", value=1970, step=1, key=f"y0_{mid}")
                    y1 = st.number_input("End Year", value=2025, step=1, key=f"y1_{mid}")
                    idx = [str(y) for y in range(int(y0), int(y1)+1)]
                elif entry_freq == "quarterly":
                    y0 = st.number_input("Start Year", value=1990, step=1, key=f"q0_{mid}")
                    y1 = st.number_input("End Year", value=2025, step=1, key=f"q1_{mid}")
                    idx = []
                    for y in range(int(y0), int(y1)+1):
                        for q in range(1,5):
                            idx.append(f"{y}-Q{q}")
                else:
                    y0 = st.number_input("Start Year", value=2000, step=1, key=f"m0_{mid}")
                    y1 = st.number_input("End Year", value=2025, step=1, key=f"m1_{mid}")
                    idx = []
                    for y in range(int(y0), int(y1)+1):
                        for mm in range(1,13):
                            idx.append(f"{y}-{mm:02d}")
                st.write(f"Index length: {len(idx)}. Paste exactly {len(idx)} numbers below (Excel column ok).")
                txt = st.text_area("Paste values", height=150, key=f"paste1_{mid}")
                if txt.strip():
                    s = paste_matrix_to_series(txt, idx)
                    s = normalize_index_to_freq(s, entry_freq)
                    series = s

            if series is not None and not series.empty:
                st.write(f"Ingested {len(series)} observations")
                st.dataframe(series.to_frame(name=m.display_name).tail(10))
                dm.add_series(mid, series, unit=m.unit, freq=entry_freq)
            else:
                st.write("No data provided yet.")

    # Coverage summary
    st.subheader("Coverage summary")
    rows = []
    for mid, m in metrics_def.items():
        if m.derived:
            continue
        s = dm.get_series(mid)
        if not s.empty:
            rows.append({
                "metric_id": mid,
                "name": m.display_name,
                "freq": dm.get_user_freq(mid),
                "start": str(s.index.min()),
                "end": str(s.index.max()),
                "obs": len(s),
            })
    if rows:
        st.dataframe(pd.DataFrame(rows))

    st.success("Data ingestion step complete. Next: Data QA.")

if __name__ == "__main__":
    page()