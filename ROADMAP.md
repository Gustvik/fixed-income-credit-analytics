# Roadmap

This toolkit is developed **incrementally alongside CFA study** — each feature maps to a
curriculum topic, so building the model and learning the theory reinforce each other.
The list below is a direction of travel, not a schedule.

## Shipped

| Feature | CFA topic |
|---|---|
| Zero-curve bootstrapping; par & forward rates | Term Structure of Interest Rates |
| YTM, Z-spread, G-spread; spread decomposition | Yield & Spread Measures / Credit Analysis |
| Macaulay & modified duration, convexity, DV01 | Interest-Rate Risk & Return |
| Key-rate (partial) durations | Interest-Rate Risk — non-parallel shifts |
| Spread duration, DTS, risk budgeting | Credit Analysis / Fixed-Income Portfolio Mgmt |
| Active risk vs. benchmark; covariance tracking error | Fixed-Income Portfolio Management |
| Option-adjusted spread on a binomial tree (callables) | Valuation of Bonds with Embedded Options |
| Rate/spread scenario re-pricing; spread early-warning | Interest-Rate Risk / Credit Analysis |
| Macro backdrop: policy rate, inflation, real vs. nominal rate, GDP (live Norges Bank + SSB) | Economics / Term Structure |
| Learning page mapping each metric to CFA topics | — (study companion) |

## Planned

### Real data
- **Real fund-holdings integration** — load actual Nordic credit fund portfolios and
  analyse them with the model (provenance-noted). *Application of everything above.*

### Curve construction
- **Nelson–Siegel–Svensson curve fitting** as an alternative to bootstrapping. *Term Structure.*
- **Multi-curve / OIS discounting** and a swap curve. *Term Structure / Swaps.*

### Credit modelling
- **Expected loss** from probability of default × loss given default; credit-spread ↔ default
  intensity. *Credit Analysis Models.*
- **Structural (Merton) & reduced-form default models.** *Credit Analysis Models.*
- **Rating-transition / migration matrices** feeding the early-warning view. *Credit Analysis.*

### Instruments
- **Floating-rate notes and interest-rate swaps** valuation. *Fixed-Income Instruments.*

### Portfolio & risk
- **Immunization / liability-driven investing** (duration & convexity matching) — directly
  relevant to pension mandates. *Liability-Driven & Index-Based Strategies.*
- **Credit portfolio optimization** — maximise information ratio subject to a tracking-error
  budget. *Active Management.*
- **Return attribution** — decompose return into carry, roll-down, curve and spread. *Fixed-Income attribution.*
- **VaR / expected shortfall** on the portfolio. *Risk Management.*

## Notes

- Sample data is illustrative; real pricing needs a data source (e.g. Nordic Bond Pricing).
- Feedback and suggestions are welcome via issues.
