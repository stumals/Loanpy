"""Plain HTML pages over the Loanpy library. Forms submit with GET, so every result has a shareable URL."""

import os
import threading
import time
from datetime import date

from dotenv import load_dotenv
from flask import Flask, render_template, request

from econ.fred_econ import FRED, FRED_SERIES_URL, FREDError

from . import analysis, fmt
from .forms import DOWN_PAYMENTS_FORM, MORTGAGE_FORM, RENT_VS_BUY_FORM, read_form

NAV = [
    ("/", "Home"),
    ("/mortgage", "Mortgage"),
    ("/rent-or-buy", "Rent or buy"),
    ("/down-payments", "Down payments"),
    ("/economy", "Economy"),
    ("/forecast", "Rate forecast"),
]

# No scripts at all: pages are HTML forms, and charts are inline SVG.
SECURITY_HEADERS = {
    "Content-Security-Policy": "default-src 'none'; style-src 'self'; img-src 'self'; "
    "form-action 'self'; base-uri 'none'; frame-ancestors 'none'",
    "X-Content-Type-Options": "nosniff",
    "Referrer-Policy": "same-origin",
}

FRED_CACHE_SECONDS = 3600
FRED_FAILURE_SECONDS = 60


class TTLCache:
    """Remembers each computed value for ttl seconds, and each failure for failure_ttl seconds.

    Each key has its own lock: requests for one key wait for a single computation instead of
    repeating it, and never wait on another key.
    """

    def __init__(self, ttl: float, failure_ttl: float) -> None:
        self.ttl, self.failure_ttl = ttl, failure_ttl
        self.lock = threading.Lock()
        self.key_locks: dict = {}
        self.items: dict = {}  # key -> (time, value, error)

    def get(self, key, compute):
        with self.lock:
            key_lock = self.key_locks.setdefault(key, threading.Lock())
        with key_lock:
            hit = self.items.get(key)
            if hit:
                stored, value, error = hit
                age = time.monotonic() - stored
                if error is None and age < self.ttl:
                    return value
                if error is not None and age < self.failure_ttl:
                    raise error
            try:
                value = compute()
            except Exception as e:
                self.items[key] = (time.monotonic(), None, e)
                raise
            self.items[key] = (time.monotonic(), value, None)
            return value


def create_app(config: dict | None = None) -> Flask:
    load_dotenv()
    app = Flask(__name__)
    app.config.update(
        FRED_API_KEY=os.environ.get("FRED_API_KEY") or os.environ.get("fred_api_key") or "",
        FRED_API_URL=os.environ.get("FRED_API_URL") or FRED_SERIES_URL,
        FRED_CLIENT=None,  # tests pass a function returning a stand-in for FRED
        TODAY=None,  # tests pin the date
    )
    app.config.update(config or {})
    if not app.config["FRED_API_KEY"] and not app.config["FRED_CLIENT"]:
        app.logger.warning("FRED_API_KEY isn't set, so the Economy and Rate forecast pages will ask for one.")

    for name in ("money", "money_cents", "signed_money", "percent", "rate", "number"):
        app.add_template_filter(getattr(fmt, name), name)
    cache = TTLCache(FRED_CACHE_SECONDS, FRED_FAILURE_SECONDS)

    @app.context_processor
    def nav():
        return {"nav": NAV}

    @app.after_request
    def headers(response):
        response.headers.update(SECURITY_HEADERS)
        return response

    def calculator(template, fieldsets, build):
        form = read_form(fieldsets, request.args)
        if form.errors:
            return render_template(template, form=form, r=None), 422
        return render_template(template, form=form, r=build(form.values))

    def fred_page(template, title, build):
        if app.config["FRED_CLIENT"]:
            client = app.config["FRED_CLIENT"]()
        elif app.config["FRED_API_KEY"]:
            client = FRED(api_key=app.config["FRED_API_KEY"], series_url=app.config["FRED_API_URL"])
        else:
            return render_template("fred_error.html", title=title, kind="no_key"), 503
        today = app.config["TODAY"] or date.today()
        try:
            result = cache.get((template, today), lambda: build(client, today))
        except FREDError as e:
            app.logger.warning("FRED request for %s failed: %s", request.path, e)
            return render_template("fred_error.html", title=title, kind=e.kind), 502
        return render_template(template, title=title, r=result)

    @app.get("/")
    def index():
        return render_template("index.html")

    @app.get("/mortgage")
    def mortgage():
        return calculator("mortgage.html", MORTGAGE_FORM, analysis.mortgage)

    @app.get("/rent-or-buy")
    def rent_or_buy():
        return calculator("rent_or_buy.html", RENT_VS_BUY_FORM, analysis.rent_vs_buy)

    @app.get("/down-payments")
    def down_payments():
        return calculator("down_payments.html", DOWN_PAYMENTS_FORM, analysis.down_payments)

    @app.get("/economy")
    def economy():
        return fred_page("economy.html", "Economic data", analysis.economy)

    @app.get("/forecast")
    def forecast():
        return fred_page("forecast.html", "Mortgage rate forecast", analysis.forecast)

    @app.errorhandler(404)
    def not_found(_):
        return render_template("error.html", title="Page not found", status=404), 404

    @app.errorhandler(405)
    def not_allowed(_):
        return render_template("error.html", title="Not allowed", status=405), 405

    @app.errorhandler(500)
    def server_error(_):
        return render_template("error.html", title="Something went wrong", status=500), 500

    return app
