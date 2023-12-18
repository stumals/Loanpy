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

    def __init__(self, loan: Loan, num_years: int):
        self.loan = loan
        self.num_years = num_years
        self.df = loan.amort_table_detail()
        self.df = self.df[self.df['year']<=num_years]
        min_x = self.df['year'].min()
        max_x = self.df['year'].max()
        self.domain = [min_x, max_x]

    def payment(self) -> alt.Chart:
        df_pmt = self.df[['year', 'principal', 'interest', 'pmi', 'prop_tax', 'maint']]
        data = df_pmt.groupby('year').mean().reset_index()
        data = data.rename(columns={'principal':'Principal', 'interest':'Interest','pmi':'PMI',
                            'prop_tax':'Property Tax', 'maint':'Maintenance'})
        plt_data = data.melt('year', var_name='Type')
        domain = [self.domain[0]-0.5, self.domain[1]+0.5]

        stacked_bar = alt.Chart(plt_data, title='Monthly Payment by Year').mark_bar(size=20).encode(
            x = alt.X('year', scale=alt.Scale(domain=domain, nice=False), title='Year'),
            y=alt.Y('sum(value)', title='Payment'),
            color='Type',
            tooltip=['Type', 'value', 'year', 'sum(Type):Q']
            )
        return stacked_bar
    
    def profit(self) -> alt.Chart:
        data = self.df[['year', 'profit']].groupby('year').max().reset_index()
        line_profit = alt.Chart(data, title='Profit by Year').mark_line().encode(
            x=alt.X('year', scale=alt.Scale(domain=self.domain, nice=False), title='Year'),
            y=alt.Y('profit', title='Profit'),
            tooltip=['year', 'profit']
            )

        if data['profit'].min() > 0:
            return line_profit
        else:
            zero = alt.Chart(pd.DataFrame({'profit': [0]})).mark_rule(color='red').encode(y='profit')
            return line_profit + zero
        
    def home_value(self) -> alt.Chart:
        data = self.df[['year', 'home_value']].groupby('year').max().reset_index()
        bar_chart = alt.Chart(data, title='Home Value by Year').mark_bar(size=15).encode(
            x=alt.X('year', scale=alt.Scale(domain=self.domain, nice=False), title='Year'),
            y=alt.Y('home_value', title='Home Value'),
            tooltip=['year', alt.Tooltip('home_value', format=',.0f')]
            )
        return bar_chart
    


#%%
# d = {'asset_amt':400000, 'rate_annual': .04, 'num_years': 30, 'pmt_freq': 12, 'down_pmt':.1}
# params = LoanInput(**d)
# a = Loan(params)

# LoanPlots.profit(a)

#%%