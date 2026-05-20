"""Helpers for option price and PnL shock surfaces."""

from __future__ import annotations

from dataclasses import dataclass

from options_pricing.options import OptionStyle, OptionType, PricingEngine
from options_pricing.pricing import price_option


@dataclass(frozen=True)
class SurfaceGrid:
    """A rectangular grid of shocked option values."""

    stock_prices: list[float]
    volatilities: list[float]
    values: list[list[float]]


def build_price_surface(
    *,
    stock_price: float,
    strike_price: float,
    time_to_expiry: float,
    interest_rate: float,
    volatility: float,
    dividend_yield: float = 0.0,
    option_type: str | OptionType,
    style: str | OptionStyle = OptionStyle.AMERICAN,
    engine: str | PricingEngine = PricingEngine.BLACK_SCHOLES,
    binomial_steps: int = 200,
    stock_shock_min: float = -0.30,
    stock_shock_max: float = 0.30,
    volatility_shock_min: float = -0.30,
    volatility_shock_max: float = 0.30,
    steps: int = 13,
) -> SurfaceGrid:
    """Build an option price surface across stock and volatility shocks."""

    pricing_engine = PricingEngine(engine)
    _validate_surface_inputs(
        stock_shock_min=stock_shock_min,
        stock_shock_max=stock_shock_max,
        volatility_shock_min=volatility_shock_min,
        volatility_shock_max=volatility_shock_max,
        steps=steps,
    )

    selected_option = OptionType(option_type)
    stock_prices = [
        max(stock_price * (1.0 + shock), 0.000001)
        for shock in _linspace(stock_shock_min, stock_shock_max, steps)
    ]
    volatilities = [
        max(volatility * (1.0 + shock), 0.0)
        for shock in _linspace(volatility_shock_min, volatility_shock_max, steps)
    ]

    values = []
    for shocked_volatility in volatilities:
        row = []
        for shocked_stock_price in stock_prices:
            quote = price_option(
                stock_price=shocked_stock_price,
                strike_price=strike_price,
                time_to_expiry=time_to_expiry,
                interest_rate=interest_rate,
                dividend_yield=dividend_yield,
                volatility=shocked_volatility,
                style=style,
                engine=pricing_engine,
                binomial_steps=binomial_steps,
            )
            row.append(quote.call if selected_option == OptionType.CALL else quote.put)
        values.append(row)

    return SurfaceGrid(
        stock_prices=stock_prices,
        volatilities=volatilities,
        values=values,
    )


def build_pnl_surface(*, purchase_price: float, price_surface: SurfaceGrid) -> SurfaceGrid:
    """Convert an option price surface into a PnL surface."""

    if purchase_price < 0:
        raise ValueError("purchase_price cannot be negative.")

    return SurfaceGrid(
        stock_prices=price_surface.stock_prices,
        volatilities=price_surface.volatilities,
        values=[
            [price - purchase_price for price in row]
            for row in price_surface.values
        ],
    )


def _linspace(start: float, stop: float, steps: int) -> list[float]:
    if steps == 1:
        return [start]
    step_size = (stop - start) / (steps - 1)
    return [start + index * step_size for index in range(steps)]


def _validate_surface_inputs(
    *,
    stock_shock_min: float,
    stock_shock_max: float,
    volatility_shock_min: float,
    volatility_shock_max: float,
    steps: int,
) -> None:
    if steps < 2:
        raise ValueError("steps must be at least 2.")
    if stock_shock_min > stock_shock_max:
        raise ValueError("stock_shock_min cannot exceed stock_shock_max.")
    if volatility_shock_min > volatility_shock_max:
        raise ValueError("volatility_shock_min cannot exceed volatility_shock_max.")
    if stock_shock_min <= -1:
        raise ValueError("stock shocks cannot reduce stock price to zero or below.")
    if volatility_shock_min <= -1:
        raise ValueError("volatility shocks cannot reduce volatility below zero.")
