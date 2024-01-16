import os
import requests
import pandas as pd
import numpy as np
import json
import matplotlib.pyplot as plt
import streamlit as st

from dotenv import load_dotenv, find_dotenv
load_dotenv()

class FRED:
    def __init__(self):
        try:
            self.api_key = os.environ.get('fred_api_key')
        except:
            self.api_key = st.secrets["FRED_API_KEY"]
            
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

    def get_fred_data(self, data_id: list, start_date: str, end_date: str, frequency: str) -> pd.DataFrame:
        df = pd.DataFrame()
        params = {'series_id': data_id,
                'api_key': self.api_key, 
                'file_type': self.file_type,
                'observation_start': start_date,
                'observation_end': end_date,
                'frequency': frequency,
                'aggregation_method': 'eop'
                }

        r = json.loads(requests.get(self.series_url, params=params).text)
        data = {'date':[], 'value':[]}
        f = lambda x: np.nan if i['value']=='.' else float(i['value'])
        for i in r['observations']:
            data['value'].append(f(i))
            data['date'].append(pd.to_datetime(i['date']))        
        
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
        
