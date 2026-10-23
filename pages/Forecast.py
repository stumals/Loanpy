#%%
import streamlit as st
import matplotlib.pyplot as plt

from econ.fred_econ import FRED
from models.forecast import rate_forecast

st.set_page_config(
    layout='wide'
)

#%%
fc = rate_forecast(FRED())

def mgt_ffr_plot(history, forecast):
    fig, ax = plt.subplots()
    ax.plot(history['date'], history['mgt_rate'], label='Mgt Rate', color='blue')
    ax.plot(history['date'], history['ffr'], label='FFR', color='orange')
    ax.plot(forecast['date'], forecast['mean'], label='Mgt Fcst', color='blue', linestyle='--')
    ax.plot(forecast['date'], forecast['obs_ci_lower'], label='Mgt Lower', color='red', linestyle='--')
    ax.plot(forecast['date'], forecast['obs_ci_upper'], label='Mgt Upper', color='red', linestyle='--')
    ax.plot(forecast['date'], forecast['ffr'], label='FFR Fcst', color='orange', linestyle='--')
    ax.legend()
    ax.grid(True)
    return fig

col1, col2 = st.columns(2, )

with col1:
    st.pyplot(mgt_ffr_plot(fc.history, fc.forecast), use_container_width=True)
with col2:
    st.markdown(
        '''
        30 Year Mortgage Rate Forecast
        - Baseline model using linear regression with only the federal funds rate as the predicting variable
        - FFR is the midpoint of the Fed's target range
        - Mortgage rate forecast based on the Fed's year-end FFR projections (FOMC Summary of Economic Projections), drawn as straight lines from today's rate
        - 95% prediction interval of rate forecast also provided
        - Model tested using time series cross validation with 5 folds
        - Final model built using full dataset

        '''
    )

    st.dataframe(fc.cv)
