"""Tests for the credit analytics module."""

import pytest

from fixed_income import (
    CreditBond,
    analyse_bond,
    durations,
    early_warning,
    mv_weights,
    portfolio_scenario,
    portfolio_summary,
    reprice,
    risk_budget,
    synthetic_spread_history,
    ytm,
    z_spread,
)
from fixed_income.data_io import load_credit_universe, load_govt_bonds, risk_free_curve

FREQ = 2


@pytest.fixture(scope="module")
def pillars():
    return risk_free_curve(load_govt_bonds(), freq=FREQ)


@pytest.fixture(scope="module")
def bonds():
    df = load_credit_universe()
    return [
        CreditBond(r["name"], r["issuer"], r["sector"], r["country"], r["rating"],
                   float(r["maturity"]), float(r["coupon"]), float(r["price"]),
                   int(r["freq"]), float(r["nominal"]))
        for _, r in df.iterrows()
    ]


def test_ytm_of_par_bond_equals_coupon():
    # A bond priced at 100 has YTM ~= coupon.
    y = ytm(coupon=4.0, maturity=5.0, price=100.0, freq=FREQ)
    assert y == pytest.approx(0.04, abs=2e-4)


def test_zspread_reprices_bond(pillars):
    bond = CreditBond("t", "i", "Energy", "NO", "A", 5.0, 4.40, 99.80, FREQ, 100)
    z = z_spread(pillars, bond.coupon, bond.maturity, bond.price, bond.freq)
    repriced = reprice(pillars, bond.coupon, bond.maturity, bond.freq, z, 0.0, 0.0)
    assert repriced == pytest.approx(bond.price, abs=1e-6)


def test_modified_less_than_macaulay():
    d = durations(coupon=4.0, maturity=7.0, price=99.0, freq=FREQ)
    assert 0 < d["modified"] < d["macaulay"]
    assert d["convexity"] > 0


def test_ig_bonds_have_positive_credit_spread(pillars, bonds):
    # Investment-grade corporates should price at a positive spread to govt.
    for b in bonds:
        rec = analyse_bond(b, pillars)
        assert rec["credit_spread_bp"] > 0


def test_scenario_signs(pillars, bonds):
    records = [analyse_bond(b, pillars) for b in bonds]
    up_rates = portfolio_scenario(bonds, records, pillars, d_rate_bp=100, d_spread_bp=0)
    wider = portfolio_scenario(bonds, records, pillars, d_rate_bp=0, d_spread_bp=50)
    assert up_rates["exact_pnl"] < 0     # rates up -> prices down
    assert wider["exact_pnl"] < 0        # spreads wider -> prices down
    # approximation should be in the same ballpark for a moderate shock
    assert up_rates["approx_pct"] == pytest.approx(up_rates["exact_pct"], abs=2e-3)


def test_weights_sum_to_one(pillars, bonds):
    records = [analyse_bond(b, pillars) for b in bonds]
    w = mv_weights(records)
    assert sum(w) == pytest.approx(1.0)
    rb = risk_budget(records, w)
    assert sum(r["pct_of_risk"] for r in rb) == pytest.approx(1.0)


def test_portfolio_summary_keys(pillars, bonds):
    records = [analyse_bond(b, pillars) for b in bonds]
    summ = portfolio_summary(records, mv_weights(records))
    for key in ["ytm", "mod_duration", "spread_duration", "dts", "credit_spread_bp"]:
        assert key in summ and summ[key] > 0


def test_early_warning_runs(pillars, bonds):
    records = [analyse_bond(b, pillars) for b in bonds]
    hist = synthetic_spread_history(records, days=90, seed=42)
    alerts = early_warning(records, hist)
    assert len(alerts) == len(records)
    assert all(a.status in {"OK", "WATCH", "ALERT"} for a in alerts)
