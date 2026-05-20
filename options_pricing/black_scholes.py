"""Black-Scholes pricing helpers."""

from __future__ import annotations

from dataclasses import dataclass
from math import erf, exp, log, sqrt

from options_pricing.options import OptionStyle


@dataclass(frozen=True)
class OptionQuote:
    """Call and put values for one option parameter set."""

    call: float
    put: float
    style: OptionStyle
    note: str | None = None


def cumulative_normal(value: float) -> float:
    """Standard normal cumulative distribution function."""

    return 0.5 * (1.0 + erf(value / sqrt(2.0)))


def price_black_scholes(
    *,
    stock_price: float,
    strike_price: float,
    time_to_expiry: float,
    interest_rate: float,
    volatility: float,
    dividend_yield: float = 0.0,
    style: str | OptionStyle = OptionStyle.AMERICAN,
) -> OptionQuote:
    """Price a call and put using the Black-Scholes framework.

    The closed-form Black-Scholes equation is exact for European options. For
    American options without dividends, the call has the same value as the
    European call. American puts require a numerical method for exact pricing,
    so this first project milestone uses the European put with an intrinsic
    value floor as a transparent baseline.
    """

    _validate_inputs(
        stock_price=stock_price,
        strike_price=strike_price,
        time_to_expiry=time_to_expiry,
        volatility=volatility,
    )
    option_style = OptionStyle(style)

    call, put = _european_black_scholes(
        stock_price=stock_price,
        strike_price=strike_price,
        time_to_expiry=time_to_expiry,
        interest_rate=interest_rate,
        dividend_yield=dividend_yield,
        volatility=volatility,
    )

    if option_style == OptionStyle.EUROPEAN:
        return OptionQuote(call=call, put=put, style=option_style)

    american_call = max(call, stock_price - strike_price)
    american_put_baseline = max(put, strike_price - stock_price)
    return OptionQuote(
        call=american_call,
        put=american_put_baseline,
        style=option_style,
        note=(
            "Black-Scholes is closed-form for European options. For this "
            "American baseline, call and put values are floored at intrinsic "
            "value. Use the binomial engine for true early-exercise pricing."
        ),
    )


def _european_black_scholes(
    *,
    stock_price: float,
    strike_price: float,
    time_to_expiry: float,
    interest_rate: float,
    volatility: float,
    dividend_yield: float,
) -> tuple[float, float]:
    if time_to_expiry == 0:
        return (
            max(stock_price - strike_price, 0.0),
            max(strike_price - stock_price, 0.0),
        )

    if volatility == 0:
        discounted_stock = stock_price * exp(-dividend_yield * time_to_expiry)
        discounted_strike = strike_price * exp(-interest_rate * time_to_expiry)
        return (
            max(discounted_stock - discounted_strike, 0.0),
            max(discounted_strike - discounted_stock, 0.0),
        )

    d1 = (
        log(stock_price / strike_price)
        + (interest_rate - dividend_yield + 0.5 * volatility**2) * time_to_expiry
    ) / (volatility * sqrt(time_to_expiry))
    d2 = d1 - volatility * sqrt(time_to_expiry)

    discounted_stock = stock_price * exp(-dividend_yield * time_to_expiry)
    discounted_strike = strike_price * exp(-interest_rate * time_to_expiry)
    call = discounted_stock * cumulative_normal(d1) - discounted_strike * cumulative_normal(d2)
    put = strike_price * exp(-interest_rate * time_to_expiry) * cumulative_normal(
        -d2
    ) - discounted_stock * cumulative_normal(-d1)
    return call, put


def _validate_inputs(
    *,
    stock_price: float,
    strike_price: float,
    time_to_expiry: float,
    volatility: float,
) -> None:
    if stock_price <= 0:
        raise ValueError("stock_price must be greater than zero.")
    if strike_price <= 0:
        raise ValueError("strike_price must be greater than zero.")
    if time_to_expiry < 0:
        raise ValueError("time_to_expiry cannot be negative.")
    if volatility < 0:
        raise ValueError("volatility cannot be negative.")
