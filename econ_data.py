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
class EconData():

    def __init__(self, start_date=str(date.today()-timedelta(days=365)), end_date=str(date.today()), date_index=True):
        
        assert type(start_date) == str and type(end_date) == str, "Enter start and end dates as 'YYYY-MM-DD'"
        self.start = start_date
        self.end = end_date
        self.date_index = date_index

    def mortgage_rates(self):
        '''
        Returns dataframe of mortgage rates from Freddie Mac
        '''
        url = 'https://www.freddiemac.com/pmms/docs/PMMS_history.csv'
        r = requests.get(url)
        df = pd.read_csv(StringIO(r.text)).fillna(0)

        assert 'date' in df.columns, 'date not a column name'

        for c in df.columns:
            if c == 'date':
                df[c] = pd.to_datetime(df[c])
            else:
                df[c] = df[c].replace(r'^\s*$', 0, regex=True)
                df[c] = df[c].astype(float)
        
        df = df.rename(columns={'pmms30':'30yr_FRM', 'pmms30p':'30yr_FeesPts', 
                                'pmms15':'15yr_FRM', 'pmms15p':'15yr_FeesPts', 
                                'pmms51':'5-1_ARM', 'pmms51p':'5-1_ARM_FeesPts',
                                'pmms51m':'5-1_ARM_margin', 'pmms51spread':'30yrFRM_ARM_spread'})
        
        start = pd.to_datetime(self.start)
        end = pd.to_datetime(self.end)

        df = df[(df['date']>=start) & (df['date']<=end)]
        
        if self.date_index:
            df.set_index('date', inplace=True)
        self.df = df
        self.df_name = 'Mortgage Rates'

    def fedfunds_rates(self, rates=['avg_rate_index'], ascending=True):
        '''
        Returns dataframe of fed funds rates from the New York Fed
        '''

        if ascending: asc_code = '1'
        else: asc_code = '-1'
        rate_type = {'unsecured_rates':'500,505', 'secured_rates':'510,515,520',
                    'avg_rate_index':'525', 'EFFR':'500', 'OBFR':'505', 'TGCR':'510', 
                    'BGCR':'515', 'SOFR':'520', 'SOFRAI':'525'}
        #assert type(start_date) == str and type(end_date) == str, "enter date args as strings in 'YYYY-MM-DD'"

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
        '&productCode=50&sort=postDt:{},eventCode:1&format=xml'.format(self.start, self.end, rt_input, asc_code)
        r = requests.get(url)

        if r.text.find('Site Maintenance') > 0:
            raise Exception('markets.newyorkfed.org site under maintenance')

        df = pd.read_xml(StringIO(r.text), xpath='//rate')
        df = df.rename(columns={'effectiveDate':'date'})

        df['date'] = pd.to_datetime(df['date'])
        start = pd.to_datetime(self.start)
        end = pd.to_datetime(self.end)
        df = df[(df['date']>=start) & (df['date']<=end)]

        if self.date_index:
            df.set_index('date', inplace=True)
        self.df = df
        self.df_name = 'Fed Funds Rates'

    def ustreasury_rates(self, type='Daily Treasury Par Yield Curve Rates'):
        '''
        Returns dataframe with US Treasury rates

        Type parameter has several options - pass second item to type parameter:

        Daily Treasury Par Yield Curve Rates : daily_treasury_yield_curve,
        Daily Treasury Bill Rates : daily_treasury_bill_rates,
        Daily Treasury Long-Term Rates : daily_treasury_long_term_rate,
        Daily Treasury Par Real Yield Curve Rates : daily_treasury_real_yield_curve,
        Daily Treasury Real Long-Term Rates : daily_treasury_real_long_term
        '''
        
        start_year = int(self.start[:4])
        end_year = int(self.end[:4])
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
        
        start = pd.to_datetime(self.start)
        end = pd.to_datetime(self.end)
        df = df[(df['date']>=start) & (df['date']<=end)]

        if self.date_index:
            df.set_index('date', inplace=True)
        self.df = df
        self.df_name = 'US Treasury Rates'

    def stock_data(self, ticker='%5EGSPC', freq='1wk'):
        '''
        Returns stock martket data from Yahoo Finance

        Update ticker parameter for different stocks
        '''
        url = 'https://query2.finance.yahoo.com/v8/finance/chart/{}'.format(ticker)
        start=int(time.mktime(time.strptime(str(self.start), '%Y-%m-%d')))
        end=int(time.mktime(time.strptime(str(self.end), '%Y-%m-%d')))
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

        start = pd.to_datetime(self.start)
        end = pd.to_datetime(self.end)
        df = df[(df['date']>=start) & (df['date']<=end)]    
        
        if self.date_index:
            df.set_index('date', inplace=True)

        self.df = df
        self.df_name = 'Stock Market Data'

    def median_home_price(self):
        '''
        Returns dataframe of median home prices from the St. Louis Fed
        '''
        url = 'https://fred.stlouisfed.org/graph/fredgraph.csv?bgcolor=%23e1e9f0&chart_type=line&drp=0&'\
            'fo=open%20sans&graph_bgcolor=%23ffffff&height=450&mode=fred&recession_bars=on&txtcolor='\
            '%23444444&ts=12&tts=12&width=1168&nt=0&thu=0&trc=0&show_legend=yes&show_axis_titles=yes&'\
            'show_tooltip=yes&id=ASPUS&scale=left&cosd=1963-01-01&coed=2022-01-01&line_color=%234572a7&'\
            'link_values=false&line_style=solid&mark_type=none&mw=3&lw=2&ost=-99999&oet=99999&mma=0&fml=a&'\
            'fq=Quarterly&fam=avg&fgst=lin&fgsnd=2020-02-01&line_index=1&transformation=lin&vintage_date='\
            '2022-06-14&revision_date=2022-06-14&nd=1963-01-01'

        r = requests.get(url)
        df = pd.read_csv(StringIO(r.text))
        df = df.rename(columns={'DATE':'date'})

        df['date'] = pd.to_datetime(df['date'])
        start = pd.to_datetime(self.start)
        end = pd.to_datetime(self.end)
        df = df[(df['date']>=start) & (df['date']<=end)]

        if self.date_index:
            df.set_index('date', inplace=True)
        self.df = df
        self.df_name = 'Median Home Prices'

    def plot_df(self, *col_names):
        plt.plot(self.df.loc[:,col_names[0]])
        plt.title(self.df_name)
        plt.legend()

# %%
a = EconData()
a.mortgage_rates()
a.plot_df(['30yr_FRM', '15yr_FRM'])
# %%
# %%

def abc(*args):
    df = pd.DataFrame(np.random.rand(5, 4))
    df.columns = ['a', 'b', 'c', 'd']
    print(df[args[0]])
abc(['a', 'b', 'c'])

# %%
df = pd.DataFrame(np.random.rand(5, 4))
df.columns = ['a', 'b', 'c', 'd']
df
# %%
