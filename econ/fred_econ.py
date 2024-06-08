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
            self.api_key = st.secrets["FRED_API_KEY"]
        except:
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
                         'afford_index': 'FIXHAI',
                         'unemployment': 'UNRATE',
                         'gdp':'GDP',
                         'consumer_exp':'PCE',
                         'gov_spend':'FGEXPND',
                         'private_investment':'GPDI',
                         '10yr_tbill':'DGS10'
                         }

    def get_fred_data(self, data_id: str, start_date: str, end_date: str=None, frequency: str=None) -> pd.DataFrame:
        fred_id = self.fred_ids[data_id]
        params = {'series_id': fred_id,
                'api_key': self.api_key, 
                'file_type': self.file_type,
                'observation_start': start_date,
                'observation_end': end_date,
                'frequency': frequency,
                'aggregation_method': 'eop'
                }

        r = json.loads(requests.get(self.series_url, params=params).text)
        data = {'date':[], data_id:[]}
        f = lambda x: np.nan if i['value']=='.' else float(i['value'])
        for i in r['observations']:
            if i['value'] == '.':
                continue
            else:
                data[data_id].append(f(i))
                data['date'].append(pd.to_datetime(i['date']))        
        
        df = pd.DataFrame(data)

        return df
    
    # def plot_mgt(self, df: pd.DataFrame, title: str, y_label: str):
    #     fig, ax = plt.subplots()
    #     ax.plot(df['date'], df.iloc[:,1])
    #     ax.annotate(str(df.iloc[:,1].iloc[-1]) + '%', xy=(df['date'].max(), df.iloc[:,1].iloc[-1]),
    #         xytext=(df['date'].iloc[-8], df.iloc[:,1].max()*.7),
    #         arrowprops=dict(arrowstyle='->'),
    #         )
    #     ax.set_title(title)
    #     ax.set_ylabel(y_label)
    #     ax.set_xlabel('Date')
    #     ax.grid(True)
    #     fig.autofmt_xdate()
    #     return fig
    
    def plot(self, df: pd.DataFrame, title: str, y_label: str):
        fig, ax = plt.subplots()
        ax.plot(df['date'], df.iloc[:,1])
        last_date = df['date'].max()
        last_value = round(df.iloc[:,1].iloc[-1], 2)
        annotation_text = f"Date: {last_date.strftime('%Y-%m-%d')}\nValue: {last_value}%"
        
        # Draw the figure first to update the limits
        fig.canvas.draw()

        # Get the limits of the x and y axes
        x_lim = ax.get_xlim()
        y_lim = ax.get_ylim()

        # Calculate the x and y coordinates for the annotation text
        x_coord = x_lim[1] - (x_lim[1] - x_lim[0]) * 0.1
        y_coord = y_lim[0] + (y_lim[1] - y_lim[0]) * 0.1
        
        ax.annotate(annotation_text, xy=(last_date, last_value),
            xytext=(x_coord, y_coord),
            arrowprops=dict(arrowstyle='->'),
            ha='right', va='bottom', # align the text to the right and bottom
            )
        ax.set_title(title)
        ax.set_ylabel(y_label)
        ax.set_xlabel('Date')
        ax.grid(True)
        fig.autofmt_xdate()
        return fig
    
    # def plot(self, df: pd.DataFrame, title: str, y_label: str):
    #     fig, ax = plt.subplots()
    #     ax.plot(df['date'], df.iloc[:,1])
    #     ax.set_title(title)
    #     ax.set_ylabel(y_label)
    #     ax.set_xlabel('Date')
    #     ax.grid(True)
    #     fig.autofmt_xdate()
    #     return fig
        
