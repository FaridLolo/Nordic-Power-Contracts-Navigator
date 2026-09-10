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

This project is a **commercial product demonstration**, not a trading
system. Its job is to take the same mechanics a pricing or portfolio team
already understands — hedging premiums, volatility, risk-sharing — and turn
them into a two-minute visual story a Commercial Product Manager can walk a
customer through in a sales or account-management conversation.

---

## How the app is structured

```
├── app.py              # Streamlit application (UI + business logic)
├── requirements.txt    # Python dependencies
└── README.md            # This file
```

The app is a single, self-contained `app.py` so it can be reviewed,
forked, and deployed in minutes — deliberately built as something a
prospective employer or colleague can run locally in under five minutes.

---

## Commercial & business logic

All calculations live in clearly commented functions in `app.py`. The
assumptions below are **illustrative defaults** chosen to produce a
realistic-looking, directionally sound demo — they are editable in the
sidebar and are explicitly *not* a market forecast or trading model.

### 1. Customer inputs
- **Annual consumption (GWh/year)** — sets the scale of the contract.
- **Risk tolerance profile** (Low / Medium / High) — frames how the
  results should be discussed (the tool itself always shows all three
  options; risk tolerance is a conversation anchor for the sales team).
- **Current purchasing model** — for context on where the customer is
  starting from.

### 2. The three contract options

| Option | Logic |
|---|---|
| **100% Spot Market** | Modeled with a Monte Carlo simulation: 12 monthly spot prices are drawn from a log-normal distribution around the customer's average spot price assumption, with a volatility parameter the user controls. This produces a realistic **distribution** of possible annual costs, not a single number — because that unpredictability *is* the commercial story for this option. |
| **Standard Fixed PPA** | Priced as the average spot price plus a **hedging premium** (default 12%), reflecting the premium a supplier typically embeds to absorb the customer's volatility risk. The result is a single flat number — full price certainty, zero variance. |
| **Hybrid PPA + Flexibility** | Splits volume into a **fixed backbone** (priced like the standard PPA) and a **flexibility-managed share** (user-adjustable, default 30%). The flexible share is simulated against the same spot volatility, but with a **discount** (default 18%) representing the value captured by shifting load to cheaper price windows, net of a **flexibility service fee** (€1.5/MWh) representing the cost of running the optimization service. |

### 3. Risk Exposure Index (0–100)
A simple, explainable proxy for "how much could your annual bill move?",
calculated as the coefficient of variation (standard deviation ÷ mean) of
each option's simulated annual cost, scaled to a 0–100 index. A flat PPA
scores near 0; spot market typically scores highest.

### 4. Savings and CO₂ impact
- **Savings** are shown for Hybrid vs. Spot and Hybrid vs. standard PPA, using
  the mean simulated annual cost of each option.
- **CO₂ impact** assumes spot-sourced power reflects the average Nordic grid
  emissions factor, while PPA and Hybrid volumes are renewable-backed
  (typical of real-world corporate PPAs), so switching away from spot
  reduces the customer's reported emissions.

> **Disclaimer:** All prices, premiums, discounts, and emissions factors
> are configurable illustrative defaults for demonstration purposes. They
> are not price forecasts, trading advice, or a substitute for a real
> pricing/risk model.

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

This Proof-of-Concept was built to demonstrate how commercial product
thinking — translating market mechanics into clear customer value — can be
expressed as a working tool, not just a slide deck.
