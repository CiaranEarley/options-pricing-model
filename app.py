"""Streamlit interface for the options pricing model."""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from options_pricing.greeks import calculate_greeks
from options_pricing.implied_volatility import solve_implied_volatility
from options_pricing.market_data import (
    MarketDataError,
    fetch_option_chain,
    fetch_ticker_snapshot,
    select_contract_by_strike,
    select_nearest_contract,
)
from options_pricing.options import OptionStyle, OptionType, PricingEngine
from options_pricing.payoff import build_payoff_curve
from options_pricing.pricing import price_option
from options_pricing.surfaces import build_pnl_surface, build_price_surface


PRICE_SCALE = [
    [0.0, "#b91c1c"],
    [0.5, "#f8fafc"],
    [1.0, "#15803d"],
]
PNL_SCALE = [
    [0.0, "#b91c1c"],
    [0.5, "#f8fafc"],
    [1.0, "#15803d"],
]
ENGINE_LABELS = {
    PricingEngine.BLACK_SCHOLES: "Black-Scholes",
    PricingEngine.BINOMIAL: "Binomial Tree",
}
DEFAULT_TICKERS = ["AAPL", "MSFT", "NVDA", "SPY", "QQQ", "TSLA", "AMZN", "GOOGL", "META"]


def main() -> None:
    st.set_page_config(
        page_title="Options Pricing Model",
        page_icon=None,
        layout="wide",
        initial_sidebar_state="expanded",
    )
    _apply_styles()

    st.title("Options Pricing Model")

    inputs = _sidebar_inputs()
    quote = price_option(
        stock_price=inputs["stock_price"],
        strike_price=inputs["strike_price"],
        time_to_expiry=inputs["time_to_expiry"],
        interest_rate=inputs["interest_rate"],
        dividend_yield=inputs["dividend_yield"],
        volatility=inputs["volatility"],
        style=inputs["style"],
        engine=inputs["engine"],
        binomial_steps=inputs["binomial_steps"],
    )
    greeks = calculate_greeks(
        stock_price=inputs["stock_price"],
        strike_price=inputs["strike_price"],
        time_to_expiry=inputs["time_to_expiry"],
        interest_rate=inputs["interest_rate"],
        dividend_yield=inputs["dividend_yield"],
        volatility=inputs["volatility"],
        style=inputs["style"],
        engine=inputs["engine"],
        binomial_steps=inputs["binomial_steps"],
    )
    implied_volatility = _solve_implied_volatility(inputs)

    _quote_metrics(quote)
    _render_selected_market_contract()
    _render_implied_volatility(implied_volatility)
    _render_greeks(greeks)
    if quote.note:
        st.info(quote.note)

    call_price_surface = _build_surface(inputs, OptionType.CALL)
    put_price_surface = _build_surface(inputs, OptionType.PUT)
    call_pnl_surface = build_pnl_surface(
        purchase_price=inputs["call_purchase_price"],
        price_surface=call_price_surface,
    )
    put_pnl_surface = build_pnl_surface(
        purchase_price=inputs["put_purchase_price"],
        price_surface=put_price_surface,
    )

    _render_heatmap_pair(
        heading="Price Heatmaps",
        call_surface=call_price_surface,
        put_surface=put_price_surface,
        call_title="Call Price Heatmap",
        put_title="Put Price Heatmap",
        z_title="Option price",
        colorscale=PRICE_SCALE,
    )
    _render_heatmap_pair(
        heading="PnL Heatmaps",
        call_surface=call_pnl_surface,
        put_surface=put_pnl_surface,
        call_title="Call PnL Heatmap",
        put_title="Put PnL Heatmap",
        z_title="PnL",
        colorscale=PNL_SCALE,
        zmid=0,
    )
    payoff_curve = build_payoff_curve(
        stock_price=inputs["stock_price"],
        strike_price=inputs["strike_price"],
        call_purchase_price=inputs["call_purchase_price"],
        put_purchase_price=inputs["put_purchase_price"],
        stock_shock_min=inputs["stock_shock_min"],
        stock_shock_max=inputs["stock_shock_max"],
    )
    _render_payoff_curve(payoff_curve)

    _render_grid_data(
        call_price_surface=call_price_surface,
        put_price_surface=put_price_surface,
        call_pnl_surface=call_pnl_surface,
        put_pnl_surface=put_pnl_surface,
    )
    _render_model_notes()


