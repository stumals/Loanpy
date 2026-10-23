import numpy as np
import pytest

from loan.compare_down_pmts import CompareDownPayments
from loan.invest import invest
from tests.test_amortization import make_loan


def test_each_contribution_compounds_from_when_it_goes_in():
    contributions = np.zeros(12)
    contributions[0] = 100
    contributions[11] = 100
    account = invest(contributions, 0.12, 12)
    assert account["value"].iloc[11] == pytest.approx(100 * 1.01**12 + 100 * 1.01)
    assert account["contributed"].iloc[11] == 200


def test_only_gains_are_taxed():
    account = invest([1000], 0.12, 12, cap_gains_tax=0.15)
    assert account["tax"].iloc[0] == pytest.approx(10 * 0.15)
    assert account["value_net"].iloc[0] == pytest.approx(1000 + 10 * 0.85)
    assert account["gain_net"].iloc[0] == pytest.approx(10 * 0.85)


def test_rent_vs_buy_gap_is_the_net_worth_gap():
    # Both sides spend the same each month, so owner total less renter total is the difference in net worth.
    loan = make_loan(down_pmt=0.2)
    owner, renter = loan.rent_vs_buy(1800, 0.03, mkt_return=0.10, cap_gains_tax=0.15, num_years_analysis=15)
    end = loan.amort_table_detail().iloc[15 * 12 - 1]
    owner_worth = (
        end["home_value"] - end["home_sale_cost"] - end["end_bal"] + owner["mkt_return_net"].iloc[-1]
    )
    renter_worth = renter["mkt_return_net"].iloc[-1]
    gap = owner["return_total"].iloc[-1] - renter["return_total"].iloc[-1]
    assert gap == pytest.approx(owner_worth - renter_worth)


def test_rent_vs_buy_reports_year_end_values():
    loan = make_loan(down_pmt=0.2)
    owner, renter = loan.rent_vs_buy(1800, 0.03, mkt_return=0.10, cap_gains_tax=0.15, num_years_analysis=2)
    assert list(owner["year"]) == [1, 2]
    assert renter["rent_cumulative"].iloc[1] == pytest.approx(1800 * 12 + 1854 * 12)
    end_of_year_1 = loan.amort_table_detail().iloc[11]
    assert owner["profit"].iloc[0] == pytest.approx(end_of_year_1["profit"])


def test_rent_vs_buy_rejects_years_past_the_loan_term():
    with pytest.raises(ValueError, match="loan term"):
        make_loan(num_years=15).rent_vs_buy(1800, 0.03, num_years_analysis=20)


def compare(down_pmts, mkt_return, **loan):
    cdp = CompareDownPayments(make_loan(**loan), down_pmts)
    cdp.get_compare_down_pmts_data()
    cdp.compare_down_pmts(mkt_return=mkt_return, cap_gains_tax=0.15)
    return cdp


def test_money_invested_is_not_counted_as_profit():
    summary = compare([0, 0.2, 0.5], mkt_return=0).get_summary(10)
    assert np.allclose(summary["mkt_gain"], 0)
    assert np.allclose(summary["total_profit"], summary["profit"])


def test_down_payment_gap_is_the_net_worth_gap():
    # Every down payment spends the same each period, so the gap in totals is the gap in net worth.
    cdp = compare([0.1, 0.4], mkt_return=0.08)
    summary = cdp.get_summary(10)
    worth = []
    for _, df, loan in cdp.loans_dict.values():
        end = loan.amort_table_detail().iloc[10 * 12 - 1]
        worth.append(
            end["home_value"] - end["home_sale_cost"] - end["end_bal"] + df["mkt_return"].iloc[10 * 12 - 1]
        )
    gap = summary["total_profit"].iloc[0] - summary["total_profit"].iloc[1]
    assert gap == pytest.approx(worth[0] - worth[1])


def test_summary_keeps_exact_down_payments():
    assert compare([0.075], mkt_return=0.1).get_summary(10)["down_pmt"].iloc[0] == 0.075


def test_summary_rejects_years_past_the_loan_term():
    with pytest.raises(ValueError, match="loan term"):
        compare([0.2], mkt_return=0.1, num_years=15).get_summary(20)
