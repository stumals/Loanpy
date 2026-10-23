from dataclasses import dataclass
from datetime import date

import numpy as np
import pandas as pd
import statsmodels.api as sm

from econ.fred_econ import FRED, FREDError, fetch_all
from models.models import LinReg

HISTORY_START = '2016-09-01'


@dataclass
class RateForecast:
    '''
    history - date, mgt_rate, ffr: monthly, ffr is the midpoint of the Fed's target range
    projections - date, ffr: the Fed's projected year-end rate, dated December of each year
    forecast - date, ffr, mean, obs_ci_lower, obs_ci_upper: monthly, from the month after the last actual
    cv - mean squared error and adjusted R-squared for each cross-validation fold, then their average
    '''
    history: pd.DataFrame
    projections: pd.DataFrame
    forecast: pd.DataFrame
    cv: pd.DataFrame


def fed_funds_path(last_date: pd.Timestamp, last_value: float, projections: pd.DataFrame) -> pd.DataFrame:
    '''
    Monthly fed funds rate from the month after last_date through the last projection, drawn as straight
    lines from the last actual rate through each later year-end projection
    '''
    later = projections[projections['date'] > last_date]
    if later.empty:
        raise FREDError(f'FRED has no fed funds projections after {last_date:%B %Y}', 'no_data')
    anchor_dates = pd.DatetimeIndex([last_date, *later['date']])
    anchor_values = [last_value, *later['ffr']]
    months = pd.date_range(last_date, anchor_dates[-1], freq='MS')[1:]
    def days(index):
        return [d.toordinal() for d in index]

    values = np.interp(days(months), days(anchor_dates), anchor_values)
    return pd.DataFrame({'date': months, 'ffr': values})


def rate_forecast(fred: FRED, start: str = HISTORY_START, today: date | None = None,
                  alpha: float = .05) -> RateForecast:
    '''
    Forecasts the 30-year mortgage rate from the fed funds rate with a linear regression, using the
    Fed's own projections of the fed funds rate. Intervals are (1 - alpha) prediction intervals.
    '''
    today = today or date.today()
    end = today.isoformat()
    data = fetch_all(fred, {'mgt_rate': ('mgt_rate', start, end, 'm'),
                            'ffr': ('ffr', start, end, 'm'),
                            'ffr_lower': ('ffr_lower', start, end, 'm'),
                            'projections': ('ffr_fcst', f'{today.year}-01-01')})
    history = data['mgt_rate'].merge(data['ffr'], on='date').merge(data['ffr_lower'], on='date')
    if len(history) < 24:
        raise FREDError(f'FRED returned only {len(history)} months of rates since {start}', 'no_data')
    history['ffr'] = (history['ffr'] + history['ffr_lower']) / 2
    history = history[['date', 'mgt_rate', 'ffr']]

    model = LinReg(history[['ffr']], history['mgt_rate'])
    cv = model.test()
    model.train()

    projections = data['projections'].rename(columns={'ffr_fcst': 'ffr'})
    projections['date'] = pd.to_datetime({'year': projections['date'].dt.year, 'month': 12, 'day': 1})

    path = fed_funds_path(history['date'].iloc[-1], history['ffr'].iloc[-1], projections)
    preds = model.predict(sm.add_constant(path[['ffr']], has_constant='add'), alpha=alpha)
    forecast = pd.concat([path, preds.reset_index(drop=True)], axis=1)
    return RateForecast(history, projections, forecast, cv)
