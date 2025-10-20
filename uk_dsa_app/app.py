import streamlit as st
import subprocess
import sys
from dsa.config import STYLE_CSS_PATH, DISCLAIMER_HEADER, DISCLAIMER_TEXT

st.set_page_config(page_title="UK DSA", page_icon="💼", layout="wide", initial_sidebar_state="expanded")

with open(STYLE_CSS_PATH, "r", encoding="utf-8") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

def disclaimer_gate():
    if "accepted_disclaimer" not in st.session_state:
        st.session_state.accepted_disclaimer = False
    if not st.session_state.accepted_disclaimer:
        st.header("UK Debt Sustainability Analysis")
        st.markdown(f"**{DISCLAIMER_HEADER}**")
        st.write(DISCLAIMER_TEXT)
        agree = st.checkbox("I have read and accept the disclaimer")
        if st.button("Continue") and agree:
            st.session_state.accepted_disclaimer = True
        st.stop()

def load_user_guide():
    try:
        with open("uk_dsa_app/docs/user_guide.md", "r", encoding="utf-8") as f:
            return f.read()
    except Exception:
        return "User guide not found."

def _get_build_info() -> str:
    """Return a short build info string with git commit sha and versions.
    If git is unavailable, returns a minimal string.
    """
    try:
        sha = subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], text=True).strip()
    except Exception:
        sha = "unknown"
    pyv = sys.version.split(" ")[0]
    stv = getattr(st, "__version__", "?")
    return f"Build: {sha} • Python {pyv} • Streamlit {stv}"

def home():
    st.title("Home")
    st.write("Welcome to the UK Debt Sustainability Analysis engine.")
    st.write("Use the sidebar pages to ingest data, run QA, set up the model, and produce baseline projections, stress tests, and Monte Carlo simulations. Export outputs on the Export page.")

    st.markdown("---")
    st.subheader("User Guide")
    guide = load_user_guide()
    st.download_button("Download User Guide (Markdown)", data=guide.encode("utf-8"), file_name="UK_DSA_User_Guide.md", mime="text/plain")
    if st.button("Read it all"):
        st.markdown(guide)

    st.markdown("---")
    st.caption(_get_build_info())

def main():
    disclaimer_gate()
    home()

if __name__ == "__main__":
    main()