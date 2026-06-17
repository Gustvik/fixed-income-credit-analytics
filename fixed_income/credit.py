"""Credit analytics for investment-grade bonds — the investor's view.

This module treats credit as an *asset class*: yield is decomposed into a
risk-free component (from the bootstrapped zero curve in :mod:`fixed_income.curve`)
and a credit-spread component (the compensation for credit risk). On top of that
it provides the building blocks an IG credit portfolio manager actually uses:

* yield to maturity, Z-spread and G-spread
* Macaulay / modified duration, convexity, spread duration, DV01
* DTS (duration times spread) — the standard measure of credit risk contribution
* exact scenario re-pricing under parallel rate shifts and spread widening
* portfolio aggregation, active risk vs. a benchmark, and risk budgeting

All discounting reuses the continuously-compounded zero curve (``Pillar`` list).
Spreads are handled in continuous-compounding terms and reported in basis points.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

from .curve import Pillar, interp_zero, convert_rate


@dataclass(frozen=True)
class CreditBond:
    """An investment-grade coupon bond, quoted clean per 100 face.

    Attributes:
        name: Short identifier, e.g. ``"DNB 4.30 2029"``.
        issuer: Issuing entity.
        sector: Sector bucket (Banking, Energy, Industrials, ...).
        country: Issuer domicile (NO / SE / FI / ...).
        rating: Composite rating label (e.g. ``"A"``, ``"BBB+"``).
        maturity: Years to maturity (assumed a multiple of 1/frequency).
        coupon: Annual coupon rate in percent.
        price: Clean market price per 100 face.
        freq: Coupon payments per year.
        nominal: Held nominal in millions (drives market-value weights).
    """

    name: str
    issuer: str
    sector: str
    country: str
    rating: str
    maturity: float
    coupon: float
    price: float
    freq: int = 2
    nominal: float = 0.0


def cashflows(coupon: float, maturity: float, freq: int, face: float = 100.0):
    """Return ``(times, amounts)`` for a fixed-rate bond on the coupon grid."""
    n = round(maturity * freq)
    period_coupon = face * (coupon / 100.0) / freq
    times = [i / freq for i in range(1, n + 1)]
    amounts = [period_coupon for _ in range(n)]
    amounts[-1] += face
    return times, amounts


# --------------------------------------------------------------------------- #
# Single-bond analytics
# --------------------------------------------------------------------------- #
def ytm(coupon: float, maturity: float, price: float, freq: int, face: float = 100.0) -> float:
    """Yield to maturity (annualised, compounded ``freq`` times/yr)."""
    times, amounts = cashflows(coupon, maturity, freq, face)

    def pv(y: float) -> float:
        return sum(cf / (1 + y / freq) ** (i + 1) for i, cf in enumerate(amounts)) - price

    lo, hi = -0.50, 1.50
    f_lo = pv(lo)
    mid = 0.5 * (lo + hi)
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        f_mid = pv(mid)
        if abs(f_mid) < 1e-10:
            break
        if f_lo * f_mid <= 0:
            hi = mid
        else:
            lo, f_lo = mid, f_mid
    return mid


def durations(coupon: float, maturity: float, price: float, freq: int, face: float = 100.0) -> dict:
    """Macaulay & modified duration and convexity, computed at the bond's YTM."""
    y = ytm(coupon, maturity, price, freq, face)
    times, amounts = cashflows(coupon, maturity, freq, face)
    disc = [cf / (1 + y / freq) ** (i + 1) for i, cf in enumerate(amounts)]
    p = sum(disc)
    macaulay = sum(t * d for t, d in zip(times, disc)) / p
    modified = macaulay / (1 + y / freq)
    convexity = sum(
        cf * (i + 1) * (i + 2) / (1 + y / freq) ** (i + 3) for i, cf in enumerate(amounts)
    ) / (p * freq ** 2)
    return {
        "ytm": y,
        "macaulay": macaulay,
        "modified": modified,
        "convexity": convexity,
        "dv01": modified * p * 1e-4,  # value change per 1bp, per 100 face
    }


def z_spread(pillars: list[Pillar], coupon: float, maturity: float, price: float, freq: int,
             face: float = 100.0) -> float:
    """Continuously-compounded Z-spread (decimal) over the zero curve.

    The constant spread ``s`` such that discounting the cashflows at
    ``z(t) + s`` reproduces the market price.
    """
    times, amounts = cashflows(coupon, maturity, freq, face)

    def pv(s: float) -> float:
        return sum(cf * math.exp(-(interp_zero(pillars, t) + s) * t)
                   for t, cf in zip(times, amounts)) - price

    lo, hi = -0.10, 0.50
    f_lo = pv(lo)
    mid = 0.5 * (lo + hi)
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        f_mid = pv(mid)
        if abs(f_mid) < 1e-10:
            break
        if f_lo * f_mid <= 0:
            hi = mid
        else:
            lo, f_lo = mid, f_mid
    return mid


