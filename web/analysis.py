"""What each page shows, computed by the Loanpy library. Payments are monthly on every page."""

import math
from collections.abc import Callable
from datetime import date

import pandas as pd
from dateutil.relativedelta import relativedelta

from econ.fred_econ import FRED, FREDError, fetch_all
from loan.compare_down_pmts import CompareDownPayments
from loan.core import Loan
from loan.loan_input import LoanInput
from models.forecast import rate_forecast

from . import fmt
from .charts import Band, Line, Marker, Stack, line_chart, stacked_bars

MONTHS = 12
DOWN_PAYMENTS = [d / 100 for d in range(0, 100, 5)]


def loan_from(values: dict, down: float | None = None) -> Loan:
    return Loan(
        LoanInput(
            asset_amt=values["price"],
            rate_annual=values["rate"],
            num_years=values["term"],
            pmt_freq=MONTHS,
            down_pmt=values["down"] if down is None else down,
            closing_cost=values["closing"],
            closing_cost_finance=values["finance_closing"],
            prop_tax_rate=values["tax"],
            pmi_rate=values["pmi"],
            maint_rate=values["maint"],
            home_value_appreciation=values["appreciation"],
            home_sale_percent=values["sale_cost"],
        )
    )


def _year(x: float) -> str:
    return f"Year {x:g}"


def _year_tick(x: float) -> str:
    return f"{x:g}"


def _month(x: float) -> str:
    year = math.floor(x + 1e-9)
    return date(year, round((x - year) * 12) + 1, 1).strftime("%b %Y")


def _decimal_year(d: pd.Timestamp) -> float:
    return d.year + (d.month - 1) / 12


def _date_ticks(xs: list[float]) -> tuple[list[float], Callable[[float], str]]:
    """Ticks at each new year, or at each quarter when that would leave fewer than three."""
    years = [y for y in range(math.ceil(xs[0]), math.floor(xs[-1]) + 1)]
    if len(years) >= 3:
        return years, lambda x: f"{x:.0f}"
    quarters = [q / 4 for q in range(math.ceil(xs[0] * 4), math.floor(xs[-1] * 4) + 1)]
    return quarters, _month


def mortgage(values: dict) -> dict:
    loan = loan_from(values)
    years = values["years"]
    yearly = loan.yearly_summary()
    yearly = yearly[yearly["year"] <= years]
    parts = loan.profit_breakdown(years)
    average = loan.average_payment_by_year()
    average = average[average["year"] <= years]
    monthly_costs = ["principal", "interest", "pmi", "prop_tax", "maint"]

    xs = list(yearly["year"])
    labels = {
        "principal": "Principal",
        "interest": "Interest",
        "pmi": "PMI",
        "prop_tax": "Property tax",
        "maint": "Maintenance",
    }
    payments_chart = stacked_bars(
        "Average monthly payment",
        xs,
        [Stack(labels[c], list(average[c]), slot) for slot, c in enumerate(monthly_costs, 1)],
        y_tick=fmt.money_short,
        y_value=fmt.money,
        x_tick=_year_tick,
        x_label=_year,
    )
    value_chart = line_chart(
        "Home value and loan balance",
        [
            Line("Home value", xs, list(yearly["home_value"]), 1),
            Line("Loan balance", xs, list(yearly["end_bal"]), 2),
        ],
        y_tick=fmt.money_short,
        y_value=fmt.money,
        x_tick=_year_tick,
        x_label=_year,
        include_zero=True,
    )
    profit_chart = line_chart(
        "Profit if you sell",
        [Line("Profit", xs, list(yearly["profit"]), 1)],
        y_tick=fmt.money_short,
        y_value=fmt.money,
        x_tick=_year_tick,
        x_label=_year,
        include_zero=True,
    )

    breakdown = [
        ("Home value growth", parts["appreciation"]),
        ("Interest", parts["interest"]),
        ("Mortgage insurance (PMI)", parts["pmi"]),
        ("Property tax", parts["prop_tax"]),
        ("Maintenance", parts["maint"]),
        ("Closing costs", parts["closing_costs"]),
        ("Cost to sell", parts["home_sale_cost"]),
    ]
    return {
        "years": years,
        "loan_amt": loan.amt,
        "payment": loan.pmt,
        "first_year_monthly": average[monthly_costs].iloc[0].sum(),
        "cash_at_closing": loan.cash_at_closing,
        "profit": parts["profit"],
        "breakdown": [(label, amount) for label, amount in breakdown if round(amount)],
        "rows": yearly.to_dict("records"),
        "charts": [payments_chart, value_chart, profit_chart],
    }


