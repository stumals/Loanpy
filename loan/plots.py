#%%
import altair as alt
import pandas as pd
import numpy as np

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
d = {'asset_amt':400000, 'rate_annual': .04, 'num_years': 30, 'pmt_freq': 12, 'down_pmt':.1}
params = LoanInput(**d)
a = Loan(params)

LoanPlots.profit(a)

#%%
def plot_debt_vs_equity(self):
    '''
    Plots the debt and equity curves of the loan amortization table - ending balance and cumulative principal
    '''
    df = self.amort_table
    df['principal_total'] = df['principal'].cumsum()

    df2 = pd.DataFrame()
    df2['equity'] = df[['year', 'principal_total']].groupby('year').max()
    df2['debt'] = df[['year', 'end_bal']].groupby('year').min()

    i = df2[df2['equity'] > df2['debt']].index.min()
    x1 = i - 1
    y1 = df2.loc[x1, 'debt']
    x2 = i
    y2 = df2.loc[x2, 'debt']
    x3 = i - 1
    y3 = df2.loc[x3, 'equity']
    x4 = i
    y4 = df2.loc[x4, 'equity']

    @staticmethod
    def get_line(x1, x2, y1, y2):
        points = [(x1, y1), (x2, y2)]
        x_coords, y_coords = zip(*points)
        a = np.vstack([x_coords, np.ones(len(x_coords))]).T
        m, c = np.linalg.lstsq(a, y_coords, rcond=None)[0]
        x = -m
        c = -c
        y = 1
        return {'a':x, 'b':y, 'c':c}

    @staticmethod
    def get_intersection(p1, p2):
        x = (p1['b']*p2['c']-p2['b']*p1['c'])/(p1['a']*p2['b']-p2['a']*p2['b'])
        y = (p1['c']*p2['a']-p2['c']*p1['a'])/(p1['a']*p2['b']-p2['a']*p1['b'])
        return (x, y)

    p1 = get_line(x1, x2, y1, y2)
    p2 = get_line(x3, x4, y3, y4)

    intersection = get_intersection(p1, p2)[0]

    plt.plot(df[['year', 'end_bal']].groupby('year').min(), label='Debt', color='r');
    plt.plot(df[['year', 'principal_total']].groupby('year').max(), label='Equity', color='g');
    plt.axvline(intersection, color='b');
    plt.xlabel('Year');
    plt.ylabel('Amount $');
    plt.title('Debt vs Equity');
    plt.legend();
    plt.xlim(1);
    plt.ylim(0);