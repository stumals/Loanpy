"""Calculator inputs: one definition per field drives both the HTML and the parsing."""

import math
from collections.abc import Mapping
from dataclasses import dataclass, field

MONEY, PERCENT, YEARS = "$", "%", "years"


class FieldError(ValueError):
    pass


@dataclass(frozen=True)
class Field:
    name: str
    label: str
    unit: str = ""  # MONEY, PERCENT, YEARS, or "" for a checkbox
    default: float | bool = 0
    lo: float = 0
    hi: float = math.inf
    hi_open: bool = False  # True when hi itself is not allowed
    info: str = ""

    @property
    def is_check(self) -> bool:
        return isinstance(self.default, bool)

    @property
    def default_text(self) -> str:
        if self.is_check:
            return "1" if self.default else ""
        return f"{self.default:,.0f}" if self.unit == MONEY else f"{self.default:g}"

    def parse(self, raw: str | None) -> float | int | bool:
        """Returns the value in the units the library uses: fractions for percents, whole years."""
        if self.is_check:
            return raw not in (None, "", "0")
        text = (raw or "").strip().replace(",", "").removeprefix("$").removesuffix("%").strip()
        if not text:
            raise FieldError("Enter a number.")
        try:
            value = float(text)
        except ValueError:
            raise FieldError("Enter a number.") from None
        if not math.isfinite(value):
            raise FieldError("Enter a number.")
        if self.unit == YEARS and value != int(value):
            raise FieldError("Enter whole years.")
        if value < self.lo:
            raise FieldError(f"Enter {self._show(self.lo)} or more.")
        if self.hi_open and value >= self.hi:
            raise FieldError(f"Enter less than {self._show(self.hi)}.")
        if value > self.hi:
            raise FieldError(f"Enter {self._show(self.hi)} or less.")
        if self.unit == YEARS:
            return int(value)
        if self.unit == PERCENT:
            return value / 100
        return value

    def _show(self, value: float) -> str:
        if self.unit == MONEY:
            return f"${value:,.0f}"
        if self.unit == PERCENT:
            return f"{value:g}%"
        return f"{value:g}"


@dataclass(frozen=True)
class Fieldset:
    legend: str
    fields: tuple[Field, ...]


@dataclass
class Form:
    fieldsets: tuple[Fieldset, ...]
    values: dict = field(default_factory=dict)
    raw: dict = field(default_factory=dict)
    errors: dict = field(default_factory=dict)


def read_form(fieldsets: tuple[Fieldset, ...], args: Mapping[str, str]) -> Form:
    """Parses query parameters. A missing number takes its default, so a link can set only what differs."""
    form = Form(fieldsets)
    for fs in fieldsets:
        for f in fs.fields:
            raw = args.get(f.name)
            if raw is None and not f.is_check:
                raw = f.default_text
            form.raw[f.name] = raw or ""
            try:
                form.values[f.name] = f.parse(raw)
            except FieldError as e:
                form.errors[f.name] = str(e)

    years, term = form.values.get("years"), form.values.get("term")
    if years is not None and term is not None and years > term:
        form.errors["years"] = f"Enter {term} or less, the loan term."
    return form


PRICE = Field("price", "Home price", MONEY, 300000, lo=1000, hi=100_000_000)
DOWN = Field(
    "down",
    "Down payment",
    PERCENT,
    20,
    hi=100,
    hi_open=True,
    info="Share of the price you pay in cash at closing. Below 20%, the loan carries PMI.",
)
RATE = Field("rate", "Interest rate", PERCENT, 5, hi=100, hi_open=True, info="Annual rate on the loan.")
TERM = Field("term", "Loan term", YEARS, 30, lo=1, hi=50)
CLOSING = Field("closing", "Closing costs", MONEY, 0, hi=10_000_000)
FINANCE_CLOSING = Field("finance_closing", "Add closing costs to the loan", default=False)

TAX = Field(
    "tax",
    "Property tax",
    PERCENT,
    1,
    hi=100,
    hi_open=True,
    info="Per year, as a share of the home's value at the start of each year.",
)
PMI = Field(
    "pmi",
    "Mortgage insurance (PMI)",
    PERCENT,
    1,
    hi=100,
    hi_open=True,
    info="Per year, as a share of the amount borrowed. Charged until you owe less than 80% of the home's value.",
)
MAINT = Field(
    "maint",
    "Maintenance",
    PERCENT,
    1,
    hi=100,
    hi_open=True,
    info="Per year, as a share of the home's value at the start of each year.",
)

APPRECIATION = Field("appreciation", "Home value growth", PERCENT, 5, hi=100, hi_open=True, info="Per year.")
SALE_COST = Field(
    "sale_cost",
    "Cost to sell",
    PERCENT,
    6,
    hi=100,
    hi_open=True,
    info="Agent and other fees when you sell, as a share of the sale price.",
)
YEARS_HELD = Field(
    "years",
    "Sell after",
    YEARS,
    15,
    lo=1,
    hi=50,
    info="Results assume you sell the home at the end of this year. Up to the loan term.",
)

RENT = Field("rent", "Monthly rent", MONEY, 1800, hi=1_000_000)
RENT_INCREASE = Field("rent_increase", "Rent increase", PERCENT, 3, hi=100, hi_open=True, info="Per year.")

MARKET_RETURN = Field(
    "market_return",
    "Market return",
    PERCENT,
    10,
    hi=100,
    hi_open=True,
    info="Annual return on money invested instead of spent on housing.",
)
CAP_GAINS = Field(
    "cap_gains",
    "Capital gains tax",
    PERCENT,
    15,
    hi=100,
    hi_open=True,
    info="Tax on investment gains, taken as if you sold your investments when you sell the home.",
)

LOAN = Fieldset("Home and loan", (PRICE, DOWN, RATE, TERM, CLOSING, FINANCE_CLOSING))
COSTS = Fieldset("Yearly costs", (TAX, PMI, MAINT))
SALE = Fieldset("Selling", (APPRECIATION, SALE_COST, YEARS_HELD))
RENTING = Fieldset("Renting", (RENT, RENT_INCREASE))
INVESTING = Fieldset("Investing", (MARKET_RETURN, CAP_GAINS))

MORTGAGE_FORM = (LOAN, COSTS, SALE)
RENT_VS_BUY_FORM = (RENTING, LOAN, COSTS, SALE, INVESTING)
DOWN_PAYMENTS_FORM = (
    Fieldset(LOAN.legend, tuple(f for f in LOAN.fields if f is not DOWN)),
    COSTS,
    SALE,
    INVESTING,
)
