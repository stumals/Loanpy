import pandas as pd
import numpy as np
import numpy_financial as npf
import matplotlib.pyplot as plt


def expected_value_cagr(start_value, end_value, years):
    '''
    Utility function to provide Constant Annual Growth Rate (CAGR) needed to acheive end_value
    '''
    cagr = (end_value/start_value)**(1/years) - 1
    return cagr

def affordability_calc(gross_income, rate=0, amt=0, pmt_percent=.28, bins=16, amt_incrmt=10000, rate_incrmt=.0025):
    '''
    Returns dataframe of varying asset amounts and rates based on a fixed payment that is calculated as a % of gross income
    '''
    pmt = gross_income/12 * pmt_percent
    def calc_rate(amt):
        return npf.rate(360, -pmt, amt, 0)*12*100
    def calc_amt(rate):
        return npf.pv(rate/12/100, 360, -pmt, 0)
    df = pd.DataFrame()
    if amt == 0:
        rates = np.linspace(rate*100 - ((bins/2)*rate_incrmt*100), rate*100 + ((bins/2)*rate_incrmt*100), num=bins+1)
        df['rates'] = rates
        df['loan_amts'] = pd.Series(rates).apply(calc_amt)
    else:
        amts = np.linspace(amt - ((bins/2)*amt_incrmt), amt + ((bins/2)*amt_incrmt), num=bins+1)
        df['loan_amts'] = amts
        df['rates'] = pd.Series(amts).apply(calc_rate)
    df['gross_income'] = gross_income
    df['gross_income_mthly'] = gross_income/12
    df['percent_gross_income'] = pmt_percent
    df['pmt_monthly'] = pmt    
    
    return df

def rent_vs_buy(loan, rent_start, time_years=10, rent_growth=.05, market_returns=.07, cap_gains_tax=.15):
    '''
    Compares net returns of buying a home vs renting. Whichever option has a lower all in monthly cost,
    that difference is invested in the stock market.

    Parameters
    ----------
    loan : instance of Loan class
    rent_start : cost of rental unit at current time
    time_years : number of years to compare
    rent_growth : how much rent grows each year
    market_returns : annual stock market return assumption
    cap_gains_tax : capital gains tax deducted from market returns

    Returns 4 dataframes in a tuple
    1. Monthly view of buy option
    2. Monthly view of rent option
    3. Yearly view of buy option
    4. Yearly view of rent option
    '''
    assert loan.num_years >= time_years, 'Loan arg num_years shorter than time_years'
    
    df = loan.amort_table_detail()

    df_rent = pd.DataFrame(data=((1+rent_growth)**(df['year'] - 1)) * rent_start).rename(columns={'year':'rent'})
    df_rent['year'] = df['year']

    df['diff'] = df_rent['rent'] - df['all_in_pmts']
    df['diff'] = df['diff'].apply(lambda x: x if x > 0 else 0)

    df_rent['diff'] = df['all_in_pmts'] - df_rent['rent']
    df_rent['diff'] = df_rent['diff'].apply(lambda x: x if x > 0 else 0)

    df['market_returns'] = df['diff'].cumsum() * np.array([1+(market_returns/loan.pmt_freq)]*loan.nper).cumprod()
    df['diff_cumulative'] = df['diff'].cumsum()
    df['cap_gains_cumulative'] = df['market_returns'] - df['diff_cumulative']
    df['cap_gains_tax'] = df['cap_gains_cumulative'] * cap_gains_tax
    df['returns_net'] = df['market_returns'] - df['cap_gains_tax']
    df['return_total'] = df['returns_net'] + df['profit']

    df_rent['market_returns'] = df_rent['diff'].cumsum() * np.array([1+(market_returns/loan.pmt_freq)]*loan.nper).cumprod()
    df_rent['diff_cumulative'] = df_rent['diff'].cumsum()
    df_rent['cap_gains_cumulative'] = df_rent['market_returns'] - df_rent['diff_cumulative']
    df_rent['cap_gains_tax'] = df_rent['cap_gains_cumulative'] * cap_gains_tax
    df_rent['returns_net'] = df_rent['market_returns'] - df_rent['cap_gains_tax']
    df_rent['rent_cumulative'] = df_rent['rent'].cumsum()
    df_rent['return_total'] = df_rent['returns_net'] - df_rent['rent_cumulative']

    cols_df = ['year', 'profit', 'returns_net', 'return_total']
    cols_rent = ['year', 'rent_cumulative', 'returns_net', 'return_total']

    df_year = df.loc[:, cols_df].groupby('year').max()
    df_rent_year = df_rent.loc[:, cols_rent].groupby('year').max()
    
    return (df.loc[:time_years*12-1, cols_df], df_rent.loc[:time_years*12-1,cols_rent], df_year.iloc[:time_years,:], df_rent_year.iloc[:time_years,:])


