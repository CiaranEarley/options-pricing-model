import unittest

from options_pricing.payoff import build_payoff_curve


class PayoffTests(unittest.TestCase):
    def test_builds_long_call_and_put_pnl_curves(self):
        curve = build_payoff_curve(
            stock_price=100,
            strike_price=100,
            call_purchase_price=8,
            put_purchase_price=6,
            stock_shock_min=-0.20,
            stock_shock_max=0.20,
            steps=3,
        )

        self.assertEqual(curve.stock_prices, [80, 100, 120])
        self.assertEqual(curve.call_payoff, [0, 0, 20])
        self.assertEqual(curve.put_payoff, [20, 0, 0])
        self.assertEqual(curve.call_pnl, [-8, -8, 12])
        self.assertEqual(curve.put_pnl, [14, -6, -6])

    def test_rejects_negative_purchase_price(self):
        with self.assertRaises(ValueError):
            build_payoff_curve(
                stock_price=100,
                strike_price=100,
                call_purchase_price=-1,
                put_purchase_price=6,
            )


if __name__ == "__main__":
    unittest.main()
