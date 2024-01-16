#%%
from utils.utils import expected_value_cagr
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

from loan.loan_input import LoanInput
from loan.core import Loan
from econ.fred_econ import FRED
from econ.models import Models, LinReg
from utils.utils import expected_value_cagr, affordability_calc

#%%
today = str(date.today())
#prev = str(date.today() - relativedelta(years=20))
prev = '2016-09-01'
today = '2023-12-31'
#%%
fred = FRED()
df_mgt = fred.get_fred_data(fred.fred_ids['mgt_rate'], prev, today, 'm')
df_hpi = fred.get_fred_data(fred.fred_ids['home_price_index'], prev, today, 'm')
df_ai = fred.get_fred_data(fred.fred_ids['afford_index'], prev, today, 'm')
df_cpi = fred.get_fred_data(fred.fred_ids['cpi'], prev, today, 'm')
df_ffr = fred.get_fred_data(fred.fred_ids['ffr'], prev, today, 'm')

#%%
series_url = 'https://api.stlouisfed.org/fred/series/observations'
params = {'series_id': 'FEDTARCTM',
        'api_key': os.environ.get('fred_api_key'), 
        'file_type': 'json',
        'observation_start': '2024-01-01',
        #'observation_end': end_date,
        #'frequency': frequency,
        #'aggregation_method': 'eop'
        }
df_ffr_fcst = pd.DataFrame()
r = json.loads(requests.get(series_url, params=params).text)
data = {'date':[], 'value':[]}
for i in r['observations']:
    data['value'].append(float(i['value']))
    data['date'].append(pd.to_datetime(i['date']))
df_ffr_fcst = pd.DataFrame(data)

#%%

df = df_mgt.set_index('date').merge(df_cpi.set_index('date'), how='left',
                                    left_index=True, right_index=True). \
                                    rename(columns={'value_x':'mgt_rate', 'value_y':'cpi'})
df = df.merge(df_ffr.set_index('date'), how='left',
                                    left_index=True, right_index=True). \
                                    rename(columns={'value':'ffr'})
#%%
x = df.loc[:,['cpi', 'ffr']]
y = df.loc[:,'mgt_rate']

#%%
lm = LinReg(x, y)
lm.test()
#%%
lm.train()
# %%
x_new = pd.DataFrame({'ffr':[5,4,3], 'cpi':[3.5,3,3]})
x_new = sm.add_constant(x_new)
#%%
lm.predict(x_new)
# %%
df_ffr_fcst