import unittest

from options_pricing.binomial import price_binomial
from options_pricing.black_scholes import price_black_scholes
from options_pricing.implied_volatility import solve_implied_volatility
from options_pricing.options import OptionStyle, OptionType, PricingEngine


class ImpliedVolatilityTests(unittest.TestCase):
    def test_solves_black_scholes_call_implied_volatility(self):
        quote = price_black_scholes(
            stock_price=100,
            strike_price=100,
            time_to_expiry=1,
            interest_rate=0.05,
            volatility=0.20,
            style=OptionStyle.EUROPEAN,
        )

        result = solve_implied_volatility(
            market_price=quote.call,
            stock_price=100,
            strike_price=100,
            time_to_expiry=1,
            interest_rate=0.05,
            volatility_guess=0.20,
            option_type=OptionType.CALL,
            style=OptionStyle.EUROPEAN,
            engine=PricingEngine.BLACK_SCHOLES,
        )

        self.assertTrue(result.solved)
        self.assertAlmostEqual(result.volatility, 0.20, places=4)

    def test_solves_black_scholes_put_implied_volatility(self):
        quote = price_black_scholes(
            stock_price=100,
            strike_price=100,
            time_to_expiry=1,
            interest_rate=0.05,
            dividend_yield=0.02,
            volatility=0.25,
            style=OptionStyle.EUROPEAN,
        )

        result = solve_implied_volatility(
            market_price=quote.put,
            stock_price=100,
            strike_price=100,
            time_to_expiry=1,
            interest_rate=0.05,
            dividend_yield=0.02,
            volatility_guess=0.25,
            option_type=OptionType.PUT,
            style=OptionStyle.EUROPEAN,
            engine=PricingEngine.BLACK_SCHOLES,
        )

        self.assertTrue(result.solved)
        self.assertAlmostEqual(result.volatility, 0.25, places=4)

    def test_solves_binomial_american_put_implied_volatility(self):
        quote = price_binomial(
            stock_price=100,
            strike_price=105,
            time_to_expiry=1,
            interest_rate=0.05,
            volatility=0.30,
            style=OptionStyle.AMERICAN,
            steps=100,
        )

        result = solve_implied_volatility(
            market_price=quote.put,
            stock_price=100,
            strike_price=105,
            time_to_expiry=1,
            interest_rate=0.05,
            volatility_guess=0.30,
            option_type=OptionType.PUT,
            style=OptionStyle.AMERICAN,
            engine=PricingEngine.BINOMIAL,
            binomial_steps=100,
        )

        self.assertTrue(result.solved)
        self.assertAlmostEqual(result.volatility, 0.30, places=4)

    def test_below_zero_volatility_value_is_unsolved(self):
        result = solve_implied_volatility(
            market_price=0.01,
            stock_price=150,
            strike_price=100,
            time_to_expiry=1,
            interest_rate=0.05,
            option_type=OptionType.CALL,
            style=OptionStyle.EUROPEAN,
            engine=PricingEngine.BLACK_SCHOLES,
        )

        self.assertFalse(result.solved)
        self.assertIn("below", result.status)

    def test_expired_option_iv_is_unavailable(self):
        result = solve_implied_volatility(
            market_price=10,
            stock_price=110,
            strike_price=100,
            time_to_expiry=0,
            interest_rate=0.05,
            option_type=OptionType.CALL,
        )

        self.assertFalse(result.solved)
        self.assertIn("Time to expiry", result.status)


if __name__ == "__main__":
    unittest.main()
