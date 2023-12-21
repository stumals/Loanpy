#%%
import altair as alt
import pandas as pd
import numpy as np

from econ_data import EconData

#%%
# import os
# os.chdir('..')
# os.getcwd()

#%%
class EconPlots:

    def mortgage_rates(df_rates) -> alt.Chart:
        data = df_rates.reset_index()
        data = data.melt(id_vars='date', var_name='type', value_name='rate')
        line_rates = alt.Chart(data, title='Mortgage Rates').mark_line().encode(
            x=alt.X('date', title='Date'),
            y=alt.Y('rate', title='Rates'),
            color='type',
            tooltip=['date', 'type', 'rate']
            )
        return line_rates

