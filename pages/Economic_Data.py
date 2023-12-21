import streamlit as st

from econ.plots import EconPlots
from econ.econ_data import EconData

ed = EconData()
ed.mortgage_rates()
df_rates = ed.df

st.altair_chart(EconPlots.mortgage_rates(df_rates), use_container_width=True)