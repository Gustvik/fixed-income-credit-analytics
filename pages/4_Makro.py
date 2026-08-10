"""Macro backdrop — Norges Bank policy rate, inflation, real rate and GDP growth."""

from __future__ import annotations

import altair as alt
import pandas as pd
import streamlit as st

from fixed_income.macro import get_macro

st.set_page_config(page_title="Makro", page_icon="🌍", layout="wide")

st.title("🌍 Makrobakteppe — Norge")
st.caption(
    "Styringsrenten, inflasjon og BNP-vekst er top-down-konteksten for rentekurven du "
    "bootstrapper og kredittspreadene du analyserer. Styringsrenten er selve ankeret for "
    "den korte enden av den risikofrie kurven."
)


@st.cache_data(ttl=6 * 3600, show_spinner="Henter makrodata …")
def load(start_year: int):
    return get_macro(start_year)

start_year = st.sidebar.slider("Historikk fra år", 2010, 2023, 2015)
m = load(start_year)

# Freshness banner
if m["all_live"]:
    st.success("Live-data fra **Norges Bank** og **SSB** (ingen API-nøkkel).", icon="🟢")
else:
    stale = [k for k, v in m["live"].items() if not v]
    st.warning(f"Bruker bundlet øyeblikksbilde for: {', '.join(stale)} (live-kilde utilgjengelig).", icon="🟡")

rates, cpi, gdp = m["rates"], m["cpi"], m["gdp"]
policy = m["policy"]

# ---- Latest values ----
last_policy = policy.iloc[-1]
last_cpi = cpi.iloc[-1]
last_gdp = gdp.iloc[-1]
last_rr = rates.iloc[-1]

c1, c2, c3, c4 = st.columns(4)
c1.metric("Styringsrente", f"{last_policy['value']:.2f} %", help=f"Per {last_policy['date']:%b %Y} (Norges Bank)")
c2.metric("Inflasjon (KPI 12m)", f"{last_cpi['value']:.1f} %", f"{last_cpi['value']-2.0:+.1f} pp vs 2 %-mål", delta_color="inverse")
c3.metric("Realrente (styring − KPI)", f"{last_rr['real_rate']:.1f} %", help=f"Per {last_rr['date']:%b %Y}")
c4.metric("BNP-vekst Fastlands-Norge", f"{last_gdp['value']:.1f} %", help=f"Volumendring å/å, per {last_gdp['date']:%b %Y}")

st.markdown("---")

# ---- Chart 1: nominal vs real rate + inflation ----
st.markdown("#### Nominell styringsrente vs. realrente")
rr_long = rates.melt("date", value_vars=["policy_rate", "cpi_yoy", "real_rate"],
                     var_name="serie", value_name="pct")
name_map = {"policy_rate": "Styringsrente (nominell)", "cpi_yoy": "Inflasjon (KPI 12m)", "real_rate": "Realrente"}
rr_long["serie"] = rr_long["serie"].map(name_map)
zero = alt.Chart(pd.DataFrame({"y": [0]})).mark_rule(color="#8b98a8", strokeDash=[4, 4]).encode(y="y:Q")
rr_chart = (
    alt.Chart(rr_long)
    .mark_line(strokeWidth=2)
    .encode(
        x=alt.X("date:T", title=None),
        y=alt.Y("pct:Q", title="Prosent"),
        color=alt.Color("serie:N", title=None, scale=alt.Scale(
            domain=list(name_map.values()), range=["#4f9dff", "#ffb454", "#7ee787"])),
        tooltip=[alt.Tooltip("date:T", title="Dato"), "serie", alt.Tooltip("pct:Q", format=".2f")],
    )
    .properties(height=340)
)
st.altair_chart(zero + rr_chart, width="stretch")
st.caption(
    "Realrenten er styringsrenten minus 12-måneders KPI-inflasjon. Det som avgjør om "
    "pengepolitikken er ekspansiv eller kontraktiv, er ikke fortegnet, men om realrenten ligger "
    "under eller over den **nøytrale realrenten (r\\*)** — nivået som verken stimulerer eller "
    "bremser. Under r\\* gir gass, over r\\* bremser. En moderat positiv realrente er normalt og "
    "sunt (sparere får realavkastning); det er en realrente godt *over* r\\* som strammer til."
)

col1, col2 = st.columns(2)
with col1:
    st.markdown("#### Inflasjon vs. Norges Banks 2 %-mål")
    target = alt.Chart(pd.DataFrame({"y": [2.0]})).mark_rule(color="#ff7b9c", strokeDash=[5, 5]).encode(y="y:Q")
    cpi_chart = (
        alt.Chart(cpi).mark_area(opacity=0.25, color="#ffb454", line={"color": "#ffb454"})
        .encode(x=alt.X("date:T", title=None), y=alt.Y("value:Q", title="KPI 12m (%)"),
                tooltip=[alt.Tooltip("date:T", title="Dato"), alt.Tooltip("value:Q", format=".1f")])
        .properties(height=300)
    )
    st.altair_chart(cpi_chart + target, width="stretch")
with col2:
    st.markdown("#### BNP-vekst Fastlands-Norge (volum, å/å)")
    gdp_chart = (
        alt.Chart(gdp).mark_bar()
        .encode(x=alt.X("date:T", title=None), y=alt.Y("value:Q", title="Volumendring (%)"),
                color=alt.condition(alt.datum.value >= 0, alt.value("#7ee787"), alt.value("#ff6b6b")),
                tooltip=[alt.Tooltip("date:T", title="Kvartal"), alt.Tooltip("value:Q", format=".1f")])
        .properties(height=300)
    )
    st.altair_chart(gdp_chart, width="stretch")

with st.expander("Hvorfor dette betyr noe for modellen"):
    st.markdown(
        "- **Styringsrenten** ankrer den korte enden av den risikofrie kurven som bootstrappes "
        "på Yield Curve-siden — endres den, flytter hele diskonteringsgrunnlaget seg.\n"
        "- **Realrenten** avgjør hvor stram pengepolitikken faktisk er, og dermed presset på "
        "kredittspreader: høy positiv realrente strammer finansieringsvilkårene og øker "
        "misligholdsrisiko over tid.\n"
        "- **BNP-vekst** er konjunktursignalet bak kredittsyklusen — svak vekst → svakere "
        "inntjening → spread-utgang, som du kan stress-teste i scenariofanen.\n\n"
        "Slik knytter top-down (makro) seg til bottom-up (spread, durasjon, DTS) i én ramme."
    )

st.caption(
    "Kilder: Norges Bank (styringsrente, IR/B.KPRA.SD.R) og Statistisk sentralbyrå "
    "(KPI tabell 03013, BNP tabell 09190). Data hentes live med bundlet reserve."
)
