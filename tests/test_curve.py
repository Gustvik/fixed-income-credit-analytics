"""Tests for the zero-curve bootstrap."""

import math

import pytest

from fixed_income import Bond, bootstrap, discount_factor, par_yield, price_bond

SAMPLE = [
    Bond(0.5, 0.00, 98.10),
    Bond(1.0, 2.00, 99.30),
    Bond(2.0, 2.75, 99.60),
    Bond(3.0, 3.25, 99.90),
    Bond(5.0, 3.75, 100.20),
    Bond(7.0, 4.00, 100.10),
    Bond(10.0, 4.25, 99.50),
]
FREQ = 2


def test_bootstrap_reprices_inputs():
    """The bootstrapped curve must re-price every input bond to its market price."""
    pillars = bootstrap(SAMPLE, FREQ)
    for bond in SAMPLE:
        modeled = price_bond(pillars, bond.coupon, bond.maturity, FREQ)
        assert modeled == pytest.approx(bond.price, abs=1e-8)


def test_discount_factors_monotone_decreasing():
    pillars = bootstrap(SAMPLE, FREQ)
    dfs = [discount_factor(p.z, p.t) for p in pillars]
    assert all(earlier > later for earlier, later in zip(dfs, dfs[1:]))
    assert all(0 < d <= 1 for d in dfs)


def test_par_yield_recovers_par_bond():
    """A bond priced at par should have coupon == par yield at that maturity."""
    pillars = bootstrap(SAMPLE, FREQ)
    par = par_yield(pillars, 5.0, FREQ) * 100
    at_par_price = price_bond(pillars, par, 5.0, FREQ)
    assert at_par_price == pytest.approx(100.0, abs=1e-6)


def test_duplicate_maturity_raises():
    with pytest.raises(ValueError, match="Duplicate maturity"):
        bootstrap([Bond(1.0, 2.0, 99.0), Bond(1.0, 3.0, 100.0)], FREQ)


def test_zero_coupon_implies_log_df():
    """A 0% bond's zero rate equals -ln(price/100)/maturity (continuous)."""
    pillars = bootstrap([Bond(2.0, 0.0, 92.0)], FREQ)
    expected = -math.log(0.92) / 2.0
    assert pillars[0].z == pytest.approx(expected, abs=1e-9)
