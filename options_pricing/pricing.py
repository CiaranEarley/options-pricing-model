"""Pricing engine dispatcher."""

from __future__ import annotations

from options_pricing.binomial import price_binomial
from options_pricing.black_scholes import OptionQuote, price_black_scholes
from options_pricing.options import OptionStyle, PricingEngine


def price_option(
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
) -> OptionQuote:
    """Price an option pair with the selected engine."""

    pricing_engine = PricingEngine(engine)
    if pricing_engine == PricingEngine.BLACK_SCHOLES:
        return price_black_scholes(
            stock_price=stock_price,
            strike_price=strike_price,
            time_to_expiry=time_to_expiry,
            interest_rate=interest_rate,
            dividend_yield=dividend_yield,
            volatility=volatility,
            style=style,
        )

    return price_binomial(
        stock_price=stock_price,
        strike_price=strike_price,
        time_to_expiry=time_to_expiry,
        interest_rate=interest_rate,
        dividend_yield=dividend_yield,
        volatility=volatility,
        style=style,
        steps=binomial_steps,
    )
