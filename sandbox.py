#%%
from utils.utils import expected_value_cagr
import numpy as np
import pandas as pd
import os
import requests
import numpy_financial as npf
from datetime import date
from dateutil.relativedelta import relativedelta
import json
import matplotlib.pyplot as plt
import statsmodels.api as sm
from dotenv import load_dotenv, find_dotenv
load_dotenv()

from loan.loan_input import LoanInput
from loan.core import Loan
from econ.fred_econ import FRED
from econ.models import Models, LinReg
from utils.utils import expected_value_cagr, affordability_calc

#%%
loan_inputs = {'asset_amt':300000, 'rate_annual': .03, 'num_years': 30, 'pmt_freq': 12,
             'down_pmt': .2, 'closing_cost': 0, 'closing_cost_finance': False,
             'prop_tax_rate': .01, 'pmi_rate': .01, 'maint_rate': .01,
             'home_value_appreciation': .05, 'home_sale_percent': .06}

params = LoanInput(**loan_inputs)
loan = Loan(params)

df = loan.amort_table_detail()

rent = 1300
rent_increase = .05
mkt_return = .10
cap_gains_tax = .15
num_years_analysis = 15

df_rent = pd.DataFrame(data=((1+rent_increase)**(df['year'] - 1)) * rent).rename(columns={'year':'rent'})
df_rent['year'] = df['year']

df['diff'] = df_rent['rent'] - df['all_in_pmts']
df['diff'] = df['diff'].apply(lambda x: x if x > 0 else 0)

df_rent['diff'] = df['all_in_pmts'] - df_rent['rent']
df_rent['diff'] = df_rent['diff'].apply(lambda x: x if x > 0 else 0)

df['mkt_return'] = df['diff'].cumsum() * np.array([1+(mkt_return/loan.pmt_freq)]*loan.nper).cumprod()
df['diff_cumulative'] = df['diff'].cumsum()
df['cap_gains_cumulative'] = df['mkt_return'] - df['diff_cumulative']
df['cap_gains_tax'] = df['cap_gains_cumulative'] * cap_gains_tax
df['mkt_return_net'] = df['mkt_return'] - df['cap_gains_tax']
df['return_total'] = df['mkt_return_net'] + df['profit']

df_rent['mkt_return'] = df_rent['diff'].cumsum() * np.array([1+(mkt_return/loan.pmt_freq)]*loan.nper).cumprod()
df_rent['diff_cumulative'] = df_rent['diff'].cumsum()
df_rent['cap_gains_cumulative'] = df_rent['mkt_return'] - df_rent['diff_cumulative']
df_rent['cap_gains_tax'] = df_rent['cap_gains_cumulative'] * cap_gains_tax
df_rent['mkt_return_net'] = df_rent['mkt_return'] - df_rent['cap_gains_tax']
df_rent['rent_cumulative'] = df_rent['rent'].cumsum()
df_rent['return_total'] = df_rent['mkt_return_net'] - df_rent['rent_cumulative']

cols_df = ['year', 'profit', 'diff_cumulative', 'mkt_return_net', 'return_total']
cols_rent = ['year', 'rent_cumulative', 'diff_cumulative', 'mkt_return_net', 'return_total']

df_year = df.loc[:, cols_df].groupby('year').max().reset_index()
df_rent_year = df_rent.loc[:, cols_rent].groupby('year').max().reset_index()
df_year = df_year[df_year['year']<=num_years_analysis]
df_rent_year = df_rent_year[df_rent_year['year']<=num_years_analysis]
#df_year.style.format("{:,.0f}")

fig, ax = plt.subplots()
ax.plot(df_year['year'], df_year['return_total'], label='home owner')
ax.plot(df_rent_year['year'], df_rent_year['return_total'], label='renter')
ax.legend()
# %%