def spread_duration(pillars: list[Pillar], coupon: float, maturity: float, freq: int,
                    z: float, face: float = 100.0) -> float:
    """Sensitivity of price to a parallel spread move: ``-(1/P) dP/ds`` (years)."""
    times, amounts = cashflows(coupon, maturity, freq, face)
    p = sum(cf * math.exp(-(interp_zero(pillars, t) + z) * t) for t, cf in zip(times, amounts))
    dpds = sum(t * cf * math.exp(-(interp_zero(pillars, t) + z) * t)
               for t, cf in zip(times, amounts))
    return dpds / p


def g_spread(bond_ytm: float, pillars: list[Pillar], maturity: float, freq: int) -> float:
    """G-spread (decimal): bond YTM minus the risk-free spot at the same maturity."""
    rf = convert_rate(interp_zero(pillars, maturity), freq)
    return bond_ytm - rf


def reprice(pillars: list[Pillar], coupon: float, maturity: float, freq: int, z: float,
            d_rate: float = 0.0, d_spread: float = 0.0, face: float = 100.0) -> float:
    """Re-price a bond under a parallel rate shift ``d_rate`` and spread move ``d_spread``.

    With ``d_rate = d_spread = 0`` this returns the bond's market price (since ``z``
    was solved to match it), giving exact internal consistency for scenarios.
    """
    times, amounts = cashflows(coupon, maturity, freq, face)
    return sum(cf * math.exp(-(interp_zero(pillars, t) + d_rate + z + d_spread) * t)
               for t, cf in zip(times, amounts))


# --------------------------------------------------------------------------- #
# Full per-bond analytics record
# --------------------------------------------------------------------------- #
def analyse_bond(bond: CreditBond, pillars: list[Pillar]) -> dict:
    """Compute the full analytics record for one bond."""
    d = durations(bond.coupon, bond.maturity, bond.price, bond.freq)
    z = z_spread(pillars, bond.coupon, bond.maturity, bond.price, bond.freq)
    sd = spread_duration(pillars, bond.coupon, bond.maturity, bond.freq, z)
    rf_yield = convert_rate(interp_zero(pillars, bond.maturity), bond.freq)
    market_value = bond.nominal * bond.price / 100.0
    return {
        "name": bond.name,
        "issuer": bond.issuer,
        "sector": bond.sector,
        "country": bond.country,
        "rating": bond.rating,
        "maturity": bond.maturity,
        "coupon": bond.coupon,
        "price": bond.price,
        "nominal": bond.nominal,
        "market_value": market_value,
        "ytm": d["ytm"],
        "rf_yield": rf_yield,                 # risk-free component
        "credit_spread_bp": z * 1e4,          # credit premium (Z-spread)
        "g_spread_bp": g_spread(d["ytm"], pillars, bond.maturity, bond.freq) * 1e4,
        "mod_duration": d["modified"],
        "mac_duration": d["macaulay"],
        "convexity": d["convexity"],
        "spread_duration": sd,
        "dv01": d["dv01"],
        "dts": sd * (z * 1e4) / 100.0,        # DTS = spread duration × spread(%) → %·yr
        "_z": z,                              # internal: continuous z-spread
    }


# --------------------------------------------------------------------------- #
# Portfolio analytics
# --------------------------------------------------------------------------- #
def portfolio_summary(records: list[dict], weights: list[float]) -> dict:
    """Market-value-weighted portfolio metrics from per-bond records."""
    w = weights
    def wsum(key):
        return sum(wi * r[key] for wi, r in zip(w, records))
    return {
        "ytm": wsum("ytm"),
        "rf_yield": wsum("rf_yield"),
        "credit_spread_bp": wsum("credit_spread_bp"),
        "mod_duration": wsum("mod_duration"),
        "spread_duration": wsum("spread_duration"),
        "convexity": wsum("convexity"),
        "dts": wsum("dts"),
    }


def mv_weights(records: list[dict]) -> list[float]:
    """Market-value weights from per-bond records."""
    total = sum(r["market_value"] for r in records)
    if total <= 0:
        n = len(records)
        return [1.0 / n] * n
    return [r["market_value"] / total for r in records]


def risk_budget(records: list[dict], weights: list[float]) -> list[dict]:
    """Contribution of each position to portfolio DTS (the credit risk budget)."""
    contrib = [wi * r["dts"] for wi, r in zip(weights, records)]
    total = sum(contrib) or 1.0
    return [
        {
            "name": r["name"],
            "sector": r["sector"],
            "weight": wi,
            "dts": r["dts"],
            "dts_contribution": c,
            "pct_of_risk": c / total,
        }
        for r, wi, c in zip(records, weights, contrib)
    ]


def active_risk(records: list[dict], port_w: list[float], bench_w: list[float]) -> dict:
    """Active exposures of the portfolio relative to a benchmark."""
    port = portfolio_summary(records, port_w)
    bench = portfolio_summary(records, bench_w)
    active_w = [pw - bw for pw, bw in zip(port_w, bench_w)]
    return {
        "active_duration": port["mod_duration"] - bench["mod_duration"],
        "active_spread_duration": port["spread_duration"] - bench["spread_duration"],
        "active_dts": port["dts"] - bench["dts"],
        "active_yield_bp": (port["ytm"] - bench["ytm"]) * 1e4,
        "active_weights": active_w,
        "portfolio": port,
        "benchmark": bench,
    }


