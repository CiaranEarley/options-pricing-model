# App Walkthrough

## Market Data

The `Market Data` sidebar section loads delayed option-chain data with
`yfinance`. A selected contract can populate spot, strike, expiry, market price,
listed IV, volume, and open interest fields.

## Inputs

The `Inputs` section controls the theoretical model: pricing engine, exercise
style, stock price, strike, time to expiry, interest rate, dividend yield, and
volatility.

## Market Prices

The market call and put prices are used by the implied-volatility solver. This
lets you compare the volatility implied by the market with the volatility used
in the model.

## Shock Grid

The shock grid defines the stock-price and volatility ranges used in the
heatmaps. Increasing grid size gives more detail; smaller grids are easier to
read in screenshots.

## Price And PnL Heatmaps

The price heatmaps show model value for calls and puts across the scenario grid.
The PnL heatmaps subtract the chosen purchase price, turning model value into a
trade payoff surface.

![Options heatmaps](../assets/options-pricing-heatmaps-wide.png)

## Expiry Payoff And PnL

The payoff chart shows the value of calls and puts at expiry across stock-price
outcomes. Solid lines show PnL after purchase cost; dashed lines show raw payoff.

![Options payoff](../assets/options-pricing-payoff-wide.png)
