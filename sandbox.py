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
import numpy_financial as npf
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
for i in np.linspace(0,.2,9):
    loan_inputs_new = loan_inputs.copy()
    loan_inputs_new['down_pmt'] = i
    params_new = LoanInput(**loan_inputs_new)
    loan_new = Loan(params_new)
    df_new = loan_new.amort_table_detail()
    print(df_new[df_new['period']==num_years_analysis*pmt_freq].loc[:,'profit'].values)





#%%
def calc_cum_int(asset_amt, down_pmt, rate_annual, num_years, pmt_freq, years_analysis):
    periods = np.arange(1, num_years*pmt_freq + 1, dtype=int)
    interest = -npf.ipmt(rate_annual/pmt_freq, periods, pmt_freq*num_years, asset_amt - (asset_amt*down_pmt), 0)
    return interest[:years_analysis*pmt_freq].sum()

def calc_cum_pmi()

#%%
np.linspace(0,.2,9)
#%%
for i in np.linspace(0,.2,9):
    print(calc_cum_int(asset_amt, i, rate_annual, num_years, pmt_freq, 15))

#%%
df_profit = df[['year', 'profit']].groupby('year').max().reset_index()
df_profit = df_profit[df_profit['year']<=num_years_analysis]
profit_year = df_profit[df_profit['profit'] > 0].min()
profit_year['year']

#%%
num_id = num_years_analysis*pmt_freq-1
data = {}
data['Home Appr'] = df.loc[num_id, 'home_value'] - df.loc[num_id, 'end_bal'] - df.loc[0, 'down_pmt']
data['Interest'] = -df.loc[:num_id, 'interest'].sum()
data['PMI'] = -df.loc[:num_id, 'pmi'].sum()
data['Maint'] = -df.loc[:num_id, 'maint'].sum()
data['Prop Tax'] = -df.loc[:num_id, 'prop_tax'].sum()
data['Broker Fees'] = -df.loc[num_id,'home_sale_cost'] - df.loc[0,'closing_costs']
data = pd.DataFrame(data, index=[0])
data_prof = pd.DataFrame({'value':data.sum(axis=1).values[0]}, index=['Profit']).reset_index().rename(columns={'index':'type'})
data = data.transpose().reset_index().rename(columns={'index':'type', 0:'value'})
data = data[data['value']!=0.0]
data_pos = data[data['value']>0]
data_neg = data[data['value']<0]

#%%
fig, ax = plt.subplots()
ax.bar(data_pos['type'], data_pos['value'], color='g')
ax.bar(data_neg['type'], data_neg['value'], color='r')
ax.bar(data_prof['type'], data_prof['value'], color='black')
for tick in ax.get_xticklabels():
    tick.set_rotation(45)
for a in ax.patches:
    ax.text(
        a.get_x() + a.get_width() / 2,
        a.get_height() / 2 + a.get_y(),
        str(round(a.get_height()/1000, 1)) + 'K',
        ha='center',
        color='white',
        size=7 
    )

ax.get_yaxis().set_visible(False)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.spines['bottom'].set_visible(False)
ax.spines['left'].set_visible(False)


#%%
for a in ax.patches:
    print(a)