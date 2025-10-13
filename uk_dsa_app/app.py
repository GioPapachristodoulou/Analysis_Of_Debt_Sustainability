import streamlit as st
import os
from dsa.config import STYLE_CSS_PATH, IMPERIAL_LOGO_PATH, DISCLAIMER_HEADER, DISCLAIMER_TEXT

st.set_page_config(page_title="UK DSA", page_icon="💼", layout="wide", initial_sidebar_state="expanded")

# Load CSS
with open(STYLE_CSS_PATH, "r", encoding="utf-8") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

def disclaimer_gate():
    if "accepted_disclaimer" not in st.session_state:
        st.session_state.accepted_disclaimer = False
    if not st.session_state.accepted_disclaimer:
        if IMPERIAL_LOGO_PATH and os.path.exists(IMPERIAL_LOGO_PATH):
            st.image(IMPERIAL_LOGO_PATH, caption="", use_column_width=False)
        st.header("UK Debt Sustainability Analysis")
        st.markdown(f"**{DISCLAIMER_HEADER}**")
        st.write(DISCLAIMER_TEXT)
        agree = st.checkbox("I have read and accept the disclaimer")
        if st.button("Continue") and agree:
            st.session_state.accepted_disclaimer = True
        st.stop()

def home():
    st.title("Home")
    st.write("Welcome to the UK Debt Sustainability Analysis engine.")
    st.write("Use the sidebar pages to ingest data, run QA, set up the model, and produce baseline projections, stress tests, Monte Carlo simulations, and OBR comparisons. Export a full report on the Report page.")
    st.markdown("---")
    if IMPERIAL_LOGO_PATH and os.path.exists(IMPERIAL_LOGO_PATH):
        st.image(IMPERIAL_LOGO_PATH, caption="", use_column_width=False)

def main():
    disclaimer_gate()
    home()

if __name__ == "__main__":
    main()