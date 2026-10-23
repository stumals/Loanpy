import re
import subprocess
import sys
import threading
import time
from pathlib import Path

import pytest

from econ.fred_econ import FREDError
from tests.fakes import TODAY, FakeFRED
from web import analysis, create_app, fmt
from web.app import TTLCache
from web.forms import MORTGAGE_FORM, read_form

ROOT = Path(__file__).resolve().parent.parent
CALCULATORS = ["/mortgage", "/rent-or-buy", "/down-payments"]
FRED_PAGES = ["/economy", "/forecast"]
NOT_A_NUMBER = re.compile(r"\b(nan|inf|infinity)\b", re.I)


@pytest.fixture
def fred():
    return FakeFRED()


@pytest.fixture
def client(fred):
    app = create_app({"FRED_CLIENT": lambda: fred, "TODAY": TODAY, "TESTING": True})
    return app.test_client()


def page(client, path, status=200):
    response = client.get(path)
    assert response.status_code == status, path
    return response.get_data(as_text=True)


@pytest.mark.parametrize("path", ["/", *CALCULATORS, *FRED_PAGES])
def test_pages_render_without_scripts_or_bad_numbers(client, path):
    response = client.get(path)
    body = response.get_data(as_text=True)
    assert response.status_code == 200
    assert "<script" not in body
    assert not NOT_A_NUMBER.search(re.sub(r"<[^>]+>", " ", body))
    assert response.headers["Content-Security-Policy"].startswith("default-src 'none'")
    assert response.headers["X-Content-Type-Options"] == "nosniff"


@pytest.mark.parametrize(
    "path",
    [
        "/mortgage?rate=0&down=0&closing=12345.67&finance_closing=1",
        "/mortgage?down=99.9&years=1&term=1",
        "/rent-or-buy?rent=0&market_return=0&cap_gains=0",
        "/rent-or-buy?rent=20000&years=30",
        "/down-payments?rate=0&market_return=0&years=30",
        "/down-payments?appreciation=0&sale_cost=0&tax=0&pmi=0&maint=0",
    ],
)
def test_edge_inputs_render(client, path):
    body = page(client, path)
    assert not NOT_A_NUMBER.search(re.sub(r"<[^>]+>", " ", body))


def test_mortgage_page_shows_the_library_numbers(client):
    body = page(client, "/mortgage?price=400000&down=10&rate=6.5&years=10")
    values = read_form(MORTGAGE_FORM, {"price": "400000", "down": "10", "rate": "6.5", "years": "10"}).values
    loan = analysis.loan_from(values)
    assert fmt.money_cents(loan.pmt) in body
    assert fmt.money(loan.profit_breakdown(10)["profit"]) in body
    assert body.count("<tr>") >= 10  # a row per year


def test_missing_inputs_take_defaults_and_inputs_are_kept(client):
    body = page(client, "/mortgage?price=450000")
    assert 'value="450000"' in body
    assert 'value="20"' in body  # the default down payment


def test_financed_closing_costs_raise_the_loan(client):
    assert "$250,000" in page(client, "/mortgage?closing=10000&finance_closing=1")
    assert "$240,000" in page(client, "/mortgage?closing=10000")


@pytest.mark.parametrize(
    "query, field, message",
    [
        ("price=abc", "price", "Enter a number."),
        ("price=nan", "price", "Enter a number."),
        ("price=inf", "price", "Enter a number."),
        ("price=", "price", "Enter a number."),
        ("price=10", "price", "Enter $1,000 or more."),
        ("rate=100", "rate", "Enter less than 100%."),
        ("down=-5", "down", "Enter 0% or more."),
        ("term=12.5", "term", "Enter whole years."),
        ("years=31", "years", "Enter 30 or less, the loan term."),
    ],
)
def test_bad_input_returns_422_with_the_field_marked(client, query, field, message):
    body = page(client, f"/mortgage?{query}", status=422)
    assert message in body
    assert f'aria-describedby="e-{field}"' in body
    assert "Some inputs need a fix" in body
    assert "Profit after" not in body


def test_calculators_accept_formatted_numbers(client):
    page(client, "/mortgage?price=%24350%2C000&rate=6.25%25")


def test_unknown_page_is_a_404_in_the_site_layout(client):
    body = page(client, "/nope", status=404)
    assert "Page not found" in body
    assert 'href="/mortgage"' in body


def test_fred_pages_without_a_key_explain_how_to_add_one():
    client = create_app({"FRED_API_KEY": "", "TESTING": True}).test_client()
    for path in FRED_PAGES:
        body = page(client, path, status=503)
        assert "FRED_API_KEY=" in body
        assert "fredaccount.stlouisfed.org" in body


@pytest.mark.parametrize(
    "kind, message",
    [
        ("refused", "FRED refused the request"),
        ("unreachable", "Couldn't reach FRED"),
        ("no_data", "FRED didn't send the data"),
    ],
)
def test_fred_failures_return_502_with_a_plain_message(kind, message):
    class FailingFRED(FakeFRED):
        def get_fred_data(self, *args, **kwargs):
            raise FREDError("failed", kind, 400 if kind == "refused" else None)

    client = create_app({"FRED_CLIENT": FailingFRED, "TODAY": TODAY, "TESTING": True}).test_client()
    for path in FRED_PAGES:
        assert message in page(client, path, status=502)


def test_fred_data_is_cached(client, fred):
    page(client, "/economy")
    calls = len(fred.calls)
    page(client, "/economy")
    assert len(fred.calls) == calls


def test_economy_page_shows_latest_values(client, fred):
    body = page(client, "/economy")
    latest = fred.monthly.iloc[-1]
    assert fmt.rate(latest["mgt_rate"]) in body
    assert "October 2026" in body


def test_forecast_page_shows_each_year_end(client):
    body = page(client, "/forecast")
    for year in (2026, 2027, 2028, 2029):
        assert f"Dec {year}" in body


def test_web_app_does_not_load_streamlit_or_matplotlib():
    code = (
        "import sys; import web; web.create_app(); "
        "loaded = [m for m in ('streamlit', 'matplotlib') if m in sys.modules]; "
        "assert not loaded, loaded"
    )
    subprocess.run([sys.executable, "-c", code], cwd=ROOT, check=True)


def test_forecast_without_projections_explains_instead_of_crashing():
    client = create_app(
        {"FRED_CLIENT": lambda: FakeFRED(projections={}), "TODAY": TODAY, "TESTING": True}
    ).test_client()
    assert "FRED didn't send the data" in page(client, "/forecast", status=502)


def test_cache_keys_wait_only_for_themselves():
    cache = TTLCache(ttl=60, failure_ttl=60)
    started, release = threading.Event(), threading.Event()

    def slow():
        started.set()
        release.wait(5)
        return "slow"

    worker = threading.Thread(target=cache.get, args=("economy", slow))
    worker.start()
    started.wait(5)
    began = time.monotonic()
    assert cache.get("forecast", lambda: "fast") == "fast"
    assert time.monotonic() - began < 1
    release.set()
    worker.join(5)
    assert cache.get("economy", lambda: "recomputed") == "slow"


def test_cache_remembers_failures_briefly():
    cache = TTLCache(ttl=60, failure_ttl=60)
    calls = []

    def failing():
        calls.append(1)
        raise FREDError("down", "unreachable")

    for _ in range(3):
        with pytest.raises(FREDError):
            cache.get("economy", failing)
    assert len(calls) == 1
