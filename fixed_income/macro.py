"""Macro data for the Norwegian rate backdrop.

Pulls three authoritative, key-free series and derives the real policy rate:

* **Policy rate (styringsrente)** — Norges Bank (nominal short rate, the anchor of
  the short end of the risk-free curve).
* **CPI 12-month inflation (KPI)** — Statistics Norway (SSB), table 03013.
* **Mainland-Norway GDP growth** — SSB table 09190 (`Volum`, year-on-year %).

Real rate = policy rate − CPI inflation.

Each fetch tries the live API and falls back to a bundled snapshot CSV in ``data/``
so the app always renders (important for a live demo). This module is Streamlit-free;
the page wraps the fetchers in ``st.cache_data``.
"""

from __future__ import annotations

import json
import os
import urllib.request

import pandas as pd

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")

NB_POLICY_URL = (
    "https://data.norges-bank.no/api/data/IR/B.KPRA.SD.R"
    "?format=csv&startPeriod={start}"
)
SSB_CPI_TABLE = "https://data.ssb.no/api/v0/no/table/03013"
SSB_GDP_TABLE = "https://data.ssb.no/api/v0/no/table/09190"


# --------------------------------------------------------------------------- #
# Low-level HTTP
# --------------------------------------------------------------------------- #
def _get(url: str, timeout: int = 30) -> str:
    with urllib.request.urlopen(url, timeout=timeout) as r:
        return r.read().decode("utf-8", "replace")


def _post(url: str, body: dict, timeout: int = 30) -> str:
    req = urllib.request.Request(
        url, data=json.dumps(body).encode(), headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", "replace")


def _tid_to_period(code: str) -> pd.Timestamp:
    """Convert an SSB time code ('2025M12' or '2025K3') to a month-start Timestamp."""
    if "M" in code:
        y, m = code.split("M")
        return pd.Timestamp(int(y), int(m), 1)
    if "K" in code:
        y, q = code.split("K")
        return pd.Timestamp(int(y), (int(q) - 1) * 3 + 1, 1)
    return pd.Timestamp(code)


def _parse_jsonstat_tid(payload: str) -> pd.DataFrame:
    """Parse an SSB json-stat2 response with a single Tid dimension into date/value."""
    d = json.loads(payload)
    idx = d["dimension"]["Tid"]["category"]["index"]
    values = d["value"]
    ordered = sorted(idx, key=lambda k: idx[k])
    rows = [(_tid_to_period(code), values[idx[code]]) for code in ordered]
    return pd.DataFrame(rows, columns=["date", "value"]).dropna()


# --------------------------------------------------------------------------- #
# Live fetchers (with snapshot fallback)
# --------------------------------------------------------------------------- #
def _snapshot_path(name: str) -> str:
    return os.path.join(DATA_DIR, f"macro_{name}.csv")


def _with_fallback(name: str, live_fn):
    """Run ``live_fn``; on any failure, load the bundled snapshot. Returns (df, is_live)."""
    try:
        df = live_fn()
        if df is None or df.empty:
            raise ValueError("empty")
        return df, True
    except Exception:
        path = _snapshot_path(name)
        if os.path.exists(path):
            df = pd.read_csv(path, parse_dates=["date"])
            return df, False
        raise


def _fetch_policy_live(start: str) -> pd.DataFrame:
    txt = _get(NB_POLICY_URL.format(start=start))
    rows = [r.split(";") for r in txt.splitlines() if r.strip()]
    h = rows[0]
    ti, vi = h.index("TIME_PERIOD"), h.index("OBS_VALUE")
    data = [(pd.Timestamp(r[ti]), float(r[vi])) for r in rows[1:] if r[vi]]
    df = pd.DataFrame(data, columns=["date", "value"])
    # daily -> month-start last observation
    df = df.set_index("date").resample("MS").last().dropna().reset_index()
    return df


def _fetch_cpi_live(start_year: int) -> pd.DataFrame:
    body = {
        "query": [
            {"code": "Konsumgrp", "selection": {"filter": "item", "values": ["TOTAL"]}},
            {"code": "ContentsCode", "selection": {"filter": "item", "values": ["Tolvmanedersendring"]}},
        ],
        "response": {"format": "json-stat2"},
    }
    df = _parse_jsonstat_tid(_post(SSB_CPI_TABLE, body))
    return df[df["date"].dt.year >= start_year].reset_index(drop=True)


def _fetch_gdp_live(start_year: int) -> pd.DataFrame:
    body = {
        "query": [
            {"code": "Makrost", "selection": {"filter": "item", "values": ["bnpb.nr23_9fn"]}},
            {"code": "ContentsCode", "selection": {"filter": "item", "values": ["Volum"]}},
        ],
        "response": {"format": "json-stat2"},
    }
    df = _parse_jsonstat_tid(_post(SSB_GDP_TABLE, body))
    return df[df["date"].dt.year >= start_year].reset_index(drop=True)


# --------------------------------------------------------------------------- #
# Public API
# --------------------------------------------------------------------------- #
def get_macro(start_year: int = 2015) -> dict:
    """Return policy/CPI/GDP series, the derived real-rate frame, and metadata."""
    start = f"{start_year}-01-01"
    policy, p_live = _with_fallback("policy_rate", lambda: _fetch_policy_live(start))
    cpi, c_live = _with_fallback("cpi_yoy", lambda: _fetch_cpi_live(start_year))
    gdp, g_live = _with_fallback("gdp_growth", lambda: _fetch_gdp_live(start_year))

    # Merge policy + CPI monthly -> real rate
    rates = (
        policy.rename(columns={"value": "policy_rate"})
        .merge(cpi.rename(columns={"value": "cpi_yoy"}), on="date", how="inner")
    )
    rates["real_rate"] = rates["policy_rate"] - rates["cpi_yoy"]

    return {
        "policy": policy,
        "cpi": cpi,
        "gdp": gdp,
        "rates": rates,
        "live": {"policy": p_live, "cpi": c_live, "gdp": g_live},
        "all_live": p_live and c_live and g_live,
    }


def save_snapshots(start_year: int = 2010) -> None:
    """Fetch live series and write them as bundled fallback CSVs (run offline/manually)."""
    start = f"{start_year}-01-01"
    _fetch_policy_live(start).to_csv(_snapshot_path("policy_rate"), index=False)
    _fetch_cpi_live(start_year).to_csv(_snapshot_path("cpi_yoy"), index=False)
    _fetch_gdp_live(start_year).to_csv(_snapshot_path("gdp_growth"), index=False)
