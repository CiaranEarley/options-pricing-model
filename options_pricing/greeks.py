"""Option Greek calculations."""

from __future__ import annotations

from dataclasses import dataclass
from math import exp, log, pi, sqrt

from options_pricing.black_scholes import cumulative_normal
from options_pricing.options import OptionStyle, OptionType, PricingEngine
from options_pricing.pricing import price_option


@dataclass(frozen=True)
class OptionGreeks:
    """Risk sensitivities for one option contract."""

    delta: float | None
    gamma: float | None
    vega: float | None
    theta: float | None
    rho: float | None


@dataclass(frozen=True)
class GreeksQuote:
    """Call and put Greeks for one parameter set."""

    call: OptionGreeks
    put: OptionGreeks


def calculate_greeks(
    *,
    stock_price: float,
    strike_price: float,
    time_to_expiry: float,
    interest_rate: float,
    volatility: float,
    dividend_yield: float = 0.0,
    style: str | OptionStyle = OptionStyle.AMERICAN,
    engine: str | PricingEngine = PricingEngine.BLACK_SCHOLES,
    binomial_steps: int = 200,
) -> GreeksQuote:
    """Calculate Greeks for the selected pricing engine.

    Vega and rho are scaled to a one percentage-point move. Theta is scaled to
    one calendar day.
    """

    pricing_engine = PricingEngine(engine)
    if pricing_engine == PricingEngine.BLACK_SCHOLES:
        return calculate_black_scholes_greeks(
            stock_price=stock_price,
            strike_price=strike_price,
            time_to_expiry=time_to_expiry,
            interest_rate=interest_rate,
            dividend_yield=dividend_yield,
            volatility=volatility,
        )

    return calculate_numerical_greeks(
        stock_price=stock_price,
        strike_price=strike_price,
        time_to_expiry=time_to_expiry,
        interest_rate=interest_rate,
        dividend_yield=dividend_yield,
        volatility=volatility,
        style=style,
        engine=pricing_engine,
        binomial_steps=binomial_steps,
    )


def calculate_black_scholes_greeks(
    *,
    stock_price: float,
    strike_price: float,
    time_to_expiry: float,
    interest_rate: float,
    volatility: float,
    dividend_yield: float = 0.0,
) -> GreeksQuote:
    """Calculate closed-form Black-Scholes-Merton Greeks."""

    _validate_greek_inputs(
        stock_price=stock_price,
        strike_price=strike_price,
        time_to_expiry=time_to_expiry,
        volatility=volatility,
    )
    if time_to_expiry == 0 or volatility == 0:
        empty = OptionGreeks(None, None, None, None, None)
        return GreeksQuote(call=empty, put=empty)

    sqrt_time = sqrt(time_to_expiry)
    d1 = (
        log(stock_price / strike_price)
        + (interest_rate - dividend_yield + 0.5 * volatility**2) * time_to_expiry
    ) / (volatility * sqrt_time)
    d2 = d1 - volatility * sqrt_time
    density = _normal_pdf(d1)
    dividend_discount = exp(-dividend_yield * time_to_expiry)
    strike_discount = exp(-interest_rate * time_to_expiry)

    call_delta = dividend_discount * cumulative_normal(d1)
    put_delta = dividend_discount * (cumulative_normal(d1) - 1.0)
    gamma = dividend_discount * density / (stock_price * volatility * sqrt_time)
    vega = stock_price * dividend_discount * density * sqrt_time / 100.0
    call_theta = (
        -(stock_price * dividend_discount * density * volatility) / (2.0 * sqrt_time)
        - interest_rate * strike_price * strike_discount * cumulative_normal(d2)
        + dividend_yield * stock_price * dividend_discount * cumulative_normal(d1)
    ) / 365.0
    put_theta = (
        -(stock_price * dividend_discount * density * volatility) / (2.0 * sqrt_time)
        + interest_rate * strike_price * strike_discount * cumulative_normal(-d2)
        - dividend_yield * stock_price * dividend_discount * cumulative_normal(-d1)
    ) / 365.0
    call_rho = strike_price * time_to_expiry * strike_discount * cumulative_normal(d2)
    put_rho = -strike_price * time_to_expiry * strike_discount * cumulative_normal(-d2)

    return GreeksQuote(
        call=OptionGreeks(
            delta=call_delta,
            gamma=gamma,
            vega=vega,
            theta=call_theta,
            rho=call_rho / 100.0,
        ),
        put=OptionGreeks(
            delta=put_delta,
            gamma=gamma,
            vega=vega,
            theta=put_theta,
            rho=put_rho / 100.0,
        ),
    )