def _build_surface(inputs: dict, option_type: OptionType):
    return build_price_surface(
        stock_price=inputs["stock_price"],
        strike_price=inputs["strike_price"],
        time_to_expiry=inputs["time_to_expiry"],
        interest_rate=inputs["interest_rate"],
        dividend_yield=inputs["dividend_yield"],
        volatility=inputs["volatility"],
        option_type=option_type,
        style=inputs["style"],
        engine=inputs["engine"],
        binomial_steps=inputs["binomial_steps"],
        stock_shock_min=inputs["stock_shock_min"],
        stock_shock_max=inputs["stock_shock_max"],
        volatility_shock_min=inputs["volatility_shock_min"],
        volatility_shock_max=inputs["volatility_shock_max"],
        steps=inputs["steps"],
    )


def _sidebar_inputs() -> dict:
    _initialize_sidebar_state()
    with st.sidebar:
        _market_data_controls()

        st.header("Inputs")
        styles = list(OptionStyle)
        engines = list(PricingEngine)
        engine = st.radio(
            "Pricing engine",
            options=engines,
            format_func=lambda value: ENGINE_LABELS[value],
            horizontal=True,
            key="pricing_engine",
        )
        style = st.radio(
            "Exercise style",
            options=styles,
            format_func=lambda value: value.value.title(),
            horizontal=True,
            key="option_style",
        )
        binomial_steps = 200
        if engine == PricingEngine.BINOMIAL:
            binomial_steps = st.slider(
                "Binomial steps",
                min_value=25,
                max_value=500,
                step=25,
                key="binomial_steps",
            )

        stock_price = st.number_input(
            "Stock price",
            min_value=0.01,
            step=1.00,
            format="%.2f",
            key="stock_price",
        )
        strike_price = st.number_input(
            "Strike price",
            min_value=0.01,
            step=1.00,
            format="%.2f",
            key="strike_price",
        )
        time_to_expiry = st.number_input(
            "Time to expiry (years)",
            min_value=0.00,
            step=0.25,
            format="%.2f",
            key="time_to_expiry",
        )
        interest_rate_pct = st.number_input(
            "Risk-free rate (%)",
            step=0.25,
            format="%.2f",
            key="interest_rate_pct",
        )
        dividend_yield_pct = st.number_input(
            "Dividend yield (%)",
            min_value=0.00,
            step=0.25,
            format="%.2f",
            key="dividend_yield_pct",
        )
        volatility_pct = st.number_input(
            "Volatility (%)",
            min_value=0.00,
            step=1.00,
            format="%.2f",
            key="volatility_pct",
        )
        call_purchase_price = st.number_input(
            "Call purchase price",
            min_value=0.00,
            step=0.50,
            format="%.2f",
            key="call_purchase_price",
        )
        put_purchase_price = st.number_input(
            "Put purchase price",
            min_value=0.00,
            step=0.50,
            format="%.2f",
            key="put_purchase_price",
        )

        st.header("Market Prices")
        market_call_price = st.number_input(
            "Market call price",
            min_value=0.00,
            step=0.25,
            format="%.2f",
            key="market_call_price",
        )
        market_put_price = st.number_input(
            "Market put price",
            min_value=0.00,
            step=0.25,
            format="%.2f",
            key="market_put_price",
        )

        st.header("Shock Grid")
        stock_range = st.slider(
            "Stock shock (%)",
            min_value=-80,
            max_value=100,
            value=(-30, 30),
            step=5,
        )
        volatility_range = st.slider(
            "Volatility shock (%)",
            min_value=-80,
            max_value=200,
            value=(-30, 30),
            step=5,
        )
        steps = st.slider("Grid size", min_value=5, max_value=17, value=10, step=1)

    return {
        "engine": engine,
        "style": style,
        "stock_price": stock_price,
        "strike_price": strike_price,
        "time_to_expiry": time_to_expiry,
        "interest_rate": interest_rate_pct / 100,
        "dividend_yield": dividend_yield_pct / 100,
        "volatility": volatility_pct / 100,
        "binomial_steps": binomial_steps,
        "call_purchase_price": call_purchase_price,
        "put_purchase_price": put_purchase_price,
        "market_call_price": market_call_price,
        "market_put_price": market_put_price,
        "stock_shock_min": stock_range[0] / 100,
        "stock_shock_max": stock_range[1] / 100,
        "volatility_shock_min": volatility_range[0] / 100,
        "volatility_shock_max": volatility_range[1] / 100,
        "steps": steps,
    }


