#%%
import numpy as np
import numpy_financial as npf
import pandas as pd

def amort(amt, nper, pmt, pmt_freq, rate):
    periods = np.arange(1, nper + 1, dtype=int)
    year_func = np.vectorize(lambda x: x // pmt_freq if x % pmt_freq == 0 else x // pmt_freq + 1)
    years = year_func(periods)
    pmts = np.array([pmt] * nper)
    interest = -npf.ipmt(rate, periods, nper, amt)
    principal = -npf.ppmt(rate, periods, nper, amt)

    def balance(pv, rate, nper, pmt):
        d = (1 + rate) ** nper
        return pv * d - pmt*(d - 1)/rate
    
    beg_bal = balance(amt, rate, periods - 1, pmt)
    end_bal = balance(amt, rate, periods, pmt)

    df = pd.DataFrame()
    df['period'] = periods
    df['year'] = years
    df['beg_bal'] = beg_bal
    df['pmt'] = pmts
    df['principal'] = principal
    df['interest'] = interest
    df['end_bal'] = end_bal

    return df