def rent_vs_buy(values: dict) -> dict:
    loan = loan_from(values)
    years = values["years"]
    owner, renter = loan.rent_vs_buy(
        values["rent"],
        rent_increase=values["rent_increase"],
        mkt_return=values["market_return"],
        cap_gains_tax=values["cap_gains"],
        num_years_analysis=years,
    )
    gap = owner["return_total"] - renter["return_total"]
    ahead = gap > 0
    # The first year buying is ahead and stays ahead through the end.
    breakeven = None
    for year, is_ahead in zip(reversed(owner["year"].tolist()), reversed(ahead.tolist()), strict=True):
        if not is_ahead:
            break
        breakeven = year

    xs = list(owner["year"])
    chart = line_chart(
        "Wealth gained, net of everything spent",
        [Line("Buy", xs, list(owner["return_total"]), 1), Line("Rent", xs, list(renter["return_total"]), 2)],
        y_tick=fmt.money_short,
        y_value=fmt.money,
        x_tick=_year_tick,
        x_label=_year,
        include_zero=True,
    )
    rows = [
        {
            "year": o["year"],
            "rent": r["rent"],
            "profit": o["profit"],
            "owner_gain": o["mkt_gain_net"],
            "owner_total": o["return_total"],
            "rent_paid": r["rent_cumulative"],
            "renter_gain": r["mkt_gain_net"],
            "renter_total": r["return_total"],
            "gap": g,
        }
        for o, r, g in zip(owner.to_dict("records"), renter.to_dict("records"), gap, strict=True)
    ]
    return {
        "years": years,
        "owner_total": owner["return_total"].iloc[-1],
        "renter_total": renter["return_total"].iloc[-1],
        "gap": gap.iloc[-1],
        "breakeven": breakeven,
        "rows": rows,
        "charts": [chart],
    }


def down_payments(values: dict) -> dict:
    years = values["years"]
    cdp = CompareDownPayments(loan_from(values, down=0), DOWN_PAYMENTS)
    cdp.get_compare_down_pmts_data()
    cdp.compare_down_pmts(mkt_return=values["market_return"], cap_gains_tax=values["cap_gains"])
    summary = cdp.get_summary(years_compare=years)
    best = summary.loc[summary["total_profit"].idxmax()]

    pct = [d * 100 for d in summary["down_pmt"]]
    chart = line_chart(
        f"Total after {years} years, by down payment",
        [Line("Total", pct, list(summary["total_profit"]), 1)],
        y_tick=fmt.money_short,
        y_value=fmt.money,
        x_tick=lambda x: f"{x:g}%",
        x_label=lambda x: f"{x:g}% down",
        x_ticks=list(range(0, 100, 10)),
        markers=[Marker(best["down_pmt"] * 100, best["total_profit"], 1)],
        end_labels=False,
        include_zero=True,
    )
    rows = summary.to_dict("records")
    for row in rows:
        row["best"] = row["down_pmt"] == best["down_pmt"]
    return {"years": years, "best": best.to_dict(), "rows": rows, "charts": [chart]}


ECONOMIC_SERIES = [
    {
        "id": "mgt_rate",
        "title": "30-year mortgage rate",
        "unit": "rate",
        "info": "Average rate on a 30-year fixed-rate mortgage in the US, from Freddie Mac's weekly survey.",
    },
    {
        "id": "cpi",
        "title": "Inflation",
        "unit": "rate",
        "info": "Change in consumer prices from a year earlier: the Consumer Price Index for all urban consumers.",
    },
    {
        "id": "home_price_index",
        "title": "Home prices",
        "unit": "index",
        "info": "S&P Case-Shiller U.S. National Home Price Index, not seasonally adjusted. "
        "January 2000 is 100, so 300 means prices tripled since then.",
    },
    {
        "id": "afford_index",
        "title": "Housing affordability",
        "unit": "index",
        "info": "From the National Association of Realtors. At 100, a family earning the median income can just "
        "qualify for a mortgage on a median-priced home with 20% down. Higher is more affordable. "
        "FRED shares only the latest 13 months.",
    },
]


