from loanpy import Loan
import pytest
import numpy as np


#%%

@pytest.fixture
def loan_data():
    return [Loan(300000, .03, 30), Loan(500000, .03, 15)]

def test_total_pmt(loan_data):
    assert np.allclose(loan_data[0].interest + loan_data[0].principal, loan_data[0].pmt), "Interest + Principal DOES NOT equal Payment"
    assert np.allclose(loan_data[1].interest + loan_data[1].principal, loan_data[1].pmt), "Interest + Principal DOES NOT equal Payment"
    
def test_end_bal(loan_data):
    assert np.allclose(loan_data[0].end_bal[-1], 0), "Ending balance after last payment DOES NOT equal 0.0"
    assert np.allclose(loan_data[1].end_bal[-1], 0), "Ending balance after last payment DOES NOT equal 0.0"

def test_beg_bal(loan_data):
    assert np.allclose(loan_data[0].beg_bal[0], loan_data[0].amt), "Beginning loan balance DOES NOT equal loan amount"
    assert np.allclose(loan_data[1].beg_bal[0], loan_data[1].amt), "Beginning loan balance DOES NOT equal loan amount"
    
def test_amort_len(loan_data):
    assert len(loan_data[0].periods)==len(loan_data[0].pmts)==len(loan_data[0].interest)==len(loan_data[0].principal)==len(loan_data[0].beg_bal) \
       ==len(loan_data[0].end_bal)==loan_data[0].nper, "Calculated arrays DO NOT all equal number of periods"
    assert len(loan_data[1].periods)==len(loan_data[1].pmts)==len(loan_data[1].interest)==len(loan_data[1].principal)==len(loan_data[1].beg_bal) \
       ==len(loan_data[1].end_bal)==loan_data[1].nper, "Calculated arrays DO NOT all equal number of periods"