def _initialize_sidebar_state() -> None:
    defaults = {
        "pricing_engine": PricingEngine.BLACK_SCHOLES,
        "option_style": OptionStyle.AMERICAN,
        "binomial_steps": 200,
        "stock_price": 100.00,
        "strike_price": 100.00,
        "time_to_expiry": 1.00,
        "interest_rate_pct": 5.00,
        "dividend_yield_pct": 0.00,
        "volatility_pct": 20.00,
        "call_purchase_price": 10.00,
        "put_purchase_price": 5.00,
        "market_call_price": 10.45,
        "market_put_price": 5.57,
        "market_ticker_choice": DEFAULT_TICKERS[0],
        "custom_market_ticker": "",
    }
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)


def _market_data_controls() -> None:
    st.header("Market Data")
    ticker_choice = st.selectbox(
        "Ticker",
        options=[*DEFAULT_TICKERS, "Custom"],
        key="market_ticker_choice",
    )
    custom_ticker = ""
    if ticker_choice == "Custom":
        custom_ticker = st.text_input("Custom ticker", key="custom_market_ticker")
    ticker = (custom_ticker if ticker_choice == "Custom" else ticker_choice).strip().upper()

    if st.button("Load ticker", use_container_width=True):
        _load_market_snapshot(ticker)

    snapshot = st.session_state.get("market_snapshot")
    if snapshot:
        st.caption(
            f"{snapshot.ticker} spot: {snapshot.spot_price:,.2f} "
            f"({snapshot.provider}, delayed)"
        )
        if st.session_state.get("market_expiry") not in snapshot.expirations:
            st.session_state["market_expiry"] = snapshot.expirations[0]
        selected_expiry = st.selectbox(
            "Expiry",
            options=snapshot.expirations,
            key="market_expiry",
        )
        if st.button("Load option chain", use_container_width=True):
            _load_market_chain(snapshot.ticker, selected_expiry)

    chain = st.session_state.get("market_chain")
    if chain:
        strikes = [contract.strike for contract in chain.contracts]
        if not strikes:
            st.warning("No strikes found in the loaded option chain.")
            return
        current_selected = st.session_state.get("market_selected_strike")
        if current_selected not in strikes:
            st.session_state["market_selected_strike"] = select_nearest_contract(chain).strike
        selected_strike = st.selectbox(
            "Strike",
            options=strikes,
            format_func=lambda value: f"{value:,.2f}",
            key="market_selected_strike",
        )
        contract = select_contract_by_strike(chain, selected_strike)
        st.caption(
            "Call "
            f"{_format_market_value(contract.call_market_price)} | "
            "Put "
            f"{_format_market_value(contract.put_market_price)} | "
            f"T={chain.time_to_expiry:.3f}y"
        )
        if st.button("Apply selected contract", use_container_width=True):
            _apply_market_contract(chain, contract)


def _load_market_snapshot(ticker: str) -> None:
    try:
        with st.spinner(f"Loading {ticker} expirations..."):
            snapshot = _cached_ticker_snapshot(ticker)
    except MarketDataError as error:
        st.warning(str(error))
        return
    except Exception as error:
        st.warning(f"Market data request failed: {error}")
        return

    st.session_state["market_snapshot"] = snapshot
    st.session_state["market_chain"] = None
    st.session_state["market_expiry"] = snapshot.expirations[0]
    st.session_state["market_selected_strike"] = None
    st.success(f"Loaded {snapshot.ticker}.")


