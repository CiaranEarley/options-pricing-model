import unittest

from options_pricing.black_scholes import OptionStyle, price_black_scholes
from options_pricing.cli import parse_number


class BlackScholesTests(unittest.TestCase):
    def test_known_european_at_the_money_prices(self):
        quote = price_black_scholes(
            stock_price=100,
            strike_price=100,
            time_to_expiry=1,
            interest_rate=0.05,
            volatility=0.20,
            style=OptionStyle.EUROPEAN,
        )

        self.assertAlmostEqual(quote.call, 10.4506, places=4)
        self.assertAlmostEqual(quote.put, 5.5735, places=4)

    def test_put_call_parity_for_european_options(self):
        quote = price_black_scholes(
            stock_price=120,
            strike_price=115,
            time_to_expiry=0.75,
            interest_rate=0.04,
            volatility=0.30,
            style=OptionStyle.EUROPEAN,
        )

        discounted_strike = 115 * 2.718281828459045 ** (-0.04 * 0.75)
        self.assertAlmostEqual(quote.call - quote.put, 120 - discounted_strike)

    def test_dividend_yield_lowers_call_and_raises_put(self):
        no_dividend = price_black_scholes(
            stock_price=100,
            strike_price=100,
            time_to_expiry=1,
            interest_rate=0.05,
            volatility=0.20,
            style=OptionStyle.EUROPEAN,
        )
        with_dividend = price_black_scholes(
            stock_price=100,
            strike_price=100,
            time_to_expiry=1,
            interest_rate=0.05,
            dividend_yield=0.03,
            volatility=0.20,
            style=OptionStyle.EUROPEAN,
        )

        self.assertLess(with_dividend.call, no_dividend.call)
        self.assertGreater(with_dividend.put, no_dividend.put)

    def test_american_put_baseline_is_floored_at_intrinsic_value(self):
        quote = price_black_scholes(
            stock_price=50,
            strike_price=100,
            time_to_expiry=1,
            interest_rate=0.05,
            volatility=0.20,
        )

        self.assertEqual(quote.style, OptionStyle.AMERICAN)
        self.assertEqual(quote.put, 50)
        self.assertIsNotNone(quote.note)

    def test_percent_parser_for_rates_and_volatility(self):
        self.assertEqual(parse_number("5%", allow_percent=True), 0.05)
        self.assertEqual(parse_number("0.2", allow_percent=True), 0.2)

    def test_rejects_invalid_price_inputs(self):
        with self.assertRaises(ValueError):
            price_black_scholes(
                stock_price=0,
                strike_price=100,
                time_to_expiry=1,
                interest_rate=0.05,
                volatility=0.20,
            )


if __name__ == "__main__":
    unittest.main()
