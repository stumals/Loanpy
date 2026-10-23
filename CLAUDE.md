# Loanpy

- Install: `uv sync`. Check everything: `scripts/check` (CI runs the same script).
- Web front end: `uv run flask --app web run --port 4100`. Streamlit: `uv run streamlit run Home.py`.
- Ports: 4100 for the web app. No database.
- `FRED_API_KEY` in `.env` turns on the Economy and Rate forecast pages; `FRED_API_URL` overrides the endpoint.
- Tests never call FRED. Use `tests/fakes.py:FakeFRED`, or pass `FRED_CLIENT` to `create_app`.
- `requirements.txt` is for Streamlit Cloud only; dependencies live in `pyproject.toml` and `uv.lock`.
- Library code under `loan/`, `econ/`, `models/`, and `utils/` predates ruff; `ruff` covers `web/` and `tests/`.
- Shared math belongs in the library, not in `web/` or `pages/`: both front ends call it.
