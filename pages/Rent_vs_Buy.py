#%%
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

from loan.loan_input import LoanInput
from loan.core import Loan
from loan.plots import LoanPlots
#%%

st.set_page_config(
    layout='wide'
)

st.markdown("<h1 style='text-align: center; color: black;'>Rent vs Buy Analysis</h1>", unsafe_allow_html=True)

with st.sidebar:
    st.header("Input Parameters")
    num_years_analysis = st.number_input("Years to Analyze", min_value=1, max_value=30, value=15, step=1)
    rent = st.number_input("Starting Rent", min_value=1, value=1800, step=100)
    rent_increase = st.number_input("Annual Rent Increase", min_value=0.0, max_value=1.0, value=.03, format='%f')
    mkt_return = st.number_input("Annual Market Return", min_value=0.0, max_value=1.0, value=.10, format='%f')
    cap_gains_tax = st.number_input("Capital Gains Tax", min_value=0.0, max_value=1.0, value=.15, format='%f')

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

df_year, df_rent_year = loan.rent_vs_buy(rent, rent_increase=rent_increase, mkt_return=mkt_return,
                                         cap_gains_tax=cap_gains_tax, num_years_analysis=num_years_analysis)


def rent_vs_buy_plot(df_year, df_rent_year):
    fig, ax = plt.subplots()
    ax.plot(df_year['year'], df_year['return_total'], label='Home Owner', color='blue', linewidth=2)
    ax.plot(df_rent_year['year'], df_rent_year['return_total'], label='Renter', color='green', linewidth=2)
    #ax.set_title('Rent vs Buy Analysis', fontsize=16)
    ax.set_xlabel('Year', fontsize=14)
    ax.set_ylabel('Total Return', fontsize=14)
    ax.grid(True)
    ax.legend(fontsize=12)
    return fig

with st.container():
    col1, col2 = st.columns(2, )
    with col1:
        st.pyplot(rent_vs_buy_plot(df_year, df_rent_year), use_container_width=True)
    with col2:
        st.markdown(
            '''
            - Compares the financial outcomes of home ownership and renting.
            - Considers all payments related to home ownership (down payment, mortgage payment, taxes, etc.) and rent.
            - If the cost of home ownership is lower than renting, the difference is invested in the market. This is shown as `diff_cumulative` in the dataframe.
            - Market returns are compounded based on the Payment Frequency, which is typically monthly.
            - Capital gains tax is deducted from market returns.
            - Home Owner Total Return is calculated as the sum of profit from home ownership and market returns.
            - Renter Total Return is calculated as the market return minus rent.
            - The analysis helps in making an informed decision between renting and buying a home based on potential returns.
            '''
        )

with st.container():
    col1, col2 = st.columns(2, )
    with col1:
        st.markdown('### Home Owner Data', unsafe_allow_html=True)
        st.dataframe(df_year.style.format("{:,.0f}"))
    with col2:
        st.markdown('### Renter Data', unsafe_allow_html=True)
        st.dataframe(df_rent_year.style.format("{:,.0f}"))

