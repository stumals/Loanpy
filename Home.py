import streamlit as st

st.set_page_config(
    page_title="Home",
)

st.write("# Welcome to Loanpy!")

st.sidebar.success("Select a page above.")

st.markdown(
    """
    Lonapy provides tools to analyze your mortgage and related economic data.
    **Select a page to navigate**
    - Mortgage Analysis - input mortgage parameters to analyze payments and profitability.
    - Economic data - see current trends of several economic indicators affecting home buying.
    - Rent vs Buy - TBD
    - Utility - TBD
"""
)