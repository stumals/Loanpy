#%%
import pandas as pd
import numpy as np
import os
import requests
from io import StringIO
from datetime import date
import matplotlib.pyplot as plt
#%%

def get_mortgage_rates(date_index=False):
    url = 'https://www.freddiemac.com/pmms/docs/PMMS_history.csv'
    r = requests.get(url)
    df = pd.read_csv(StringIO(r.text)).fillna(0)

    assert 'date' in df.columns, 'date not a column name'

    for c in df.columns:
        print(c)
        if c == 'date':
            df[c] = pd.to_datetime(df[c])
        else:
            df[c] = df[c].replace(r'^\s*$', 0, regex=True)
            df[c] = df[c].astype(float)
    
    if date_index:
        df.set_index('date', inplace=True)
    return df


def get_fedfunds_rate(start_date, end_date=str(date.today()), rates=['avg_rate_index'], ascending=True, date_index=False):
    if ascending: asc_code = '1'
    else: asc_code = '-1'
    rate_type = {'unsecured_rates':'500,505', 'secured_rates':'510,515,520', 'avg_rate_index':'525', 
                'EFFR':'500', 'OBFR':'505', 'TGCR':'510', 'BGCR':'515', 'SOFR':'520', 'SOFRAI':'525'}
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
    print(url)
    r = requests.get(url)
    df = pd.read_xml(StringIO(r.text), xpath='//rate')
    if date_index:
        return df.set_index('effectiveDate')
    return df


def get_ustreasury_rates(year, type='Daily Treasury Par Yield Curve Rates', date_index=False):

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
    url = 'https://home.treasury.gov/resource-center/data-chart-center/interest-rates/' \
    'daily-treasury-rates.csv/{}/all?type={}&' \
    'amp;field_tdr_date_value={}&amp;page&amp;_format=csv'.format(year, rate_type[type], year)

    r = requests.get(url)
    df = pd.read_csv(StringIO(r.text))
    df.Date = pd.to_datetime(df.Date)
    if date_index:
        return df.set_index('Date')
    return df


