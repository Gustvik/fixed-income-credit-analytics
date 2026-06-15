"""Zero-curve bootstrapping from fixed-rate coupon bonds.

The model works entirely with **continuously-compounded** zero rates internally;
``DF(t) = exp(-z * t)``. Display rates can be converted to any compounding
frequency via :func:`convert_rate`.

The bootstrap sorts instruments by maturity and solves each bond's terminal zero
rate with a bisection root-finder so the curve re-prices that bond exactly. Zero
rates between solved pillars are interpolated linearly in the zero rate, which is
robust to instruments spaced more widely than one coupon period.
"""

from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class Bond:
    """A fixed-rate coupon bond quoted per 100 face.

    Attributes:
        maturity: Time to maturity in years (assumed a multiple of 1/frequency).
        coupon: Annual coupon rate in percent (e.g. 4.25 for 4.25%).
        price: Market dirty price per 100 face.
    """

    maturity: float
    coupon: float
    price: float


@dataclass(frozen=True)
class Pillar:
    """A solved point on the zero curve: continuously-compounded rate ``z`` at ``t``."""

    t: float
    z: float


def interp_zero(pillars: list[Pillar], t: float) -> float:
    """Linear-in-zero-rate interpolation with flat extrapolation at both ends."""
    if not pillars:
        return 0.0
    if t <= pillars[0].t:
        return pillars[0].z
    if t >= pillars[-1].t:
        return pillars[-1].z
    for i in range(1, len(pillars)):
        if t <= pillars[i].t:
            a, b = pillars[i - 1], pillars[i]
            w = (t - a.t) / (b.t - a.t)
            return a.z + w * (b.z - a.z)
    return pillars[-1].z


def discount_factor(z: float, t: float) -> float:
    """Continuously-compounded discount factor."""
    return math.exp(-z * t)


def price_bond(pillars: list[Pillar], coupon: float, maturity: float, freq: int) -> float:
    """Price a coupon bond (face 100) off a pillar set at ``freq`` payments/year."""
    n = round(maturity * freq)
    period_coupon = coupon / freq  # currency per period, per 100 face
    price = 0.0
    for i in range(1, n + 1):
        t = i / freq
        cash_flow = period_coupon + (100.0 if i == n else 0.0)
        price += cash_flow * discount_factor(interp_zero(pillars, t), t)
    return price


def bootstrap(bonds: list[Bond], freq: int, *, max_iter: int = 200, tol: float = 1e-11) -> list[Pillar]:
    """Bootstrap a zero curve so each bond re-prices to its market price.

    Bonds are sorted by maturity; duplicate maturities raise ``ValueError``.
    """
    ordered = sorted(bonds, key=lambda b: b.maturity)
    for i in range(1, len(ordered)):
        if abs(ordered[i].maturity - ordered[i - 1].maturity) < 1e-9:
            raise ValueError(f"Duplicate maturity: {ordered[i].maturity}y.")

    pillars: list[Pillar] = []
    for b in ordered:
        lo, hi = -0.20, 1.50  # zero-rate bracket
        g = lambda z, b=b: price_bond(pillars + [Pillar(b.maturity, z)], b.coupon, b.maturity, freq) - b.price
        g_lo, g_hi = g(lo), g(hi)
        if g_lo * g_hi > 0:
            raise ValueError(f"No solution for {b.maturity}y bond - check the price.")
        z_mid = 0.5 * (lo + hi)
        for _ in range(max_iter):
            z_mid = 0.5 * (lo + hi)
            g_mid = g(z_mid)
            if abs(g_mid) < tol:
                break
            if g_lo * g_mid <= 0:
                hi = z_mid
            else:
                lo, g_lo = z_mid, g_mid
        pillars.append(Pillar(b.maturity, z_mid))
    return pillars


def par_yield(pillars: list[Pillar], maturity: float, freq: int) -> float:
    """Par coupon rate (annualized fraction) on the frequency grid at ``maturity``."""
    n = round(maturity * freq)
    annuity, df_t = 0.0, 1.0
    for i in range(1, n + 1):
        t = i / freq
        df = discount_factor(interp_zero(pillars, t), t)
        annuity += df
        if i == n:
            df_t = df
    return freq * (1.0 - df_t) / annuity


def forward_rate(pillars: list[Pillar], t1: float, t2: float) -> float:
    """Continuously-compounded forward rate over ``[t1, t2]``."""
    z1, z2 = interp_zero(pillars, t1), interp_zero(pillars, t2)
    return (z2 * t2 - z1 * t1) / (t2 - t1)


def convert_rate(z_continuous: float, m: int) -> float:
    """Convert a continuous rate to ``m`` compoundings/year (``m=0`` => continuous)."""
    if m == 0:
        return z_continuous
    return m * (math.exp(z_continuous / m) - 1.0)
