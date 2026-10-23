import pandas as pd
import numpy as np
import numpy_financial as npf


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
    import matplotlib.pyplot as plt

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