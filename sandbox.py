#%%
from loan.loan_input import LoanInput
from loan.core import Loan
from utils.utils import expected_value_cagr
import numpy as np
import pandas as pd
import os
from econ.econ_data import EconData
import requests
from io import StringIO
#%%
os.getcwd()

#%%
ed = EconData()
ed.mortgage_rates()
df = ed.df[['30yr_FRM', '15yr_FRM']]
df['30_vs_15'] = df['30yr_FRM'] - df['15yr_FRM']

#%%
df.reset_index()
#%%
import altair as alt
# %%
data = df
line_rates = alt.Chart(data, title='Mortgage Rates').mark_line().encode(
    x=alt.X('year', scale=alt.Scale(domain=self.domain, nice=False), title='Year'),
    y=alt.Y('profit', title='Profit'),
    tooltip=['year', 'profit']
    )