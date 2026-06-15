# Fixed Income — Yield Curve Builder

Bootstrap a **zero (spot) curve from fixed-rate coupon bonds**, then derive
**discount factors, par yields and forward rates** — as an interactive
[Streamlit](https://streamlit.io) app.

![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![License: MIT](https://img.shields.io/badge/license-MIT-green)

## Quick start

```bash
pip install -r requirements.txt
streamlit run app.py
```

Then open the local URL Streamlit prints (default <http://localhost:8501>).

## Project layout

```
.
├── app.py                  # Streamlit front-end
├── fixed_income/
│   ├── __init__.py
│   └── curve.py            # core bootstrap / pricing math (single source of truth)
├── tests/
│   └── test_curve.py       # pytest: re-price round-trip + invariants
├── requirements.txt
├── index.html              # standalone offline version (no Python needed)
├── LICENSE
└── README.md
```

## What it does

1. **Input** — a table of fixed-rate coupon bonds: maturity (years), coupon (% of
   face), and market price (per 100 face). Pick the coupon frequency.
2. **Bootstrap** — instruments are sorted by maturity; a bisection root-finder
   solves each bond's terminal zero rate so the curve re-prices it exactly. Zero
   rates between solved pillars are interpolated linearly in the zero rate.
3. **Output** — zero curve, discount factors `DF(t) = exp(-z·t)`, par yields
   `f·(1 − DF(T)) / Σ DF(tᵢ)`, and forward rates, shown as charts and a table.
   Display compounding is selectable (continuous / annual / semi-annual).

## Using the model in code

```python
from fixed_income import Bond, bootstrap, discount_factor, par_yield

bonds = [Bond(1.0, 2.0, 99.30), Bond(2.0, 2.75, 99.60), Bond(5.0, 3.75, 100.20)]
pillars = bootstrap(bonds, freq=2)
for p in pillars:
    print(p.t, p.z, discount_factor(p.z, p.t))
```

## Tests

```bash
pip install pytest
pytest
```

The key test re-prices the input bonds with the bootstrapped curve and asserts the
result matches the market prices (to ~1e-8).

## Deploy on Streamlit Community Cloud

1. Push this repo to GitHub (see below).
2. Go to <https://share.streamlit.io>, sign in with GitHub.
3. **New app** → pick this repo, branch `main`, main file `app.py`.
4. Deploy. Community Cloud installs `requirements.txt` automatically.

## Publish to GitHub

```bash
git init
git add .
git commit -m "Initial commit: fixed income yield-curve builder"
gh repo create fixed-income-curve --public --source=. --push
# or create the repo on github.com and:
#   git remote add origin https://github.com/<you>/fixed-income-curve.git
#   git push -u origin main
```

## Method notes

- Discounting uses **continuously-compounded** zero rates internally; display
  rates convert via `r_m = m·(exp(z_c/m) − 1)`.
- Each bond pays coupons on the chosen frequency grid up to maturity, face = 100.
- Linear-in-zero interpolation is robust to instruments spaced more widely than one
  coupon period (intermediate coupon dates are interpolated).

## License

MIT — see [LICENSE](LICENSE).