def buy_vs_buy(loan_a, loan_b, time_years=10, market_returns=.07, cap_gains_tax=.15, detail=False):
    '''
    Compares net returns 2 different buy options. Whichever option has a lower all in monthly cost,
    that difference is invested in the stock market.

    Parameters
    ----------
    loan_a : first instance of Loan class
    loan_b : second instance of Loan class
    time_years : number of years comparison is carried out to
    market_returns : annual stock market return assumption
    cap_gains_tax : capital gains tax deducted from market returns
    detail : flag to show additional columns or not

    Returns 4 dataframes in a tuple
    1. Monthly view of loan_a
    2. Monthly view of loan_b
    3. Yearly view of loan_a
    4. Yearly view of loan_b
    '''
    assert loan_a.num_years >= time_years, 'Loan A shorter than investment time'
    assert loan_b.num_years >= time_years, 'Loan B shorter than investment time'
    
    df_a = loan_a.amort_table_detail()
    df_b = loan_b.amort_table_detail()
    
    df_a['diff'] = df_b['all_in_pmts'] - df_a['all_in_pmts']
    df_a['diff'] = df_a['diff'].apply(lambda x: x if x > 0 else 0)
    
    df_b['diff'] = df_a['all_in_pmts'] - df_b['all_in_pmts']
    df_b['diff'] = df_b['diff'].apply(lambda x: x if x > 0 else 0)
    
    df_a['investment'] = df_a['diff'].cumsum() * np.array([1+(market_returns/loan_a.pmt_freq)]*loan_a.nper).cumprod()
    df_a['diff_cumulative'] = df_a['diff'].cumsum()
    df_a['cap_gains_cumulative'] = df_a['investment'] - df_a['diff_cumulative']
    df_a['cap_gains_tax'] = df_a['cap_gains_cumulative'] * cap_gains_tax
    df_a['investment_net'] = df_a['investment'] - df_a['cap_gains_tax']
    df_a['return_total'] = df_a['investment_net'] + df_a['home_sale_net']
    
    df_b['investment'] = df_b['diff'].cumsum() * np.array([1+(market_returns/loan_b.pmt_freq)]*loan_b.nper).cumprod()
    df_b['diff_cumulative'] = df_b['diff'].cumsum()
    df_b['cap_gains_cumulative'] = df_b['investment'] - df_b['diff_cumulative']
    df_b['cap_gains_tax'] = df_b['cap_gains_cumulative'] * cap_gains_tax
    df_b['investment_net'] = df_b['investment'] - df_b['cap_gains_tax']
    df_b['return_total'] = df_b['investment_net'] + df_b['home_sale_net']
    
    if detail:
        cols = ['year', 'home_sale_net', 'investment_net', 'return_total', 'diff', 'diff_cumulative', 'investment',
                'cap_gains_cumulative', 'cap_gains_tax']
    else:
        cols = ['year', 'home_sale_net', 'investment_net', 'return_total']
    
    df_a_year = df_a[cols].groupby('year').max()
    df_b_year = df_b[cols].groupby('year').max()

    return (df_a.loc[:time_years*12-1, cols], df_b.loc[:time_years*12-1, cols], df_a_year.iloc[:time_years,:], df_b_year.iloc[:time_years,:])


