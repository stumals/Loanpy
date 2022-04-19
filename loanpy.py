
#%%
import numpy as np
import numpy_financial as npf
import pandas as pd
import matplotlib.pyplot as plt
#%%
class Loan():
    def __init__(self, asset_amt, rate_annual, num_years, pmt_freq=12, down_pmt=0.0, closing_cost=0,
                 closing_cost_finance=False, prop_tax_rate=.01, pmi_rate=.01, maint_rate=.01,
                 home_value_appreciation=.03, home_sale_percent=.1):
                 
        assert asset_amt > 0, 'asset_amt must be greater than 0'
        assert rate_annual > 0 and rate_annual < 1, 'rate_annual must be between 0 and 1'
        assert down_pmt > 0 and down_pmt < 1, 'down_pmt must be between 0 and 1'
        assert closing_cost > 0, 'closing_cost must be greater than 0'
        assert type(closing_cost_finance)==bool, 'closing_cost_finance must be bool type'
        assert prop_tax_rate > 0 and prop_tax_rate < 1, 'prop_tax_rate must be between 0 and 1'
        assert pmi_rate > 0 and pmi_rate < 1, 'pmi_rate must be between 0 and 1'
        assert maint_rate > 0 and maint_rate < 1, 'maint_rate must be between 0 and 1'
        assert home_value_appreciation > 0 and home_value_appreciation < 1, 'home_value_appreciation must be between 0 and 1'
        assert home_sale_percent > 0 and home_sale_percent < 1, 'home_sale_percent must be between 0 and 1'

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

        # check if calculations are accurate
        assert np.allclose(self.interest + self.principal, self.pmt), "Interest + Principal DOES NOT equal Payment"
        assert np.allclose(self.end_bal[-1], 0), "Ending balance after last payment DOES NOT equal 0.0"
        assert np.allclose(self.beg_bal[0], self.amt), "Beginning loan balance DOES NOT equal loan amount"
        assert len(self.periods)==len(self.pmts)==len(self.interest)==len(self.principal)==len(self.beg_bal) \
               ==len(self.end_bal)==self.nper, "Calculated arrays DO NOT all equal number of periods"
    
    def get_attrs(self):
        d = self.__dict__
        df = pd.DataFrame(index=d.keys(), data=d.values(), columns=['attributes'])
        to_drop = ['pmts', 'periods', 'interest', 'principal', 'beg_bal', 'end_bal']
        return df.drop(to_drop)
    
    def amort_table(self):
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
        
        if not self.closing_cost_finance:
            closing_costs = np.array([0]*self.nper)
            closing_costs[0] = self.closing_cost
            df['closing_costs'] = closing_costs
        else:
            df['closing_costs'] = 0
        
        # cost of selling house (fees to 3rd parties)
        df['home_sale_cost'] = df['home_equity'] * self.home_sale_percent    
        
        # cumulative costs
        costs = df['interest'] + df['pmi'] + df['prop_tax'] + df['maint'] + df['closing_costs']
        df['cumulative_costs'] = costs.cumsum()
        
        # all_in_pmts - used in rent vs buy analysis
        df['all_in_pmts'] = df[['pmt', 'pmi', 'prop_tax', 'maint', 'closing_costs']].sum(axis=1)
        d_pmt = np.array([0]*self.nper)
        d_pmt[0] = (self.asset_start_value * self.down_pmt)
        df['down_pmt'] = d_pmt
        df['all_in_pmts'] = df['all_in_pmts'] + df['down_pmt']
        df = df.drop(columns='down_pmt')
        
        # profit_loss on home sale calc - home_equity less home_sale_percent minus cumulative_costs (property tax, pmi, etc.)
        df['home_sale_net'] = (df['home_equity'] - df['home_sale_cost']) - df['cumulative_costs']
        
        return df
    
    def profit_loss_summary(self, monthly=True, expand=False):
        df = self.amort_table_detail()
        df = df[['period', 'year', 'interest', 'pmi', 'prop_tax', 'maint', 'closing_costs', 'home_sale_cost', 
                 'cumulative_costs', 'home_equity', 'principal']]
        df['cost_total'] = df[['cumulative_costs', 'home_sale_cost']].sum(axis=1)
        #df['investment'] = df['principal'].cumsum() + np.array([self.asset_start_value*self.down_pmt]*df.shape[0]) 
        df['profit'] = df['home_equity'] - df['cumulative_costs']
        if monthly:
            df = df.drop(columns='year')
        else:
            df = df.drop(columns='period')
            df = df.groupby('year').sum()
        if expand:
            return df
        else:
            return df[['home_equity', 'cost_total', 'profit']]
    
    def pmt_matrix(self, bins=10, amt_incrmt=10000, rate_incrmt=.0025):
        assert bins%2 == 0, 'Number of bins must be even'
        #assert amount > 0, 'Amount is not greater than 0'
        #assert rate > 0 and rate < 1, 'Rate is not greater than 0 and less than 1'

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
        return df_pmts.pivot(index='amts', columns='rates', values='pmt')
    



