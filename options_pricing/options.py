"""Shared option metadata types."""

from __future__ import annotations

from enum import Enum


class OptionStyle(str, Enum):
    """Supported exercise styles."""

    EUROPEAN = "european"
    AMERICAN = "american"


class OptionType(str, Enum):
    """Supported option contract types."""

    CALL = "call"
    PUT = "put"


class PricingEngine(str, Enum):
    """Pricing engines available in the app."""

    BLACK_SCHOLES = "black_scholes"
    BINOMIAL = "binomial"
