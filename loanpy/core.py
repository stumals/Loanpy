#%%
import numpy as np
import numpy_financial as npf
import pandas as pd
import matplotlib.pyplot as plt
#%%
class Loan():
    '''
    Framework for generating and analyzing mortgage amortization data

    Parameters
    ----------
    asset_amt : value of property to get loan for
    rate_annual : annual rate of loan
    num_years : number of years of loan
    pmt_freq : number of payments per year
    down_pmt : down payment percentage on loan
    closing_cost : closing cost of loan
    closing_cost_finance : boolean if the closing cost is financied through loan or not
    prop_tax_rate : property tax rate
    pmi_rate : private mortgage insurance rate
    maint_rate : maintance rate
    home_value_appreciation : annual appreciation rate of property
    home_sale_percent : percent cost of sale of property
    '''
    def __init__(self, asset_amt, rate_annual, num_years, pmt_freq=12, down_pmt=0.0, closing_cost=0,
                 closing_cost_finance=False, prop_tax_rate=.01, pmi_rate=.01, maint_rate=.01,
                 home_value_appreciation=.03, home_sale_percent=.06):
       
        assert asset_amt > 0, 'asset_amt must be greater than 0'
        assert rate_annual > 0 and rate_annual < 1, 'rate_annual must be between 0 and 1'
        assert down_pmt >= 0 and down_pmt < 1, 'down_pmt must be between 0 and 1'
        assert closing_cost >= 0, 'closing_cost must be greater than 0'
        assert type(closing_cost_finance)==bool, 'closing_cost_finance must be bool type'
        assert prop_tax_rate >= 0 and prop_tax_rate < 1, 'prop_tax_rate must be between 0 and 1'
        assert pmi_rate >= 0 and pmi_rate < 1, 'pmi_rate must be between 0 and 1'
        assert maint_rate >= 0 and maint_rate < 1, 'maint_rate must be between 0 and 1'
        assert home_value_appreciation >= 0 and home_value_appreciation < 1, 'home_value_appreciation must be between 0 and 1'
        assert home_sale_percent >= 0 and home_sale_percent < 1, 'home_sale_percent must be between 0 and 1'

        self.asset_start_value = asset_amt
        self.rate_annual = rate_annual
        self.rate = rate_annual / pmt_freq
        self.nper = num_years * pmt_freq
        self.closing_cost = closing_cost
        self.closing_cost_finance = closing_cost_finance
        self.down_pmt = down_pmt
        self.home_sale_percent = home_sale_percent
        if closing_cost_finance:
            self.amt = (asset_amt*(1-self.down_pmt)) + self.closing_cost
        else:
            self.amt = (asset_amt*(1-self.down_pmt))
        self.pmt = -npf.pmt(self.rate, self.nper, self.amt)
        self.num_years = num_years
        self.pmt_freq = pmt_freq
        self.tax = prop_tax_rate
        self.pmi = pmi_rate
        self.maint = maint_rate
        self.appr_rate = home_value_appreciation
        
        # numpy arrays used in amortization calculation
        self.periods = np.arange(1, self.nper + 1, dtype=int)
        self.pmts = np.array([self.pmt] * self.nper)
        self.interest = -npf.ipmt(self.rate, self.periods, self.nper, self.amt)
        self.principal = -npf.ppmt(self.rate, self.periods, self.nper, self.amt)

        # beg / end balance calculations used in amortization
        def balance(pv, rate, nper, pmt):
            d = (1 + rate) ** nper
            return pv * d - pmt*(d - 1)/rate

        self.beg_bal = balance(self.amt, self.rate, self.periods - 1, self.pmt)
        self.end_bal = balance(self.amt, self.rate, self.periods, self.pmt)

        # check if calculations are correct
        assert np.allclose(self.interest + self.principal, self.pmt), "Interest + Principal DOES NOT equal Payment"
        assert np.allclose(self.end_bal[-1], 0), "Ending balance after last payment DOES NOT equal 0.0"
        assert np.allclose(self.beg_bal[0], self.amt), "Beginning loan balance DOES NOT equal loan amount"
        assert len(self.periods)==len(self.pmts)==len(self.interest)==len(self.principal)==len(self.beg_bal) \
               ==len(self.end_bal)==self.nper, "Calculated arrays DO NOT all equal number of periods"
    
    def get_attrs(self):
        '''
        Returns parameters used in loan instantiation
        '''
        d = self.__dict__
        df = pd.DataFrame(index=d.keys(), data=d.values(), columns=['attributes'])
        to_drop = ['pmts', 'periods', 'interest', 'principal', 'beg_bal', 'end_bal']
        return df.drop(to_drop)
    
    def amort_table(self):
        '''
        Returns amortization table with number of periods equaling pmt_freq * num_years

        Table columns - period, year, beg_bal, pmt, principal, interest, end_bal
        '''
        df = pd.DataFrame()
        df['period'] = self.periods
        df['year'] = df['period'].apply(lambda x: x // self.pmt_freq if x % self.pmt_freq == 0 else x // self.pmt_freq + 1)
        assert df['year'].iloc[-1] == self.num_years 
        df['beg_bal'] = self.beg_bal
        df['pmt'] = self.pmts
        df['principal'] = self.principal
        df['interest'] = self.interest
        df['end_bal'] = self.end_bal
        return df.round(2)
        
    def amort_table_detail(self):
        '''
        Returns amortization table with additional details

        Table columns - period, year, beg_bal, pmt, principal, interest, end_bal, home_value,
        ltv_ratio, home_equity, pmi, prop_tax, maint, closing_costs, home_sale_cost,
        cumulative_costs, all_in_pmts, home_sale_net, investment, cumulative_investment, down_pmt        
        '''
        df = self.amort_table()
        
        # home value calc, appreciating by home_value_appreciation by pmt_freq per year
        df['home_value'] = self.asset_start_value * np.array([1+(self.appr_rate/self.pmt_freq)]*self.nper).cumprod()
        
        # Loan-to-Value ratio calc: current loan balance / current appraised value
        df['ltv_ratio'] = df['end_bal'] / df['home_value']
        assert np.allclose(df['ltv_ratio'].iloc[-1], 0), "Loan to Value ratio after last payment DOES NOT equal 0.0"
        
        # Equity balance calc: current appraised value - loan balance
        df['home_equity'] = df['home_value'] - df['end_bal']
        assert df['home_equity'].iloc[-1] == df['home_value'].iloc[-1], "home_equity DOES NOT equal home_value at end of loan"
        
        # Private Mortgage Insurance calc, required when LTV > 80%. Loan amount * PMI rate (per year) 
        df['pmi'] =  df['ltv_ratio'].apply(lambda x: self.amt*.01/self.pmt_freq if x > .8 else 0) 
        
        # monthly property value tax calc
        df_tax = df[['year', 'home_value']].groupby('year').min()*self.tax/12
        df_tax = df_tax.rename(columns={'home_value':'prop_tax'})
        df = df.merge(df_tax, how='left', left_on='year', right_index=True)
        
        # monthly maintenance on home calc
        df_maint = df[['year', 'home_value']].groupby('year').min()*self.maint/12
        df_maint = df_maint.rename(columns={'home_value':'maint'})
        df = df.merge(df_maint, how='left', left_on='year', right_index=True)
        
        # closing cost
        if not self.closing_cost_finance:
            closing_costs = np.array([0]*self.nper)
            closing_costs[0] = self.closing_cost
            df['closing_costs'] = closing_costs
        else:
            df['closing_costs'] = 0

        
        # cost of selling house (fees to 3rd parties)
        df['home_sale_cost'] = df['home_value'] * self.home_sale_percent    
        
        # cumulative costs
        costs = df['interest'] + df['pmi'] + df['prop_tax'] + df['maint'] + df['closing_costs']
        df['cumulative_costs'] = costs.cumsum()
        
        # all_in_pmts - used in rent vs buy analysis and profit calc
        df['all_in_pmts'] = df[['pmt', 'pmi', 'prop_tax', 'maint', 'closing_costs']].sum(axis=1)
        d_pmt = np.array([0]*self.nper)
        d_pmt[0] = (self.asset_start_value * self.down_pmt)
        df['down_pmt'] = d_pmt
        df['all_in_pmts'] = df['all_in_pmts'] + df['down_pmt']

        # investment - principal plus down payment
        df['investment'] = df['principal'] + df['down_pmt']
        df['cumulative_investment'] = df['investment'].cumsum()
        df['investment_gains'] = df['home_equity'] - df['cumulative_investment']
        
        # profit_loss on home sale calc - home_equity less home_sale_percent minus cumulative_costs (property tax, pmi, etc.)
        df['home_sale_net'] = df['home_equity'] - df['home_sale_cost'] - df['cumulative_costs']
        df['profit'] = df['home_sale_net'] - df['investment_gains']

        
        return df
    
    def expected_value_cagr(self, end_value, years):
        '''
        Utility function to provide Constant Annual Growth Rate (CAGR) needed to acheive end_value
        '''
        start_value = self.asset_start_value
        cagr = (end_value/start_value)**(1/years) - 1
        return cagr

    def plot_debt_vs_equity(self):
        '''
        Plots the debt and equity curves of the loan amortization table - ending balance and cumulative principal
        '''
        df = self.amort_table()
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

        def get_line(x1, x2, y1, y2):
            points = [(x1, y1), (x2, y2)]
            x_coords, y_coords = zip(*points)
            a = np.vstack([x_coords, np.ones(len(x_coords))]).T
            m, c = np.linalg.lstsq(a, y_coords, rcond=None)[0]
            x = -m
            c = -c
            y = 1
            return {'a':x, 'b':y, 'c':c}

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

    def plot_total_pmt(self):
        '''
        Plots a stacked bar chart showing the all in payment each month through the life of the loan

        Includes interest, principal, property tax, maintenance, and PMI
        '''
        df = self.amort_table_detail()
        df_pmt = df[['year', 'pmt', 'pmi', 'prop_tax', 'maint']]
        data = df_pmt.groupby('year').mean()
        x = data.index
        a = data['pmi']
        b = data['maint']
        c = data['prop_tax']
        d = data['pmt']
        if df_pmt['pmi'].sum() != 0:
            plt.bar(x, data['pmi'], color='y', label='PMI', bottom=b+c+d);
        plt.bar(x, data['maint'], color='r', label='Maintenance', bottom=c+d);
        plt.bar(x, data['prop_tax'], color='b', label='Property Tax', bottom=d);
        plt.bar(x, data['pmt'], color='g', label='Mortgage Payment');
        plt.legend(loc='lower left');
        plt.ylim(self.pmt*.5);
        plt.xlabel('Year');
        plt.ylabel('Payment');
        plt.title('Monthly Total Payment by Year');
    
    def profit_loss_summary(self, monthly=False, expand=True):
        '''
        Returns a dataframe showing the net profit of the home loan over each year
        '''
        df = self.amort_table_detail()
        df = df[['period', 'year', 'interest', 'pmi', 'prop_tax', 'maint', 'closing_costs', 
                 'principal', 'down_pmt']]
        # cumulative_costs, cost_total, cumulative_investment, home_equity, investment_gains, profit
        if monthly:
            df = df.drop(columns='year')
            df = df.cumsum()
            df['period'] = self.amort_table_detail()['period']
            df['home_sale_cost'] = self.amort_table_detail()['home_sale_cost']
            df['cost_total'] = df['interest'] + df['pmi'] + df['prop_tax'] + df['maint'] + df['closing_costs']  + df['home_sale_cost']
            df['investment_total'] = df['principal'] + df['down_pmt']
            df['home_equity'] = self.amort_table_detail()['home_equity']
            df['investment_gains'] = df['home_equity'] - df['investment_total']
            df['profit'] = df['investment_gains'] - df['cost_total']
            df = df[['period', 'interest', 'pmi', 'prop_tax', 'maint', 'closing_costs', 'home_sale_cost', 
                    'cost_total', 'principal', 'down_pmt', 'investment_total', 'home_equity', 
                    'investment_gains', 'profit']]
        else:
            df = df.drop(columns='period')
            df = df.groupby('year').sum()
            df = df.cumsum()
            home_sale_cost = self.amort_table_detail()[['year', 'home_sale_cost']].groupby('year').max()
            df['home_sale_cost'] = home_sale_cost
            df['cost_total'] = df['interest'] + df['pmi'] + df['prop_tax'] + df['maint'] + df['closing_costs'] + df['home_sale_cost']
            df['investment_total'] = df['principal'] + df['down_pmt']
            home_equity = self.amort_table_detail()[['year', 'home_equity']].groupby('year').max()
            df['home_equity'] = home_equity
            df['investment_gains'] = df['home_equity'] - df['investment_total']
            df['profit'] = df['investment_gains'] - df['cost_total']
            df = df[['interest', 'pmi', 'prop_tax', 'maint', 'closing_costs', 'home_sale_cost', 
                    'cost_total', 'principal', 'down_pmt', 'investment_total', 'home_equity', 
                    'investment_gains', 'profit']]

        if expand:
            return df
        else:
            #return df[['home_equity', 'cumulative_investment', 'investment_gains', 'cost_total', 'profit']]
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
    time_years : number of years comparison is carried out to
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

# %%
