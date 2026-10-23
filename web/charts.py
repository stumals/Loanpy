"""SVG charts drawn on the server.

No JavaScript: hovering a column shows every series' value there through a native <title> tooltip,
and each chart sits beside a table with the same numbers. Colors come from CSS variables
(--series-N), so light and dark mode are the stylesheet's job.
"""

import math
from collections.abc import Callable, Sequence
from dataclasses import dataclass

from markupsafe import Markup, escape

WIDTH = 700  # viewBox width; pass the width a chart renders at, so text stays near 12px
PAD_LEFT, PAD_TOP, PAD_BOTTOM = 60, 12, 30
LABEL_ROOM = 96  # right margin for end-of-line labels
BAR_MAX = 24
GAP = 2


@dataclass(frozen=True)
class Line:
    label: str
    xs: Sequence[float]
    ys: Sequence[float]
    slot: int
    dashed: bool = False
    in_legend: bool = True


@dataclass(frozen=True)
class Band:
    """A shaded range, such as a prediction interval."""

    label: str
    xs: Sequence[float]
    lows: Sequence[float]
    highs: Sequence[float]
    slot: int


@dataclass(frozen=True)
class Stack:
    label: str
    values: Sequence[float]
    slot: int


@dataclass(frozen=True)
class Marker:
    """A highlighted point, such as the best result."""

    x: float
    y: float
    slot: int


def nice_ticks(lo: float, hi: float, count: int = 5, whole: bool = False) -> list[float]:
    """Round tick values covering lo..hi: steps of 1, 2, 2.5, or 5 times a power of ten."""
    if hi <= lo:
        lo, hi = lo - 1, hi + 1
    raw = (hi - lo) / count
    power = 10 ** math.floor(math.log10(raw))
    step = next(m * power for m in (1, 2, 2.5, 5, 10) if m * power >= raw)
    if whole:
        step = max(1, round(step))
    first = math.floor(lo / step) * step
    ticks = []
    tick = first
    while tick < hi + step * 1e-9:
        ticks.append(round(tick, 10))
        tick += step
    if ticks[-1] < hi:
        ticks.append(round(tick, 10))
    return ticks


def _text(x: float, y: float, text: str, cls: str = "tick", anchor: str = "start") -> str:
    return f'<text class="{cls}" x="{x:.1f}" y="{y:.1f}" text-anchor="{anchor}">{escape(text)}</text>'


class _Frame:
    """Maps data to SVG coordinates and draws the axes and grid."""

    def __init__(self, xs, ys, width, height, y_tick, x_tick, x_ticks, right, x_pad, include_zero):
        self.width, self.height = width, height
        self.right = right
        ys = list(ys) + ([0] if include_zero else [])
        self.y_ticks = nice_ticks(min(ys), max(ys))
        self.y0, self.y1 = self.y_ticks[0], self.y_ticks[-1]
        self.x0, self.x1 = min(xs) - x_pad, max(xs) + x_pad
        if self.x1 == self.x0:
            self.x0, self.x1 = self.x0 - 1, self.x1 + 1
        self.x_ticks = [t for t in x_ticks if self.x0 <= t <= self.x1]
        self.y_tick, self.x_tick = y_tick, x_tick
        self.left, self.top, self.bottom = PAD_LEFT, PAD_TOP, height - PAD_BOTTOM

    def x(self, value: float) -> float:
        return self.left + (value - self.x0) / (self.x1 - self.x0) * (self.width - self.right - self.left)

    def y(self, value: float) -> float:
        return self.bottom - (value - self.y0) / (self.y1 - self.y0) * (self.bottom - self.top)

    def axes(self) -> list[str]:
        out = []
        for t in self.y_ticks:
            cls = "baseline" if t == 0 or (t == self.y0 and self.y0 > 0) else "grid"
            y = self.y(t)
            out.append(
                f'<line class="{cls}" x1="{self.left}" x2="{self.width - self.right}" y1="{y:.1f}" y2="{y:.1f}"/>'
            )
            out.append(_text(self.left - 8, y + 4, self.y_tick(t), anchor="end"))
        for t in self.x_ticks:
            out.append(_text(self.x(t), self.bottom + 20, self.x_tick(t), anchor="middle"))
        return out


