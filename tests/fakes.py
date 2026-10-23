from datetime import date

import numpy as np
import pandas as pd

TODAY = date(2026, 10, 23)


def _monthly_series() -> pd.DataFrame:
    # Made-up rates shaped like the real ones: near zero, a fast climb, then easing.
    months = pd.date_range("2016-09-01", "2026-10-01", freq="MS")
    t = np.arange(len(months))
    upper = np.select([t < 42, t < 66, t < 85, t < 110], [0.75 + 0.25 * (t // 7), 0.25, 4.0, 5.5], default=4.0)
    df = pd.DataFrame({"date": months, "ffr": upper, "ffr_lower": upper - 0.25})
    df["mgt_rate"] = 3.0 + 0.6 * (upper - 0.125) + 0.3 * np.sin(t / 5)
    df["cpi"] = 2.0 + 1.5 * np.sin(t / 15)
    df["home_price_index"] = 190 + 1.2 * t
    df["afford_index"] = 100 + 5 * np.cos(t / 9)
    return df


class FakeFRED:
    """Serves made-up data in the shape FRED.get_fred_data returns, so tests never call FRED."""

    def __init__(self, projections=None):
        self.monthly = _monthly_series()
        if projections is None:
            projections = {2026: 4.25, 2027: 4.0, 2028: 3.6, 2029: 3.35}
        self.projections = pd.DataFrame(
            {
                "date": pd.to_datetime([f"{y}-01-01" for y in projections]),
                "ffr_fcst": list(projections.values()),
            }
        )
        self.calls = []

    def get_fred_data(self, data_id, start_date, end_date=None, frequency=None):
        self.calls.append(data_id)
        if data_id == "ffr_fcst":
            df = self.projections
        else:
            df = self.monthly[["date", data_id]]
        df = df[df["date"] >= pd.Timestamp(start_date)]
        if end_date:
            df = df[df["date"] <= pd.Timestamp(end_date)]
        return df.reset_index(drop=True)
