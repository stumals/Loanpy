import pandas as pd
import numpy as np
from core import Loan
import matplotlib.pyplot as plt


def expected_value_cagr(start_value, end_value, years):
    '''
    Utility function to provide Constant Annual Growth Rate (CAGR) needed to acheive end_value
    '''
    cagr = (end_value/start_value)**(1/years) - 1
    return cagr

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

    df['investment'] = df['diff'].cumsum() * np.array([1+(market_returns/loan.pmt_freq)]*loan.nper).cumprod()
    df['diff_cumulative'] = df['diff'].cumsum()
    df['cap_gains_cumulative'] = df['investment'] - df['diff_cumulative']
    df['cap_gains_tax'] = df['cap_gains_cumulative'] * cap_gains_tax
    df['investment_net'] = df['investment'] - df['cap_gains_tax']
    df['return_total'] = df['investment_net'] + df['home_sale_net']

    df_rent['investment'] = df_rent['diff'].cumsum() * np.array([1+(market_returns/loan.pmt_freq)]*loan.nper).cumprod()
    df_rent['diff_cumulative'] = df_rent['diff'].cumsum()
    df_rent['cap_gains_cumulative'] = df_rent['investment'] - df_rent['diff_cumulative']
    df_rent['cap_gains_tax'] = df_rent['cap_gains_cumulative'] * cap_gains_tax
    df_rent['investment_net'] = df_rent['investment'] - df_rent['cap_gains_tax']
    df_rent['rent_cumulative'] = -df_rent['rent'].cumsum()
    df_rent['return_total'] = df_rent['investment_net'] + df_rent['rent_cumulative']

    cols_df = ['year', 'home_sale_net', 'investment_net', 'return_total']
    cols_rent = ['year', 'rent_cumulative', 'investment_net', 'return_total']

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
    plt.xlabel('Year');
    plt.ylabel('Return $');
    plt.legend();

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
