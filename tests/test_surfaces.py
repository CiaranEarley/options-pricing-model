import unittest

from options_pricing.options import OptionType, PricingEngine
from options_pricing.surfaces import build_pnl_surface, build_price_surface


class SurfaceTests(unittest.TestCase):
    def test_price_surface_uses_requested_grid_size(self):
        surface = build_price_surface(
            stock_price=100,
            strike_price=100,
            time_to_expiry=1,
            interest_rate=0.05,
            volatility=0.20,
            option_type=OptionType.CALL,
            stock_shock_min=-0.10,
            stock_shock_max=0.10,
            volatility_shock_min=-0.10,
            volatility_shock_max=0.10,
            steps=5,
        )

        self.assertEqual(len(surface.stock_prices), 5)
        self.assertEqual(len(surface.volatilities), 5)
        self.assertEqual(len(surface.values), 5)
        self.assertEqual(len(surface.values[0]), 5)
        self.assertAlmostEqual(surface.stock_prices[0], 90)
        self.assertAlmostEqual(surface.stock_prices[-1], 110)

    def test_pnl_surface_subtracts_purchase_price(self):
        surface = build_price_surface(
            stock_price=100,
            strike_price=100,
            time_to_expiry=1,
            interest_rate=0.05,
            volatility=0.20,
            option_type=OptionType.PUT,
            stock_shock_min=0,
            stock_shock_max=0.10,
            volatility_shock_min=0,
            volatility_shock_max=0.10,
            steps=2,
        )

        pnl_surface = build_pnl_surface(purchase_price=5, price_surface=surface)

        self.assertAlmostEqual(pnl_surface.values[0][0], surface.values[0][0] - 5)
        self.assertEqual(pnl_surface.stock_prices, surface.stock_prices)
        self.assertEqual(pnl_surface.volatilities, surface.volatilities)

    def test_rejects_shocks_that_zero_out_stock(self):
        with self.assertRaises(ValueError):
            build_price_surface(
                stock_price=100,
                strike_price=100,
                time_to_expiry=1,
                interest_rate=0.05,
                volatility=0.20,
                option_type=OptionType.CALL,
                stock_shock_min=-1,
            )

    def test_price_surface_can_use_binomial_engine(self):
        surface = build_price_surface(
            stock_price=100,
            strike_price=100,
            time_to_expiry=1,
            interest_rate=0.05,
            volatility=0.20,
            option_type=OptionType.CALL,
            engine=PricingEngine.BINOMIAL,
            binomial_steps=25,
            steps=3,
        )

        self.assertEqual(len(surface.values), 3)
        self.assertGreater(surface.values[1][1], 0)


if __name__ == "__main__":
    unittest.main()
