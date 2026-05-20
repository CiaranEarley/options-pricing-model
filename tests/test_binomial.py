import unittest

from options_pricing.binomial import price_binomial
from options_pricing.black_scholes import price_black_scholes
from options_pricing.options import OptionStyle


class BinomialTests(unittest.TestCase):
    def test_european_binomial_converges_toward_black_scholes(self):
        black_scholes = price_black_scholes(
            stock_price=100,
            strike_price=100,
            time_to_expiry=1,
            interest_rate=0.05,
            volatility=0.20,
            style=OptionStyle.EUROPEAN,
        )
        binomial = price_binomial(
            stock_price=100,
            strike_price=100,
            time_to_expiry=1,
            interest_rate=0.05,
            volatility=0.20,
            style=OptionStyle.EUROPEAN,
            steps=500,
        )

        self.assertAlmostEqual(binomial.call, black_scholes.call, delta=0.02)
        self.assertAlmostEqual(binomial.put, black_scholes.put, delta=0.02)

    def test_american_put_is_at_least_european_put(self):
        european = price_binomial(
            stock_price=100,
            strike_price=105,
            time_to_expiry=1,
            interest_rate=0.05,
            volatility=0.25,
            style=OptionStyle.EUROPEAN,
            steps=200,
        )
        american = price_binomial(
            stock_price=100,
            strike_price=105,
            time_to_expiry=1,
            interest_rate=0.05,
            volatility=0.25,
            style=OptionStyle.AMERICAN,
            steps=200,
        )

        self.assertGreaterEqual(american.put, european.put)

    def test_non_dividend_american_call_matches_european_call(self):
        european = price_binomial(
            stock_price=100,
            strike_price=95,
            time_to_expiry=1,
            interest_rate=0.05,
            volatility=0.25,
            style=OptionStyle.EUROPEAN,
            steps=200,
        )
        american = price_binomial(
            stock_price=100,
            strike_price=95,
            time_to_expiry=1,
            interest_rate=0.05,
            volatility=0.25,
            style=OptionStyle.AMERICAN,
            steps=200,
        )

        self.assertAlmostEqual(american.call, european.call, places=10)

    def test_zero_time_returns_intrinsic_value(self):
        quote = price_binomial(
            stock_price=110,
            strike_price=100,
            time_to_expiry=0,
            interest_rate=0.05,
            volatility=0.20,
            steps=50,
        )

        self.assertEqual(quote.call, 10)
        self.assertEqual(quote.put, 0)

    def test_rejects_invalid_steps(self):
        with self.assertRaises(ValueError):
            price_binomial(
                stock_price=100,
                strike_price=100,
                time_to_expiry=1,
                interest_rate=0.05,
                volatility=0.20,
                steps=0,
            )


if __name__ == "__main__":
    unittest.main()
