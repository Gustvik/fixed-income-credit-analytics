"""Investment-grade credit portfolio model — yield/spread, risk, scenarios, monitoring."""

from __future__ import annotations

import altair as alt
import pandas as pd
import streamlit as st

from fixed_income import (
    CreditBond,
    active_risk,
    analyse_bond,
    early_warning,
    mv_weights,
    oas_analysis,
    portfolio_key_rate_durations,
    portfolio_scenario,
    portfolio_summary,
    risk_budget,
    synthetic_spread_history,
    tracking_error,
)
from fixed_income.data_io import load_credit_universe, load_govt_bonds, risk_free_curve

st.set_page_config(page_title="Credit Portfolio", page_icon="📊", layout="wide")

st.title("Investment-Grade Credit Portfolio")
st.caption(
    "Credit as an asset class: spread analysis, duration & DTS, portfolio construction "
    "with active risk vs. benchmark, rate/spread scenarios, and spread-based monitoring. "
    "Risk-free base = bootstrapped NOK government curve."
)

# --------------------------------------------------------------------------- #
# Inputs: risk-free curve + credit universe
# --------------------------------------------------------------------------- #
with st.sidebar:
    st.header("Universe")
    upload = st.file_uploader("Upload credit universe (CSV)", type="csv")
    st.caption(
        "Columns: name, issuer, sector, country, rating, maturity, coupon, price, freq, nominal. "
        "Leave empty to use the illustrative Nordic IG sample."
    )
    st.markdown("---")
    st.header("Benchmark")
    bench_mode = st.radio(
        "Benchmark weighting",
        ["Equal weight", "Market value"],
        help="Portfolio is market-value weighted from nominals; the benchmark is the comparison.",
    )

govt = load_govt_bonds()
pillars = risk_free_curve(govt, freq=2)

universe = pd.read_csv(upload) if upload is not None else load_credit_universe()

st.subheader("Credit universe")
edited = st.data_editor(
    universe,
    num_rows="dynamic",
    width="stretch",
    hide_index=True,
    column_config={
        "maturity": st.column_config.NumberColumn("Maturity (y)", format="%.2f", min_value=0.0),
        "coupon": st.column_config.NumberColumn("Coupon %", format="%.3f", min_value=0.0),
        "price": st.column_config.NumberColumn("Price /100", format="%.2f", min_value=0.0),
        "nominal": st.column_config.NumberColumn("Nominal (mill)", format="%.0f", min_value=0.0),
        "freq": st.column_config.NumberColumn("Freq", format="%d"),
    },
)


def build_bonds(df: pd.DataFrame) -> list[CreditBond]:
    bonds = []
    for _, r in df.iterrows():
        if pd.isna(r.get("maturity")) or pd.isna(r.get("price")):
            continue
        bonds.append(
            CreditBond(
                name=str(r["name"]),
                issuer=str(r.get("issuer", "")),
                sector=str(r.get("sector", "")),
                country=str(r.get("country", "")),
                rating=str(r.get("rating", "")),
                maturity=float(r["maturity"]),
                coupon=float(r["coupon"]),
                price=float(r["price"]),
                freq=int(r.get("freq", 2)),
                nominal=float(r.get("nominal", 0.0)),
            )
        )
    return bonds


try:
    bonds = build_bonds(edited)
    if not bonds:
        st.error("Add at least one bond.")
        st.stop()
    records = [analyse_bond(b, pillars) for b in bonds]
except (ValueError, KeyError) as exc:
    st.error(f"Could not parse the universe: {exc}")
    st.stop()

rec_df = pd.DataFrame(records)

# Weights
port_w = mv_weights(records)
n = len(records)
eq_w = [1.0 / n] * n
bench_w = eq_w if bench_mode == "Equal weight" else mv_weights(records)

