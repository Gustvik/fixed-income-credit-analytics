"""Fixed Income Toolkit — landing page for the multipage Streamlit app."""

from __future__ import annotations

import streamlit as st

st.set_page_config(page_title="Fixed Income Toolkit", page_icon="📊", layout="wide")

st.title("Fixed Income Toolkit")
st.caption("Rate curves and investment-grade credit portfolio analytics.")

st.markdown(
    """
This toolkit treats **credit as an asset class**, not just credit risk in lending.
Use the pages in the sidebar:

### 📈 Yield Curve
Bootstrap a zero (spot) curve from coupon bonds and derive discount factors, par yields
and forward rates. This is the **risk-free foundation** the credit spreads are measured against.

### 📊 Credit Portfolio
An investment-grade credit model from the **investor's perspective**:

- **Yield & spread** — YTM, Z-spread and G-spread on a Nordic IG universe
- **Duration** — Macaulay, modified, convexity, spread duration, DV01
- **Spread decomposition** — yield split into risk-free rate + credit premium
- **Portfolio construction** — DTS, risk budgeting, and active risk vs. a benchmark
- **Scenario analysis** — exact re-pricing under parallel rate shifts and spread widening
- **Early warning** — spread-movement monitoring with z-score alerts

### 📖 Læring & metodikk
The finance behind every metric — intuition, formula, worked example, CFA Level II
link and an interview-ready one-liner for each concept.

---
*Sample data (Nordic IG names, NOK) is illustrative. Upload your own CSV on the Credit
Portfolio page to use real instruments.*
"""
)

st.info(
    "Methodology: discounting uses continuously-compounded zero rates internally; "
    "spreads are reported in basis points. See the README for formulas and the "
    "CFA Level II topics each component maps to.",
    icon="ℹ️",
)
