#%%
import streamlit as st
from datetime import date
from dateutil.relativedelta import relativedelta

from econ.fred_econ import FRED

#%%
today = str(date.today())
prev = str(date.today() - relativedelta(years=3))
today = '2023-12-31'
#%%
fred = FRED()
df_mgt = fred.get_fred_data(fred.fred_ids['mgt_rate'], prev, today, 'm')
df_hpi = fred.get_fred_data(fred.fred_ids['home_price_index'], prev, today, 'm')
df_ai = fred.get_fred_data(fred.fred_ids['afford_index'], prev, today, 'm')
df_cpi = fred.get_fred_data(fred.fred_ids['cpi'], prev, today, 'm')

st.set_page_config(
    layout='wide'
)

col1, col2 = st.columns(2, )

with col1:
    st.pyplot(fred.plot_mgt(df_mgt, '30 Year Mortgage Rate', 'Rate'), use_container_width=True)

    st.pyplot(fred.plot(df_hpi, 'Home Price Index', 'Index'), use_container_width=True)
    st.markdown(
        '''
        *The S&P CoreLogic Case-Shiller 10-City Composite Home Price Index
          is a value-weighted average of the 10 original metro area indices. 
          The S&P CoreLogic Case-Shiller 20-City Composite Home Price Index 
          is a value-weighted average of the 20 metro area indices. The 
          indices have a base value of 100 in January 2000; thus, for example, 
          a current index value of 150 translates to a 50% appreciation rate 
          since January 2000 for a typical home located within the subject market.*

          *prnewswire.com*
        '''
    )

with col2:
    st.pyplot(fred.plot(df_cpi, 'CPI', 'Inflation'), use_container_width=True)

    st.pyplot(fred.plot(df_ai, 'Home Affordability Index', 'Index'), use_container_width=True)
    st.markdown(
        '''
        *Measures the degree to which a typical family can afford the 
        monthly mortgage payments on a typical home.*
        
        *Value of 100 means that a family with the median income has exactly 
        enough income to qualify for a mortgage on a median-priced home. An 
        index above 100 signifies that family earning the median income has 
        more than enough income to qualify for a mortgage loan on a median-priced 
        home, assuming a 20 percent down payment. This index is calculated 
        for fixed mortgages.*

        *fred.stlouisfed.org*
        '''
    )
    
