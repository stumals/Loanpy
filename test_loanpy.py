#%%
from loan.core import Loan
from loan.loan_input import LoanInput
import pytest
import numpy as np

#%%
@pytest.fixture
def loan_data():
    loan_inputs = {'asset_amt': 300000,
                   'rate_annual': .03,
                   'num_years': 30,
                   'pmt_freq': 12,
                   'down_pmt': .20,
                   'closing_cost': 0,
                   'closing_cost_finance': False,
                   'prop_tax_rate': .01,
                   'pmi_rate': .01,
                   'maint_rate': .01,
                   'home_value_appreciation': .03,
                   'home_sale_percent': .06
                   }

    params = LoanInput(**loan_inputs)
    loan_a = Loan(params)
    
    loan_inputs = {'asset_amt': 300000,
                   'rate_annual': .03,
                   'num_years': 15,
                   'pmt_freq': 12,
                   'down_pmt': .20,
                   'closing_cost': 0,
                   'closing_cost_finance': False,
                   'prop_tax_rate': .01,
                   'pmi_rate': .01,
                   'maint_rate': .01,
                   'home_value_appreciation': .03,
                   'home_sale_percent': .06
                   }
    params = LoanInput(**loan_inputs)
    loan_b = Loan(params)
    
    return {'loan_obj':[loan_a, loan_b],
            'loan_data':[loan_a.amort_table_detail(), loan_b.amort_table_detail()]}

def test_periods(loan_data):
    loan_a = loan_data['loan_data'][0]
    loan_b = loan_data['loan_data'][1]

    periods_a = loan_data['loan_obj'][0].nper
    periods_b = loan_data['loan_obj'][1].nper

    assert loan_a.shape[0] == periods_a, "Number of periods DOES NOT equal 360 for 30 year loan"
    assert loan_b.shape[0] == periods_b, "Number of periods DOES NOT equal 180 for 15 year loan"
    

def test_total_pmt(loan_data):
    loan_a = loan_data['loan_data'][0]
    loan_b = loan_data['loan_data'][1]

    interest_a = loan_a.loc[:,'interest']
    principal_a = loan_a.loc[:,'principal']
    pmt_a = loan_a.loc[:,'pmt']

    interest_b = loan_b.loc[:,'interest']
    principal_b = loan_b.loc[:,'principal']
    pmt_b = loan_b.loc[:,'pmt']

    assert np.allclose(interest_a + principal_a, pmt_a), "Interest + Principal DOES NOT equal Payment for 30 year loan"
    assert np.allclose(interest_b + principal_b, pmt_b), "Interest + Principal DOES NOT equal Payment for 15 year loan"
    

def test_end_bal(loan_data):
    loan_a = loan_data['loan_data'][0]
    loan_b = loan_data['loan_data'][1]

    end_bal_a = loan_a['end_bal'].iloc[-1]
    end_bal_b = loan_b['end_bal'].iloc[-1]

    assert np.allclose(end_bal_a, 0), "Ending balance after last payment DOES NOT equal 0.0 for 30 year loan"
    assert np.allclose(end_bal_b, 0), "Ending balance after last payment DOES NOT equal 0.0 for 15 year loan"


def test_beg_bal(loan_data):
    loan_a = loan_data['loan_data'][0]
    loan_b = loan_data['loan_data'][1]

    beg_bal_a = loan_a['beg_bal'].iloc[0]
    beg_bal_b = loan_b['beg_bal'].iloc[0]

    assert np.allclose(beg_bal_a, loan_data['loan_obj'][0].amt), "Beginning loan balance DOES NOT equal loan amount"
    assert np.allclose(beg_bal_b, loan_data['loan_obj'][1].amt), "Beginning loan balance DOES NOT equal loan amount"
     

def test_loan_to_value_ratio(loan_data):
    loan_a = loan_data['loan_data'][0]
    loan_b = loan_data['loan_data'][1]

    ltv_a = loan_a['ltv_ratio'].iloc[-1]
    ltv_b = loan_b['ltv_ratio'].iloc[-1]

    assert np.allclose(ltv_a, 0), "Loan to Value ratio after last payment DOES NOT equal 0.0 for 30 year loan"
    assert np.allclose(ltv_b, 0), "Loan to Value ratio after last payment DOES NOT equal 0.0 for 15 year loan"


def test_all_in_pmts(loan_data):
    loan_a = loan_data['loan_data'][0]
    loan_b = loan_data['loan_data'][1]

    all_in_calc_a = loan_a[['pmt', 'pmi', 'prop_tax', 'maint', 'closing_costs', 'down_pmt']].sum(axis=1)
    all_in_calc_b = loan_b[['pmt', 'pmi', 'prop_tax', 'maint', 'closing_costs', 'down_pmt']].sum(axis=1)

    assert np.allclose(all_in_calc_a, loan_a['all_in_pmts']), "All in payments calc DOES NOT equal all_in_pmts 30 year loan"
    assert np.allclose(all_in_calc_b, loan_b['all_in_pmts']), "All in payments calc DOES NOT equal all_in_pmts 15 year loan"












