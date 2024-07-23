#%%
import streamlit as st
import numpy as np

from loan.loan_input import LoanInput
from loan.core import Loan
from loan.compare_down_pmts import CompareDownPayments
#%%

st.set_page_config(
    layout='wide'
)

st.markdown("<h1 style='text-align: center; color: black;'>Compare Down Payments</h1>", unsafe_allow_html=True)

with st.sidebar:
    st.header("Input Parameters")
    num_years_analysis = st.number_input("Years to Analyze", min_value=1, max_value=30, value=15, step=1)
    mkt_return = st.number_input("Annual Market Return", min_value=0.0, max_value=1.0, value=.10, format='%f')
    asset_amt = st.number_input("Asset Value", min_value=0, value=300000, step=25000)
    down_pmt = st.number_input("Down Payment %", min_value=0.0, max_value=1.0, value=.2, format='%f')
    rate_annual = st.number_input("Annual Interest Rate", min_value=0.0, max_value=1.0, value=.05, step=.005, format='%f')
    home_value_appreciation = st.number_input("Annual Asset Appreciation", min_value=0.0, max_value=1.0, value=.05, step=.005, format='%f')
    num_years = st.number_input("Number of Year", min_value=1, value=30)
    pmt_freq = st.number_input("Payment Frequency", min_value=1, value=12)
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

dwn_pmts = np.arange(0,1,.025).tolist()

cdp = CompareDownPayments(loan, dwn_pmts)
cdp.get_compare_down_pmts_data()
cdp.compare_down_pmts(mkt_return=.10)
results = cdp.get_summary(years_compare=num_years_analysis)
cdp.plot_summary(results)

with st.container():
    st.markdown(
        '''
        Details TBD
        '''
    )

with st.container():
    st.pyplot(cdp.plot_summary(results), use_container_width=True)