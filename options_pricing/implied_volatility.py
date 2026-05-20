"""Implied volatility solvers."""

from __future__ import annotations

from dataclasses import dataclass

from options_pricing.options import OptionStyle, OptionType, PricingEngine
from options_pricing.pricing import price_option


@dataclass(frozen=True)
class ImpliedVolatilityResult:
    """Result of an implied volatility solve."""

    volatility: float | None
    model_price: float | None
    status: str

    @property
    def solved(self) -> bool:
        return self.volatility is not None


def solve_implied_volatility(
    *,
    market_price: float,
    stock_price: float,
    strike_price: float,
    time_to_expiry: float,
    interest_rate: float,
    volatility_guess: float | None = None,
    dividend_yield: float = 0.0,
    option_type: str | OptionType,
    style: str | OptionStyle = OptionStyle.AMERICAN,
    engine: str | PricingEngine = PricingEngine.BLACK_SCHOLES,
    binomial_steps: int = 200,
    tolerance: float = 1e-6,
    max_iterations: int = 100,
    max_volatility: float = 5.0,
) -> ImpliedVolatilityResult:
    """Solve the volatility that makes model price match a market price."""

    _validate_inputs(
        market_price=market_price,
        stock_price=stock_price,
        strike_price=strike_price,
        time_to_expiry=time_to_expiry,
        tolerance=tolerance,
        max_iterations=max_iterations,
        max_volatility=max_volatility,
    )
    if time_to_expiry == 0:
        return ImpliedVolatilityResult(
            volatility=None,
            model_price=None,
            status="Time to expiry must be greater than zero.",
        )

    selected_option = OptionType(option_type)
    pricing_engine = PricingEngine(engine)
    option_style = OptionStyle(style)

    lower_volatility = 0.0
    lower_price = _model_price(
        volatility=lower_volatility,
        stock_price=stock_price,
        strike_price=strike_price,
        time_to_expiry=time_to_expiry,
        interest_rate=interest_rate,
        dividend_yield=dividend_yield,
        option_type=selected_option,
        style=option_style,
        engine=pricing_engine,
        binomial_steps=binomial_steps,
    )
    if abs(lower_price - market_price) <= tolerance:
        return ImpliedVolatilityResult(
            volatility=lower_volatility,
            model_price=lower_price,
            status="Solved.",
        )
    if market_price < lower_price:
        return ImpliedVolatilityResult(
            volatility=None,
            model_price=lower_price,
            status="Market price is below the zero-volatility model value.",
        )

    upper_volatility = max(max_volatility, volatility_guess or 0.0, 0.01)
    upper_price = _model_price(
        volatility=upper_volatility,
        stock_price=stock_price,
        strike_price=strike_price,
        time_to_expiry=time_to_expiry,
        interest_rate=interest_rate,
        dividend_yield=dividend_yield,
        option_type=selected_option,
        style=option_style,
        engine=pricing_engine,
        binomial_steps=binomial_steps,
    )
    while upper_price < market_price and upper_volatility < 10.0:
        upper_volatility *= 2.0
        upper_price = _model_price(
            volatility=upper_volatility,
            stock_price=stock_price,
            strike_price=strike_price,
            time_to_expiry=time_to_expiry,
            interest_rate=interest_rate,
            dividend_yield=dividend_yield,
            option_type=selected_option,
            style=option_style,
            engine=pricing_engine,
            binomial_steps=binomial_steps,
        )

    if market_price > upper_price:
        return ImpliedVolatilityResult(
            volatility=None,
            model_price=upper_price,
            status="Market price is above the maximum-volatility model value.",
        )

    best_volatility = upper_volatility
    best_price = upper_price
    for _ in range(max_iterations):
        midpoint = (lower_volatility + upper_volatility) / 2.0
        try:
            midpoint_price = _model_price(
                volatility=midpoint,
                stock_price=stock_price,
                strike_price=strike_price,
                time_to_expiry=time_to_expiry,
                interest_rate=interest_rate,
                dividend_yield=dividend_yield,
                option_type=selected_option,
                style=option_style,
                engine=pricing_engine,
                binomial_steps=binomial_steps,
            )
        except ValueError:
            lower_volatility = midpoint
            continue

        best_volatility = midpoint
        best_price = midpoint_price
        difference = midpoint_price - market_price
        if abs(difference) <= tolerance:
            return ImpliedVolatilityResult(
                volatility=midpoint,
                model_price=midpoint_price,
                status="Solved.",
            )
        if difference < 0:
            lower_volatility = midpoint
        else:
            upper_volatility = midpoint

    return ImpliedVolatilityResult(
        volatility=best_volatility,
        model_price=best_price,
        status="Reached iteration limit.",
    )


def _model_price(
    *,
    volatility: float,
    stock_price: float,
    strike_price: float,
    time_to_expiry: float,
    interest_rate: float,
    dividend_yield: float,
    option_type: OptionType,
    style: OptionStyle,
    engine: PricingEngine,
    binomial_steps: int,
) -> float:
    quote = price_option(
        stock_price=stock_price,
        strike_price=strike_price,
        time_to_expiry=time_to_expiry,
        interest_rate=interest_rate,
        dividend_yield=dividend_yield,
        volatility=volatility,
        style=style,
        engine=engine,
        binomial_steps=binomial_steps,
    )
    return quote.call if option_type == OptionType.CALL else quote.put


def _validate_inputs(
    *,
    market_price: float,
    stock_price: float,
    strike_price: float,
    time_to_expiry: float,
    tolerance: float,
    max_iterations: int,
    max_volatility: float,
) -> None:
    if market_price < 0:
        raise ValueError("market_price cannot be negative.")
    if stock_price <= 0:
        raise ValueError("stock_price must be greater than zero.")
    if strike_price <= 0:
        raise ValueError("strike_price must be greater than zero.")
    if time_to_expiry < 0:
        raise ValueError("time_to_expiry cannot be negative.")
    if tolerance <= 0:
        raise ValueError("tolerance must be greater than zero.")
    if max_iterations < 1:
        raise ValueError("max_iterations must be at least 1.")
    if max_volatility <= 0:
        raise ValueError("max_volatility must be greater than zero.")
