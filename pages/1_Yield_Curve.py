"""Streamlit front-end for the fixed income yield-curve builder."""

from __future__ import annotations

import math

import pandas as pd
import streamlit as st

from fixed_income import (
    Bond,
    bootstrap,
    convert_rate,
    discount_factor,
    forward_rate,
    interp_zero,
    par_yield,
)

st.set_page_config(page_title="Fixed Income — Yield Curve Builder", page_icon="📈", layout="wide")

DEFAULT_BONDS = pd.DataFrame(
    [
        {"Maturity (y)": 0.5, "Coupon %": 0.00, "Price /100": 98.10},
        {"Maturity (y)": 1.0, "Coupon %": 2.00, "Price /100": 99.30},
        {"Maturity (y)": 2.0, "Coupon %": 2.75, "Price /100": 99.60},
        {"Maturity (y)": 3.0, "Coupon %": 3.25, "Price /100": 99.90},
        {"Maturity (y)": 5.0, "Coupon %": 3.75, "Price /100": 100.20},
        {"Maturity (y)": 7.0, "Coupon %": 4.00, "Price /100": 100.10},
        {"Maturity (y)": 10.0, "Coupon %": 4.25, "Price /100": 99.50},
    ]
)

COMP_OPTIONS = {"Continuous": 0, "Annual": 1, "Semi-annual": 2}

st.title("Fixed Income — Yield Curve Builder")
st.caption(
    "Bootstrap a zero (spot) curve from fixed-rate coupon bonds, then derive "
    "discount factors, par yields and forward rates."
)

# ---------------- Sidebar controls ----------------
with st.sidebar:
    st.header("Conventions")
    freq = st.selectbox(
        "Coupon frequency / yr",
        options=[1, 2, 4],
        index=1,
        format_func=lambda f: {1: "Annual (1)", 2: "Semi-annual (2)", 4: "Quarterly (4)"}[f],
    )
    comp_name = st.selectbox("Display compounding", options=list(COMP_OPTIONS), index=2)
    m = COMP_OPTIONS[comp_name]
    st.markdown("---")
    st.markdown(
        "Edit the instruments on the right, then the curve rebuilds automatically. "
        "Each bond pays coupons on the frequency grid up to maturity, face = 100."
    )

# ---------------- Instrument editor ----------------
col_in, col_out = st.columns([1, 2], gap="large")

with col_in:
    st.subheader("Market instruments")
    edited = st.data_editor(
        DEFAULT_BONDS,
        num_rows="dynamic",
        width="stretch",
        key="bonds",
        column_config={
            "Maturity (y)": st.column_config.NumberColumn(format="%.2f", min_value=0.0),
            "Coupon %": st.column_config.NumberColumn(format="%.3f", min_value=0.0),
            "Price /100": st.column_config.NumberColumn(format="%.2f", min_value=0.0),
        },
    )

# ---------------- Bootstrap ----------------
def build_curve(df: pd.DataFrame, freq: int) -> list:
    bonds = []
    for _, row in df.iterrows():
        mat, cpn, px = row["Maturity (y)"], row["Coupon %"], row["Price /100"]
        if pd.isna(mat) or pd.isna(cpn) or pd.isna(px):
            continue
        if mat <= 0 or px <= 0:
            raise ValueError("Maturity and price must be positive.")
        bonds.append(Bond(float(mat), float(cpn), float(px)))
    if not bonds:
        raise ValueError("Enter at least one bond.")
    return bootstrap(bonds, freq)


with col_out:
    st.subheader("Curves")
    try:
        pillars = build_curve(edited, freq)
    except ValueError as exc:
        st.error(str(exc))
        st.stop()

    max_t = pillars[-1].t

    # Smooth sampled curves for plotting
    n_grid = 200
    rows = []
    for k in range(1, n_grid + 1):
        t = k / n_grid * max_t
        zc = interp_zero(pillars, t)
        # instantaneous forward via a small step: f = -d(ln DF)/dt
        dt = max_t / n_grid * 0.5 + 1e-6
        t2 = min(t + dt, max_t)
        if t2 > t:
            df1 = discount_factor(interp_zero(pillars, t), t)
            df2 = discount_factor(interp_zero(pillars, t2), t2)
            fwd_c = (math.log(df1) - math.log(df2)) / (t2 - t)
        else:
            fwd_c = zc
        rows.append(
            {
                "Maturity": t,
                "Zero rate %": convert_rate(zc, m) * 100,
                "Forward rate %": convert_rate(fwd_c, m) * 100,
                "Discount factor": discount_factor(zc, t),
            }
        )
    curve_df = pd.DataFrame(rows)

    # Par yields on the frequency grid
    par_rows = []
    for i in range(1, round(max_t * freq) + 1):
        t = i / freq
        par_rows.append({"Maturity": t, "Par yield %": par_yield(pillars, t, freq) * 100})
    par_df = pd.DataFrame(par_rows)

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Zero / forward rates** (%)")
        st.line_chart(curve_df.set_index("Maturity")[["Zero rate %", "Forward rate %"]])
        st.markdown("**Par yields** (%)")
        st.line_chart(par_df.set_index("Maturity"))
    with c2:
        st.markdown("**Discount factors**")
        st.line_chart(curve_df.set_index("Maturity")[["Discount factor"]])

# ---------------- Results table ----------------
st.subheader(f"Bootstrapped results · {comp_name.lower()} compounding")
res_rows = []
for i, p in enumerate(pillars):
    fwd = None
    if i > 0:
        fwd = convert_rate(forward_rate(pillars, pillars[i - 1].t, p.t), m) * 100
    res_rows.append(
        {
            "Maturity (y)": p.t,
            "Zero rate %": round(convert_rate(p.z, m) * 100, 4),
            "Discount factor": round(discount_factor(p.z, p.t), 6),
            "Par yield %": round(par_yield(pillars, p.t, freq) * 100, 4),
            "Forward rate %": None if fwd is None else round(fwd, 4),
        }
    )
st.dataframe(pd.DataFrame(res_rows), width="stretch", hide_index=True)

st.caption(
    "Discounting uses continuously-compounded zero rates internally; "
    "displayed rates are converted to the selected compounding. Discount factors are convention-free."
)
