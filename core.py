#%%
import numpy as np
import numpy_financial as npf
import pandas as pd
import matplotlib.pyplot as plt

#%%
class Loan():
    '''
    API for generating and analyzing mortgage amortization data

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
        cumulative_costs, all_in_pmts, investment, cumulative_investment, down_pmt, profit

        profit = home value at each period less cost to sell, cumulative costs, remaining loan balance        
        '''
        df = self.amort_table()
        
        # home value calc, appreciating by home_value_appreciation by pmt_freq per year
        df['home_value'] = self.asset_start_value * np.array([1+(self.appr_rate/self.pmt_freq)]*self.nper).cumprod()
        
        # Loan-to-Value ratio calc: current loan balance / current appraised value
        df['ltv_ratio'] = df['end_bal'] / df['home_value']
        
        # Equity balance calc: current appraised value - loan balance
        df['home_equity'] = df['home_value'] - df['end_bal']
        
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
        
        # profit on home sale calc - home_value less home_sale_percent, cumulative_costs, and remaining loan amount
        # profit not cumulative, calcs profit at each period after selling home
        df['profit'] = df['home_value'] - df['home_sale_cost'] - df['cumulative_costs'] - df['end_bal']

        return df

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
    
    def plot_profit(self, num_years=10, monthly=False):
        '''
        Plot profit by month or year
        profit assumes price of home sold that period less cost to sell, 
        cumulative costs, and remaining loan balance
        '''
        df = self.amort_table_detail()
        df = df[df['year']<=num_years]
        if monthly:
            df_profit = df['profit']
            df_profit.index += 1
            x_max = df_profit.index.to_series().max()
        else:
            df_profit = df[['year', 'profit']].groupby('year').max()
            x_max = df_profit.index.to_series().max()
        plt.plot(df_profit);
        plt.xlabel('Month' if monthly else 'Year');
        plt.ylabel('Profit');
        title = 'Month' if monthly else 'Year'
        plt.title(f'Profit by {title}');
        plt.xlim(1, x_max)
        
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



