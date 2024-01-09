#%%
import os
import requests
import pandas as pd
import json
import matplotlib.pyplot as plt

from dotenv import load_dotenv, find_dotenv
load_dotenv()

#%%
class FRED:
    def __init__(self):
        self.api_key = os.environ.get('fred_api_key')
        self.series_url = 'https://api.stlouisfed.org/fred/series/observations'
        self.file_type = 'json'
        self.fred_ids = {'mgt_rate': 'MORTGAGE30US',
                         'cpi': 'USACPALTT01CTGYM',
                         'sofr': 'SOFR',
                         'ffr': 'DFEDTARU',
                         'ffr_fcst': 'FEDTARCTM',
                         'usdx': 'DTWEXBGS',
                         'home_price_index': 'CSUSHPINSA',
                         'afford_index': 'FIXHAI'}

    def get_fred_data(self, data_id: list, start_date: str, end_date: str, frequency='m') -> pd.DataFrame:
        df = pd.DataFrame()
        params = {'series_id': data_id,
                'api_key': self.api_key, 
                'file_type': self.file_type,
                'observation_start': start_date,
                'observation_end': end_date,
                'frequency': frequency}

        r = json.loads(requests.get(self.series_url, params=params).text)
        data = {'date':[], 'value':[]}
        for i in r['observations']:
            data['date'].append(pd.to_datetime(i['date']))
            data['value'].append(float(i['value']))
        
        df = pd.DataFrame(data)

        return df
    
    def plot_mgt(self, df: pd.DataFrame, title: str, y_label: str):
        fig, ax = plt.subplots()
        ax.plot(df['date'], df['value'])
        ax.annotate(str(df['value'].iloc[-1]) + '%', xy=(df['date'].max(), df['value'].iloc[-1]),
            xytext=(df['date'].iloc[-8], df['value'].max()*.7),
            arrowprops=dict(arrowstyle='->'),
            )
        ax.set_title(title)
        ax.set_ylabel(y_label)
        ax.set_xlabel('Date')
        ax.grid(True)
        fig.autofmt_xdate()
        return fig
    
    def plot(self, df: pd.DataFrame, title: str, y_label: str):
        fig, ax = plt.subplots()
        ax.plot(df['date'], df['value'])
        ax.set_title(title)
        ax.set_ylabel(y_label)
        ax.set_xlabel('Date')
        ax.grid(True)
        fig.autofmt_xdate()
        return fig
        


# %%
from datetime import date
from dateutil.relativedelta import relativedelta
today = '2023-12-31'
prev = str(date.today() - relativedelta(years=3))

fred = FRED()
df_mgt = fred.get_fred_data(fred.fred_ids['mgt_rate'], prev, today)
# %%
fig, ax = plt.subplots()
ax.plot(df_mgt['date'], df_mgt['value'])
ax.annotate(str(df_mgt['value'].iloc[-1]) + '%', xy=(df_mgt['date'].max(), df_mgt['value'].iloc[-1]),
            xytext=(df_mgt['date'].iloc[-8], df_mgt['value'].max()*.7),
            arrowprops=dict(arrowstyle='->'),
            )

ax.set_title('mgt rate')
ax.set_ylabel('rate')
ax.set_xlabel('Date')
ax.grid(True)
fig.autofmt_xdate()

#%%

str(df_mgt['date'].iloc[-2])