tab_an, tab_pf, tab_kr, tab_te, tab_sc, tab_oas, tab_ew = st.tabs(
    ["📈 Yield & Spread", "🧮 Portfolio & Risk", "📐 Curve Risk", "🎯 Tracking Error",
     "⚡ Scenarios", "📞 OAS (Callable)", "🚨 Early Warning"]
)

# --------------------------------------------------------------------------- #
# TAB 1 — Yield & spread analysis + decomposition
# --------------------------------------------------------------------------- #
with tab_an:
    st.markdown("#### Per-bond analytics")
    show = rec_df[[
        "name", "sector", "rating", "maturity", "ytm", "rf_yield",
        "credit_spread_bp", "g_spread_bp", "mod_duration", "spread_duration",
        "convexity", "dv01", "dts",
    ]].copy()
    show["ytm"] = (show["ytm"] * 100).round(3)
    show["rf_yield"] = (show["rf_yield"] * 100).round(3)
    for c in ["credit_spread_bp", "g_spread_bp"]:
        show[c] = show[c].round(1)
    for c in ["mod_duration", "spread_duration", "convexity", "dts"]:
        show[c] = show[c].round(2)
    show["dv01"] = show["dv01"].round(4)
    show = show.rename(columns={
        "name": "Bond", "sector": "Sector", "rating": "Rating", "maturity": "Mat (y)",
        "ytm": "YTM %", "rf_yield": "Risk-free %", "credit_spread_bp": "Z-spread bp",
        "g_spread_bp": "G-spread bp", "mod_duration": "Mod dur", "spread_duration": "Sprd dur",
        "convexity": "Convexity", "dv01": "DV01", "dts": "DTS",
    })
    st.dataframe(show, width="stretch", hide_index=True)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("#### Spread decomposition — yield = risk-free + credit premium")
        decomp = pd.DataFrame({
            "Bond": rec_df["name"],
            "Risk-free": (rec_df["rf_yield"] * 100),
            "Credit premium": (rec_df["credit_spread_bp"] / 100.0),
        })
        decomp_long = decomp.melt("Bond", var_name="Component", value_name="Yield %")
        chart = (
            alt.Chart(decomp_long)
            .mark_bar()
            .encode(
                x=alt.X("Yield %:Q", title="Yield (%)"),
                y=alt.Y("Bond:N", sort="-x", title=None),
                color=alt.Color("Component:N",
                                scale=alt.Scale(domain=["Risk-free", "Credit premium"],
                                                range=["#4f9dff", "#ff7b9c"])),
                tooltip=["Bond", "Component", alt.Tooltip("Yield %:Q", format=".2f")],
            )
            .properties(height=380)
        )
        st.altair_chart(chart, width="stretch")
    with col2:
        st.markdown("#### Spread vs. duration (risk/return map)")
        scatter_df = rec_df.assign(spread_bp=rec_df["credit_spread_bp"])
        scatter = (
            alt.Chart(scatter_df)
            .mark_circle(size=140, opacity=0.8)
            .encode(
                x=alt.X("spread_duration:Q", title="Spread duration (yr)"),
                y=alt.Y("spread_bp:Q", title="Z-spread (bp)"),
                color=alt.Color("rating:N", title="Rating"),
                tooltip=["name", "sector", "rating",
                         alt.Tooltip("spread_bp:Q", title="Z-spread bp", format=".0f"),
                         alt.Tooltip("spread_duration:Q", title="Sprd dur", format=".2f")],
            )
            .properties(height=380)
            .interactive()
        )
        st.altair_chart(scatter, width="stretch")

