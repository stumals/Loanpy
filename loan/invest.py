import numpy as np
import pandas as pd


def invest(contributions, rate_annual: float, pmt_freq: int, cap_gains_tax: float = 0) -> pd.DataFrame:
    '''
    Grows per-period contributions in a market account

    Each contribution goes in at the start of its period and compounds at rate_annual / pmt_freq
    from then on. Gains are taxed at cap_gains_tax as if the account were sold that period.

    Table columns:
        contributed - cumulative contributions
        value - account value before tax
        gain - value less contributions
        tax - capital gains tax due on the gain
        value_net - value after tax
        gain_net - gain after tax
    '''
    contributions = np.asarray(contributions, dtype=float)
    growth = 1 + rate_annual / pmt_freq
    values = np.empty(len(contributions))
    value = 0.0
    for i, c in enumerate(contributions):
        value = (value + c) * growth
        values[i] = value

    df = pd.DataFrame({'contributed': contributions.cumsum(), 'value': values})
    df['gain'] = df['value'] - df['contributed']
    df['tax'] = df['gain'].clip(lower=0) * cap_gains_tax
    df['value_net'] = df['value'] - df['tax']
    df['gain_net'] = df['gain'] - df['tax']
    return df
