import math
import xml.etree.ElementTree as ET

import pytest

from web import charts, fmt
from web.forms import DOWN, PRICE, RATE, TERM, Field, FieldError


@pytest.mark.parametrize(
    "func, value, text",
    [
        (fmt.money, 1234.4, "$1,234"),
        (fmt.money, -1234.6, "-$1,235"),
        (fmt.money, -0.4, "$0"),
        (fmt.money_cents, 1288.3699, "$1,288.37"),
        (fmt.signed_money, 5, "+$5"),
        (fmt.signed_money, -5, "-$5"),
        (fmt.signed_money, 0, "$0"),
        (fmt.money_short, 950, "$950"),
        (fmt.money_short, 12000, "$12K"),
        (fmt.money_short, -1_250_000, "-$1.2M"),
        (fmt.percent, 0.0525, "5.25%"),
        (fmt.percent, 0.1, "10%"),
        (fmt.rate, 6.3, "6.30%"),
        (fmt.number, 337.25, "337.2"),
    ],
)
def test_formats(func, value, text):
    assert func(value) == text


@pytest.mark.parametrize("func", [fmt.money, fmt.money_cents, fmt.money_short, fmt.percent, fmt.rate, fmt.number])
@pytest.mark.parametrize("value", [math.nan, math.inf, -math.inf])
def test_formats_refuse_non_finite_numbers(func, value):
    with pytest.raises(ValueError):
        func(value)


def test_fields_convert_to_library_units():
    assert DOWN.parse("20") == 0.2
    assert RATE.parse(" 6.5% ") == 0.065
    assert PRICE.parse("$350,000") == 350000
    assert TERM.parse("30") == 30 and isinstance(TERM.parse("30.0"), int)


def test_open_upper_bound_excludes_the_bound():
    assert DOWN.parse("99.99") == pytest.approx(0.9999)
    with pytest.raises(FieldError, match="less than 100%"):
        DOWN.parse("100")


def test_checkbox():
    box = Field("x", "X", default=False)
    assert box.parse("1") is True
    assert box.parse(None) is False


def svg_root(markup) -> ET.Element:
    svg = str(markup)[str(markup).index("<svg") : str(markup).index("</svg>") + 6]
    return ET.fromstring(svg.replace("<svg ", '<svg xmlns="http://www.w3.org/2000/svg" ', 1))


def year_chart(lines, **kwargs):
    return charts.line_chart(
        "Title <b>", lines, y_tick=str, y_value=fmt.money, x_tick=str, x_label=lambda x: f"Year {x}", **kwargs
    )


def test_line_chart_is_well_formed_and_escapes_text():
    markup = year_chart(
        [charts.Line("A & <b>", [1, 2, 3], [0, 50, 100], 1), charts.Line("B", [1, 2, 3], [100, -50, -400], 2)]
    )
    root = svg_root(markup)
    assert "Title &lt;b&gt;" in str(markup)
    assert "A &amp; &lt;b&gt;" in str(markup)
    titles = [t.text for t in root.iter("{http://www.w3.org/2000/svg}title")]
    assert titles[0].splitlines() == ["Year 1", "A & <b>: $0", "B: $100"]
    assert len(titles) == 3  # one hover target per x


def test_end_labels_are_dropped_when_they_would_collide():
    apart = year_chart([charts.Line("A", [1, 2], [0, 0], 1), charts.Line("B", [1, 2], [0, 100], 2)])
    close = year_chart([charts.Line("A", [1, 2], [0, 100], 1), charts.Line("B", [1, 2], [0, 99], 2)])
    assert str(apart).count('class="label"') == 2
    assert str(close).count('class="label"') == 0


def test_stacked_bars_are_well_formed():
    markup = charts.stacked_bars(
        "Bars",
        [1, 2, 3],
        [charts.Stack("P", [1, 2, 3], 1), charts.Stack("I", [3, 2, 0], 2)],
        y_tick=str,
        y_value=fmt.money,
        x_tick=str,
        x_label=str,
    )
    root = svg_root(markup)
    bars = [p for p in root.iter("{http://www.w3.org/2000/svg}path") if "bar" in p.get("class", "")]
    assert len(bars) == 5  # the zero segment is skipped
    # TESTGAP(pytest): bar geometry: 2px gaps between segments, rounded top only on the top segment, width cap.


@pytest.mark.parametrize("lo, hi", [(0, 1), (-225615, 34604), (3.1, 7.8), (100, 100), (0, 800000)])
def test_nice_ticks_cover_the_range(lo, hi):
    ticks = charts.nice_ticks(lo, hi)
    assert ticks[0] <= lo and ticks[-1] >= hi
    assert 2 <= len(ticks) <= 12
    steps = {round(b - a, 9) for a, b in zip(ticks, ticks[1:], strict=False)}
    assert len(steps) == 1
