#%%
import altair as alt
import pandas as pd
import numpy as np

from loan.core import Loan
from loan.loan_input import LoanInput
#%%
# import os
# os.chdir('..')
# os.getcwd()

#%%
class LoanPlots:

    def payment(loan: Loan):
        df = loan.amort_table_detail()
        df_pmt = df[['year', 'principal', 'interest', 'pmi', 'prop_tax', 'maint']]
        data = df_pmt.groupby('year').mean().reset_index()
        data = data.rename(columns={'principal':'Principal', 'interest':'Interest','pmi':'PMI',
                            'prop_tax':'Property Tax', 'maint':'Maintenance'})
        plt_data = data.melt('year', var_name='Type')
        min_x = loan.amort_table['year'].min()
        max_x = loan.amort_table['year'].max()
        domain = [min_x, max_x]
        return alt.Chart(plt_data, title='Monthly Payment by Year').mark_bar(size=10).encode(
            x = alt.X('year', scale=alt.Scale(domain=domain, nice=False), title='Year'),
            y=alt.Y('sum(value)', title='Payment'),
            color='Type',
            tooltip = ['Type', 'value', 'year']
        )
    def profit(loan: Loan):
        df = loan.amort_table_detail()
        data = df[['year', 'profit', 'home_value']].groupby('year').max().reset_index()
        min_x = loan.amort_table['year'].min()
        max_x = loan.amort_table['year'].max()
        domain = [min_x, max_x]

        line_profit = alt.Chart(data).mark_line().encode(
            x=alt.X('year', scale=alt.Scale(domain=domain, nice=False), title='Year'),
            y=alt.Y('profit', title='Profit'),
            tooltip=['year', 'profit']
        )
        # line_value = alt.Chart(data).mark_line().encode(
        #     x=alt.X('year', scale=alt.Scale(domain=domain, nice=False), title='Year'),
        #     y=alt.Y('home_value', title='Home Value'),
        #     tooltip=['year', 'home_value']
        # )
        # layered = alt.layer(line_profit, line_value).resolve_scale(y='independent')

        if data['profit'].min() > 0:
            return line_profit
        else:
            zero = alt.Chart(pd.DataFrame({'profit': [0]})).mark_rule(color='red').encode(y='profit')
            return line_profit + zero

#%%
# d = {'asset_amt':400000, 'rate_annual': .04, 'num_years': 30, 'pmt_freq': 12, 'down_pmt':.1}
# params = LoanInput(**d)
# a = Loan(params)

# LoanPlots.profit(a)

#%%
