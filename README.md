# ⚡ Nordic Power Contracts Navigator

A lightweight, interactive Proof-of-Concept that helps large corporate
electricity customers understand and compare three procurement strategies:

1. **100% Spot Market** — full exposure to hourly/monthly price swings
2. **Standard Fixed PPA** — a long-term Power Purchase Agreement at a flat price
3. **Hybrid PPA + Flexibility** — a fixed backbone combined with an actively
   managed flexible share of consumption

Built with **Python + Streamlit + Plotly**.

---

## Why this tool exists

Finland's electricity demand is projected to grow substantially this decade,
and the market is shifting away from simple spot-price purchasing toward
longer-term contracts, PPAs, and flexibility services. For a corporate
buyer, this shift raises real questions that are hard to answer from a
spreadsheet:

- *How much price certainty am I actually buying with a fixed PPA — and what
  am I giving up?*
- *Does a flexibility solution genuinely lower my costs, or is it just
  added complexity?*
- *How do I explain this trade-off internally, to a CFO who wants numbers,
  not market jargon?*

This is a commercial product demonstration, not a trading system. It takes
mechanics a pricing or portfolio team already works with — hedging premiums,
volatility, risk-sharing — and puts them in a visual form a Commercial
Product Manager can walk a customer through.

---

## How the app is structured

```
├── app.py              # Streamlit application (UI + business logic)
├── requirements.txt    # Python dependencies
└── README.md            # This file
```

The app is a single, self-contained `app.py` so it's easy to review, fork,
and run locally.

---

## Methodology

### 1. Purpose
The model answers one question for a corporate electricity buyer: *for a
given consumption volume and risk tolerance, what does each of the three
procurement options cost, and how much does that cost vary?* It is a
comparison tool, not a forecasting or trading model.

### 2. Inputs and assumptions

| Parameter | Value | Source / status |
|---|---|---|
| Annual consumption, risk profile, current model | User input | Set by the customer conversation |
| Average spot price | Default €55/MWh, adjustable €30–90 | Anchored to Nord Pool day-ahead Finland: ≈€38.7/MWh (H1 2025) to ≈€71.7/MWh (H1 2026) |
| Spot price volatility | Default 35%/year, adjustable | User-set; no single published figure for future volatility |
| PPA hedging premium | 12% over average spot price | Modeled assumption — real premiums vary by duration, volume and counterparty credit; see BloombergNEF range below |
| Flexibility discount | 18% on the managed share | Modeled assumption, adjustable |
| Flexibility service fee | €1.5/MWh | Modeled assumption |
| Grid carbon intensity | 70 gCO₂/kWh | Within the 57–95 g/kWh range reported by Electricity Maps and Ember for Finland |
| Renewable PPA residual emissions | 11 gCO₂/kWh | In line with published wind lifecycle emission factors |

Sources:
[Nord Pool day-ahead prices](https://data.nordpoolgroup.com/auction/day-ahead/prices) ·
[Electricity Maps — Finland](https://app.electricitymaps.com/zone/FI) ·
[Ember — Electricity Data Explorer](https://ember-energy.org/data/electricity-data-explorer/) ·
[Fingrid — real-time CO₂ estimate](https://www.fingrid.fi/en/electricity-market-information/real-time-co2-emissions-estimate/) ·
[BloombergNEF — European Corporate PPA Price Survey](https://about.bnef.com/insights/clean-energy/sweden-spain-the-cheapest-european-markets-for-wind-and-solar-corporate-ppas-bnef-survey-finds/)

The hedging premium, flexibility discount and service fee are left as
adjustable parameters rather than fixed to a single "market" number,
because real PPA pricing depends on contract duration, volume, structure,
and counterparty credit risk — there is no single correct value to hard-code.

### 3. Calculation logic

- **100% Spot Market**: a Monte Carlo simulation draws 12 monthly spot
  prices per run from a log-normal distribution around the average spot
  price, with the user-set volatility as the distribution's spread. This
  produces a distribution of annual costs rather than a single number,
  since variability is what the customer is actually exposed to.
- **Standard Fixed PPA**: average spot price × (1 + hedging premium),
  applied to the full volume. A flat number with no simulated variance.
- **Hybrid PPA + Flexibility**: volume is split into a fixed backbone
  (priced as the standard PPA) and a flexibility-managed share (default
  30%, adjustable). The flexible share is simulated against the same spot
  volatility, discounted by the flexibility discount, and charged the
  service fee per MWh.
- **Risk Exposure Index (0–100)**: coefficient of variation (standard
  deviation ÷ mean) of each option's simulated annual cost, scaled to a
  0–100 index for readability. A flat PPA sits near 0; spot market is
  typically highest.
- **Savings and CO₂ impact**: savings compare mean simulated annual cost
  across options. CO₂ impact assumes spot-sourced volume reflects the
  average grid emissions factor and PPA/Hybrid volume is renewable-backed.

### 4. Simulation parameters
Monte Carlo runs (default 1,500, adjustable 200–5,000) and a fixed random
seed (default 42, adjustable) control the simulation. A fixed seed makes
results reproducible between runs with the same inputs; changing it shows
how much the specific numbers depend on random draw versus the underlying
assumptions.

### 5. Limitations
- Monthly prices are drawn independently (log-normal), not modeled with
  month-to-month correlation or seasonality.
- The hedging premium, flexibility discount and service fee are static
  inputs, not derived from a counterparty credit or contract-structure model.
- No modeling of extreme/tail scenarios (e.g. multi-month price spikes),
  contract default risk, or currency effects.
- CO₂ figures use a single national grid-average factor, not hourly or
  regional variation.

### 6. Interpreting the output
The absolute € and tons-CO₂ figures should be read as directional, not as
a quote. The more load-bearing outputs are the *shape* of the comparison —
that a flat PPA removes variance at a premium, and that a flexibility share
can reduce cost while keeping most of the volume protected — since that
relationship holds regardless of the exact parameter values.

> All prices, premiums, discounts and emissions factors above are
> adjustable illustrative defaults, not price forecasts or trading advice.

---

## Visual design

The interface uses a deliberately restrained, **Scandinavian-inspired**
visual language: a light neutral background, a single deep "fjord blue" as
the primary color, muted supporting colors for risk (amber/red) and
sustainability (forest green), and generous white space — aiming to feel
like something a Nordic energy company's commercial team would actually
put in front of a customer.

---

## Running locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

The app will open at `http://localhost:8501`.

---

## Possible next steps (roadmap)

- Connect to a real day-ahead spot price feed (e.g. Nord Pool) for the
  volatility assumptions instead of the illustrative log-normal model.
- Add a multi-year contract view (3–10 year PPA horizon) with price
  escalation scenarios.
- Add a portfolio view for customers comparing multiple sites/meters.
- Export a one-page PDF "customer proposal" summary from the app.

---

## About this project

This is a proof-of-concept built to explore how commercial product
thinking — translating market mechanics into customer-facing value — holds
up as a working tool rather than a slide deck.
