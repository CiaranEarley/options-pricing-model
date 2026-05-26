# Project Architecture

The repo separates pricing math, market data loading, Streamlit UI, and tests.

## Main Files

| File | Role |
| --- | --- |
| `app.py` | Streamlit dashboard. |
| `options_pricing/black_scholes.py` | Black-Scholes pricing. |
| `options_pricing/binomial.py` | Cox-Ross-Rubinstein binomial tree. |
| `options_pricing/greeks.py` | Greeks calculations. |
| `options_pricing/implied_volatility.py` | Implied volatility solver. |
| `options_pricing/market_data.py` | yfinance market data adapter. |
| `options_pricing/payoff.py` | Expiry payoff and PnL curves. |
| `options_pricing/surfaces.py` | Price and PnL scenario grids. |
| `tests/` | Unit tests for pricing, Greeks, IV, payoff, and surfaces. |

## App Pipeline

```text
user inputs / option-chain data
        |
        v
pricing engine
        |
        v
Greeks, implied volatility, surfaces, payoff curves
        |
        v
Streamlit tables, metrics, heatmaps, and charts
```

## Design Choices

- Pure pricing functions are kept outside Streamlit so they can be tested.
- Market data is optional; the model can be used entirely with manual inputs.
- The binomial tree is used where early-exercise behavior matters.
- Heatmaps use scenario grids so risk is visible across spot and volatility.
