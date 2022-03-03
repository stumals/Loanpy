from loanpy import Loan
import pytest
import numpy as np


#%%

@pytest.fixture
def loan_data():
    return Loan(300000, .03, 30)

def test_total_pmt(loan_data):
    assert np.allclose(loan_data.interest + loan_data.principal, loan_data.pmt), "Interest + Principal DOES NOT equal Payment"
    
def test_end_bal(loan_data):
    assert np.allclose(loan_data.end_bal[-1], 0), "Ending balance after last payment DOES NOT equal 0.0"

def test_beg_bal(loan_data):
    assert np.allclose(loan_data.beg_bal[0], loan_data.amt), "Beginning loan balance DOES NOT equal loan amount"
    
def test_amort_len(loan_data):
    assert len(loan_data.periods)==len(loan_data.pmts)==len(loan_data.interest)==len(loan_data.principal)==len(loan_data.beg_bal) \
       ==len(loan_data.end_bal)==loan_data.nper, "Calculated arrays DO NOT all equal number of periods"
    













