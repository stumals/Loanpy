#%%
from loan.loan_input import LoanInput
from loan.core import Loan
from utils.utils import expected_value_cagr
import numpy as np
import pandas as pd

#%%
d = {'asset_amt':100000, 'rate_annual': .03, 'num_years': 30, 'pmt_freq': 12, 'down_pmt':.2}
params = LoanInput(**d)
a = Loan(params)

#%%
year = 15
down_pmts = np.arange(start=0, stop=.225, step=.025).tolist()
data = {'down_pmts':[], 'profits':[]}
year = 15

d = {'asset_amt':100000, 'rate_annual': .03, 'num_years': 30, 'pmt_freq': 12, 'down_pmt':.2}

def profits_down_pmts(loan_inputs: dict, year: int) -> pd.DataFrame:
    down_pmts = np.arange(start=0, stop=.225, step=.025).tolist()
    data = {'down_pmts':[], 'profits':[]}

    def get_profit(amort_table_detail: pd.DataFrame, year: int) -> float:
        df_profit = amort_table_detail[['year', 'profit']]
        df_profit = df_profit[df_profit['year']==year]
        profit = df_profit['profit'].max()
        return profit

    for down_pmt in down_pmts:
        input_new = loan_inputs.copy()
        input_new['down_pmt'] = down_pmt
        params = LoanInput(**input_new)
        loan_new = Loan(params)
        profit = get_profit(loan_new.amort_table_detail(), year)
        data['down_pmts'].append(down_pmt)
        data['profits'].append(profit)

    return pd.DataFrame(data)

#%%



