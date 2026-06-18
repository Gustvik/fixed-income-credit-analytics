"""Tests for key-rate durations, tracking error, and OAS."""

import math

import pytest

from fixed_income import (
    CreditBond,
    analyse_bond,
    calibrate_tree,
    key_rate_durations,
    mv_weights,
    oas_analysis,
    portfolio_key_rate_durations,
    tracking_error,
    value_bond,
)
from fixed_income.curve import discount_factor, interp_zero
from fixed_income.data_io import load_credit_universe, load_govt_bonds, risk_free_curve

FREQ = 2


@pytest.fixture(scope="module")
def pillars():
    return risk_free_curve(load_govt_bonds(), freq=FREQ)


@pytest.fixture(scope="module")
def records(pillars):
    df = load_credit_universe()
    bonds = [
        CreditBond(r["name"], r["issuer"], r["sector"], r["country"], r["rating"],
                   float(r["maturity"]), float(r["coupon"]), float(r["price"]),
                   int(r["freq"]), float(r["nominal"]))
        for _, r in df.iterrows()
    ]
    return [analyse_bond(b, pillars) for b in bonds]


# ---- Key-rate durations ----
def test_krd_sums_to_effective_duration(pillars, records):
    r = records[4]  # Equinor 5y
    krds = key_rate_durations(pillars, r["coupon"], r["maturity"], FREQ, r["_z"])
    total = sum(k for _, k in krds)
    # Sum of KRDs approximates effective duration (close to modified duration).
    assert total == pytest.approx(r["mod_duration"], rel=0.05)


def test_krd_concentrated_at_maturity(pillars, records):
    r = records[4]  # 5y bond -> 5y pillar should dominate
    krds = dict(key_rate_durations(pillars, r["coupon"], r["maturity"], FREQ, r["_z"]))
    assert krds[5.0] == max(krds.values())


def test_portfolio_krd_length(pillars, records):
    w = mv_weights(records)
    pk = portfolio_key_rate_durations(records, w, pillars)
    assert len(pk) == len(pillars)


# ---- Tracking error ----
def test_te_zero_when_weights_match(records):
    w = mv_weights(records)
    te = tracking_error(records, w, w)  # identical -> no active risk
    assert te["tracking_error"] == pytest.approx(0.0, abs=1e-12)


def test_te_positive_and_contributions_sum(records):
    w = mv_weights(records)
    n = len(records)
    eq = [1.0 / n] * n
    te = tracking_error(records, w, eq)
    assert te["tracking_error"] > 0
    total = sum(c["ctr_te"] for c in te["contributions"])
    assert total == pytest.approx(te["tracking_error"], rel=1e-9)


# ---- OAS / tree ----
def test_tree_reprices_riskfree_zero(pillars):
    # A risk-free zero priced off the curve should imply ~0 static spread.
    price = 100 * discount_factor(interp_zero(pillars, 5), 5)
    res = oas_analysis(pillars, coupon_pct=0.0, maturity=5, price=price,
                       sigma=1e-4, call_price=200, first_call=2)
    assert res["static_spread_bp"] == pytest.approx(0.0, abs=0.5)


def test_oas_below_static_for_callable(pillars):
    res = oas_analysis(pillars, coupon_pct=5.0, maturity=5, price=101.0,
                       sigma=0.15, call_price=100.0, first_call=3)
    assert res["oas_bp"] < res["static_spread_bp"]
    assert res["option_cost_bp"] > 0


def test_option_cost_rises_with_vol(pillars):
    low = oas_analysis(pillars, 5.0, 5, 101.0, 0.10, 100.0, 3)
    high = oas_analysis(pillars, 5.0, 5, 101.0, 0.30, 100.0, 3)
    assert high["option_cost_bp"] > low["option_cost_bp"]


def test_tree_calibration_matches_discount_factors(pillars):
    sigma = 0.15
    n = 7
    rates = calibrate_tree(pillars, n, sigma)
    # Value a unit zero maturing at year n on the tree (coupon 0, no call, oas 0),
    # compare to the curve discount factor.
    modeled = value_bond(rates, coupon_pct=0.0, n_years=n, oas=0.0) / 100.0
    target = discount_factor(interp_zero(pillars, n), n)
    assert modeled == pytest.approx(target, rel=1e-4)
