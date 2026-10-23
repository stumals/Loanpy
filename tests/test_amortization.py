import itertools

import numpy as np
import pytest

from loan.core import Loan
from loan.loan_input import LoanInput

BASE = {
    "asset_amt": 300000,
    "rate_annual": 0.05,
    "num_years": 30,
    "pmt_freq": 12,
    "down_pmt": 0.10,
    "closing_cost": 0,
    "closing_cost_finance": False,
    "prop_tax_rate": 0.01,
    "pmi_rate": 0.01,
    "maint_rate": 0.01,
    "home_value_appreciation": 0.05,
    "home_sale_percent": 0.06,
}


def make_loan(**overrides):
    return Loan(LoanInput(**{**BASE, **overrides}))


def test_pmi_uses_the_pmi_rate():
    df = make_loan(pmi_rate=0.005).amort_table_detail()
    assert df["pmi"].iloc[0] == pytest.approx(270000 * 0.005 / 12)


def test_tax_and_maintenance_follow_the_payment_frequency():
    df = make_loan(pmt_freq=26).amort_table_detail()
    year1 = df[df["year"] == 1]
    start_value = year1["home_value"].min()
    assert year1["prop_tax"].sum() == pytest.approx(start_value * 0.01)
    assert year1["maint"].sum() == pytest.approx(start_value * 0.01)


def test_zero_rate_loan_amortizes_without_nan():
    df = make_loan(rate_annual=0).amort_table_detail()
    assert np.isfinite(df.select_dtypes("number").to_numpy()).all()
    assert df["interest"].sum() == 0
    assert df["principal"].iloc[0] == pytest.approx(270000 / 360)
    assert df["end_bal"].iloc[-1] == pytest.approx(0)


def test_down_payment_and_closing_costs_keep_cents():
    df = make_loan(asset_amt=333333, down_pmt=0.2, closing_cost=1234.56).amort_table_detail()
    assert df["down_pmt"].iloc[0] == pytest.approx(66666.6)
    assert df["closing_costs"].iloc[0] == pytest.approx(1234.56)


def test_detail_leaves_the_base_table_alone():
    loan = make_loan()
    columns = list(loan.amort_table.columns)
    loan.amort_table_detail()
    assert list(loan.amort_table.columns) == columns


@pytest.mark.parametrize(
    "rate, down, finance, freq",
    list(itertools.product([0, 0.05], [0, 0.2, 0.5], [False, True], [12, 26])),
)
def test_detail_invariants(rate, down, finance, freq):
    loan = make_loan(rate_annual=rate, down_pmt=down, closing_cost=5000, closing_cost_finance=finance, pmt_freq=freq)
    df = loan.amort_table_detail()

    assert np.isfinite(df.select_dtypes("number").to_numpy()).all()
    assert len(df) == loan.nper
    assert df["principal"].sum() == pytest.approx(loan.amt)
    assert df["closing_costs"].sum() + (loan.amt - 300000 * (1 - down)) == pytest.approx(5000)

    parts = df[["pmt", "pmi", "prop_tax", "maint", "closing_costs", "down_pmt"]].sum(axis=1)
    assert np.allclose(parts, df["all_in_pmts"])

    # Profit if sold: sale proceeds less everything paid in, period by period.
    paid_in = df["down_pmt"].cumsum() + df["principal"].cumsum() + df["cum_costs"]
    proceeds = df["home_value"] - df["home_sale_cost"] - df["end_bal"]
    assert np.allclose(df["profit"], proceeds - paid_in)


@pytest.mark.parametrize("finance", [False, True])
def test_yearly_summary_counts_each_period_once(finance):
    loan = make_loan(closing_cost=5000, closing_cost_finance=finance)
    detail = loan.amort_table_detail()
    yearly = loan.yearly_summary()

    assert list(yearly["year"]) == list(range(1, 31))
    for col in [
        "principal",
        "interest",
        "pmi",
        "prop_tax",
        "maint",
        "closing_costs",
        "down_pmt",
        "all_in_pmts",
    ]:
        assert yearly[col].sum() == pytest.approx(detail[col].sum())
    year_ends = detail.groupby("year").tail(1).reset_index(drop=True)
    for col in ["end_bal", "home_value", "profit"]:
        assert np.allclose(yearly[col], year_ends[col])


@pytest.mark.parametrize("finance", [False, True])
@pytest.mark.parametrize("years", [1, 7, 30])
def test_profit_breakdown_sums_to_profit(finance, years):
    loan = make_loan(closing_cost=5000, closing_cost_finance=finance)
    parts = loan.profit_breakdown(years)
    profit = parts.pop("profit")
    assert sum(parts.values()) == pytest.approx(profit)
    assert profit == pytest.approx(loan.yearly_summary()["profit"].iloc[years - 1])
    assert parts["closing_costs"] == -5000


def test_profit_breakdown_rejects_years_past_the_loan_term():
    with pytest.raises(ValueError, match="loan term"):
        make_loan(num_years=15).profit_breakdown(16)


@pytest.mark.parametrize("finance, cash", [(False, 60000 + 5000), (True, 60000)])
def test_cash_at_closing(finance, cash):
    assert make_loan(down_pmt=0.2, closing_cost=5000, closing_cost_finance=finance).cash_at_closing == cash


def test_average_payment_by_year_is_yearly_totals_per_payment():
    loan = make_loan(pmt_freq=26)
    average, yearly = loan.average_payment_by_year(), loan.yearly_summary()
    for col in ["principal", "interest", "pmi", "prop_tax", "maint"]:
        assert np.allclose(average[col] * 26, yearly[col])


def test_detail_is_computed_once_and_callers_get_their_own_copy():
    loan = make_loan()
    first = loan.amort_table_detail()
    first["profit"] = 0
    assert loan.amort_table_detail()["profit"].iloc[-1] != 0
    assert loan._detail is not None
