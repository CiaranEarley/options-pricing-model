"""Cox-Ross-Rubinstein binomial tree pricing."""

from __future__ import annotations

from math import exp, sqrt

from options_pricing.black_scholes import OptionQuote
from options_pricing.options import OptionStyle


def price_binomial(
    *,
    stock_price: float,
    strike_price: float,
    time_to_expiry: float,
    interest_rate: float,
    volatility: float,
    dividend_yield: float = 0.0,
    style: str | OptionStyle = OptionStyle.AMERICAN,
    steps: int = 200,
) -> OptionQuote:
    """Price call and put options with a CRR binomial tree.

    American style is handled by comparing continuation value with immediate
    exercise value at every node.
    """

    _validate_inputs(
        stock_price=stock_price,
        strike_price=strike_price,
        time_to_expiry=time_to_expiry,
        volatility=volatility,
        steps=steps,
    )
    option_style = OptionStyle(style)

    if time_to_expiry == 0:
        return OptionQuote(
            call=max(stock_price - strike_price, 0.0),
            put=max(strike_price - stock_price, 0.0),
            style=option_style,
        )

    if volatility == 0:
        call, put = _price_deterministic_path(
            stock_price=stock_price,
            strike_price=strike_price,
            time_to_expiry=time_to_expiry,
            interest_rate=interest_rate,
            dividend_yield=dividend_yield,
            style=option_style,
            steps=steps,
        )
        return OptionQuote(call=call, put=put, style=option_style)

    time_step = time_to_expiry / steps
    up = exp(volatility * sqrt(time_step))
    down = 1.0 / up
    growth = exp((interest_rate - dividend_yield) * time_step)
    probability_up = (growth - down) / (up - down)

    if not 0 <= probability_up <= 1:
        raise ValueError(
            "CRR risk-neutral probability is outside [0, 1]. "
            "Try increasing binomial steps or using less extreme inputs."
        )

    discount = exp(-interest_rate * time_step)
    call_values = []
    put_values = []
    for up_moves in range(steps + 1):
        terminal_stock_price = stock_price * up**up_moves * down ** (steps - up_moves)
        call_values.append(max(terminal_stock_price - strike_price, 0.0))
        put_values.append(max(strike_price - terminal_stock_price, 0.0))

    for step in range(steps - 1, -1, -1):
        for up_moves in range(step + 1):
            call_continuation = discount * (
                probability_up * call_values[up_moves + 1]
                + (1.0 - probability_up) * call_values[up_moves]
            )
            put_continuation = discount * (
                probability_up * put_values[up_moves + 1]
                + (1.0 - probability_up) * put_values[up_moves]
            )

            if option_style == OptionStyle.AMERICAN:
                node_stock_price = stock_price * up**up_moves * down ** (step - up_moves)
                call_values[up_moves] = max(
                    call_continuation,
                    node_stock_price - strike_price,
                )
                put_values[up_moves] = max(
                    put_continuation,
                    strike_price - node_stock_price,
                )
            else:
                call_values[up_moves] = call_continuation
                put_values[up_moves] = put_continuation

    return OptionQuote(
        call=call_values[0],
        put=put_values[0],
        style=option_style,
    )


def _price_deterministic_path(
    *,
    stock_price: float,
    strike_price: float,
    time_to_expiry: float,
    interest_rate: float,
    dividend_yield: float,
    style: OptionStyle,
    steps: int,
) -> tuple[float, float]:
    time_step = time_to_expiry / steps
    discount = exp(-interest_rate * time_step)
    terminal_stock_price = stock_price * exp(
        (interest_rate - dividend_yield) * time_to_expiry
    )
    call_value = max(terminal_stock_price - strike_price, 0.0)
    put_value = max(strike_price - terminal_stock_price, 0.0)

    for step in range(steps - 1, -1, -1):
        call_value *= discount
        put_value *= discount
        if style == OptionStyle.AMERICAN:
            node_stock_price = stock_price * exp(
                (interest_rate - dividend_yield) * time_step * step
            )
            call_value = max(call_value, node_stock_price - strike_price)
            put_value = max(put_value, strike_price - node_stock_price)

    return call_value, put_value


def _validate_inputs(
    *,
    stock_price: float,
    strike_price: float,
    time_to_expiry: float,
    volatility: float,
    steps: int,
) -> None:
    if stock_price <= 0:
        raise ValueError("stock_price must be greater than zero.")
    if strike_price <= 0:
        raise ValueError("strike_price must be greater than zero.")
    if time_to_expiry < 0:
        raise ValueError("time_to_expiry cannot be negative.")
    if volatility < 0:
        raise ValueError("volatility cannot be negative.")
    if steps < 1:
        raise ValueError("steps must be at least 1.")
