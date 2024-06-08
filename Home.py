import streamlit as st

st.set_page_config(
    page_title="Home",
)

st.write("# Welcome to MortgageAnalyzer!")

st.sidebar.success("Navigate to a page using the menu above.")


st.markdown(
    """
    MortgageAnalyzer is your comprehensive mortgage analysis tool. It provides a suite of features to help you make informed decisions about your mortgage and understand the economic factors that influence the housing market. Here's what you can do:

    - **Mortgage Analysis**: Enter your mortgage parameters to get a detailed breakdown of your payments and the profitability of your mortgage over time.
    
    - **Economic Data**: Stay informed with the latest trends in key economic indicators that impact the housing market.
    
    - **Forecast**: Get a 30-year mortgage rate forecast based on a baseline linear regression model that uses the federal funds rate. More models coming soon!
    
    - **Rent vs Buy**: Compare the costs of renting versus buying a home to see which option is more financially beneficial for you.
    
    - **Utility**: (Coming Soon) Additional tools to help you with your mortgage decisions.
    """
)
