import streamlit as st
from dsa.config import DEVELOPER_CREDIT

def page():
    st.title("About & Credits")
    st.write(DEVELOPER_CREDIT)
    st.write("Imperial College Business School — Department of Finance. Project date: October 2025.")
    st.write("Contact: Provide your contact details or repository link.")

if __name__ == "__main__":
    page()