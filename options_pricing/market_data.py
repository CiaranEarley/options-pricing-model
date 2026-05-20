"""Market data helpers for listed option chains."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from math import isnan
from typing import Any

import pandas as pd


class MarketDataError(RuntimeError):
    """Raised when market data cannot be fetched or parsed."""


@dataclass(frozen=True)
class MarketTickerSnapshot:
    """Basic market data for one ticker."""

    ticker: str
    spot_price: float
    expirations: list[str]
    provider: str = "Yahoo Finance via yfinance"


@dataclass(frozen=True)
class MarketOptionContract:
    """Call and put market data at a single strike."""

    strike: float
    call_bid: float | None
    call_ask: float | None
    call_last_price: float | None
    call_implied_volatility: float | None
    call_volume: int | None
    call_open_interest: int | None
    put_bid: float | None
    put_ask: float | None
    put_last_price: float | None
    put_implied_volatility: float | None
    put_volume: int | None
    put_open_interest: int | None

    @property
    def call_mid(self) -> float | None:
        return _mid_price(self.call_bid, self.call_ask)

    @property
    def put_mid(self) -> float | None:
        return _mid_price(self.put_bid, self.put_ask)

    @property
    def call_market_price(self) -> float | None:
        return _preferred_market_price(self.call_bid, self.call_ask, self.call_last_price)

    @property
    def put_market_price(self) -> float | None:
        return _preferred_market_price(self.put_bid, self.put_ask, self.put_last_price)


@dataclass(frozen=True)
class MarketOptionChain:
    """Option chain market data for one ticker and expiry."""

    ticker: str
    spot_price: float
    expiration: str
    time_to_expiry: float
    contracts: list[MarketOptionContract]
    provider: str = "Yahoo Finance via yfinance"


def fetch_ticker_snapshot(ticker: str) -> MarketTickerSnapshot:
    """Fetch ticker spot price and option expirations using yfinance."""

    yf = _import_yfinance()
    normalized_ticker = _normalize_ticker(ticker)
    ticker_object = yf.Ticker(normalized_ticker)
    expirations = _future_expirations(list(ticker_object.options or []))
    if not expirations:
        raise MarketDataError(f"No option expirations found for {normalized_ticker}.")

    return MarketTickerSnapshot(
        ticker=normalized_ticker,
        spot_price=_fetch_spot_price(ticker_object),
        expirations=expirations,
    )


def fetch_option_chain(ticker: str, expiration: str) -> MarketOptionChain:
    """Fetch an option chain for one ticker and expiration using yfinance."""

    yf = _import_yfinance()
    normalized_ticker = _normalize_ticker(ticker)
    ticker_object = yf.Ticker(normalized_ticker)
    chain = ticker_object.option_chain(expiration)
    return build_option_chain(
        ticker=normalized_ticker,
        spot_price=_fetch_spot_price(ticker_object),
        expiration=expiration,
        calls=chain.calls,
        puts=chain.puts,
    )


def build_option_chain(
    *,
    ticker: str,
    spot_price: float,
    expiration: str,
    calls: pd.DataFrame,
    puts: pd.DataFrame,
    valuation_date: date | None = None,
) -> MarketOptionChain:
    """Build a normalized option chain from call and put data frames."""

    if calls.empty and puts.empty:
        raise MarketDataError("Option chain has no contracts.")

    call_rows = _rows_by_strike(calls)
    put_rows = _rows_by_strike(puts)
    strikes = sorted(set(call_rows) | set(put_rows))
    contracts = [
        MarketOptionContract(
            strike=strike,
            call_bid=_row_value(call_rows.get(strike), "bid"),
            call_ask=_row_value(call_rows.get(strike), "ask"),
            call_last_price=_row_value(call_rows.get(strike), "lastPrice"),
            call_implied_volatility=_row_value(call_rows.get(strike), "impliedVolatility"),
            call_volume=_row_int(call_rows.get(strike), "volume"),
            call_open_interest=_row_int(call_rows.get(strike), "openInterest"),
            put_bid=_row_value(put_rows.get(strike), "bid"),
            put_ask=_row_value(put_rows.get(strike), "ask"),
            put_last_price=_row_value(put_rows.get(strike), "lastPrice"),
            put_implied_volatility=_row_value(put_rows.get(strike), "impliedVolatility"),
            put_volume=_row_int(put_rows.get(strike), "volume"),
            put_open_interest=_row_int(put_rows.get(strike), "openInterest"),
        )
        for strike in strikes
    ]

    return MarketOptionChain(
        ticker=_normalize_ticker(ticker),
        spot_price=spot_price,
        expiration=expiration,
        time_to_expiry=calculate_time_to_expiry(
            expiration,
            valuation_date=valuation_date,
        ),
        contracts=contracts,
    )


def select_nearest_contract(
    chain: MarketOptionChain,
    target_strike: float | None = None,
) -> MarketOptionContract:
    """Select the contract with strike nearest to the target or spot price."""

    if not chain.contracts:
        raise MarketDataError("Option chain has no contracts.")
    target = chain.spot_price if target_strike is None else target_strike
    return min(chain.contracts, key=lambda contract: abs(contract.strike - target))


def select_contract_by_strike(
    chain: MarketOptionChain,
    strike: float,
) -> MarketOptionContract:
    """Select a contract by exact strike, falling back to the nearest strike."""

    return min(chain.contracts, key=lambda contract: abs(contract.strike - strike))


def calculate_time_to_expiry(
    expiration: str,
    *,
    valuation_date: date | None = None,
) -> float:
    """Calculate calendar-year time to expiry from an expiration date string."""

    valuation_date = valuation_date or date.today()
    expiration_date = datetime.strptime(expiration, "%Y-%m-%d").date()
    days_to_expiry = max((expiration_date - valuation_date).days, 0)
    return days_to_expiry / 365.0


def _future_expirations(expirations: list[str]) -> list[str]:
    today = date.today()
    future_expirations = []
    for expiration in expirations:
        try:
            expiration_date = datetime.strptime(expiration, "%Y-%m-%d").date()
        except ValueError:
            continue
        if expiration_date >= today:
            future_expirations.append(expiration)
    return future_expirations


def _import_yfinance():
    try:
        import yfinance as yf
    except ImportError as error:
        raise MarketDataError(
            "yfinance is not installed. Run `python -m pip install -e .` first."
        ) from error
    return yf


def _fetch_spot_price(ticker_object: Any) -> float:
    fast_info = getattr(ticker_object, "fast_info", None)
    for key in ("last_price", "lastPrice", "regular_market_price"):
        value = _fast_info_value(fast_info, key)
        if value is not None:
            return value

    history = ticker_object.history(period="5d")
    if history.empty or "Close" not in history:
        raise MarketDataError("Could not fetch a recent spot price.")
    return float(history["Close"].dropna().iloc[-1])


def _fast_info_value(fast_info: Any, key: str) -> float | None:
    if fast_info is None:
        return None
    try:
        value = fast_info[key]
    except (KeyError, TypeError):
        value = getattr(fast_info, key, None)
    return _clean_number(value)


def _rows_by_strike(data: pd.DataFrame) -> dict[float, pd.Series]:
    if data.empty or "strike" not in data:
        return {}
    return {
        float(row["strike"]): row
        for _, row in data.dropna(subset=["strike"]).iterrows()
    }


def _row_value(row: pd.Series | None, key: str) -> float | None:
    if row is None or key not in row:
        return None
    return _clean_number(row[key])


def _row_int(row: pd.Series | None, key: str) -> int | None:
    value = _row_value(row, key)
    if value is None:
        return None
    return int(value)


def _clean_number(value: Any) -> float | None:
    if value is None:
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if isnan(number):
        return None
    return number


def _mid_price(bid: float | None, ask: float | None) -> float | None:
    if bid is None or ask is None or bid <= 0 or ask <= 0:
        return None
    return (bid + ask) / 2.0


def _preferred_market_price(
    bid: float | None,
    ask: float | None,
    last_price: float | None,
) -> float | None:
    mid = _mid_price(bid, ask)
    if mid is not None:
        return mid
    if last_price is not None and last_price > 0:
        return last_price
    return None


def _normalize_ticker(ticker: str) -> str:
    normalized_ticker = ticker.strip().upper()
    if not normalized_ticker:
        raise MarketDataError("Ticker cannot be blank.")
    return normalized_ticker
