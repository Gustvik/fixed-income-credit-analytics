"""Fixed income analytics: zero-curve bootstrapping and IG credit portfolio tools."""

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
from .credit import (
    CreditBond,
    SpreadAlert,
    active_risk,
    analyse_bond,
    cashflows,
    durations,
    early_warning,
    g_spread,
    mv_weights,
    portfolio_scenario,
    portfolio_summary,
    reprice,
    risk_budget,
    scenario_pnl,
    spread_duration,
    synthetic_spread_history,
    ytm,
    z_spread,
)

__all__ = [
    # curve
    "Bond",
    "Pillar",
    "bootstrap",
    "convert_rate",
    "discount_factor",
    "forward_rate",
    "interp_zero",
    "par_yield",
    "price_bond",
    # credit
    "CreditBond",
    "SpreadAlert",
    "active_risk",
    "analyse_bond",
    "cashflows",
    "durations",
    "early_warning",
    "g_spread",
    "mv_weights",
    "portfolio_scenario",
    "portfolio_summary",
    "reprice",
    "risk_budget",
    "scenario_pnl",
    "spread_duration",
    "synthetic_spread_history",
    "ytm",
    "z_spread",
]

__version__ = "0.2.0"