# --------------------------------------------------------------------------- #
# TAB 2 — Portfolio construction, active risk, risk budget
# --------------------------------------------------------------------------- #
with tab_pf:
    port = portfolio_summary(records, port_w)
    act = active_risk(records, port_w, bench_w)

    st.markdown("#### Portfolio characteristics (market-value weighted)")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Yield to maturity", f"{port['ytm']*100:.2f} %")
    m2.metric("Modified duration", f"{port['mod_duration']:.2f} yr")
    m3.metric("Credit spread", f"{port['credit_spread_bp']:.0f} bp")
    m4.metric("DTS", f"{port['dts']:.2f}")

    st.markdown("#### Active risk vs. benchmark")
    a1, a2, a3, a4 = st.columns(4)
    a1.metric("Active duration", f"{act['active_duration']:+.2f} yr")
    a2.metric("Active spread dur.", f"{act['active_spread_duration']:+.2f} yr")
    a3.metric("Active DTS", f"{act['active_dts']:+.2f}")
    a4.metric("Active yield", f"{act['active_yield_bp']:+.0f} bp")
    st.caption(
        f"Benchmark = {bench_mode.lower()}. Positive active duration/DTS means the portfolio "
        "carries more rate/credit risk than the benchmark."
    )

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("#### Risk budget — contribution to portfolio DTS")
        rb = pd.DataFrame(risk_budget(records, port_w))
        rb_show = rb[["name", "sector", "weight", "dts_contribution", "pct_of_risk"]].copy()
        rb_show["weight"] = (rb_show["weight"] * 100).round(2)
        rb_show["pct_of_risk"] = (rb_show["pct_of_risk"] * 100).round(2)
        rb_show["dts_contribution"] = rb_show["dts_contribution"].round(3)
        rb_show = rb_show.rename(columns={
            "name": "Bond", "sector": "Sector", "weight": "Weight %",
            "dts_contribution": "DTS contrib", "pct_of_risk": "% of risk"})
        st.dataframe(rb_show, width="stretch", hide_index=True)

    with col2:
        st.markdown("#### Sector allocation — active weights vs. benchmark")
        sec = pd.DataFrame({
            "Sector": rec_df["sector"],
            "Portfolio": port_w,
            "Benchmark": bench_w,
        }).groupby("Sector", as_index=False).sum()
        sec["Active"] = sec["Portfolio"] - sec["Benchmark"]
        sec_long = sec.melt("Sector", value_vars=["Portfolio", "Benchmark"],
                            var_name="Book", value_name="Weight")
        sec_chart = (
            alt.Chart(sec_long)
            .mark_bar()
            .encode(
                x=alt.X("Weight:Q", axis=alt.Axis(format="%"), title="Weight"),
                y=alt.Y("Sector:N", sort="-x", title=None),
                color=alt.Color("Book:N", scale=alt.Scale(
                    domain=["Portfolio", "Benchmark"], range=["#7ee787", "#8b98a8"])),
                yOffset="Book:N",
                tooltip=["Sector", "Book", alt.Tooltip("Weight:Q", format=".1%")],
            )
            .properties(height=360)
        )
        st.altair_chart(sec_chart, width="stretch")

# --------------------------------------------------------------------------- #
# TAB 3 — Curve risk: key-rate durations
# --------------------------------------------------------------------------- #
with tab_kr:
    st.markdown("#### Key-rate (partial) durations")
    st.caption(
        "Sensitivity to a 1bp move at each curve pillar, holding other tenors fixed. "
        "Unlike a single modified duration, this shows *where* on the curve the risk sits "
        "— so you can see bullet vs. barbell exposure and steepener/flattener tilts."
    )
    port_krd = portfolio_key_rate_durations(records, port_w, pillars)
    bench_krd = portfolio_key_rate_durations(records, bench_w, pillars)
    krd_df = pd.DataFrame({
        "Tenor": [f"{t:g}y" for t, _ in port_krd],
        "Portfolio": [k for _, k in port_krd],
        "Benchmark": [k for _, k in bench_krd],
    })
    krd_df["Active"] = krd_df["Portfolio"] - krd_df["Benchmark"]

    col1, col2 = st.columns([3, 2])
    with col1:
        krd_long = krd_df.melt("Tenor", value_vars=["Portfolio", "Benchmark"],
                               var_name="Book", value_name="KRD")
        krd_chart = (
            alt.Chart(krd_long)
            .mark_bar()
            .encode(
                x=alt.X("Tenor:N", sort=list(krd_df["Tenor"]), title="Curve pillar"),
                y=alt.Y("KRD:Q", title="Key-rate duration (yr)"),
                color=alt.Color("Book:N", scale=alt.Scale(
                    domain=["Portfolio", "Benchmark"], range=["#4f9dff", "#8b98a8"])),
                xOffset="Book:N",
                tooltip=["Tenor", "Book", alt.Tooltip("KRD:Q", format=".3f")],
            )
            .properties(height=360)
        )
        st.altair_chart(krd_chart, width="stretch")
    with col2:
        show_krd = krd_df.copy()
        for c in ["Portfolio", "Benchmark", "Active"]:
            show_krd[c] = show_krd[c].round(3)
        st.dataframe(show_krd, width="stretch", hide_index=True)
        st.metric("Σ KRD (≈ effective duration)", f"{krd_df['Portfolio'].sum():.2f} yr")

