#%%
import pandas as pd
import numpy as np

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

    