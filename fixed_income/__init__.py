"""Fixed income analytics: zero-curve bootstrapping from coupon bonds."""

from .curve import (
    Bond,
    Pillar,
    bootstrap,
    convert_rate,
    discount_factor,
    forward_rate,
    interp_zero,
    par_yield,
    price_bond,
)

__all__ = [
    "Bond",
    "Pillar",
    "bootstrap",
    "convert_rate",
    "discount_factor",
    "forward_rate",
    "interp_zero",
    "par_yield",
    "price_bond",
]

__version__ = "0.1.0"
