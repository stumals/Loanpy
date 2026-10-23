from pathlib import Path

import pytest

pytest.importorskip("streamlit")
from streamlit.testing.v1 import AppTest  # noqa: E402

from econ import fred_econ  # noqa: E402
from tests.fakes import FakeFRED  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
PAGES = ["Home.py", *sorted(p.relative_to(ROOT).as_posix() for p in (ROOT / "pages").glob("*.py"))]


class PageFRED(fred_econ.FRED):
    """The real client, plotting included, fed by the fake so pages never call FRED."""

    def __init__(self):
        super().__init__(api_key="test")
        self.fake = FakeFRED(projections={year: 3.5 for year in range(2026, 2060)})

    def get_fred_data(self, *args, **kwargs):
        return self.fake.get_fred_data(*args, **kwargs)


@pytest.mark.parametrize("page", PAGES)
def test_page_runs(page, monkeypatch):
    monkeypatch.setattr(fred_econ, "FRED", PageFRED)
    app = AppTest.from_file(str(ROOT / page), default_timeout=60)
    app.run()
    assert not app.exception, app.exception
