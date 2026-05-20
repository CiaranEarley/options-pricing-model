"""Options pricing models and command-line tools."""

from options_pricing.binomial import price_binomial
from options_pricing.black_scholes import OptionQuote, price_black_scholes
from options_pricing.greeks import GreeksQuote, OptionGreeks, calculate_greeks
from options_pricing.implied_volatility import (
    ImpliedVolatilityResult,
    solve_implied_volatility,
)
from options_pricing.market_data import (
    MarketDataError,
    MarketOptionChain,
    MarketOptionContract,
    MarketTickerSnapshot,
    fetch_option_chain,
    fetch_ticker_snapshot,
)
from options_pricing.options import OptionStyle, OptionType, PricingEngine
from options_pricing.payoff import PayoffCurve, build_payoff_curve
from options_pricing.pricing import price_option

__all__ = [
    "GreeksQuote",
    "ImpliedVolatilityResult",
    "MarketDataError",
    "MarketOptionChain",
    "MarketOptionContract",
    "MarketTickerSnapshot",
    "OptionQuote",
    "OptionGreeks",
    "OptionStyle",
    "OptionType",
    "PayoffCurve",
    "PricingEngine",
    "build_payoff_curve",
    "calculate_greeks",
    "fetch_option_chain",
    "fetch_ticker_snapshot",
    "price_binomial",
    "price_black_scholes",
    "price_option",
    "solve_implied_volatility",
]