def _load_market_chain(ticker: str, expiry: str) -> None:
    try:
        with st.spinner(f"Loading {ticker} {expiry} chain..."):
            chain = _cached_option_chain(ticker, expiry)
    except MarketDataError as error:
        st.warning(str(error))
        return
    except Exception as error:
        st.warning(f"Option chain request failed: {error}")
        return

    st.session_state["market_chain"] = chain
    st.session_state["market_selected_strike"] = select_nearest_contract(chain).strike
    st.success(f"Loaded {chain.ticker} {chain.expiration}.")


def _apply_market_contract(chain, contract) -> None:
    st.session_state["stock_price"] = float(chain.spot_price)
    st.session_state["strike_price"] = float(contract.strike)
    st.session_state["time_to_expiry"] = float(chain.time_to_expiry)

    if contract.call_market_price is not None:
        st.session_state["market_call_price"] = float(contract.call_market_price)
        st.session_state["call_purchase_price"] = float(contract.call_market_price)
    if contract.put_market_price is not None:
        st.session_state["market_put_price"] = float(contract.put_market_price)
        st.session_state["put_purchase_price"] = float(contract.put_market_price)

    market_ivs = [
        value
        for value in (
            contract.call_implied_volatility,
            contract.put_implied_volatility,
        )
        if value is not None and value > 0
    ]
    if market_ivs:
        st.session_state["volatility_pct"] = float(sum(market_ivs) / len(market_ivs) * 100)

    st.session_state["market_contract_summary"] = {
        "Ticker": chain.ticker,
        "Expiry": chain.expiration,
        "Strike": f"{contract.strike:,.2f}",
        "Spot": f"{chain.spot_price:,.2f}",
        "Call market": _format_market_value(contract.call_market_price),
        "Put market": _format_market_value(contract.put_market_price),
    }
    st.success("Applied market contract to model inputs.")


@st.cache_data(ttl=300, show_spinner=False)
def _cached_ticker_snapshot(ticker: str):
    return fetch_ticker_snapshot(ticker)


@st.cache_data(ttl=300, show_spinner=False)
def _cached_option_chain(ticker: str, expiry: str):
    return fetch_option_chain(ticker, expiry)


def _quote_metrics(quote) -> None:
    call_col, put_col = st.columns(2)
    call_col.metric("Call price", f"{quote.call:,.4f}")
    put_col.metric("Put price", f"{quote.put:,.4f}")


def _render_selected_market_contract() -> None:
    summary = st.session_state.get("market_contract_summary")
    if not summary:
        return
    st.subheader("Selected Market Contract")
    st.dataframe(pd.DataFrame([summary]), use_container_width=True, hide_index=True)


def _solve_implied_volatility(inputs: dict):
    common_inputs = {
        "stock_price": inputs["stock_price"],
        "strike_price": inputs["strike_price"],
        "time_to_expiry": inputs["time_to_expiry"],
        "interest_rate": inputs["interest_rate"],
        "dividend_yield": inputs["dividend_yield"],
        "volatility_guess": inputs["volatility"],
        "style": inputs["style"],
        "engine": inputs["engine"],
        "binomial_steps": inputs["binomial_steps"],
    }
    return {
        OptionType.CALL: solve_implied_volatility(
            market_price=inputs["market_call_price"],
            option_type=OptionType.CALL,
            **common_inputs,
        ),
        OptionType.PUT: solve_implied_volatility(
            market_price=inputs["market_put_price"],
            option_type=OptionType.PUT,
            **common_inputs,
        ),
    }


def _render_implied_volatility(results: dict) -> None:
    st.subheader("Implied Volatility")
    st.dataframe(
        pd.DataFrame(
            {
                "Implied vol": [
                    _format_percent_optional(results[OptionType.CALL].volatility),
                    _format_percent_optional(results[OptionType.PUT].volatility),
                ],
                "Model price": [
                    _format_optional(results[OptionType.CALL].model_price),
                    _format_optional(results[OptionType.PUT].model_price),
                ],
                "Status": [
                    results[OptionType.CALL].status,
                    results[OptionType.PUT].status,
                ],
            },
            index=["Call", "Put"],
        ),
        use_container_width=True,
    )


