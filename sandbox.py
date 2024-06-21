#%%
import numpy as np
import pandas as pd
import os
import requests
import numpy_financial as npf
from datetime import date
from dateutil.relativedelta import relativedelta
import json
import matplotlib.pyplot as plt
import statsmodels.api as sm
from dotenv import load_dotenv, find_dotenv
load_dotenv()

from utils.utils import expected_value_cagr
from loan.loan_input import LoanInput
from loan.core import Loan
from econ.fred_econ import FRED
from models.models import Models, LinReg
from utils.utils import expected_value_cagr, affordability_calc

#%%

dwn_pmts = [.05, .10, .15, .20, .25, .30]
loan_inputs = {'asset_amt': 300000,
                   'rate_annual': .03,
                   'num_years': 30,
                   'pmt_freq': 12,
                   'down_pmt': .20,
                   'closing_cost': 0,
                   'closing_cost_finance': False,
                   'prop_tax_rate': .01,
                   'pmi_rate': .01,
                   'maint_rate': .01,
                   'home_value_appreciation': .03,
                   'home_sale_percent': .06
                   }
for d in dwn_pmts:
    loan_inputs['down_pmt'] = d
    params = LoanInput(**loan_inputs)
    loan = Loan(params)
    df = loan.amort_table_detail()
    print(df['profit'].iloc[-1])



#%%
api_key = os.environ.get('fred_api_key')            
series_url = 'https://api.stlouisfed.org/fred/series/observations'
file_type = 'json'

def get_data(series_id, name):
    params = {'series_id': series_id,
            'api_key': api_key, 
            'file_type': file_type,
            'observation_start': '2000-01-01',
            #'observation_end': end_date,
            #'frequency': frequency,
            #'aggregation_method': 'eop'
            }

    r = json.loads(requests.get(series_url, params=params).text)
    data = {'date':[], name:[]}
    f = lambda x: np.nan if i['value']=='.' else float(i['value'])
    for i in r['observations']:
        if i['value'] == '.':
            continue
        else:
            data[name].append(f(i))
            data['date'].append(pd.to_datetime(i['date']))        

    return pd.DataFrame(data)

# %%
# GDP = C + G + I + NX
# C = consumption = PCE
# G = gov exp = FGEXPND
# I = investment = GPDI
# NX = net exports = NETEXP
df_gdp = get_data('GDP', 'gdp')
df_c = get_data('PCE', 'c')
df_g = get_data('FGEXPND', 'g')
df_i = get_data('GPDI', 'i')
df_nx = get_data('NETEXP', 'nx')

# %%
df2 = df_gdp.copy()
df2 = df2.merge(df_c, how='left', on='date')
df2 = df2.merge(df_g, how='left', on='date')
df2 = df2.merge(df_i, how='left', on='date')
df2 = df2.merge(df_nx, how='left', on='date')
#%%
df3 = df2[['date','c','g','i','nx']].set_index('date')
# %%
df3.pct_change().dropna().cumsum().plot()
#%%
df3['i'].plot()