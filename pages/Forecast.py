#%%
import streamlit as st
from datetime import date
from dateutil.relativedelta import relativedelta
import matplotlib.pyplot as plt
import requests
import json
import pandas as pd
import numpy as np
import os
import statsmodels.api as sm
from dotenv import load_dotenv, find_dotenv
load_dotenv()

from econ.fred_econ import FRED
from models.models import LinReg

st.set_page_config(
    layout='wide'
)

#%%
# today = str(date.today())
# prev = str(date.today() - relativedelta(years=3))
# today = '2023-12-31'
prev = '2016-09-01'
today = str(date.today())
#%%
fred = FRED()
df_mgt = fred.get_fred_data('mgt_rate', prev, today, 'm')
df_cpi = fred.get_fred_data('cpi', prev, today, 'm')
df_ffr = fred.get_fred_data('ffr', prev, today, 'm')

try:
    api_key = st.secrets["FRED_API_KEY"]
except:
    api_key = os.environ.get('fred_api_key')

series_url = 'https://api.stlouisfed.org/fred/series/observations'
params = {'series_id': 'FEDTARCTM',
        'api_key': api_key, 
        'file_type': 'json',
        'observation_start': '2024-01-01',
        }
df_ffr_fcst = pd.DataFrame()
r = json.loads(requests.get(series_url, params=params).text)
data = {'date':[], 'value':[]}
for i in r['observations']:
    if i['value'] == '.':
        continue
    else:
        data['value'].append(float(i['value']))
        data['date'].append(pd.to_datetime(i['date']))
df_ffr_fcst = pd.DataFrame(data)

df = df_mgt.set_index('date').merge(df_cpi.set_index('date'), how='left',
                                    left_index=True, right_index=True). \
                                    rename(columns={'value_x':'mgt_rate', 'value_y':'cpi'})
df = df.merge(df_ffr.set_index('date'), how='left',
                                    left_index=True, right_index=True). \
                                    rename(columns={'value':'ffr'})

x = df.loc[:,['ffr']]
y = df.loc[:,'mgt_rate']

lm = LinReg(x, y)
df_test = lm.test()
lm.train()

data = {}
dates = []
vals = []
for i, d in enumerate(df_ffr_fcst['date']):
    if i == 0:
        continue
    else:
        dates_new = pd.date_range(df_ffr_fcst['date'].iloc[i-1], df_ffr_fcst['date'].iloc[i],freq='M')
        dates.append(dates_new)
        vals_new = vals.append(np.linspace(df_ffr_fcst['value'].iloc[i-1], df_ffr_fcst['value'].iloc[i], len(dates_new)))
data['date'] = [dt for d in dates for dt in d ]
data['value'] = [vl for v in vals for vl in v]
df_ffr_new = pd.DataFrame(data).set_index('date')

df_ffr_new = sm.add_constant(df_ffr_new, has_constant='add')

preds = lm.predict(df_ffr_new).reset_index()
def rollback(row):
    return pd.offsets.MonthBegin().rollback(row)
preds['date'] = preds['date'].apply(rollback)
preds['ffr'] = df_ffr_new['value'].values

def mgt_ffr_plot(df_mgt, df_ffr, df_preds):
    fig, ax = plt.subplots()
    ax.plot(df_mgt['date'], df_mgt.iloc[:,1], label='Mgt Rate', color='blue')
    ax.plot(df_ffr['date'], df_ffr.iloc[:,1], label='FFR', color='orange')
    ax.plot(df_preds['date'], df_preds['mean'], label='Mgt Fcst', color='blue', linestyle='--')
    ax.plot(df_preds['date'], df_preds['obs_ci_lower'], label='Mgt Lower', color='red', linestyle='--')
    ax.plot(df_preds['date'], df_preds['obs_ci_upper'], label='Mgt Upper', color='red', linestyle='--')
    ax.plot(df_preds['date'], df_preds['ffr'], label='FFR Fcst', color='orange', linestyle='--')
    ax.legend()
    ax.grid(True)
    return fig

col1, col2 = st.columns(2, )

with col1:
    st.pyplot(mgt_ffr_plot(df_mgt, df_ffr, preds), use_container_width=True)
with col2:
    st.markdown(
        '''
        30 Year Mortgage Rate Forecast
        - Baseline model using linear regression with only the federal funds rate as the predicting variable
        - Mortgage rate forecast based on forecasted FFR from the St. Louis Fed
        - 95% prediction interval of rate forecast also provided
        - Model tested using cross validation with 5 folds
        - Final model built using full dataset

        '''
    )

    st.dataframe(df_test)