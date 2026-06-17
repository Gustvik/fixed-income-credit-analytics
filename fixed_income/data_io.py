"""Helpers for loading sample data and building the risk-free curve."""

from __future__ import annotations

import os

import pandas as pd

from .curve import Bond, bootstrap

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")


def load_govt_bonds() -> pd.DataFrame:
    """Sample Norwegian government bonds used to bootstrap the risk-free NOK curve."""
    return pd.read_csv(os.path.join(DATA_DIR, "norwegian_govt_sample.csv"))


def load_credit_universe() -> pd.DataFrame:
    """Illustrative Nordic investment-grade credit universe."""
    return pd.read_csv(os.path.join(DATA_DIR, "nordic_ig_sample.csv"))


def risk_free_curve(govt: pd.DataFrame, freq: int = 2):
    """Bootstrap the risk-free zero curve from a govt-bond DataFrame."""
    bonds = [
        Bond(float(r["maturity"]), float(r["coupon"]), float(r["price"]))
        for _, r in govt.iterrows()
        if not pd.isna(r["maturity"])
    ]
    return bootstrap(bonds, freq)
