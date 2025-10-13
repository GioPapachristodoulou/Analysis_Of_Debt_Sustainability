import streamlit as st
from dsa.config import IMPERIAL_LOGO_PATH, DEVELOPER_CREDIT

def page():
    st.title("About & Credits")
    st.image(IMPERIAL_LOGO_PATH, caption="Placeholder logo.", use_column_width=False)
    st.write(DEVELOPER_CREDIT)
    st.write("Imperial College Business School — Department of Finance. Project date: October 2025.")
    st.write("Contact: Provide your contact details or repository link.")

if __name__ == "__main__":
    page()