def _render_greeks(greeks) -> None:
    st.subheader("Greeks")
    st.dataframe(
        pd.DataFrame(
            {
                "Delta": [
                    _format_optional(greeks.call.delta),
                    _format_optional(greeks.put.delta),
                ],
                "Gamma": [
                    _format_optional(greeks.call.gamma),
                    _format_optional(greeks.put.gamma),
                ],
                "Vega (1%)": [
                    _format_optional(greeks.call.vega),
                    _format_optional(greeks.put.vega),
                ],
                "Theta/day": [
                    _format_optional(greeks.call.theta),
                    _format_optional(greeks.put.theta),
                ],
                "Rho (1%)": [
                    _format_optional(greeks.call.rho),
                    _format_optional(greeks.put.rho),
                ],
            },
            index=["Call", "Put"],
        ),
        use_container_width=True,
    )


def _render_heatmap_pair(
    *,
    heading: str,
    call_surface,
    put_surface,
    call_title: str,
    put_title: str,
    z_title: str,
    colorscale,
    zmid: float | None = None,
) -> None:
    st.subheader(heading)
    call_col, put_col = st.columns(2)
    call_col.plotly_chart(
        _heatmap(
            call_surface,
            title=call_title,
            z_title=z_title,
            colorscale=colorscale,
            zmid=zmid,
        ),
        use_container_width=True,
    )
    put_col.plotly_chart(
        _heatmap(
            put_surface,
            title=put_title,
            z_title=z_title,
            colorscale=colorscale,
            zmid=zmid,
        ),
        use_container_width=True,
    )