def rent_vs_buy(loan, rent_start, time_years=5, rent_growth=.05, market_returns=.07, cap_gains_tax=.15):
    df = loan.amort_table_detail()
    df['rent'] = ((1+rent_growth)**(df['year'] - 1)) * rent_start
    
    # difference between all in pmts in owning home vs rent goes to invest in stock market
    df['diff'] = df['all_in_pmts'] - df['rent']
    
    # $0 to invest once rent is greater than all in home pmts
    df['diff'] = df['diff'].apply(lambda x: x if x > 0 else 0)
    
    # cumulative monthly investment returns based on diff calculated
    df['investment'] = df['diff'].cumsum() * np.array([1+(market_returns/loan.pmt_freq)]*loan.nper).cumprod()
    df['diff_cumulative'] = df['diff'].cumsum()
    
    # capital gains is amount investment has grown less amount invested
    df['cap_gains_cumulative'] = df['investment'] - df['diff_cumulative']
    
    # only taxing the cap gains, not full investment 
    df['cap_gains_tax'] = df['cap_gains_cumulative'] * cap_gains_tax
    df['investment_net'] = df['investment'] - df['cap_gains_tax']
    
    df2 = df[['year', 'home_sale_net', 'investment_net']].groupby('year').max()
    df2['rent_vs_buy'] = df2['home_sale_net'] - df2['investment_net']
    
    return df2

def buy_vs_buy(loan_a, loan_b, time_years=10, market_returns=.07, cap_gains_tax=.15):
    
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
    
    cols = ['year', 'home_sale_net', 'investment_net', 'return_total']
    
    df_a_year = df_a[cols].groupby('year').max()
    #df_a_year.rename(columns={'home_sale_net':'Option A - Net Home Sale', 'investment_net':'Option A - Net Investment',
    #                          'return_total':'Option A - Return Total'}, inplace=True)
    
    df_b_year = df_b[cols].groupby('year').max()
    #df_b_year.rename(columns={'home_sale_net':'Option B - Net Home Sale', 'investment_net':'Option B - Net Investment',
    #                          'return_total':'Option B - Return Total'}, inplace=True)
    #df_year = pd.concat([df_a_year, df_b_year], axis=1)
    
    #return (df_a.loc[:time_years*12, cols], df_b.loc[:time_years*12, cols], df_year.iloc[:time_years,:])
    return (df_a.loc[:time_years*12-1, cols], df_b.loc[:time_years*12-1, cols], df_a_year.iloc[:time_years,:], df_b_year.iloc[:time_years,:])
    
 #%%

def plot_comparison(option_a, option_b):
    plt.plot(option_a['return_total'], label='Option A');
    plt.plot(option_b['return_total'], label='Option B');
    plt.xlim(0, option_a.shape[0]);
    plt.xlabel('Month');
    plt.ylabel('Return $');
    plt.legend();


#%%
l = Loan(300000,.04,30)
print(l.pmt)
print(l.pmt_matrix(bins=4))

#%%

print(type(False)==bool)