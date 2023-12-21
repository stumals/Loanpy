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
    - Mortgage Analysis - input mortgage parameters to analyze payments, profitability, etc.
    - Economic data - see current trends of several economic indicators affecting home buying.
    - Comparison - compares profitability of rent vs buy and 2 different buy scenarios
    - Utility - provides tools to help determine inputs in Mortgage Analysis, such as CAGR 
        (to see home apprecation rate to see desired selling price) and home affordability based on income.
"""
)