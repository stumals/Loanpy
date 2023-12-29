#%%
import altair as alt
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

from .econ_data import EconData

#%%
# import os
# os.chdir('..')
# os.getcwd()

#%%
class EconPlots:

    def mortgage_rates(df_rates) -> alt.Chart:
        df = df_rates[['30yr_FRM', '15yr_FRM']]
        df['30_vs_15'] = df['30yr_FRM'] - df['15yr_FRM']
        data = df.reset_index()
        data = data.melt(id_vars='date', var_name='type', value_name='rate')
        line_rates = alt.Chart(data, title='Mortgage Rates').mark_line().encode(
            x=alt.X('date', title='Date'),
            y=alt.Y('rate', title='Rates'),
            color='type',
            tooltip=['date', 'type', 'rate']
            )
        return line_rates
    
    def mort_rates2(df_rates):
        df = df_rates[['30yr_FRM', '15yr_FRM']].reset_index()
        fig, ax = plt.subplots()
        ax.plot(df['date'], df['30yr_FRM'], label='30yr')
        ax.plot(df['date'], df['15yr_FRM'], label='15yr')
        ax.set_title('Mortgage Rates')
        ax.legend()
        ax.set_ylabel('Rates')
        ax.set_xlabel('Date')
        #ax.set_xticklabels(df['date'], rotation=45)
        ax.set_xlim(xmin=df['date'].min(), xmax=df['date'].max())
        ax.grid(True)
        fig.autofmt_xdate()
        return fig


# %%