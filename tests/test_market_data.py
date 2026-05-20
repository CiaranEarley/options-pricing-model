from datetime import date
import unittest

import pandas as pd

from options_pricing.market_data import (
    build_option_chain,
    calculate_time_to_expiry,
    select_contract_by_strike,
    select_nearest_contract,
    _future_expirations,
)


class MarketDataTests(unittest.TestCase):
    def test_builds_chain_and_prefers_bid_ask_mid(self):
        calls = pd.DataFrame(
            [
                {
                    "strike": 100,
                    "bid": 4.8,
                    "ask": 5.2,
                    "lastPrice": 4.9,
                    "impliedVolatility": 0.22,
                    "volume": 10,
                    "openInterest": 100,
                }
            ]
        )
        puts = pd.DataFrame(
            [
                {
                    "strike": 100,
                    "bid": 3.8,
                    "ask": 4.2,
                    "lastPrice": 3.9,
                    "impliedVolatility": 0.24,
                    "volume": 12,
                    "openInterest": 120,
                }
            ]
        )

        chain = build_option_chain(
            ticker="aapl",
            spot_price=101,
            expiration="2026-06-20",
            calls=calls,
            puts=puts,
            valuation_date=date(2026, 5, 21),
        )

        contract = chain.contracts[0]
        self.assertEqual(chain.ticker, "AAPL")
        self.assertEqual(contract.call_market_price, 5.0)
        self.assertEqual(contract.put_market_price, 4.0)
        self.assertEqual(contract.call_open_interest, 100)
        self.assertAlmostEqual(chain.time_to_expiry, 30 / 365)

    def test_falls_back_to_last_price_when_mid_missing(self):
        calls = pd.DataFrame([{"strike": 100, "bid": 0, "ask": 0, "lastPrice": 6}])
        puts = pd.DataFrame([{"strike": 100, "bid": None, "ask": None, "lastPrice": 7}])

        chain = build_option_chain(
            ticker="MSFT",
            spot_price=100,
            expiration="2026-06-20",
            calls=calls,
            puts=puts,
            valuation_date=date(2026, 5, 21),
        )

        self.assertEqual(chain.contracts[0].call_market_price, 6)
        self.assertEqual(chain.contracts[0].put_market_price, 7)

    def test_selects_nearest_contract(self):
        data = pd.DataFrame(
            [
                {"strike": 95, "lastPrice": 8},
                {"strike": 105, "lastPrice": 4},
            ]
        )
        chain = build_option_chain(
            ticker="SPY",
            spot_price=103,
            expiration="2026-06-20",
            calls=data,
            puts=data,
            valuation_date=date(2026, 5, 21),
        )

        self.assertEqual(select_nearest_contract(chain).strike, 105)
        self.assertEqual(select_contract_by_strike(chain, 94).strike, 95)

    def test_calculates_zero_for_expired_date(self):
        self.assertEqual(
            calculate_time_to_expiry(
                "2026-05-01",
                valuation_date=date(2026, 5, 21),
            ),
            0,
        )

    def test_filters_stale_expirations(self):
        today = date.today()
        stale = today.replace(year=today.year - 1).isoformat()
        future = today.replace(year=today.year + 1).isoformat()

        self.assertEqual(_future_expirations([stale, future]), [future])


if __name__ == "__main__":
    unittest.main()
