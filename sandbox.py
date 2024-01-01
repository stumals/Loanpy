#%%
import altair as alt
from loan.loan_input import LoanInput
from loan.core import Loan
from utils.utils import expected_value_cagr
import numpy as np
import pandas as pd
import os
from econ.econ_data import EconData
import requests
from io import StringIO
#%%
os.getcwd()

#%%
ed = EconData()
ed.mortgage_rates()
df = ed.df[['30yr_FRM', '15yr_FRM']]
df['30_vs_15'] = df['30yr_FRM'] - df['15yr_FRM']

#%%
df.reset_index()
#%%
ed = EconData()
ed.mortgage_rates()
df_rates = ed.df
#%%
df_rates
# %%
data = df_rates.reset_index()
data = data.melt(id_vars='date', var_name='type', value_name='rate')
line_rates = alt.Chart(data, title='Mortgage Rates').mark_line().encode(
    x=alt.X('date', title='Date'),
    y=alt.Y('rate', title='Rates'),
    color='type',
    tooltip=['date', 'type', 'rate']
    )
line_rates
#%%
import matplotlib.pyplot as plt
# %%
def plot_rates():
    df = df_rates[['30yr_FRM', '15yr_FRM']].reset_index()

    fig, ax = plt.subplots()
    ax.plot(df['date'], df['30yr_FRM'], label='30yr')
    ax.plot(df['date'], df['15yr_FRM'], label='15yr')
    ax.set_title('Mortgage Rates')
    ax.legend()
    ax.set_ylabel('Rates')
    ax.set_xlabel('Date')
    #ax.set_xticklabels(df['date'], rotation=45)
    ax.set_xlim(xmin=df['date'].min(), xmax=df['date'].max())
    ax.grid(True)
    fig.autofmt_xdate()


#ax.set_xticklabels(rotation=45);
#%%
num_years_analysis = 15
asset_amt = 300000
down_pmt = .2
rate_annual = .05
home_value_appreciation = .05
num_years = 30
pmt_freq = 12
closing_cost = 0
closing_cost_finance = False
prop_tax_rate = .01
pmi_rate = .01
maint_rate = .01
home_sale_percent = .06

loan_inputs = {'asset_amt':asset_amt, 'rate_annual': rate_annual, 'num_years': num_years, 'pmt_freq': pmt_freq,
             'down_pmt': down_pmt, 'closing_cost': closing_cost, 'closing_cost_finance': closing_cost_finance,
             'prop_tax_rate': prop_tax_rate, 'pmi_rate': pmi_rate, 'maint_rate': maint_rate,
             'home_value_appreciation': home_value_appreciation, 'home_sale_percent': home_sale_percent}

params = LoanInput(**loan_inputs)
loan = Loan(params)
df = loan.amort_table_detail()
#%%
df_profit = df[['year', 'profit']].groupby('year').max().reset_index()
fig, ax = plt.subplots()
ax.plot(df_profit['year'], df_profit['profit'])
ax.axhline(0, color='r')
ax.set_xlabel('Year')
ax.set_ylabel('Profit')
ax.set_title('Profit by Year')  
#ax.set_xlim(xmin=df_profit['year'].min(), xmax=df_profit['year'].max())






#%%
df_value = df[['year', 'home_value']].groupby('year').max().reset_index()
fig, ax = plt.subplots()
ax.bar(df_value['year'], df_value['home_value'])

# y_offset = 50
# for i, total in enumerate(df_value['home_value']):
#     if i == 0 or i == df_value.shape[1]-1:
#         ax.text(totals.index[i]+1, total + y_offset,
#                 str(round(total/1000,1))+'K',
#                 ha='center',
#                 size=8
#         )


ax.set_xlabel('Year')
ax.set_ylabel('Home Value')
ax.set_title('Home Value by Year')
ax.set_ylim(ymin=0, ymax=df_value['home_value'].max()*1.1)