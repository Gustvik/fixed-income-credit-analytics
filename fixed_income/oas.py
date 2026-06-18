"""Option-adjusted spread (OAS) for callable bonds via a binomial rate tree.

Implements the CFA-style approach: build a one-period binomial short-rate tree,
**calibrated to the risk-free curve** (so it re-prices the zero-coupon discount
factors), with a lognormal rate dispersion set by a volatility assumption. The
callable bond is valued by backward induction with an issuer call rule, and the
**OAS** is the constant spread added to every node's rate that makes the model
price equal the market price.

The *option cost* is the static spread (same tree, calls disabled) minus the OAS:
the yield the holder gives up for writing the call. The tree uses annual steps and
annual coupons — a transparent, exam-aligned engine, not a production lattice.
"""

from __future__ import annotations

import math

from .curve import Pillar, interp_zero, discount_factor


def calibrate_tree(pillars: list[Pillar], n_years: int, sigma: float) -> list[list[float]]:
    """Calibrate annual one-period rates to the curve via forward induction.

    Returns ``rates[i][j]`` — the rate from year ``i`` to ``i+1`` at node ``j``
    (``j`` up-moves), such that discounting through the tree reproduces every
    risk-free discount factor ``DF(1..n_years)``.
    """
    dfs = [discount_factor(interp_zero(pillars, t), t) for t in range(1, n_years + 1)]
    q = [[0.0] * (i + 1) for i in range(n_years + 1)]
    q[0][0] = 1.0
    rates: list[list[float]] = []
    for i in range(n_years):
        target = dfs[i]  # price today of 1 paid at year i+1

        def f(r0: float, i=i) -> float:
            return sum(q[i][j] / (1 + r0 * math.exp(2 * j * sigma)) for j in range(i + 1)) - target

        lo, hi = 0.0, 1.0  # f is decreasing in r0; f(0) = DF(i) - DF(i+1) > 0
        for _ in range(200):
            mid = 0.5 * (lo + hi)
            if f(mid) > 0:
                lo = mid
            else:
                hi = mid
        r0 = 0.5 * (lo + hi)
        row = [r0 * math.exp(2 * j * sigma) for j in range(i + 1)]
        rates.append(row)
        for j in range(i + 1):
            disc = q[i][j] / (1 + row[j])
            q[i + 1][j] += 0.5 * disc
            q[i + 1][j + 1] += 0.5 * disc
    return rates


def value_bond(rates: list[list[float]], coupon_pct: float, n_years: int, oas: float,
               call_price: float | None = None, first_call: int | None = None,
               face: float = 100.0) -> float:
    """Value a (callable) annual-coupon bond on the tree at a given OAS."""
    coupon = face * coupon_pct / 100.0
    v = [face + coupon] * (n_years + 1)  # values at maturity (all nodes)
    for i in range(n_years - 1, 0, -1):
        new_v = []
        for j in range(i + 1):
            cont = 0.5 * (v[j] + v[j + 1]) / (1 + rates[i][j] + oas)
            if call_price is not None and first_call is not None and i >= first_call:
                cont = min(cont, call_price)  # issuer calls when continuation > call price
            new_v.append(cont + coupon)
        v = new_v
    return 0.5 * (v[0] + v[1]) / (1 + rates[0][0] + oas)


def _solve_spread(rates, coupon_pct, n_years, price, call_price, first_call, face) -> float:
    def f(s: float) -> float:
        return value_bond(rates, coupon_pct, n_years, s, call_price, first_call, face) - price

    lo, hi = -0.10, 0.50  # f decreasing in s
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        if f(mid) > 0:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


def oas_analysis(pillars: list[Pillar], coupon_pct: float, maturity: float, price: float,
                 sigma: float, call_price: float, first_call: float,
                 face: float = 100.0) -> dict:
    """Compute OAS, static spread and option cost for a callable bond (annual steps)."""
    n = max(1, round(maturity))
    rates = calibrate_tree(pillars, n, sigma)
    oas = _solve_spread(rates, coupon_pct, n, price, call_price, round(first_call), face)
    static = _solve_spread(rates, coupon_pct, n, price, None, None, face)
    return {
        "oas_bp": oas * 1e4,
        "static_spread_bp": static * 1e4,
        "option_cost_bp": (static - oas) * 1e4,
        "n_years": n,
        "sigma": sigma,
    }
