import streamlit as st
from dsa.legal import disclaimer_text, terms_text, privacy_text, ogl_attribution_text

def page():
    st.title("Legal & Attributions")
    st.subheader("Disclaimer")
    st.text(disclaimer_text())
    st.subheader("Terms of Use")
    st.text(terms_text())
    st.subheader("Privacy")
    st.text(privacy_text())
    st.subheader("Attribution")
    st.text(ogl_attribution_text())
    st.info("Replace placeholder logo only with authorized asset if you have explicit permission.")

if __name__ == "__main__":
    page()