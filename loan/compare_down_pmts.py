#%%
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

from loan.core import Loan
from loan.loan_input import LoanInput

class CompareDownPayments():

    def __init__(self, loan: Loan, down_pmts: list) -> None:
        self.loan = loan
        self.down_pmts = down_pmts

        self.pmt_freq = loan.pmt_freq
        self.nper = loan.nper

    def get_compare_down_pmts_data(self) -> None:
        loans = {}
        for i, d in enumerate(self.down_pmts):
            loan_inputs = {'asset_amt': self.loan.asset_start_value,
                            'rate_annual': self.loan.rate_annual,
                            'num_years': self.loan.num_years,
                            'pmt_freq': self.loan.pmt_freq,
                            'down_pmt': d,
                            'closing_cost': self.loan.closing_cost,
                            'closing_cost_finance': self.loan.closing_cost_finance,
                            'prop_tax_rate': self.loan.tax,
                            'pmi_rate': self.loan.pmi,
                            'maint_rate': self.loan.maint,
                            'home_value_appreciation': self.loan.appr_rate,
                            'home_sale_percent': self.loan.home_sale_percent
                            }
            params = LoanInput(**loan_inputs)
            loan_new = Loan(params)
            df = loan_new.amort_table_detail().loc[:,['interest','all_in_pmts','profit']]
            loans[f'loan_{i}'] = (d, df)
        self.loans_dict = loans

    @staticmethod
    def get_max_all_in_pmts(loans_dict: dict) -> pd.Series:
        df = pd.DataFrame()
        for k, v in loans_dict.items():
            df[k] = v[1]['all_in_pmts']
        return df.max(axis=1)

    def compare_down_pmts(self, mkt_return: float=.10) -> None:
        max_pmt = CompareDownPayments.get_max_all_in_pmts(self.loans_dict)
        for k, v in self.loans_dict.items():
            v[1]['max_pmt'] = max_pmt
            v[1]['diff'] = v[1]['max_pmt'] - v[1]['all_in_pmts']
            v[1]['diff'] = v[1]['diff'].apply(lambda x: x if x > 0 else 0)
            v[1]['mkt_return'] = v[1]['diff'].cumsum() * np.array([1+(mkt_return/self.pmt_freq)]*self.nper).cumprod()
            v[1]['total_profit'] = v[1]['profit'] + v[1]['mkt_return']

    def get_summary(self, years_compare=15) -> pd.DataFrame:
        self.years_compare = years_compare
        results_dict = {'down_pmt':[], 'total_profit':[]}
        for k, v in self.loans_dict.items():
            results_dict['down_pmt'].append(round(v[0],2))
            results_dict['total_profit'].append(v[1]['total_profit'].iloc[self.pmt_freq*years_compare-1])
        return pd.DataFrame(results_dict)
    
    def plot_summary(self, summary_results):
        fig, ax = plt.subplots()
        x = summary_results['down_pmt']
        y = summary_results['total_profit']
        ax.plot(x, y)
        #ax.set_xticks(x, ["{0:.1f}%".format(val * 100) for val in x])
        ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: '{:.0%}'.format(x)))
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda y, _: '${:,.0f}'.format(y)))
        ax.set_ylim(ymin=summary_results['total_profit'].min()*.9, ymax=summary_results['total_profit'].max()*1.1)
        ax.set_xlim(xmin=x[0])
        ax.set_xlabel('Down Payment')
        ax.set_ylabel('Total Profit')
        ax.set_title('Total Profit by Down Payment at Year {}'.format(self.years_compare))
        ax.grid(True)

        return fig
    