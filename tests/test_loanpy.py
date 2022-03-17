from loanpy import Loan
import pytest
import numpy as np


#%%

@pytest.fixture
def loan_data1():
    return Loan(300000, .03, 30)

def test_total_pmt(loan_data1):
    assert np.allclose(loan_data1.interest + loan_data1.principal, loan_data1.pmt), "Interest + Principal DOES NOT equal Payment"
    
def test_end_bal(loan_data1):
    assert np.allclose(loan_data1.end_bal[-1], 0), "Ending balance after last payment DOES NOT equal 0.0"

def test_beg_bal(loan_data1):
    assert np.allclose(loan_data1.beg_bal[0], loan_data1.amt), "Beginning loan balance DOES NOT equal loan amount"
    
def test_amort_len(loan_data1):
    assert len(loan_data1.periods)==len(loan_data1.pmts)==len(loan_data1.interest)==len(loan_data1.principal)==len(loan_data1.beg_bal) \
       ==len(loan_data1.end_bal)==loan_data1.nper, "Calculated arrays DO NOT all equal number of periods"
    













