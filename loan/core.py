import numpy as np
import numpy_financial as npf
import pandas as pd
import matplotlib.pyplot as plt
from typing import Tuple

from .loan_input import LoanInput
from utils.npf_amort import amort


class Loan():
    
    def __init__(self, loan_params: LoanInput) -> None:

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
        df['profit'] = df['home_value'] - df['home_sale_cost'] - df['cum_costs'] - self.asset_start_value*self.down_pmt - self.amt

        return df
    
    def rent_vs_buy(self, rent: int, rent_increase: float, mkt_return: float=.10,
                    cap_gains_tax: float=.15, num_years_analysis: int=10) -> pd.DataFrame:

        df = self.amort_table_detail()

        df_rent = pd.DataFrame(data=((1+rent_increase)**(df['year'] - 1)) * rent).rename(columns={'year':'rent'})
        df_rent['year'] = df['year']

        df['diff'] = df_rent['rent'] - df['all_in_pmts']
        df['diff'] = df['diff'].apply(lambda x: x if x > 0 else 0)

        df_rent['diff'] = df['all_in_pmts'] - df_rent['rent']
        df_rent['diff'] = df_rent['diff'].apply(lambda x: x if x > 0 else 0)

        df['mkt_return'] = df['diff'].cumsum() * np.array([1+(mkt_return/self.pmt_freq)]*self.nper).cumprod()
        df['diff_cumulative'] = df['diff'].cumsum()
        df['cap_gains_cumulative'] = df['mkt_return'] - df['diff_cumulative']
        df['cap_gains_tax'] = df['cap_gains_cumulative'] * cap_gains_tax
        df['mkt_return_net'] = df['mkt_return'] - df['cap_gains_tax']
        df['return_total'] = df['mkt_return_net'] + df['profit']

        df_rent['mkt_return'] = df_rent['diff'].cumsum() * np.array([1+(mkt_return/self.pmt_freq)]*self.nper).cumprod()
        df_rent['diff_cumulative'] = df_rent['diff'].cumsum()
        df_rent['cap_gains_cumulative'] = df_rent['mkt_return'] - df_rent['diff_cumulative']
        df_rent['cap_gains_tax'] = df_rent['cap_gains_cumulative'] * cap_gains_tax
        df_rent['mkt_return_net'] = df_rent['mkt_return'] - df_rent['cap_gains_tax']
        df_rent['rent_cumulative'] = df_rent['rent'].cumsum()
        df_rent['return_total'] = df_rent['mkt_return_net'] - df_rent['rent_cumulative']

        cols_df = ['year', 'profit', 'diff_cumulative', 'mkt_return_net', 'return_total']
        cols_rent = ['year', 'rent', 'rent_cumulative', 'diff_cumulative', 'mkt_return_net', 'return_total']

        df_year = df.loc[:, cols_df].groupby('year').max().reset_index()
        df_rent_year = df_rent.loc[:, cols_rent].groupby('year').max().reset_index()
        df_year = df_year[df_year['year']<=num_years_analysis]
        df_rent_year = df_rent_year[df_rent_year['year']<=num_years_analysis]
        
        return (df_year, df_rent_year)





