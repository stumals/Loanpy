import pandas as pd
import pytest
import requests

from econ import fred_econ
from econ.fred_econ import FRED, FREDError, fetch_all
from models.forecast import fed_funds_path, rate_forecast
from tests.fakes import TODAY, FakeFRED


class FakeResponse:
    def __init__(self, status_code, body):
        self.status_code = status_code
        self.body = body

    def json(self):
        if self.body is None:
            raise ValueError("not JSON")
        return self.body


@pytest.fixture
def http(monkeypatch):
    """Replaces requests.get in the FRED client; set .response, read .params."""

    class Http:
        response = FakeResponse(200, {"observations": []})
        params = None
        timeout = None

    def get(url, params=None, timeout=None):
        Http.params, Http.timeout = params, timeout
        if isinstance(Http.response, Exception):
            raise Http.response
        return Http.response

    monkeypatch.setattr(fred_econ.requests, "get", get)
    return Http


def test_parses_observations_and_skips_missing_values(http):
    http.response = FakeResponse(
        200,
        {
            "observations": [
                {"date": "2026-08-01", "value": "6.5"},
                {"date": "2026-09-01", "value": "."},
                {"date": "2026-10-01", "value": "6.25"},
            ]
        },
    )
    df = FRED(api_key="k").get_fred_data("mgt_rate", "2026-08-01", "2026-10-31", "m")
    assert list(df.columns) == ["date", "mgt_rate"]
    assert df["mgt_rate"].tolist() == [6.5, 6.25]
    assert df["date"].tolist() == [pd.Timestamp("2026-08-01"), pd.Timestamp("2026-10-01")]


def test_request_parameters(http):
    FRED(api_key="k").get_fred_data("cpi", "2021-01-01", "2026-10-23", "m")
    assert http.params["series_id"] == "CPIAUCSL"
    assert http.params["api_key"] == "k"
    assert http.params["units"] == "pc1"
    assert http.params["frequency"] == "m"
    assert http.params["aggregation_method"] == "eop"
    assert http.timeout

    FRED(api_key="k").get_fred_data("ffr_fcst", "2026-01-01")
    assert http.params["series_id"] == "FEDTARCTM"
    assert http.params["units"] is None
    assert http.params["frequency"] is None
    assert http.params["aggregation_method"] is None


def test_refused_request_raises(http):
    http.response = FakeResponse(400, {"error_code": 400, "error_message": "Bad Request. api_key is not registered."})
    with pytest.raises(FREDError) as e:
        FRED(api_key="bad").get_fred_data("mgt_rate", "2026-01-01")
    assert e.value.kind == "refused"
    assert e.value.status == 400


def test_unreachable_fred_raises(http):
    http.response = requests.ConnectTimeout("timed out")
    with pytest.raises(FREDError) as e:
        FRED(api_key="k").get_fred_data("mgt_rate", "2026-01-01")
    assert e.value.kind == "unreachable"


@pytest.mark.parametrize("body", [None, {}, {"observations": None}])
def test_answer_without_observations_raises(http, body):
    http.response = FakeResponse(200, body)
    with pytest.raises(FREDError) as e:
        FRED(api_key="k").get_fred_data("mgt_rate", "2026-01-01")
    assert e.value.kind == "no_data"


def test_api_key_comes_from_the_environment(monkeypatch):
    monkeypatch.setenv("FRED_API_KEY", "from-env")
    assert FRED().api_key == "from-env"


def test_fed_funds_path_runs_through_each_projection():
    projections = pd.DataFrame(
        {"date": pd.to_datetime(["2026-12-01", "2027-12-01"]), "ffr": [4.25, 4.0]},
    )
    path = fed_funds_path(pd.Timestamp("2026-10-01"), 3.875, projections)
    assert path["date"].iloc[0] == pd.Timestamp("2026-11-01")
    assert path["date"].iloc[-1] == pd.Timestamp("2027-12-01")
    assert len(path) == 14
    by_date = path.set_index("date")["ffr"]
    assert by_date[pd.Timestamp("2026-11-01")] == pytest.approx(3.875 + 0.375 * 31 / 61)
    assert by_date[pd.Timestamp("2026-12-01")] == pytest.approx(4.25)
    assert by_date[pd.Timestamp("2027-12-01")] == pytest.approx(4.0)


def test_fed_funds_path_needs_a_later_projection():
    projections = pd.DataFrame({"date": pd.to_datetime(["2025-12-01"]), "ffr": [4.0]})
    with pytest.raises(FREDError) as e:
        fed_funds_path(pd.Timestamp("2026-10-01"), 3.875, projections)
    assert e.value.kind == "no_data"


def test_rate_forecast():
    fc = rate_forecast(FakeFRED(), today=TODAY)

    # The fake mortgage rate is 3 + 0.6 * midpoint + a wiggle, so the fit lands near those numbers.
    assert fc.history["ffr"].iloc[-1] == pytest.approx(3.875)
    first = fc.forecast.iloc[0]
    assert first["date"] == pd.Timestamp("2026-11-01")
    assert fc.forecast["date"].iloc[-1] == pd.Timestamp("2029-12-01")
    assert len(fc.forecast) == 38

    december = fc.forecast.set_index("date").loc[pd.Timestamp("2027-12-01")]
    assert december["ffr"] == pytest.approx(4.0)
    assert december["mean"] == pytest.approx(3.0 + 0.6 * 4.0, abs=0.15)
    assert (fc.forecast["obs_ci_lower"] < fc.forecast["mean"]).all()
    assert (fc.forecast["mean"] < fc.forecast["obs_ci_upper"]).all()

    assert list(fc.projections["date"].dt.month.unique()) == [12]
    assert list(fc.cv["folds"]) == [0, 1, 2, 3, 4, "Avg"]


def test_empty_answer_keeps_dates_typed(http):
    http.response = FakeResponse(200, {"observations": [{"date": "2026-01-01", "value": "."}]})
    df = FRED(api_key="k").get_fred_data("ffr_fcst", "2026-01-01")
    assert df.empty
    assert pd.api.types.is_datetime64_any_dtype(df["date"])


def test_forecast_without_projections_is_a_no_data_error():
    with pytest.raises(FREDError) as e:
        rate_forecast(FakeFRED(projections={}), today=TODAY)
    assert e.value.kind == "no_data"


def test_fetch_all_maps_names_to_results_and_raises_failures():
    data = fetch_all(FakeFRED(), {"m": ("mgt_rate", "2026-01-01"), "c": ("cpi", "2026-01-01")})
    assert list(data["m"].columns) == ["date", "mgt_rate"]
    assert list(data["c"].columns) == ["date", "cpi"]

    class Broken(FakeFRED):
        def get_fred_data(self, data_id, *args):
            if data_id == "cpi":
                raise FREDError("down", "unreachable")
            return super().get_fred_data(data_id, *args)

    with pytest.raises(FREDError):
        fetch_all(Broken(), {"m": ("mgt_rate", "2026-01-01"), "c": ("cpi", "2026-01-01")})
