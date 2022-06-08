#%%
import pandas as pd
import numpy as np
import os
import requests
from io import StringIO
from datetime import date, datetime, timedelta
import time
import matplotlib.pyplot as plt
#%%

def mortgage_rates(start_date=str(date.today()-timedelta(days=365)), end_date=str(date.today()), date_index=True):

    assert type(start_date) == str and type(end_date) == str, "Enter start and end dates as 'YYYY-MM-DD'"

    url = 'https://www.freddiemac.com/pmms/docs/PMMS_history.csv'
    r = requests.get(url)
    df = pd.read_csv(StringIO(r.text)).fillna(0)

    assert 'date' in df.columns, 'date not a column name'

    for c in df.columns:
        #print(c)
        if c == 'date':
            df[c] = pd.to_datetime(df[c])
        else:
            df[c] = df[c].replace(r'^\s*$', 0, regex=True)
            df[c] = df[c].astype(float)
    
    df = df.rename(columns={'pmms30':'30yr_FRM', 'pmms30p':'30yr_FeesPts', 
                            'pmms15':'15yr_FRM', 'pmms15p':'15yr_FeesPts', 
                            'pmms51':'5-1_ARM', 'pmms51p':'5-1_ARM_FeesPts',
                            'pmms51m':'5-1_ARM_margin', 'pmms51spread':'30yrFRM_ARM_spread'})
    
    start = pd.to_datetime(start_date)
    end = pd.to_datetime(end_date)

    df = df[(df['date']>=start) & (df['date']<=end)]
    
    if date_index:
        df.set_index('date', inplace=True)
    return df

#%%
def fedfunds_rates(start_date=str(date.today()-timedelta(days=365)), end_date=str(date.today()), 
                   rates=['avg_rate_index'], ascending=True, date_index=True):

    if ascending: asc_code = '1'
    else: asc_code = '-1'
    rate_type = {'unsecured_rates':'500,505', 'secured_rates':'510,515,520',
                 'avg_rate_index':'525', 'EFFR':'500', 'OBFR':'505', 'TGCR':'510', 
                 'BGCR':'515', 'SOFR':'520', 'SOFRAI':'525'}
    assert type(start_date) == str and type(end_date) == str, "enter date args as strings in 'YYYY-MM-DD'"

    assert type(rates) == list, 'rates arg must be of type list'
    for _rate in rates:
        assert _rate in rate_type.keys(), "rates arg options - 'unsecured_rates', 'secured_rates'," \
                                    "avg_rate_index, 'EFFR', 'OBFR', 'TGCR', 'BGCR', 'SOFR', 'SOFRAI'"
    
    assert not('unsecured_rates' in rates and 'EFFR' in rates and 'OBFR' in rates), 'rates are double counted'
    assert not('unsecured_rates' in rates and 'EFFR' in rates), 'rates are double counted'
    assert not('unsecured_rates' in rates and 'OBFR' in rates), 'rates are double counted'
    assert not('secured_rates' in rates and 'TGCR' in rates and 'BGCR' in rates and 'SOFR' in rates), 'rates are double counted'
    assert not('secured_rates' in rates and 'TGCR' in rates and 'BGCR' in rates), 'rates are double counted'
    assert not('secured_rates' in rates and 'TGCR' in rates and 'SOFR' in rates), 'rates are double counted'
    assert not('secured_rates' in rates and 'BGCR' in rates and 'SOFR' in rates), 'rates are double counted'

    if len(rates) == 1:
        rt_input = rate_type[rates[0]]
    else:
        rt_input_li = []
        for _r in rates:
            rt_input_li.append(rate_type[_r])
        rt_input = ','.join(rt_input_li)

    url = 'https://markets.newyorkfed.org/read?startDt={}&endDt={}&eventCodes={}'\
    '&productCode=50&sort=postDt:{},eventCode:1&format=xml'.format(start_date, end_date, rt_input, asc_code)
    #print(url)
    r = requests.get(url)
    df = pd.read_xml(StringIO(r.text), xpath='//rate')
    df = df.rename(columns={'effectiveDate':'date'})
    if date_index:
        return df.set_index('date')
    return df

