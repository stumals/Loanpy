#%%
import altair as alt
import pandas as pd

from loan.core import Loan
from loan.loan_input import LoanInput
#%%
import os
os.chdir('..')
os.getcwd()

#%%
class LoanPlots:

    def payment(loan: Loan):
        df = loan.amort_table_detail()
        df_pmt = df[['year', 'principal', 'interest', 'pmi', 'prop_tax', 'maint']]
        data = df_pmt.groupby('year').mean().reset_index()

        domain = [loan.amort_table['year'].min(), loan.amort_table['year'].max()]
        return alt.Chart(data.melt('year', var_name='Type'), title='Monthly Payment by Year').mark_bar().encode(
            x = alt.X('year', scale=alt.Scale(domain=domain, nice=False), title='Year'),
            y=alt.Y('sum(value)', title='Payment'),
            color='Type'
        )
    def profit(loan: Loan):
        pass

#%%
d = {'asset_amt':100000, 'rate_annual': .03, 'num_years': 30, 'down_pmt':.2}
params = LoanInput(**d)
a = Loan(params)
a.amort_table_detail()['profit']
# %%
LoanPlots.payment(a)

# %%
num_years=15

df = a.amort_table_detail()
df = df[df['year']<=num_years]
df_profit = df[['year', 'profit']].groupby('year').max().reset_index()
domain = [df_profit['profit'].min()*.9, df_profit['profit'].max()*1.1]
alt.Chart(df_profit, title='Profit by Year').mark_line().encode(
    x=alt.X('year', title='Year'),
    y=alt.Y('profit', title='Profit', scale=alt.Scale(domain=domain))
)

# %%
df.columns
# %%
home_appr = df['home_value'][df.shape[0]-1] - a.asset_start_value
interest = -df['interest'].sum()
pmi = -df['pmi'].sum()
prop_tax = -df['prop_tax'].sum()
maint = -df['maint'].sum()
closing_costs = -df['closing_costs'].sum()
sale_cost = -df['home_sale_cost'][df.shape[0]-1]