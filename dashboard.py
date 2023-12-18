import streamlit as st
import pandas as pd
import numpy as np

from loan.loan_input import LoanInput
from loan.core import Loan
from loan.plots import LoanPlots

# Create a sidebar for inputs
with st.sidebar:
    st.header("Input Parameters")
    num_years_analysis = st.number_input("Years to Analyze", min_value=1, max_value=30, value=15, step=1)
    asset_amt = st.number_input("Asset Value", min_value=0, value=300000, step=25000)
    rate_annual = st.number_input("Annual Interest Rate", min_value=0.0, max_value=1.0, value=.05, step=.005, format='%f')
    home_value_appreciation = st.number_input("Annual Asset Appreciation", min_value=0.0, max_value=1.0, value=.03, step=.005, format='%f')
    num_years = st.number_input("Number of Year", min_value=1, value=30)
    pmt_freq = st.number_input("Payment Frequency", min_value=1, value=12)
    down_pmt = st.number_input("Down Payment %", min_value=0.0, max_value=1.0, value=.2, format='%f')
    closing_cost = st.number_input("Closing Cost", min_value=0, value=0)
    closing_cost_finance = st.checkbox("Finance Closing Cost", value=False)
    prop_tax_rate = st.number_input("Property Tax Rate", min_value=0.0, max_value=1.0, value=.01, step=.005, format='%f')
    pmi_rate = st.number_input("PMI Rate", min_value=0.0, max_value=1.0, value=.01, step=.005, format='%f')
    maint_rate = st.number_input("Maintenance", min_value=0.0, max_value=1.0, value=.01, step=.005, format='%f')
    home_sale_percent = st.number_input("Asset Sale % Cost", min_value=0.0, max_value=1.0, value=.06, step=.005, format='%f')

loan_inputs = {'asset_amt':asset_amt, 'rate_annual': rate_annual, 'num_years': num_years, 'pmt_freq': pmt_freq,
             'down_pmt': down_pmt, 'closing_cost': closing_cost, 'closing_cost_finance': closing_cost_finance,
             'prop_tax_rate': prop_tax_rate, 'pmi_rate': pmi_rate, 'maint_rate': maint_rate,
             'home_value_appreciation': home_value_appreciation, 'home_sale_percent': home_sale_percent}

params = LoanInput(**loan_inputs)
loan = Loan(params)


lp = LoanPlots(loan, num_years_analysis)

st.altair_chart(lp.payment(), use_container_width=True)

with st.container():
    col1, col2 = st.columns(2)
    with col1:
        st.altair_chart(lp.profit(), use_container_width=True)        
    with col2:
        st.altair_chart(lp.home_value(), use_container_width=True)


