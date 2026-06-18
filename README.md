# Fixed Income Toolkit

Rate-curve construction and an **investment-grade credit portfolio model** — credit
treated as an *asset class* (spread as a return source and risk factor), not just
credit risk in lending. Built as a multipage [Streamlit](https://streamlit.io) app.

![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![License: MIT](https://img.shields.io/badge/license-MIT-green)

## Quick start

```bash
pip install -r requirements.txt
streamlit run app.py
```

Streamlit opens a multipage app:

- **📈 Yield Curve** — bootstrap a zero curve from coupon bonds → discount factors,
  par yields, forward rates. The risk-free foundation for credit spreads.
- **📊 Credit Portfolio** — the IG credit model (below).

## Credit Portfolio — what it does

| Component | Method |
|---|---|
| **Yield & spread** | YTM, **Z-spread** (constant spread over the zero curve), G-spread |
| **Duration** | Macaulay, modified, convexity, **spread duration**, DV01 |
| **Spread decomposition** | yield = risk-free rate + credit premium, per bond and portfolio |
| **Portfolio construction** | MV weights, **DTS** (duration × spread), risk budgeting |
| **Active risk** | active duration / spread duration / DTS / yield vs. a benchmark |
| **Curve risk** | **key-rate (partial) durations** per pillar — bullet/barbell and curve tilts |
| **Tracking error** | **covariance/factor model** TE = √(wᵀΣw) with per-name risk contributions |
| **Scenario analysis** | exact re-pricing under parallel rate shift Δr and spread widening Δs (+ duration/convexity approximation and a Δr×Δs heatmap) |
| **OAS (callable)** | **option-adjusted spread** on a curve-calibrated binomial rate tree; option cost vs. volatility |
| **Early warning** | spread-movement z-score monitor → OK / WATCH / ALERT |

The risk-free base is a bootstrapped **NOK government curve**; the universe is an
illustrative **Nordic IG** set (NOK). Upload your own CSV to use real instruments.

## Mapping to CFA Level II (Fixed Income)

- *Yield & spread measures* → YTM, Z-spread, G-spread
- *Term structure* → bootstrapped zero/forward curve (Yield Curve page)
- *Interest-rate risk* → modified duration, convexity, DV01, **key-rate durations**
- *Valuation of bonds with embedded options* → **OAS** via a binomial rate tree, option cost
- *Credit analysis* → spread decomposition, spread duration, **DTS**
- *Portfolio management* → benchmark-relative active risk, risk budgeting, **tracking error**

## Project layout

```
.
├── app.py                          # landing page
├── pages/
│   ├── 1_Yield_Curve.py            # zero-curve bootstrap UI
│   └── 2_Credit_Portfolio.py       # IG credit model UI
├── fixed_income/
│   ├── curve.py                    # bootstrap / discounting / par & forward rates
│   ├── credit.py                   # YTM, spreads, durations, KRD, DTS, scenarios, TE, alerts
│   ├── oas.py                      # binomial rate tree + option-adjusted spread
│   └── data_io.py                  # sample-data loaders + risk-free curve
├── data/
│   ├── norwegian_govt_sample.csv   # risk-free curve instruments
│   └── nordic_ig_sample.csv        # illustrative IG universe
├── tests/                          # pytest (curve + credit)
├── index.html                      # standalone offline curve tool (no Python)
├── requirements.txt
└── LICENSE
```

## Using the model in code

```python
from fixed_income import CreditBond, analyse_bond, portfolio_summary, mv_weights
from fixed_income.data_io import load_govt_bonds, risk_free_curve

pillars = risk_free_curve(load_govt_bonds())
bond = CreditBond("Equinor 4.40 2031", "Equinor", "Energy", "NO", "AA-",
                  maturity=5.0, coupon=4.40, price=99.80, freq=2, nominal=90)
rec = analyse_bond(bond, pillars)
print(rec["ytm"], rec["credit_spread_bp"], rec["mod_duration"], rec["dts"])
```

## Tests

```bash
pip install pytest
pytest
```

Key invariants checked: the bootstrapped curve re-prices its inputs (~1e-8); the
Z-spread re-prices each bond; IG bonds price at positive spread to govt; scenario
signs are correct (rates up / spreads wider → value down); weights and risk-budget
contributions sum to 1.

## Methodology notes

- Discounting uses **continuously-compounded** zero rates internally; spreads are
  reported in basis points. DTS = spread duration × spread (%).
- Each bond pays coupons on its frequency grid up to maturity, face = 100.
- **Sample data is illustrative.** Real Nordic IG prices require a data subscription
  (e.g. Nordic Bond Pricing / Stamdata); the CSV uploader lets you plug those in.

## Deploy

- **GitHub:** `git push` to a repo (see below).
- **Streamlit Community Cloud:** <https://share.streamlit.io> → New app → this repo →
  main file `app.py`. `requirements.txt` is installed automatically.

```bash
git remote add origin https://github.com/<you>/fixed-income-toolkit.git
git push -u origin main
```

## License

MIT — see [LICENSE](LICENSE).