def _legend(items: list[tuple[str, str, int, bool]]) -> str:
    """items: (label, "line" | "bar" | "band", slot, dashed)."""
    if len(items) < 2:
        return ""
    keys = []
    for label, kind, slot, dashed in items:
        cls = f"key key-{kind} s{slot}" + (" dashed" if dashed else "")
        keys.append(f'<li><span class="{cls}" aria-hidden="true"></span>{escape(label)}</li>')
    return f'<ul class="legend">{"".join(keys)}</ul>'


def _figure(title: str, show_title: bool, legend: str, frame: _Frame, body: list[str]) -> Markup:
    title = escape(title)
    caption = f"<figcaption>{title}</figcaption>" if show_title else ""
    return Markup(
        f'<figure class="chart w{frame.width}">{caption}{legend}<svg viewBox="0 0 {frame.width} {frame.height}" '
        f'width="{frame.width}" height="{frame.height}" role="img" aria-label="{title}">{"".join(body)}</svg></figure>'
    )


def _hover_columns(frame: _Frame, columns: dict[float, list[str]], x_label: Callable[[float], str]) -> list[str]:
    """Invisible full-height targets, one per x, each showing a hairline and every value at that x."""
    xs = sorted(columns)
    out = ['<g class="hover">']
    for i, x in enumerate(xs):
        left = frame.x((xs[i - 1] + x) / 2) if i else frame.x(x) - 6
        right = frame.x((x + xs[i + 1]) / 2) if i + 1 < len(xs) else frame.x(x) + 6
        tip = escape("\n".join([x_label(x), *columns[x]]))
        cx, width, height = frame.x(x), max(right - left, 1), frame.bottom - frame.top
        out.append(
            f"<g><title>{tip}</title>"
            f'<rect x="{left:.1f}" y="{frame.top}" width="{width:.1f}" height="{height}"/>'
            f'<line x1="{cx:.1f}" x2="{cx:.1f}" y1="{frame.top}" y2="{frame.bottom}"/></g>'
        )
    out.append("</g>")
    return out


def _end_labels(frame: _Frame, lines: Sequence[Line], value: Callable[[float], str]) -> list[str]:
    """Value at the end of each line, unless two would collide; then the legend and hover carry it."""
    ends = sorted(((frame.y(line.ys[-1]), line) for line in lines), key=lambda end: end[0])
    if len(ends) > 4 or any(b[0] - a[0] < 14 for a, b in zip(ends, ends[1:], strict=False)):
        return []
    out = []
    for y, line in ends:
        x = frame.x(line.xs[-1])
        out.append(f'<circle class="end f{line.slot}" cx="{x:.1f}" cy="{y:.1f}" r="4"/>')
        out.append(_text(x + 8, y + 4, value(line.ys[-1]), cls="label"))
    return out


