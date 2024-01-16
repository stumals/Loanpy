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
df_ffr.iloc[-1,0].year

# %%
fred.plot(df_mgt, 'mgt rate', 'rate')
#fred.plot(df_cpi, 'cpi', 'rate')
fred.plot(df_ffr, 'ffr', 'rate')
#%%
df = df_mgt.set_index('date').merge(df_cpi.set_index('date'), how='left',
                                    left_index=True, right_index=True). \
                                    rename(columns={'value_x':'mgt_rate', 'value_y':'cpi'})
df = df.merge(df_ffr.set_index('date'), how='left',
                                    left_index=True, right_index=True). \
                                    rename(columns={'value':'ffr'})
#%%
x = df.loc[:,'ffr']
y = df.loc[:,'mgt_rate']
#%%
lm = LinReg(x, y, num_splits=10)
lm.test()
#%%
len(x.shape)

# %%
from sklearn.model_selection import TimeSeriesSplit
import sklearn.metrics as metrics
from sklearn.linear_model import LinearRegression
import statsmodels.api as sm

#%%
def regression_results(y_true, y_pred):

    # Regression metrics
    explained_variance=metrics.explained_variance_score(y_true, y_pred)
    mean_absolute_error=metrics.mean_absolute_error(y_true, y_pred) 
    mse=metrics.mean_squared_error(y_true, y_pred) 
    median_absolute_error=metrics.median_absolute_error(y_true, y_pred)
    r2=metrics.r2_score(y_true, y_pred)

    print('MSE: ', round(mse,4))
    
# %%
#x_train = x.iloc[:,:]
#y_train = y.iloc[:]
#%%
x2 = sm.add_constant(x)
lm = sm.OLS(y, x2).fit()
lm.predict([4.2,0])
#%%
tscv = TimeSeriesSplit(5)
scores = []

for i, (train_index, test_index) in enumerate(tscv.split(x)):
    print(f"Fold {i}:")
    lm = LinearRegression().fit(x.iloc[train_index].to_numpy().reshape(-1,1), y.iloc[train_index])
    preds = lm.predict(x.iloc[test_index].to_numpy().reshape(-1,1))
    mse = metrics.mean_squared_error(y.iloc[test_index], preds)
    scores.append(mse)
    print(mse)
print(np.array(scores).mean())

lm = LinearRegression().fit(x.to_numpy().reshape(-1,1), y)


#%%
x.iloc[train_index].to_numpy().reshape(-1,1) 
#%%
plt.scatter(df['ffr'], df['mgt_rate'])
#%%
plt.scatter(df['cpi'], df['mgt_rate'])
#%%
metrics.PredictionErrorDisplay(y_true=y_train, y_pred=preds).plot()
#%%
plt.hist(resids, bins=10)
#%%
sm.qqplot(resids, fit=True, line='45')
#%%

# %%
#preds_test = lm.predict(x_test)
regression_results(y_train, preds)
#%%

fig, ag = plt.subplots()
ag.plot(df_mgt['date'], (df_mgt['value'] - df_mgt['value'].min())/(df_mgt['value'].max() - df_mgt['value'].min()))
ag.plot(df_ffr['date'], (df_ffr['value'] - df_ffr['value'].min())/(df_ffr['value'].max() - df_ffr['value'].min()))
ag.plot(df_cpi['date'], (df_cpi['value'] - df_cpi['value'].min())/(df_cpi['value'].max() - df_cpi['value'].min()))

# %%
