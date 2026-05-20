import unittest

from options_pricing.greeks import calculate_black_scholes_greeks, calculate_greeks
from options_pricing.options import OptionStyle, PricingEngine


class GreeksTests(unittest.TestCase):
    def test_known_black_scholes_greeks(self):
        greeks = calculate_black_scholes_greeks(
            stock_price=100,
            strike_price=100,
            time_to_expiry=1,
            interest_rate=0.05,
            volatility=0.20,
        )

        self.assertAlmostEqual(greeks.call.delta, 0.6368, places=4)
        self.assertAlmostEqual(greeks.put.delta, -0.3632, places=4)
        self.assertAlmostEqual(greeks.call.gamma, 0.0188, places=4)
        self.assertAlmostEqual(greeks.call.vega, 0.3752, places=4)
        self.assertAlmostEqual(greeks.call.theta, -0.0176, places=4)
        self.assertAlmostEqual(greeks.call.rho, 0.5323, places=4)

    def test_expired_option_greeks_are_unavailable(self):
        greeks = calculate_black_scholes_greeks(
            stock_price=100,
            strike_price=100,
            time_to_expiry=0,
            interest_rate=0.05,
            volatility=0.20,
        )

        self.assertIsNone(greeks.call.delta)
        self.assertIsNone(greeks.put.gamma)

    def test_binomial_greeks_are_available(self):
        greeks = calculate_greeks(
            stock_price=100,
            strike_price=100,
            time_to_expiry=1,
            interest_rate=0.05,
            volatility=0.20,
            style=OptionStyle.AMERICAN,
            engine=PricingEngine.BINOMIAL,
            binomial_steps=100,
        )

        self.assertGreater(greeks.call.delta, 0)
        self.assertLess(greeks.put.delta, 0)
        self.assertGreater(greeks.call.vega, 0)


if __name__ == "__main__":
    unittest.main()
