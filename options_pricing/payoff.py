"""Payoff and PnL curve helpers."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PayoffCurve:
    """Long call and put payoff/PnL values across expiry stock prices."""

    stock_prices: list[float]
    call_payoff: list[float]
    put_payoff: list[float]
    call_pnl: list[float]
    put_pnl: list[float]


def build_payoff_curve(
    *,
    stock_price: float,
    strike_price: float,
    call_purchase_price: float,
    put_purchase_price: float,
    stock_shock_min: float = -0.50,
    stock_shock_max: float = 0.50,
    steps: int = 101,
) -> PayoffCurve:
    """Build long-option payoff and PnL curves at expiry."""

    _validate_inputs(
        stock_price=stock_price,
        strike_price=strike_price,
        call_purchase_price=call_purchase_price,
        put_purchase_price=put_purchase_price,
        stock_shock_min=stock_shock_min,
        stock_shock_max=stock_shock_max,
        steps=steps,
    )
    stock_prices = [
        stock_price * (1.0 + shock)
        for shock in _linspace(stock_shock_min, stock_shock_max, steps)
    ]
    call_payoff = [max(expiry_stock_price - strike_price, 0.0) for expiry_stock_price in stock_prices]
    put_payoff = [max(strike_price - expiry_stock_price, 0.0) for expiry_stock_price in stock_prices]

    return PayoffCurve(
        stock_prices=stock_prices,
        call_payoff=call_payoff,
        put_payoff=put_payoff,
        call_pnl=[payoff - call_purchase_price for payoff in call_payoff],
        put_pnl=[payoff - put_purchase_price for payoff in put_payoff],
    )


def _linspace(start: float, stop: float, steps: int) -> list[float]:
    if steps == 1:
        return [start]
    step_size = (stop - start) / (steps - 1)
    return [start + index * step_size for index in range(steps)]


def _validate_inputs(
    *,
    stock_price: float,
    strike_price: float,
    call_purchase_price: float,
    put_purchase_price: float,
    stock_shock_min: float,
    stock_shock_max: float,
    steps: int,
) -> None:
    if stock_price <= 0:
        raise ValueError("stock_price must be greater than zero.")
    if strike_price <= 0:
        raise ValueError("strike_price must be greater than zero.")
    if call_purchase_price < 0:
        raise ValueError("call_purchase_price cannot be negative.")
    if put_purchase_price < 0:
        raise ValueError("put_purchase_price cannot be negative.")
    if stock_shock_min > stock_shock_max:
        raise ValueError("stock_shock_min cannot exceed stock_shock_max.")
    if stock_shock_min <= -1:
        raise ValueError("stock shocks cannot reduce stock price to zero or below.")
    if steps < 2:
        raise ValueError("steps must be at least 2.")
