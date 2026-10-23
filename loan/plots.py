#%%
import altair as alt
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

from loan.core import Loan
from loan.loan_input import LoanInput

class LoanPlots:

    def __init__(self, loan: Loan, num_years: int):
        loan.check_years(num_years)
        self.loan = loan
        self.num_years = num_years
        self.yearly = loan.yearly_summary()
        self.yearly = self.yearly[self.yearly['year']<=num_years]
        self.domain = [1, num_years]
    
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
        cols = ['principal', 'interest', 'pmi', 'prop_tax', 'maint']
        data = self.loan.average_payment_by_year()
        data = data[data['year']<=self.num_years]
        totals = data[cols].sum(axis=1)
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
        ax.set_xlim(xmin=.5, xmax=self.num_years+.5)
        
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
        df_profit = self.yearly[['year', 'profit']]
        fig, ax = plt.subplots()
        ax.plot(df_profit.loc[:,'year'], df_profit.loc[:,'profit'])
        if df_profit.loc[:,'profit'].min() < 0:
            ax.axhline(0, color='r')
        ax.set_xlabel('Year')
        ax.set_ylabel('Profit')
        ax.set_title('Profit by Year')
        ax.grid(True)
        return fig
    
    def home_value(self, cagr):
        df_value = self.yearly[['year', 'home_value']]
        asset_start = pd.DataFrame({'year':0, 'home_value':self.loan.asset_start_value}, index=[0])
        df_value = pd.concat([asset_start, df_value]).reset_index(drop = True)
        fig, ax = plt.subplots()
        ax.bar(df_value['year'], df_value['home_value'])

        y_offset = 5000
        for i, v in enumerate(df_value['home_value']):
            if i == 0 or i == df_value.shape[0]-1:
                ax.text(df_value.index[i], v*1.06,
                        str(round(v/1000,1))+'K',
                        ha='center',
                        size=10,
                        weight='bold'
                )

        mid_patch = round(len(ax.patches)/3) 
        x = list(ax.patches)[mid_patch].get_x()
        y = list(ax.patches)[mid_patch].get_height()*1.2

        ax.text(x, y, '{}% CAGR'.format(round(cagr*100,1)), color='r', weight='bold', fontsize=10)

        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.set_xlabel('Year')
        ax.set_ylabel('Home Value')
        ax.set_title('Home Value by Year')
        ax.set_ylim(ymin=0, ymax=df_value['home_value'].max()*1.12)
        return fig
    
    def profit_waterfall(self):
        parts = self.loan.profit_breakdown(self.num_years)
        data = {}
        data['Home Appr'] = parts['appreciation']
        data['Interest'] = parts['interest']
        data['PMI'] = parts['pmi']
        data['Maint'] = parts['maint']
        data['Prop Tax'] = parts['prop_tax']
        data['Broker Fees'] = parts['home_sale_cost'] + parts['closing_costs']
        data['Profit'] = parts['profit']
        data = pd.DataFrame(data, index=[0])
        data = data.transpose().reset_index().rename(columns={'index':'type', 0:'value'})
        data = data[data['value'] != 0]

        fig, ax = plt.subplots()

        bottom = 0
        for i, t in enumerate(data['type']):
            val = data[data['type']==t].loc[:,'value'].values[0]
            if t == 'Profit':
                ax.bar(t, val, color='black')
            elif val < 0:
                ax.bar(t, val, color='red', bottom=bottom)
            else:
                ax.bar(t, val, color='green', bottom=bottom)
            bottom += val

        for tick in ax.get_xticklabels():
            tick.set_rotation(45)

        for a in ax.patches:
            ax.text(
                a.get_x() + a.get_width() / 2,
                a.get_height() / 2 + a.get_y(),
                str(round(a.get_height()/1000, 1)) + 'K',
                ha='center',
                color='white',
                size=9,
                weight='bold' 
            )
        ax.set_ylim(ymax=data['value'].max()*1.1)
        ax.set_facecolor('tan')
        ax.set_title('Profit Waterfall at Year {}'.format(self.num_years))
        ax.get_yaxis().set_visible(False)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['bottom'].set_visible(False)
        ax.spines['left'].set_visible(False)

        return fig


#%%