# Getting Started

## Install

```powershell
python -m pip install -e .
```

## Run The Streamlit App

```powershell
python -m streamlit run app.py
```

Use the app to:

- Price calls and puts with Black-Scholes or a binomial tree.
- Compare model prices, Greeks, and implied volatility.
- Load delayed option-chain data through `yfinance`.
- Inspect price and PnL heatmaps across spot and volatility shocks.
- View expiry payoff and PnL curves.

![Options pricing dashboard](../assets/options-pricing-dashboard-wide.png)

## Run The CLI

```powershell
python -m options_pricing.cli --stock-price 100 --strike-price 100 --time-to-expiry 1 --interest-rate 5% --dividend-yield 2% --volatility 20%
```

## Run Tests

```powershell
python -m unittest discover
```