def line_chart(
    title: str,
    lines: Sequence[Line],
    *,
    y_tick: Callable[[float], str],
    y_value: Callable[[float], str],
    x_tick: Callable[[float], str],
    x_label: Callable[[float], str],
    x_ticks: Sequence[float] | None = None,
    bands: Sequence[Band] = (),
    markers: Sequence[Marker] = (),
    extra_legend: Sequence[tuple[str, str, int, bool]] = (),
    end_labels: bool = True,
    include_zero: bool = False,
    show_title: bool = True,
    width: int = WIDTH,
    height: int = 280,
) -> Markup:
    all_x = [x for line in lines for x in line.xs] + [x for b in bands for x in b.xs]
    all_y = [y for line in lines for y in line.ys] + [v for b in bands for v in (*b.lows, *b.highs)]
    labelled = [line for line in lines if not line.dashed]
    right = LABEL_ROOM if end_labels and labelled else 16
    ticks = x_ticks if x_ticks is not None else nice_ticks(min(all_x), max(all_x), 8, whole=True)
    frame = _Frame(all_x, all_y, width, height, y_tick, x_tick, ticks, right, 0, include_zero)

    body = frame.axes()
    for band in bands:
        top = [f"{frame.x(x):.1f},{frame.y(v):.1f}" for x, v in zip(band.xs, band.highs, strict=True)]
        bottom = [f"{frame.x(x):.1f},{frame.y(v):.1f}" for x, v in zip(band.xs, band.lows, strict=True)]
        body.append(f'<polygon class="band f{band.slot}" points="{" ".join(top + bottom[::-1])}"/>')
    for line in lines:
        points = " ".join(f"{frame.x(x):.1f},{frame.y(y):.1f}" for x, y in zip(line.xs, line.ys, strict=True))
        dashed = " dashed" if line.dashed else ""
        body.append(f'<polyline class="line s{line.slot}{dashed}" points="{points}"/>')
    for m in markers:
        body.append(f'<circle class="end f{m.slot}" cx="{frame.x(m.x):.1f}" cy="{frame.y(m.y):.1f}" r="5"/>')
    if end_labels:
        body += _end_labels(frame, labelled, y_value)

    columns: dict[float, list[str]] = {}
    for line in lines:
        for x, y in zip(line.xs, line.ys, strict=True):
            columns.setdefault(x, []).append(f"{line.label}: {y_value(y)}")
    for band in bands:
        for x, lo, hi in zip(band.xs, band.lows, band.highs, strict=True):
            columns.setdefault(x, []).append(f"{band.label}: {y_value(lo)} to {y_value(hi)}")
    body += _hover_columns(frame, columns, x_label)

    legend = [(line.label, "line", line.slot, line.dashed) for line in lines if line.in_legend]
    legend += [(band.label, "band", band.slot, False) for band in bands] + list(extra_legend)
    return _figure(title, show_title, _legend(legend), frame, body)


def _bar_path(x: float, y_top: float, width: float, y_bottom: float, round_top: bool) -> str:
    """A column, with a 4px rounded data end on top when round_top."""
    h = y_bottom - y_top
    r = min(4, width / 2, h) if round_top else 0
    return (
        f"M{x:.1f},{y_bottom:.1f}V{y_top + r:.1f}"
        f"Q{x:.1f},{y_top:.1f} {x + r:.1f},{y_top:.1f}H{x + width - r:.1f}"
        f"Q{x + width:.1f},{y_top:.1f} {x + width:.1f},{y_top + r:.1f}V{y_bottom:.1f}Z"
    )


def stacked_bars(
    title: str,
    xs: Sequence[float],
    stacks: Sequence[Stack],
    *,
    y_tick: Callable[[float], str],
    y_value: Callable[[float], str],
    x_tick: Callable[[float], str],
    x_label: Callable[[float], str],
    width: int = WIDTH,
    height: int = 280,
) -> Markup:
    totals = [sum(s.values[i] for s in stacks) for i in range(len(xs))]
    ticks = nice_ticks(min(xs), max(xs), 8, whole=True)
    frame = _Frame(xs, totals, width, height, y_tick, x_tick, ticks, 16, 0.5, include_zero=True)
    slot_width = frame.x(xs[1]) - frame.x(xs[0]) if len(xs) > 1 else 40
    bar_width = min(BAR_MAX, slot_width * 0.6)

    body = frame.axes()
    columns: dict[float, list[str]] = {}
    for i, x in enumerate(xs):
        left = frame.x(x) - bar_width / 2
        segments = [(s, s.values[i]) for s in stacks if s.values[i] > 0]
        running = 0.0
        for j, (stack, value) in enumerate(segments):
            top_px, bottom_px = frame.y(running + value), frame.y(running)
            running += value
            last = j == len(segments) - 1
            # Split a 2px surface gap between touching segments.
            top_px += 0 if last else GAP / 2
            bottom_px -= 0 if j == 0 else GAP / 2
            if bottom_px - top_px < 0.5:
                continue
            body.append(f'<path class="bar f{stack.slot}" d="{_bar_path(left, top_px, bar_width, bottom_px, last)}"/>')
        columns[x] = [f"{s.label}: {y_value(s.values[i])}" for s in stacks] + [f"Total: {y_value(totals[i])}"]
    body += _hover_columns(frame, columns, x_label)

    legend = [(s.label, "bar", s.slot, False) for s in stacks]
    return _figure(title, True, _legend(legend), frame, body)