# --------------------------------------------------------------------------- #
# TAB 4 — Ex-ante tracking error (covariance model)
# --------------------------------------------------------------------------- #
with tab_te:
    st.markdown("#### Ex-ante tracking error vs. benchmark")
    st.caption(
        "Covariance/factor model: each bond's return = −ModDur·Δrate − SprdDur·Δspread, "
        "with a hierarchical spread factor (common + sector + name). "
        "TE = √(wᵀΣw) on active weights. Tune the annualised factor vols below."
    )
    if bench_mode == "Market value":
        st.info("Benchmark is set to *Market value* = the portfolio, so active weights "
                "are zero and TE = 0. Switch the benchmark to *Equal weight* in the sidebar.")
    c = st.columns(5)
    sig_rate = c[0].slider("Rate vol (bp/yr)", 20, 200, 100, 10) / 1e4
    sig_sys = c[1].slider("Systematic spread (bp/yr)", 20, 200, 80, 10) / 1e4
    sig_sec = c[2].slider("Sector spread (bp/yr)", 0, 150, 40, 10) / 1e4
    sig_idio = c[3].slider("Idiosyncratic (bp/yr)", 0, 200, 50, 10) / 1e4
    rho = c[4].slider("Rate–spread corr", -0.9, 0.9, -0.2, 0.1)

    te = tracking_error(records, port_w, bench_w, sig_rate, sig_sys, sig_sec, sig_idio, rho)
    st.metric("Tracking error", f"{te['tracking_error']*100:.2f} % / yr")

    ctr = pd.DataFrame(te["contributions"])
    ctr = ctr.reindex(ctr["ctr_te"].abs().sort_values(ascending=False).index)
    ctr_show = ctr.copy()
    ctr_show["active_weight"] = (ctr_show["active_weight"] * 100).round(2)
    ctr_show["ctr_te"] = (ctr_show["ctr_te"] * 100).round(3)
    ctr_show["pct_of_te"] = (ctr_show["pct_of_te"] * 100).round(1)
    ctr_show = ctr_show.rename(columns={
        "name": "Bond", "sector": "Sector", "active_weight": "Active wt %",
        "ctr_te": "Contrib to TE %", "pct_of_te": "% of TE"})

    col1, col2 = st.columns([2, 3])
    with col1:
        st.dataframe(ctr_show, width="stretch", hide_index=True)
    with col2:
        ctr_chart = (
            alt.Chart(ctr.assign(ctr_pct=ctr["ctr_te"] * 100))
            .mark_bar()
            .encode(
                x=alt.X("ctr_pct:Q", title="Contribution to TE (%)"),
                y=alt.Y("name:N", sort="-x", title=None),
                color=alt.condition(alt.datum.ctr_pct > 0,
                                    alt.value("#ff7b9c"), alt.value("#7ee787")),
                tooltip=["name", alt.Tooltip("ctr_pct:Q", format=".3f")],
            )
            .properties(height=380)
        )
        st.altair_chart(ctr_chart, width="stretch")

