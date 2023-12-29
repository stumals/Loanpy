#%%
import altair as alt
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

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
    
    @staticmethod
    def get_bar_values(patches):
        bar_dict = {}
        bar_map = {}
        i = 0
        for a in patches: 
            if a.get_x() not in bar_dict.keys():
                bar_dict[a.get_x()] = []
                if a.get_height() > 0:
                    bar_dict[a.get_x()].append({'get_x':a.get_x(), 'get_width':a.get_width(),
                                                'get_height': a.get_height(), 'get_y': a.get_y()})
                bar_map[a.get_x()] = i
                i += 1
            else:
                if a.get_height() > 0:
                    bar_dict[a.get_x()].append({'get_x':a.get_x(), 'get_width':a.get_width(),
                                                'get_height': a.get_height(), 'get_y': a.get_y()})
        bar_dict = dict((bar_map[key], value) for (key, value) in bar_dict.items())
        return bar_dict
    
    def payment(self, datalabels=3):
        df_pmt = self.df[['year', 'principal', 'interest', 'pmi', 'prop_tax', 'maint']]
        data = df_pmt.groupby('year').max().reset_index()
        totals = data.sum(axis=1)
        data = data.to_dict('Series')
        y = data['year']
        del data['year']
        bottom = np.zeros(len(y))
        fig, ax = plt.subplots()
        for k, v in data.items():
            ax.bar(y, v, label=k, bottom=bottom)
            bottom += v
        ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.1),
          fancybox=True, shadow=True, ncol=5)
        ax.set_xlabel('Year')
        ax.set_ylabel('Payment')
        ax.set_title('Monthly Total Payments by Year')  
        ax.set_ylim(ymin=0, ymax=totals.max()*1.1)
        ax.set_xlim(xmin=.5, xmax=df_pmt['year'].max()+.5)  
        
        # total data labels
        y_offset = 50
        for i, total in enumerate(totals):
            if i % datalabels == 0:
                ax.text(totals.index[i]+1, total + y_offset,
                        str(round(total/1000,1))+'K',
                        ha='center',
                        size=8
                )
        
        # stacked bar data labels
        bar_dict = LoanPlots.get_bar_values(ax.patches)
        for i in bar_dict:
            if i % datalabels == 0:
                for v in bar_dict[i]:
                    ax.text(
                        v['get_x'] + v['get_width'] / 2,
                        v['get_height']/2 + v['get_y'],
                        round(v['get_height']),
                        ha='center',
                        color='black',
                        size=6
                    )
        ax.get_yaxis().set_visible(False)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['bottom'].set_visible(False)
        ax.spines['left'].set_visible(False)
        return fig
    
    def profit(self):
        df_profit = self.df[['year', 'profit']].groupby('year').max().reset_index()
        fig, ax = plt.subplots()
        ax.plot(df_profit['year'], df_profit['profit'])
        if df_profit['profit'].min() < 0:
            ax.axhline(0, color='r')
        ax.set_xlabel('Year')
        ax.set_ylabel('Profit')
        ax.set_title('Profit by Year')
        ax.grid(True)
        return fig
    
    def home_value(self):
        df_value = self.df[['year', 'home_value']].groupby('year').max().reset_index()
        fig, ax = plt.subplots()
        ax.bar(df_value['year'], df_value['home_value'])
        # total data labels
        y_offset = 50
        # for i, total in enumerate(df_value['home_value'].to_list()):
        #     if i%3 == 0:
        #         ax.text(totals.index[i]+1, total + y_offset, str(round(total/1000,1))+'K', ha='center')
        
        #ax.grid(True)
        return fig


#%%
# d = {'asset_amt':400000, 'rate_annual': .04, 'num_years': 30, 'pmt_freq': 12, 'down_pmt':.1}
# params = LoanInput(**d)
# a = Loan(params)

# LoanPlots.profit(a)

#%%