def plot_comparison(option_a, option_b):
    '''
    Plots the comparisons calculated in rent_vs_buy or buy_vs_buy

    Use the same time period of options when plotting (monthly vs yearly)
    '''
    plt.plot(option_a['return_total'], label='Option A');
    plt.plot(option_b['return_total'], label='Option B');
    plt.xlim(1, option_a.shape[0]);
    plt.xlabel('Period');
    plt.ylabel('Return $');
    plt.legend();


def pmt_matrix(self, bins=10, amt_incrmt=10000, rate_incrmt=.0025, variance=False):
    '''
    Returns matrix of how payment changes with increasing/decreasing inital asset amount and rate
    '''
    assert bins%2 == 0, 'Number of bins must be even'
    assert amt_incrmt > 0, 'Amount is not greater than 0'
    assert rate_incrmt > 0 and rate_incrmt < 1, 'Rate is not greater than 0 and less than 1'

    rates = np.linspace(self.rate_annual*100 - ((bins/2)*rate_incrmt*100), self.rate_annual*100 + ((bins/2)*rate_incrmt*100), num=bins+1)
    amts = np.linspace(self.amt - ((bins/2)*amt_incrmt), self.amt + ((bins/2)*amt_incrmt), num=bins+1)

    rates = rates[rates>0]
    amts = amts[amts>0]

    pmts = {'amts':[], 'rates':[], 'pmt':[]}
    for a in amts:
        for r in rates:
            pmt = -npf.pmt(r/100/self.pmt_freq, self.nper, a)
            pmts['amts'].append(a)
            pmts['rates'].append(r)
            pmts['pmt'].append(pmt)
    df_pmts = pd.DataFrame(pmts)
    df_matrix = df_pmts.pivot(index='amts', columns='rates', values='pmt')
    if variance:
        df_matrix = df_matrix - self.pmt 
    return df_matrix


def plot_debt_vs_equity(self):
    '''
    Plots the debt and equity curves of the loan amortization table - ending balance and cumulative principal
    '''
    df = self.amort_table
    df['principal_total'] = df['principal'].cumsum()

    df2 = pd.DataFrame()
    df2['equity'] = df[['year', 'principal_total']].groupby('year').max()
    df2['debt'] = df[['year', 'end_bal']].groupby('year').min()

    i = df2[df2['equity'] > df2['debt']].index.min()
    x1 = i - 1
    y1 = df2.loc[x1, 'debt']
    x2 = i
    y2 = df2.loc[x2, 'debt']
    x3 = i - 1
    y3 = df2.loc[x3, 'equity']
    x4 = i
    y4 = df2.loc[x4, 'equity']

    @staticmethod
    def get_line(x1, x2, y1, y2):
        points = [(x1, y1), (x2, y2)]
        x_coords, y_coords = zip(*points)
        a = np.vstack([x_coords, np.ones(len(x_coords))]).T
        m, c = np.linalg.lstsq(a, y_coords, rcond=None)[0]
        x = -m
        c = -c
        y = 1
        return {'a':x, 'b':y, 'c':c}

    @staticmethod
    def get_intersection(p1, p2):
        x = (p1['b']*p2['c']-p2['b']*p1['c'])/(p1['a']*p2['b']-p2['a']*p2['b'])
        y = (p1['c']*p2['a']-p2['c']*p1['a'])/(p1['a']*p2['b']-p2['a']*p1['b'])
        return (x, y)

    p1 = get_line(x1, x2, y1, y2)
    p2 = get_line(x3, x4, y3, y4)

    intersection = get_intersection(p1, p2)[0]

    plt.plot(df[['year', 'end_bal']].groupby('year').min(), label='Debt', color='r');
    plt.plot(df[['year', 'principal_total']].groupby('year').max(), label='Equity', color='g');
    plt.axvline(intersection, color='b');
    plt.xlabel('Year');
    plt.ylabel('Amount $');
    plt.title('Debt vs Equity');
    plt.legend();
    plt.xlim(1);
    plt.ylim(0);