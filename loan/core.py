import numpy as np
import numpy_financial as npf
import pandas as pd

from .invest import invest
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

        df = self.amort_table.copy()
        df['home_value'] = self.asset_start_value * np.array([1+(self.appr_rate/self.pmt_freq)]*self.nper).cumprod()
        df['ltv_ratio'] = df['end_bal'] / df['home_value']
        df['pmi'] =  df['ltv_ratio'].apply(lambda x: self.amt*self.pmi/self.pmt_freq if x > .8 else 0)
        
        df_tax_maint = df[['year', 'home_value']].groupby('year').min()
        #df_tax_maint = df_tax_maint.rename(columns={'home_value':'prop_tax'})
        df_tax_maint['prop_tax'] = df_tax_maint['home_value']*self.tax/self.pmt_freq
        df_tax_maint['maint'] = df_tax_maint['home_value']*self.maint/self.pmt_freq
        df = df.merge(df_tax_maint[['prop_tax', 'maint']], how='left', left_on='year', right_index=True)

        if not self.closing_cost_finance:
            closing_costs = np.zeros(self.nper)
            closing_costs[0] = self.closing_cost
            df['closing_costs'] = closing_costs
        else:
            df['closing_costs'] = 0
        
        costs = df['interest'] + df['pmi'] + df['prop_tax'] + df['maint'] + df['closing_costs']
        df['cum_costs'] = costs.cumsum()

        df['all_in_pmts'] = df[['pmt', 'pmi', 'prop_tax', 'maint', 'closing_costs']].sum(axis=1)
        d_pmt = np.zeros(self.nper)
        d_pmt[0] = (self.asset_start_value * self.down_pmt)
        df['down_pmt'] = d_pmt
        df['all_in_pmts'] = df['all_in_pmts'] + df['down_pmt']

        df['home_sale_cost'] = df['home_value'] * self.home_sale_percent
        df['profit'] = df['home_value'] - df['home_sale_cost'] - df['cum_costs'] - self.asset_start_value*self.down_pmt - self.amt

        return df
    
    def check_years(self, num_years: int) -> None:
        '''
        Raises ValueError unless num_years is between 1 and the loan term
        '''
        if not 1 <= num_years <= self.num_years:
            raise ValueError(f'years to analyze ({num_years}) must be between 1 and the loan term ({self.num_years})')

    def rent_vs_buy(self, rent: float, rent_increase: float, mkt_return: float=.10,
                    cap_gains_tax: float=.15, num_years_analysis: int=10) -> tuple[pd.DataFrame, pd.DataFrame]:
        '''
        Compares owning the home against renting on the same budget

        Each period the owner and the renter both spend the larger of the all-in ownership cost and the rent
        (rent is per period). Whoever pays less for housing invests the difference in the market.

        Totals are wealth gained net of every dollar spent, so owner total less renter total is the
        difference in net worth between the two:
            owner return_total - profit if the home were sold, plus after-tax market gains
            renter return_total - after-tax market gains, less all rent paid

        Returns one row per year for the owner and one for the renter, with values at the end of each year.

        Table columns:
            year - loan year
            profit - owner's profit if the home were sold (owner only)
            rent, rent_cumulative - rent per period, and all rent paid so far (renter only)
            diff_cumulative - money invested so far
            mkt_return_net - market account value after capital gains tax
            mkt_gain_net - market gains after capital gains tax
            return_total - wealth gained net of every dollar spent
        '''
        self.check_years(num_years_analysis)
        df = self.amort_table_detail()
        rent_pmts = rent * (1 + rent_increase) ** (df['year'] - 1)

        def side(contributions):
            account = invest(contributions.clip(lower=0), mkt_return, self.pmt_freq, cap_gains_tax)
            return pd.DataFrame({'year': df['year'],
                                 'diff_cumulative': account['contributed'],
                                 'mkt_return_net': account['value_net'],
                                 'mkt_gain_net': account['gain_net']})

        owner = side(rent_pmts - df['all_in_pmts'])
        owner['profit'] = df['profit']
        owner['return_total'] = owner['profit'] + owner['mkt_gain_net']

        renter = side(df['all_in_pmts'] - rent_pmts)
        renter['rent'] = rent_pmts
        renter['rent_cumulative'] = rent_pmts.cumsum()
        renter['return_total'] = renter['mkt_gain_net'] - renter['rent_cumulative']

        cols_owner = ['year', 'profit', 'diff_cumulative', 'mkt_return_net', 'mkt_gain_net', 'return_total']
        cols_renter = ['year', 'rent', 'rent_cumulative', 'diff_cumulative', 'mkt_return_net', 'mkt_gain_net',
                       'return_total']

        def by_year(table, cols):
            table = table.loc[:, cols].groupby('year').last().reset_index()
            return table[table['year'] <= num_years_analysis]

        return (by_year(owner, cols_owner), by_year(renter, cols_renter))
