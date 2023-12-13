from loan.loan_input import LoanInput
from loan.core import Loan

d = {'asset_amt':100000, 'rate_annual': .03, 'num_years': 30, 'pmt_freq': 12, 'down_pmt':.2}
params = LoanInput(**d)
a = Loan(params)

print(a.amort_table_detail())