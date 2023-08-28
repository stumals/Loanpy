#%%
import streamlit as st
import altair as alt
import pandas as pd

from core import Loan
from utils import expected_value_cagr, rent_vs_buy
#%%
st.write('''
        # Rent vs Buy
        ''')

a = Loan(300000, .05, 30)
df = a.amort_table_detail() \
        .loc[:,['year', 'profit']] \
        .groupby('year').max() \
        .reset_index()
        
plot = alt.Chart(df, title='Profit by Year').mark_line().encode(
    x=alt.X('year', scale=alt.Scale(domain=[1, df.year.max()])), 
    y='profit'
)
#%%
st.altair_chart(plot, use_container_width=True)
#%%
month_buy, month_rent, year_buy, year_rent = rent_vs_buy(a, 1500)
return_buy = year_buy.return_total
return_rent = year_rent.return_total

#%%
df2 = pd.DataFrame()
df2['buy'] = return_buy
df2['rent'] = return_rent
df2 = df2.reset_index().melt('year')
#df2 = df2.reset_index()
#df2['year'] = year_buy.index
#df2 = df2.melt(id_vars='year', value_vars=['rent', 'buy'], var_name='options', value_name='profit').reset_index()
#df2 = df2[['year', 'options', 'profit']]
#%%
plot2 = alt.Chart(df2, title='Rent vs Buy').mark_line().encode(
    x='year',
    y='value',
    color='variable'
)

st.altair_chart(plot2, use_container_width=True)