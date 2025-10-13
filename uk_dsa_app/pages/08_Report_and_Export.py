import streamlit as st
import pandas as pd
from dsa.report import build_html_report, html_download_bytes, _fig_to_png_bytes
from dsa.plotting import line_chart
from dsa.config import IMPERIAL_LOGO_PATH

def page():
    st.title("Report and Export")
    st.write("Generate a publication-ready HTML report with figures and tables.")

    # Compose some figures from session
    ms = st.session_state.get("model_setup", {})
    figs = []
    tables = []

    if "b_ratio" in ms:
        b = ms["b_ratio"]
        fig = line_chart({"Debt/GDP": b}, "Historical debt ratio", "ratio")
        figs.append({"caption": "Historical debt-to-GDP ratio.", "png_bytes": _fig_to_png_bytes(fig)})

    if "mc_qdfs" in ms:
        qdf = ms["mc_qdfs"]["debt_ratio"]
        # Use mid as a simple figure
        st.write("Monte Carlo quantiles ready for report.")
        # Not embedding fan chart as PNG here due to image export limitations

    summary = {
        "Horizon": str(ms.get("horizon_end", "N/A")),
        "Latest debt ratio": f"{ms['b_ratio'].iloc[-1]:.1%}" if "b_ratio" in ms and not ms["b_ratio"].empty else "N/A",
    }
    credits = "Developed by: Mr. Giorgos Papachristodoulou; Mrs. Aaisha Keshari; Supervision: Prof. Alex Michaelides. October 2025."

    html = build_html_report("UK DSA Report", summary, figs, tables, credits=credits, logo_svg_path=IMPERIAL_LOGO_PATH)
    st.download_button("Download HTML report", data=html_download_bytes(html), file_name="uk_dsa_report.html", mime="text/html")

    st.success("Report generated.")

if __name__ == "__main__":
    page()