# --------------------------------------------------------------------------- #
# Scenario analysis
# --------------------------------------------------------------------------- #
def scenario_pnl(bond: CreditBond, pillars: list[Pillar], z: float,
                 d_rate_bp: float, d_spread_bp: float) -> float:
    """Exact P&L (per 100 face) for one bond under a rate+spread scenario."""
    base = reprice(pillars, bond.coupon, bond.maturity, bond.freq, z, 0.0, 0.0)
    shocked = reprice(pillars, bond.coupon, bond.maturity, bond.freq, z,
                      d_rate_bp * 1e-4, d_spread_bp * 1e-4)
    return shocked - base


def portfolio_scenario(bonds: list[CreditBond], records: list[dict], pillars: list[Pillar],
                       d_rate_bp: float, d_spread_bp: float) -> dict:
    """Portfolio value change under a parallel rate shift and spread widening.

    Returns both the exact re-price result and the duration/convexity approximation
    so the two can be compared (the approximation breaks down for large shocks).
    """
    base_mv = sum(r["market_value"] for r in records)
    exact_mv = 0.0
    approx_pct = 0.0
    for bond, r in zip(bonds, records):
        scale = r["nominal"] / 100.0  # market value per unit price
        base_price = r["price"]
        new_price = reprice(pillars, bond.coupon, bond.maturity, bond.freq, r["_z"],
                            d_rate_bp * 1e-4, d_spread_bp * 1e-4)
        exact_mv += new_price * scale
        # duration/convexity approximation on this bond's return
        dr, ds = d_rate_bp * 1e-4, d_spread_bp * 1e-4
        ret = (-r["mod_duration"] * dr
               + 0.5 * r["convexity"] * dr ** 2
               - r["spread_duration"] * ds)
        w = r["market_value"] / base_mv if base_mv else 0.0
        approx_pct += w * ret
    return {
        "base_mv": base_mv,
        "exact_mv": exact_mv,
        "exact_pnl": exact_mv - base_mv,
        "exact_pct": (exact_mv - base_mv) / base_mv if base_mv else 0.0,
        "approx_pct": approx_pct,
    }


# --------------------------------------------------------------------------- #
# Early-warning monitoring
# --------------------------------------------------------------------------- #
def synthetic_spread_history(records: list[dict], days: int = 90, seed: int = 42) -> dict[str, list[float]]:
    """Build a reproducible mean-reverting spread history ending at today's spread.

    Illustrative only — for the demo and tests. Replace with a real time series
    (e.g. daily Z-spreads from a pricing source) when available.
    """
    import random

    rng = random.Random(seed)
    history: dict[str, list[float]] = {}
    for idx, r in enumerate(records):
        cur = r["credit_spread_bp"]
        level = cur * 0.92          # start a bit tighter, drift toward current
        path = []
        vol = max(2.0, cur * 0.05)  # daily vol scales with spread level
        for _ in range(days):
            level += 0.06 * (cur - level) + rng.gauss(0, vol)
            path.append(max(1.0, level))
        # nudge a couple of names into a widening regime so alerts are visible
        if idx % 5 == 0:
            path = [p * 0.8 for p in path]
        history[r["name"]] = path
    return history


@dataclass
class SpreadAlert:
    name: str
    sector: str
    current_bp: float
    avg_bp: float
    change_bp: float
    zscore: float
    status: str  # OK / WATCH / ALERT


def early_warning(records: list[dict], history: dict[str, list[float]],
                  watch_z: float = 1.5, alert_z: float = 2.5) -> list[SpreadAlert]:
    """Flag bonds whose current spread has widened abnormally vs. its own history.

    ``history`` maps bond name -> list of recent daily Z-spreads (bp). The current
    spread is compared to the trailing mean using a z-score; widening beyond the
    thresholds raises WATCH / ALERT. (Widening = spread up = credit deterioration.)
    """
    alerts: list[SpreadAlert] = []
    for r in records:
        hist = history.get(r["name"], [])
        cur = r["credit_spread_bp"]
        if len(hist) < 5:
            alerts.append(SpreadAlert(r["name"], r["sector"], cur, cur, 0.0, 0.0, "OK"))
            continue
        mean = sum(hist) / len(hist)
        var = sum((x - mean) ** 2 for x in hist) / (len(hist) - 1)
        std = math.sqrt(var) if var > 0 else 0.0
        z = (cur - mean) / std if std > 0 else 0.0
        if z >= alert_z:
            status = "ALERT"
        elif z >= watch_z:
            status = "WATCH"
        else:
            status = "OK"
        alerts.append(SpreadAlert(r["name"], r["sector"], cur, mean, cur - mean, z, status))
    return alerts