# --------------------------------------------------------------------------- #
# TAB 5 — Scenario analysis
# --------------------------------------------------------------------------- #
with tab_sc:
    st.markdown("#### Single scenario")
    s1, s2 = st.columns(2)
    d_rate = s1.slider("Parallel rate shift Δr (bp)", -200, 200, 100, 25)
    d_spread = s2.slider("Spread widening Δs (bp)", -100, 300, 50, 25)

    sc = portfolio_scenario(bonds, records, pillars, d_rate, d_spread)
    c1, c2, c3 = st.columns(3)
    c1.metric("Portfolio value", f"{sc['base_mv']:.1f} mill", f"{sc['exact_pnl']:+.2f} mill")
    c2.metric("Return (exact reprice)", f"{sc['exact_pct']*100:+.2f} %")
    c3.metric("Return (dur+convex approx)", f"{sc['approx_pct']*100:+.2f} %")
    st.caption(
        "Exact = full re-pricing off the shifted curve and widened spread. "
        "Approx = −ModDur·Δr + ½·Convexity·Δr² − SpreadDur·Δs. "
        "The gap grows with shock size — that gap is convexity/cross-term."
    )

    st.markdown("#### Scenario grid — portfolio return %")
    rate_shifts = [-100, -50, 0, 50, 100]
    spread_shifts = [0, 25, 50, 100, 150]
    grid_rows = []
    for ds in spread_shifts:
        for dr in rate_shifts:
            g = portfolio_scenario(bonds, records, pillars, dr, ds)
            grid_rows.append({"Δrate (bp)": dr, "Δspread (bp)": ds,
                              "pnl": g["exact_pct"] * 100})
    grid = pd.DataFrame(grid_rows)
    heat = (
        alt.Chart(grid)
        .mark_rect()
        .encode(
            x=alt.X("Δrate (bp):O", title="Parallel rate shift (bp)"),
            y=alt.Y("Δspread (bp):O", sort="descending", title="Spread widening (bp)"),
            color=alt.Color("pnl:Q", title="Return %",
                            scale=alt.Scale(scheme="redyellowgreen", domainMid=0)),
            tooltip=[alt.Tooltip("pnl:Q", title="Return %", format=".2f"),
                     "Δrate (bp)", "Δspread (bp)"],
        )
        .properties(height=300)
    )
    text = heat.mark_text(baseline="middle", fontSize=11).encode(
        text=alt.Text("pnl:Q", format=".1f"),
        color=alt.value("#1a1a1a"),
    )
    st.altair_chart(heat + text, width="stretch")

