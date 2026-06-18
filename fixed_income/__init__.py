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
    key_rate_durations,
    mv_weights,
    portfolio_key_rate_durations,
    portfolio_scenario,
    portfolio_summary,
    reprice,
    risk_budget,
    scenario_pnl,
    spread_duration,
    synthetic_spread_history,
    tracking_error,
    ytm,
    z_spread,
)
from .oas import calibrate_tree, oas_analysis, value_bond

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
    "key_rate_durations",
    "mv_weights",
    "portfolio_key_rate_durations",
    "portfolio_scenario",
    "portfolio_summary",
    "reprice",
    "risk_budget",
    "scenario_pnl",
    "spread_duration",
    "synthetic_spread_history",
    "tracking_error",
    "ytm",
    "z_spread",
    # oas
    "calibrate_tree",
    "oas_analysis",
    "value_bond",
]

__version__ = "0.3.0"