def _render_payoff_curve(curve) -> None:
    st.subheader("Expiry Payoff and PnL")
    figure = go.Figure()
    figure.add_trace(
        go.Scatter(
            x=curve.stock_prices,
            y=curve.call_pnl,
            mode="lines",
            name="Call PnL",
            line={"color": "#15803d", "width": 3},
        )
    )
    figure.add_trace(
        go.Scatter(
            x=curve.stock_prices,
            y=curve.put_pnl,
            mode="lines",
            name="Put PnL",
            line={"color": "#b91c1c", "width": 3},
        )
    )
    figure.add_trace(
        go.Scatter(
            x=curve.stock_prices,
            y=curve.call_payoff,
            mode="lines",
            name="Call payoff",
            line={"color": "#15803d", "dash": "dash"},
        )
    )
    figure.add_trace(
        go.Scatter(
            x=curve.stock_prices,
            y=curve.put_payoff,
            mode="lines",
            name="Put payoff",
            line={"color": "#b91c1c", "dash": "dash"},
        )
    )
    figure.add_hline(y=0, line_dash="dot", line_color="#6b7280")
    figure.update_layout(
        xaxis_title="Stock price at expiry",
        yaxis_title="Value",
        height=460,
        margin={"l": 20, "r": 20, "t": 20, "b": 20},
        legend={"orientation": "h", "yanchor": "bottom", "y": 1.02, "x": 0},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(figure, use_container_width=True)


def _render_grid_data(
    *,
    call_price_surface,
    put_price_surface,
    call_pnl_surface,
    put_pnl_surface,
) -> None:
    with st.expander("Grid Data"):
        grids = [
            ("Call Price Grid", "call_price_grid.csv", call_price_surface),
            ("Put Price Grid", "put_price_grid.csv", put_price_surface),
            ("Call PnL Grid", "call_pnl_grid.csv", call_pnl_surface),
            ("Put PnL Grid", "put_pnl_grid.csv", put_pnl_surface),
        ]
        for left, right in zip(grids[0::2], grids[1::2], strict=True):
            left_col, right_col = st.columns(2)
            _render_grid_download(left_col, *left)
            _render_grid_download(right_col, *right)


def _render_grid_download(container, title: str, file_name: str, surface) -> None:
    dataframe = _surface_dataframe(surface)
    container.write(title)
    container.dataframe(dataframe, use_container_width=True)
    container.download_button(
        "Download CSV",
        data=dataframe.to_csv().encode("utf-8"),
        file_name=file_name,
        mime="text/csv",
        use_container_width=True,
        key=f"download_{file_name}",
    )


def _render_model_notes() -> None:
    with st.expander("Model Notes"):
        st.markdown(
            """
            - Black-Scholes is a closed-form model for European options. The app keeps
              an American-style Black-Scholes baseline by flooring prices at intrinsic
              value, but true early exercise is handled by the binomial tree.
            - The binomial tree uses the Cox-Ross-Rubinstein framework and checks
              early exercise at every node for American options.
            - Dividend yield is treated as a continuous yield in both pricing engines.
            - Greeks are analytic for Black-Scholes and finite-difference estimates for
              the binomial tree.
            - Market data from yfinance is delayed and suitable for demos, not live
              trading or execution.
            """
        )


def _heatmap(surface, *, title: str, z_title: str, colorscale, zmid: float | None = None):
    x_labels = [f"{value:.2f}" for value in surface.stock_prices]
    y_labels = [f"{value:.1%}" for value in surface.volatilities]
    figure = go.Figure(
        data=go.Heatmap(
            x=x_labels,
            y=y_labels,
            z=surface.values,
            colorscale=colorscale,
            zmid=zmid,
            colorbar={"title": z_title},
            xgap=1,
            ygap=1,
            hovertemplate=(
                "Stock price: %{x}<br>"
                "Volatility: %{y}<br>"
                f"{z_title}: " + "%{z:.4f}<extra></extra>"
            ),
        )
    )
    _add_value_labels(figure, surface.values, x_labels, y_labels, zmid=zmid)
    figure.update_layout(
        title=title,
        xaxis_title="Stock price",
        yaxis_title="Volatility",
        margin={"l": 20, "r": 20, "t": 50, "b": 20},
        height=520,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    return figure


def _add_value_labels(
    figure,
    values: list[list[float]],
    x_labels: list[str],
    y_labels: list[str],
    *,
    zmid: float | None,
) -> None:
    flattened_values = [value for row in values for value in row]
    minimum_value = min(flattened_values)
    maximum_value = max(flattened_values)
    span = maximum_value - minimum_value or 1.0
    max_distance = max(
        abs(minimum_value - (zmid or 0.0)),
        abs(maximum_value - (zmid or 0.0)),
        1.0,
    )

    label_x = []
    label_y = []
    label_text = []
    label_colors = []
    font_size = 12 if len(x_labels) <= 10 else 10

    for row_index, row in enumerate(values):
        for column_index, value in enumerate(row):
            if zmid is None:
                normalized_value = (value - minimum_value) / span
                font_color = (
                    "#111827" if 0.28 <= normalized_value <= 0.72 else "#ffffff"
                )
            else:
                normalized_distance = abs(value - zmid) / max_distance
                font_color = "#111827" if normalized_distance < 0.28 else "#ffffff"

            label_x.append(x_labels[column_index])
            label_y.append(y_labels[row_index])
            label_text.append(f"{value:.2f}")
            label_colors.append(font_color)

    figure.add_trace(
        go.Scatter(
            x=label_x,
            y=label_y,
            mode="text",
            text=label_text,
            textfont={"size": font_size, "color": label_colors},
            hoverinfo="skip",
            showlegend=False,
        )
    )


def _surface_dataframe(surface) -> pd.DataFrame:
    return pd.DataFrame(
        surface.values,
        index=[f"{value:.1%}" for value in surface.volatilities],
        columns=[f"{value:.2f}" for value in surface.stock_prices],
    )


def _format_optional(value: float | None) -> str:
    if value is None:
        return "n/a"
    return f"{value:,.4f}"


def _format_percent_optional(value: float | None) -> str:
    if value is None:
        return "n/a"
    return f"{value:.2%}"


def _format_market_value(value: float | None) -> str:
    if value is None:
        return "n/a"
    return f"{value:,.2f}"


def _apply_styles() -> None:
    st.markdown(
        """
        <style>
        .block-container {
            padding-top: 2rem;
            padding-bottom: 2rem;
        }
        div[data-testid="stMetric"] {
            border: 1px solid #334155;
            border-radius: 8px;
            padding: 1rem;
            background: #111827;
            box-shadow: none;
        }
        div[data-testid="stMetric"] * {
            color: #f8fafc !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
