import numpy as np
import numpy_financial as npf
import pandas as pd
import matplotlib.pyplot as plt

from .loan_input import LoanInput
from utils.npf_amort import amort


class Loan():
    '''
    API for generating and analyzing mortgage amortization data
    '''
    def __init__(self, loan_params: LoanInput):

        self.asset_start_value = loan_params.asset_amt
        self.rate_annual = loan_params.rate_annual
        self.rate = loan_params.rate_annual / loan_params.pmt_freq
        self.nper = loan_params.num_years * loan_params.pmt_freq
        self.closing_cost = loan_params.closing_cost
        self.closing_cost_finance = loan_params.closing_cost_finance
        self.down_pmt = loan_params.down_pmt
        self.home_sale_percent = loan_params.home_sale_percent
        if loan_params.closing_cost_finance:
            self.amt = (self.asset_start_value*(1-self.down_pmt)) + self.closing_cost
        else:
            self.amt = (self.asset_start_value*(1-self.down_pmt))
        self.pmt = -npf.pmt(self.rate, self.nper, self.amt)
        self.num_years = loan_params.num_years
        self.pmt_freq = loan_params.pmt_freq
        self.tax = loan_params.prop_tax_rate
        self.pmi = loan_params.pmi_rate
        self.maint = loan_params.maint_rate
        self.appr_rate = loan_params.home_value_appreciation
        self.amort_table = amort(self.amt, self.nper, self.pmt, self.pmt_freq, self.rate)

    def amort_table_detail(self) -> pd.DataFrame:
        '''
        Returns amortization table with additional details

        Table columns:
            period - num of payment
            year - periods divided into years based on pmt_freq
            beg_bal - beginning balance of loan in the period
            pmt - mortgage payment
            principal - principal portion of mortgage payment
            interest - interest portion of mortgage payment
            end_bal - ending balance of loan in the period
            home_value - value of home in the period based on compounding growth from self.appr_rate
            ltv_ratio - loan to value ratio of loan
            pmi - private mortage insurance payment (required when less then 20%)
            prop_tax - property tax payment
            maint - estimated maintanence payment
            closing_costs - closing costs of loan (0 if financed through the loan)
            home_sale_cost - cost to sell home (3rd party fees)
            cum_costs - cumulative costs each period
            all_in_pmts - total dollars spent by period: pmt + pmi + prop_tax + maint + closing_costs + down_pmt
            down_pmt - down payment on loan in period 0
            profit - home value at each period less home_sale_cost, cum_costs, down_pmt, end_bal (remaining loan balance)      
        '''

        df = self.amort_table
        df['home_value'] = self.asset_start_value * np.array([1+(self.appr_rate/self.pmt_freq)]*self.nper).cumprod()
        df['ltv_ratio'] = df['end_bal'] / df['home_value']
        df['pmi'] =  df['ltv_ratio'].apply(lambda x: self.amt*.01/self.pmt_freq if x > .8 else 0)
        
        df_tax_maint = df[['year', 'home_value']].groupby('year').min()
        #df_tax_maint = df_tax_maint.rename(columns={'home_value':'prop_tax'})
        df_tax_maint['prop_tax'] = df_tax_maint['home_value']*self.tax/12
        df_tax_maint['maint'] = df_tax_maint['home_value']*self.maint/12
        df = df.merge(df_tax_maint[['prop_tax', 'maint']], how='left', left_on='year', right_index=True)

        if not self.closing_cost_finance:
            closing_costs = np.array([0]*self.nper)
            closing_costs[0] = self.closing_cost
            df['closing_costs'] = closing_costs
        else:
            df['closing_costs'] = 0
        
        costs = df['interest'] + df['pmi'] + df['prop_tax'] + df['maint'] + df['closing_costs']
        df['cum_costs'] = costs.cumsum()

        df['all_in_pmts'] = df[['pmt', 'pmi', 'prop_tax', 'maint', 'closing_costs']].sum(axis=1)
        d_pmt = np.array([0]*self.nper)
        d_pmt[0] = (self.asset_start_value * self.down_pmt)
        df['down_pmt'] = d_pmt
        df['all_in_pmts'] = df['all_in_pmts'] + df['down_pmt']

        df['home_sale_cost'] = df['home_value'] * self.home_sale_percent
        df['profit'] = df['home_value'] - df['home_sale_cost'] - df['cum_costs'] - self.asset_start_value*self.down_pmt - df['end_bal']

        return df



