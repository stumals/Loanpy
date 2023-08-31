#%%
import altair as alt
import pandas as pd

from loan.core import Loan
from loan.loan_input import LoanInput
#%%
d = {'asset_amt':100000, 'rate_annual': .03, 'num_years': 30, 'pmt_freq': 12, 'down_pmt':.1}
params = LoanInput(**d)
a = Loan(params)
#%%
df = a.amort_table_detail()
df_pmt = df[['year', 'principal', 'interest', 'pmi', 'prop_tax', 'maint']]
data = df_pmt.groupby('year').mean().reset_index()
# x = data.index
# a = data['pmi']
# b = data['maint']
# c = data['prop_tax']
# d = data['pmt']
#%%
data.melt('year', var_name='Cost ')
#%%
a.amort_table['year'].max()

#%%
domain = [a.amort_table['year'].min(), a.amort_table['year'].max()]
alt.Chart(data.melt('year')).mark_bar().encode(
    x = alt.X('year', scale=alt.Scale(domain=[1,30], nice=False), title='Year'),
    y=alt.Y('sum(value)', title='Dollars'),
    color='variable'
)
#%%


    def plot_total_pmt(self):
        '''
        Plots a stacked bar chart showing the all in payment each month through the life of the loan
        Includes interest, principal, property tax, maintenance, and PMI
        '''
        df = self.amort_table_detail()
        df_pmt = df[['year', 'pmt', 'pmi', 'prop_tax', 'maint']]
        data = df_pmt.groupby('year').mean()
        x = data.index
        a = data['pmi']
        b = data['maint']
        c = data['prop_tax']
        d = data['pmt']
        if df_pmt['pmi'].sum() != 0:
            plt.bar(x, data['pmi'], color='y', label='PMI', bottom=b+c+d);
        plt.bar(x, data['maint'], color='r', label='Maintenance', bottom=c+d);
        plt.bar(x, data['prop_tax'], color='b', label='Property Tax', bottom=d);
        plt.bar(x, data['pmt'], color='g', label='Mortgage Payment');
        plt.legend(loc='lower left');
        plt.ylim(self.pmt*.5);
        plt.xlabel('Year');
        plt.ylabel('Payment');
        plt.title('Monthly Total Payment by Year');