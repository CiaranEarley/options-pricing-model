"""REPL-style command-line interface for the pricing app."""

from __future__ import annotations

import argparse

from options_pricing.black_scholes import price_black_scholes
from options_pricing.options import OptionStyle


INPUTS = (
    ("stock_price", "Stock price (S)", False),
    ("strike_price", "Strike price (K)", False),
    ("time_to_expiry", "Time to expiry in years (T)", False),
    ("interest_rate", "Risk-free interest rate (r)", True),
    ("dividend_yield", "Dividend yield (q)", True),
    ("volatility", "Volatility (sigma)", True),
)


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    provided_values = [
        args.stock_price,
        args.strike_price,
        args.time_to_expiry,
        args.interest_rate,
        args.volatility,
    ]
    if any(value is not None for value in provided_values):
        if not all(value is not None for value in provided_values):
            parser.error("provide all five pricing inputs, or provide none for REPL mode")
        quote = price_black_scholes(
            stock_price=args.stock_price,
            strike_price=args.strike_price,
            time_to_expiry=args.time_to_expiry,
            interest_rate=args.interest_rate,
            dividend_yield=args.dividend_yield,
            volatility=args.volatility,
            style=args.style,
        )
        print_quote(quote)
        return 0

    run_repl(default_style=args.style)
    return 0


def run_repl(*, default_style: str) -> None:
    print("Options Pricing Model")
    print("Enter the Black-Scholes inputs. Type q at any prompt to quit.")
    print("Rates, dividend yield, and volatility accept decimals like 0.05 or 5%.")

    while True:
        print()
        values: dict[str, float] = {}
        for key, label, allow_percent in INPUTS:
            entered_value = _prompt_float(label, allow_percent=allow_percent)
            if entered_value is None:
                print("Goodbye.")
                return
            values[key] = entered_value

        quote = price_black_scholes(**values, style=default_style)
        print_quote(quote)

        again = input("\nPrice another option? [Y/n]: ").strip().lower()
        if again in {"n", "no", "q", "quit", "exit"}:
            print("Goodbye.")
            return


def print_quote(quote) -> None:
    print()
    print(f"Style: {quote.style.value.title()}")
    print(f"Call price: {quote.call:,.4f}")
    print(f"Put price:  {quote.put:,.4f}")
    if quote.note:
        print(f"Note: {quote.note}")


def _prompt_float(label: str, *, allow_percent: bool) -> float | None:
    while True:
        raw_value = input(f"{label}: ").strip()
        if raw_value.lower() in {"q", "quit", "exit"}:
            return None
        try:
            return parse_number(raw_value, allow_percent=allow_percent)
        except ValueError as error:
            print(error)


def parse_number(raw_value: str, *, allow_percent: bool) -> float:
    if not raw_value:
        raise ValueError("Please enter a value.")

    if raw_value.endswith("%"):
        if not allow_percent:
            raise ValueError("Percent input is only supported for rates and volatility.")
        return float(raw_value[:-1]) / 100.0

    return float(raw_value)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Price call and put options from Black-Scholes inputs."
    )
    parser.add_argument("--stock-price", type=float, help="current stock price, S")
    parser.add_argument("--strike-price", type=float, help="strike price, K")
    parser.add_argument(
        "--time-to-expiry",
        type=float,
        help="time to expiry in years, T",
    )
    parser.add_argument(
        "--interest-rate",
        type=lambda value: parse_number(value, allow_percent=True),
        help="risk-free interest rate, e.g. 0.05 or 5%",
    )
    parser.add_argument(
        "--dividend-yield",
        type=lambda value: parse_number(value, allow_percent=True),
        default=0.0,
        help="continuous dividend yield, e.g. 0.02 or 2%",
    )
    parser.add_argument(
        "--volatility",
        type=lambda value: parse_number(value, allow_percent=True),
        help="volatility, e.g. 0.20 or 20%",
    )
    parser.add_argument(
        "--style",
        choices=[style.value for style in OptionStyle],
        default=OptionStyle.AMERICAN.value,
        help="exercise style to report",
    )
    return parser


if __name__ == "__main__":
    raise SystemExit(main())