def economy(fred: FRED, today: date) -> dict:
    start = (today - relativedelta(years=5)).isoformat()
    series = []
    by_month: dict[pd.Timestamp, dict[str, str]] = {}
    data = fetch_all(fred, {spec["id"]: (spec["id"], start, today.isoformat(), "m") for spec in ECONOMIC_SERIES})
    for spec in ECONOMIC_SERIES:
        df = data[spec["id"]]
        if df.empty:
            raise FREDError(f"FRED returned no data for {spec['id']} since {start}", "no_data")
        values = df[spec["id"]]
        show = fmt.rate if spec["unit"] == "rate" else lambda v: fmt.number(v, 1)
        xs = [_decimal_year(d) for d in df["date"]]
        ticks, tick_label = _date_ticks(xs)
        chart = line_chart(
            spec["title"],
            [Line(spec["title"], xs, list(values), 1)],
            y_tick=(lambda v: f"{v:g}%") if spec["unit"] == "rate" else (lambda v: f"{v:g}"),
            y_value=show,
            x_tick=tick_label,
            x_label=_month,
            x_ticks=ticks,
            end_labels=False,
            show_title=False,
            width=500,
            height=220,
        )
        series.append(
            {
                **spec,
                "latest": show(values.iloc[-1]),
                "as_of": df["date"].iloc[-1].strftime("%B %Y"),
                "chart": chart,
            }
        )
        for d, v in zip(df["date"], values, strict=True):
            by_month.setdefault(d, {})[spec["id"]] = show(v)
    rows = [
        {"month": d.strftime("%b %Y"), "cells": [cells.get(spec["id"], "") for spec in ECONOMIC_SERIES]}
        for d, cells in sorted(by_month.items(), reverse=True)
    ]
    return {"series": series, "rows": rows}


def forecast(fred: FRED, today: date) -> dict:
    fc = rate_forecast(fred, today=today)
    hist, path = fc.history, fc.forecast
    hx = [_decimal_year(d) for d in hist["date"]]
    fx = [_decimal_year(d) for d in path["date"]]
    last = hist.iloc[-1]
    # Start the dashed lines at the last actual month so they connect.
    joined_x = [hx[-1], *fx]
    chart = line_chart(
        "Mortgage and fed funds rates, with forecast",
        [
            Line("30-year mortgage rate", hx, list(hist["mgt_rate"]), 1),
            Line("Fed funds rate", hx, list(hist["ffr"]), 2),
            Line("Mortgage rate forecast", joined_x, [last["mgt_rate"], *path["mean"]], 1, True, False),
            Line("Fed funds projection", joined_x, [last["ffr"], *path["ffr"]], 2, True, False),
        ],
        bands=[Band("95% prediction interval", fx, list(path["obs_ci_lower"]), list(path["obs_ci_upper"]), 1)],
        extra_legend=[("Forecast", "line", 0, True)],
        y_tick=lambda v: f"{v:g}%",
        y_value=fmt.rate,
        x_tick=lambda x: f"{x:.0f}",
        x_label=_month,
        x_ticks=list(range(int(hx[0]) + 1, int(fx[-1]) + 1, 2)),
        end_labels=False,
        include_zero=True,
        width=1000,
        height=360,
    )
    year_ends = path[path["date"].dt.month == 12]
    cv = fc.cv.rename(columns={"MSE_train": "mse_train", "MSE_test": "mse_test", "R-Squared Adj": "r2"})
    months = [
        {
            "date": row["date"],
            "mgt_rate": row["mean"],
            "ffr": row["ffr"],
            "lower": row["obs_ci_lower"],
            "upper": row["obs_ci_upper"],
            "forecast": True,
        }
        for row in path.to_dict("records")
    ] + [{**row, "forecast": False} for row in hist.to_dict("records")]
    return {
        "as_of": last["date"].strftime("%B %Y"),
        "months": sorted(months, key=lambda row: row["date"], reverse=True),
        "mortgage_now": last["mgt_rate"],
        "ffr_now": last["ffr"],
        "year_ends": year_ends.to_dict("records"),
        "cv": cv.to_dict("records"),
        "charts": [chart],
    }
