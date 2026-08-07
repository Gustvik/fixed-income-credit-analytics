"""Offline tests for the macro module (uses bundled snapshots, no network)."""

import os

import pandas as pd
import pytest

from fixed_income.macro import DATA_DIR, _tid_to_period


def test_tid_to_period_month():
    assert _tid_to_period("2025M12") == pd.Timestamp(2025, 12, 1)


def test_tid_to_period_quarter():
    # K3 -> third quarter starts in July
    assert _tid_to_period("2025K3") == pd.Timestamp(2025, 7, 1)


@pytest.mark.parametrize("name", ["policy_rate", "cpi_yoy", "gdp_growth"])
def test_snapshot_present_and_valid(name):
    path = os.path.join(DATA_DIR, f"macro_{name}.csv")
    assert os.path.exists(path), f"missing snapshot {name}"
    df = pd.read_csv(path, parse_dates=["date"])
    assert list(df.columns) == ["date", "value"]
    assert len(df) > 12
    assert df["value"].notna().all()


def test_real_rate_reconstructs():
    p = pd.read_csv(os.path.join(DATA_DIR, "macro_policy_rate.csv"), parse_dates=["date"])
    c = pd.read_csv(os.path.join(DATA_DIR, "macro_cpi_yoy.csv"), parse_dates=["date"])
    merged = p.rename(columns={"value": "pol"}).merge(c.rename(columns={"value": "cpi"}), on="date")
    assert not merged.empty
    real = merged["pol"] - merged["cpi"]
    # Norwegian real policy rate has stayed within a sane band over the sample.
    assert real.between(-8, 6).all()