# --------------------------------------------------------------------------- #
# TAB 6 — OAS for callable bonds
# --------------------------------------------------------------------------- #
with tab_oas:
    st.markdown("#### Option-adjusted spread — callable bond calculator")
    st.caption(
        "Values an embedded issuer call on a binomial short-rate tree calibrated to the "
        "risk-free curve (annual steps). The OAS strips the option out of the spread: "
        "Option cost = static spread − OAS. Higher rate vol → more valuable call → "
        "higher option cost → lower OAS."
    )
    c = st.columns(3)
    o_cpn = c[0].number_input("Coupon %", 0.0, 15.0, 5.00, 0.25)
    o_mat = c[1].number_input("Maturity (years)", 1, 30, 5, 1)
    o_px = c[2].number_input("Market price /100", 50.0, 160.0, 101.00, 0.25)
    c2 = st.columns(3)
    o_call = c2[0].number_input("Call price /100", 90.0, 115.0, 100.00, 0.5)
    o_first = c2[1].number_input("First call (years)", 1, int(o_mat), min(3, int(o_mat)), 1)
    o_vol = c2[2].slider("Rate volatility σ (%/yr)", 1, 40, 15, 1) / 100.0

    res = oas_analysis(pillars, o_cpn, float(o_mat), o_px, o_vol, o_call, float(o_first))
    k1, k2, k3 = st.columns(3)
    k1.metric("Static spread (Z)", f"{res['static_spread_bp']:.0f} bp")
    k2.metric("OAS", f"{res['oas_bp']:.0f} bp")
    k3.metric("Option cost", f"{res['option_cost_bp']:.0f} bp")

    # Option cost vs volatility curve
    vols = [v / 100.0 for v in range(2, 41, 2)]
    oc = [oas_analysis(pillars, o_cpn, float(o_mat), o_px, v, o_call, float(o_first))
          for v in vols]
    oc_df = pd.DataFrame({
        "Volatility %": [v * 100 for v in vols],
        "OAS": [r["oas_bp"] for r in oc],
        "Static spread": [r["static_spread_bp"] for r in oc],
    })
    oc_long = oc_df.melt("Volatility %", var_name="Measure", value_name="bp")
    oc_chart = (
        alt.Chart(oc_long)
        .mark_line(point=True)
        .encode(
            x=alt.X("Volatility %:Q", title="Rate volatility σ (%/yr)"),
            y=alt.Y("bp:Q", title="Spread (bp)"),
            color=alt.Color("Measure:N", scale=alt.Scale(
                domain=["Static spread", "OAS"], range=["#8b98a8", "#4f9dff"])),
            tooltip=["Volatility %", "Measure", alt.Tooltip("bp:Q", format=".0f")],
        )
        .properties(height=320)
    )
    st.altair_chart(oc_chart, width="stretch")
    st.caption(
        "The gap between the two lines is the option cost. It widens with volatility "
        "(the call is worth more to the issuer), so a callable bond's OAS is the spread "
        "you actually earn after paying for the optionality."
    )

# --------------------------------------------------------------------------- #
# TAB 7 — Early-warning monitoring
# --------------------------------------------------------------------------- #
with tab_ew:
    st.markdown("#### Spread-movement monitor")
    e1, e2 = st.columns(2)
    watch_z = e1.slider("WATCH threshold (z-score)", 0.5, 3.0, 1.5, 0.1)
    alert_z = e2.slider("ALERT threshold (z-score)", 1.0, 4.0, 2.5, 0.1)

    history = synthetic_spread_history(records, days=90, seed=42)
    alerts = early_warning(records, history, watch_z=watch_z, alert_z=alert_z)
    alert_df = pd.DataFrame([{
        "Bond": a.name, "Sector": a.sector,
        "Current bp": round(a.current_bp, 1), "90d avg bp": round(a.avg_bp, 1),
        "Change bp": round(a.change_bp, 1), "Z-score": round(a.zscore, 2),
        "Status": a.status,
    } for a in alerts]).sort_values("Z-score", ascending=False)

    n_alert = (alert_df["Status"] == "ALERT").sum()
    n_watch = (alert_df["Status"] == "WATCH").sum()
    k1, k2, k3 = st.columns(3)
    k1.metric("🚨 Alerts", int(n_alert))
    k2.metric("⚠️ Watch", int(n_watch))
    k3.metric("✅ OK", int((alert_df["Status"] == "OK").sum()))

    def color_status(val):
        return {
            "ALERT": "background-color: #5c1a1a; color: #ff9c9c",
            "WATCH": "background-color: #5c4a1a; color: #ffd479",
            "OK": "color: #7ee787",
        }.get(val, "")

    st.dataframe(
        alert_df.style.map(color_status, subset=["Status"]),
        width="stretch", hide_index=True,
    )
    st.caption(
        "Z-score = (current spread − trailing mean) / trailing std. Widening beyond the "
        "thresholds raises WATCH/ALERT. History here is a reproducible synthetic series "
        "(illustrative); swap in a real daily Z-spread feed for production."
    )