#%%

def ustreasury_rates(start_date=str(date.today()-timedelta(days=365)), end_date=str(date.today()),
                     type='Daily Treasury Par Yield Curve Rates', date_index=True):
    
    #assert type(start_date) == str and type(end_date) == str, "Enter start and end dates as 'YYYY-MM-DD'"

    start_year = int(start_date[:4])
    end_year = int(end_date[:4])
    years = list(range(start_year, end_year+1))

    rate_type = {'Daily Treasury Par Yield Curve Rates':'daily_treasury_yield_curve',
                'Daily Treasury Bill Rates':'daily_treasury_bill_rates',
                'Daily Treasury Long-Term Rates':'daily_treasury_long_term_rate',
                'Daily Treasury Par Real Yield Curve Rates':'daily_treasury_real_yield_curve',
                'Daily Treasury Real Long-Term Rates':'daily_treasury_real_long_term'}

    assert type in rate_type.keys(), 'invalid type arg, must be one of the following:\n'\
                                     'Daily Treasury Par Yield Curve Rates\n'\
                                     'Daily Treasury Bill Rates\n'\
                                     'Daily Treasury Long-Term Rates\n'\
                                     'Daily Treasury Par Real Yield Curve Rates\n'\
                                     'Daily Treasury Real Long-Term Rates'
    df = pd.DataFrame()
    for year in years:
        url = 'https://home.treasury.gov/resource-center/data-chart-center/interest-rates/' \
        'daily-treasury-rates.csv/{}/all?type={}&' \
        'amp;field_tdr_date_value={}&amp;page&amp;_format=csv'.format(year, rate_type[type], year)
        r = requests.get(url)
        df1 = pd.read_csv(StringIO(r.text))
        df1.Date = pd.to_datetime(df1.Date)
        df1 = df1.rename(columns={'Date':'date'})
        df = pd.concat([df, df1], axis=0)

    df = df.sort_values('date')
    df = df.reset_index(drop=True)

    if date_index:
        return df.set_index('date')
    return df

#%%
#int(str(date.today()-timedelta(days=365))[:4])
ustreasury_rates()
# df = pd.DataFrame()
# df1 = mortgage_rates(start_date='2022-01-01', end_date='2022-01-31', date_index=False)
# df2 = mortgage_rates(start_date='2022-02-01', end_date='2022-02-28', date_index=False)
# df = pd.concat([df, df1], axis=0)
# df = pd.concat([df, df2], axis=0)
# df


#%%
def get_stock_data(start_date, end_date=str(date.today()), ticker='%5EGSPC', date_index=True, freq='1wk'):
    url = 'https://query2.finance.yahoo.com/v8/finance/chart/{}'.format(ticker)
    start=int(time.mktime(time.strptime(str(start_date), '%Y-%m-%d')))
    end=int(time.mktime(time.strptime(str(end_date), '%Y-%m-%d')))
    params = {"period1": start, "period2": end}
    params["interval"] = freq
    session = requests.Session()
    session.headers.update({'User-Agent': 'Custom user agent'})
    data_json = session.get(url, params=params).json()

    data = {'price': data_json['chart']['result'][0]['indicators']['quote'][0]['close']}
    data['date'] = pd.to_datetime(data_json['chart']['result'][0]['timestamp'], unit='s')
    
    df = pd.DataFrame(data)
    if ticker == '%5EGSPC':   
        df = df.rename(columns={'price':'SP500'})
    else:
        df = df.rename(columns={'price':ticker})
    if date_index:
        return df.set_index('date')

    return df
#%%

url = 'https://www.fhfa.gov/HPI_master.csv'
r = requests.get(url).text
r

#%%