def calculate_numerical_greeks(
    *,
    stock_price: float,
    strike_price: float,
    time_to_expiry: float,
    interest_rate: float,
    volatility: float,
    dividend_yield: float = 0.0,
    style: str | OptionStyle = OptionStyle.AMERICAN,
    engine: str | PricingEngine = PricingEngine.BINOMIAL,
    binomial_steps: int = 200,
) -> GreeksQuote:
    """Calculate finite-difference Greeks from the selected pricing engine."""

    _validate_greek_inputs(
        stock_price=stock_price,
        strike_price=strike_price,
        time_to_expiry=time_to_expiry,
        volatility=volatility,
    )
    if time_to_expiry == 0:
        empty = OptionGreeks(None, None, None, None, None)
        return GreeksQuote(call=empty, put=empty)

    def priced(
        *,
        shifted_stock_price: float = stock_price,
        shifted_time_to_expiry: float = time_to_expiry,
        shifted_interest_rate: float = interest_rate,
        shifted_volatility: float = volatility,
    ):
        return price_option(
            stock_price=shifted_stock_price,
            strike_price=strike_price,
            time_to_expiry=shifted_time_to_expiry,
            interest_rate=shifted_interest_rate,
            dividend_yield=dividend_yield,
            volatility=max(shifted_volatility, 0.0),
            style=style,
            engine=engine,
            binomial_steps=binomial_steps,
        )

    base_quote = priced()
    stock_step = max(stock_price * 0.01, 0.01)
    volatility_step = max(volatility * 0.05, 0.0001)
    rate_step = 0.0001
    day_step = min(time_to_expiry, 1.0 / 365.0)

    up_stock = priced(shifted_stock_price=stock_price + stock_step)
    down_stock = (
        priced(shifted_stock_price=stock_price - stock_step)
        if stock_price > stock_step
        else None
    )
    up_volatility = priced(shifted_volatility=volatility + volatility_step)
    down_volatility = (
        priced(shifted_volatility=volatility - volatility_step)
        if volatility > volatility_step
        else None
    )
    up_rate = priced(shifted_interest_rate=interest_rate + rate_step)
    down_rate = priced(shifted_interest_rate=interest_rate - rate_step)
    shorter_time = priced(shifted_time_to_expiry=time_to_expiry - day_step)

    return GreeksQuote(
        call=_numerical_contract_greeks(
            option_type=OptionType.CALL,
            base_quote=base_quote,
            up_stock=up_stock,
            down_stock=down_stock,
            stock_step=stock_step,
            up_volatility=up_volatility,
            down_volatility=down_volatility,
            volatility_step=volatility_step,
            up_rate=up_rate,
            down_rate=down_rate,
            rate_step=rate_step,
            shorter_time=shorter_time,
            day_step=day_step,
        ),
        put=_numerical_contract_greeks(
            option_type=OptionType.PUT,
            base_quote=base_quote,
            up_stock=up_stock,
            down_stock=down_stock,
            stock_step=stock_step,
            up_volatility=up_volatility,
            down_volatility=down_volatility,
            volatility_step=volatility_step,
            up_rate=up_rate,
            down_rate=down_rate,
            rate_step=rate_step,
            shorter_time=shorter_time,
            day_step=day_step,
        ),
    )


def _numerical_contract_greeks(
    *,
    option_type: OptionType,
    base_quote,
    up_stock,
    down_stock,
    stock_step: float,
    up_volatility,
    down_volatility,
    volatility_step: float,
    up_rate,
    down_rate,
    rate_step: float,
    shorter_time,
    day_step: float,
) -> OptionGreeks:
    base = _value(base_quote, option_type)
    up_stock_value = _value(up_stock, option_type)

    if down_stock is None:
        delta = (up_stock_value - base) / stock_step
        gamma = None
    else:
        down_stock_value = _value(down_stock, option_type)
        delta = (up_stock_value - down_stock_value) / (2.0 * stock_step)
        gamma = (up_stock_value - 2.0 * base + down_stock_value) / stock_step**2

    if down_volatility is None:
        vega = (_value(up_volatility, option_type) - base) / volatility_step / 100.0
    else:
        vega = (
            _value(up_volatility, option_type) - _value(down_volatility, option_type)
        ) / (2.0 * volatility_step) / 100.0

    theta = (_value(shorter_time, option_type) - base) / (day_step * 365.0)
    rho = (
        _value(up_rate, option_type) - _value(down_rate, option_type)
    ) / (2.0 * rate_step) / 100.0

    return OptionGreeks(
        delta=delta,
        gamma=gamma,
        vega=vega,
        theta=theta,
        rho=rho,
    )


def _value(quote, option_type: OptionType) -> float:
    return quote.call if option_type == OptionType.CALL else quote.put


def _normal_pdf(value: float) -> float:
    return exp(-0.5 * value**2) / sqrt(2.0 * pi)


def _validate_greek_inputs(
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
