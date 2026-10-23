# Loanpy

Loanpy analyzes mortgage amortization, costs, profitability, and key economic data. It comes with two
front ends that share the same library:

- **Web**: plain HTML pages in `web/`, served by Flask. No JavaScript.
- **Streamlit**: the original dashboard in `Home.py` and `pages/`, live at
  [mortgage-analyzer-beta.streamlit.app](https://mortgage-analyzer-beta.streamlit.app/).

## Pages

| Page | What it shows |
|---|---|
| Mortgage analysis | Monthly payments, home value, loan balance, and profit if you sell, year by year |
| Rent or buy | Owning compared with renting and investing the difference |
| Compare down payments | Total after N years for down payments from 0% to 95% |
| Economic data | Mortgage rates, inflation, home prices, and affordability from FRED |
| Mortgage rate forecast | A regression on the fed funds rate, driven by the Fed's own projections |

## Run the web front end

You need [uv](https://docs.astral.sh/uv/).

```sh
uv sync
uv run flask --app web run --port 4100
```

Then open `http://localhost:4100/`. The calculators work as they are. The Economic data and forecast pages
need a free [FRED API key](https://fredaccount.stlouisfed.org/apikeys): copy `.env.example` to `.env` and
set `FRED_API_KEY`. Without a key, those two pages explain how to add one.

Every form submits with GET, so you can share or bookmark a result. Parameters you leave out take their
defaults, so `/rent-or-buy?rent=2400` works.

## Run the Streamlit dashboard

```sh
uv run streamlit run Home.py
```

Streamlit Cloud installs from `requirements.txt`, so the live dashboard doesn't use `uv.lock`.

## Test

```sh
scripts/check        # format, lint, lockfile, and every test
scripts/check fast   # everything but the tests
```

CI runs `scripts/check full` on every push. Tests never call FRED: `tests/fakes.py` serves made-up data in
FRED's shape, and `tests/test_streamlit_pages.py` runs each Streamlit page headless against it.

## How the comparisons work

**Rent or buy** puts the buyer and the renter on the same budget. Each month, both spend the full cost of
owning or the rent, whichever is more, and whoever spends less on housing invests the difference. Each
total is wealth gained net of everything spent:

- Buyer: profit from selling the home, plus after-tax gains on money invested.
- Renter: after-tax gains on money invested, less all rent paid.

So the gap between the two totals is the gap in net worth.

**Compare down payments** works the same way. Each month, every option spends as much as the costliest
option costs that month, and the options that cost less invest the difference.

Investments compound monthly from the month each dollar goes in. Capital gains tax applies as if you sold
your investments when you sell the home.

## Layout

```
loan/       amortization (core.py), investing (invest.py), down payment comparison, Streamlit plots
econ/       FRED client
models/     regression model and the mortgage rate forecast
utils/      amortization table and small helpers
web/        Flask app: routes, forms, page analysis, SVG charts, templates, CSS
pages/      Streamlit pages; Home.py is the Streamlit entry point
tests/      pytest suite
```

## Deviations

- **Python and Flask, not Go and React.** The math lives in pandas, numpy-financial, and statsmodels, so the
  web front end is a thin Flask layer over the same library the Streamlit app uses. A Go port would mean a
  second copy of every calculation.
- **No JavaScript, by design.** Pages are server-rendered HTML in the style of
  [SimpleFIN Bridge](https://beta-bridge.simplefin.org/). Charts are inline SVG drawn on the server, and the
  Content Security Policy blocks all scripts.
- **No database.** Every page computes from its inputs, and FRED responses are cached in memory for an hour.
