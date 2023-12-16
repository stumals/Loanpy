import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

from loan.loan_input import LoanInput
from loan.core import Loan
from loan.plots import LoanPlots

# Create a sidebar for inputs
with st.sidebar:
    st.header("Input Parameters")
    asset_amt = st.number_input("Asset Value", min_value=0, value=300000, step=25000)
    rate_annual = st.number_input("Annual Interest Rate", min_value=0.0, max_value=1.0, value=.05, step=.005)
    num_years = st.number_input("Number of Year", min_value=1, value=30)
    pmt_freq = st.number_input("Payment Frequency", min_value=1, value=12)
    down_pmt = st.number_input("Down Payment %", min_value=0.0, max_value=1.0, value=.2)
    closing_cost = st.number_input("Closing Cost", min_value=0, value=0)
    closing_cost_finance = st.checkbox("Finance Closing Cost", value=False)
    prop_tax_rate = st.number_input("Property Tax Rate", min_value=0.0, max_value=1.0, value=.01, step=.005)
    pmi_rate = st.number_input("PMI Rate", min_value=0.0, max_value=1.0, value=.01, step=.005)
    maint_rate = st.number_input("Maintenance", min_value=0.0, max_value=1.0, value=.01, step=.005)
    home_value_appreciation = st.number_input("Annual Asset Appreciation", min_value=0.0, max_value=1.0, value=.03, step=.005)
    home_sale_percent = st.number_input("Asset Sale % Cost", min_value=0.0, max_value=1.0, value=.06, step=.005)

loan_inputs = {'asset_amt':asset_amt, 'rate_annual': rate_annual, 'num_years': num_years, 'pmt_freq': pmt_freq,
             'down_pmt': down_pmt, 'closing_cost': closing_cost, 'closing_cost_finance': closing_cost_finance,
             'prop_tax_rate': prop_tax_rate, 'pmi_rate': pmi_rate, 'maint_rate': maint_rate,
             'home_value_appreciation': home_value_appreciation, 'home_sale_percent': home_sale_percent}

params = LoanInput(**loan_inputs)
loan = Loan(params)

#st.dataframe(loan.amort_table_detail())

st.altair_chart(LoanPlots.payment(loan))
st.altair_chart(LoanPlots.profit(loan))
