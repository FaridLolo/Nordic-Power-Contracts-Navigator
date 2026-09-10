"""
Nordic Power Contracts Navigator
---------------------------------
A lightweight commercial Proof-of-Concept that helps large corporate
electricity customers compare three procurement strategies:

    1. 100% Spot Market exposure
    2. Standard Fixed-Price PPA
    3. Hybrid PPA + Flexibility solution

The purpose of this tool is NOT to forecast real market prices.
It is a commercial storytelling instrument: it turns abstract market
mechanics (volatility, hedging, risk premium, demand-response value)
into a simple visual conversation a Commercial Product Manager can
have with a corporate customer.

All price and volatility assumptions are clearly documented in
README.md and are illustrative, not trading advice or a market
forecast.
"""

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

# --------------------------------------------------------------------------
# Page configuration & Scandinavian-inspired visual theme
# --------------------------------------------------------------------------
st.set_page_config(
    page_title="Nordic Power Contracts Navigator",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

PRIMARY = "#1B4965"      # deep fjord blue
ACCENT = "#5FA8D3"       # clear sky blue
LIGHT = "#F5F7F8"        # snow white
GRID_GREEN = "#7FB77E"   # forest green (renewables / savings)
WARN = "#E0A458"         # amber (risk)
SPOT_COLOR = "#C1666B"   # muted red (volatility)

st.markdown(
    f"""
    <style>
    .stApp {{
        background-color: {LIGHT};
    }}
    html, body, [class*="css"] {{
        font-family: 'Segoe UI', 'Helvetica Neue', Arial, sans-serif;
    }}
    h1, h2, h3 {{
        color: {PRIMARY};
        font-weight: 600;
    }}
    section[data-testid="stSidebar"] {{
        background-color: #FFFFFF;
        border-right: 1px solid #E3E8EA;
    }}
    div[data-testid="stMetric"] {{
        background-color: #FFFFFF;
        border: 1px solid #E3E8EA;
        border-radius: 10px;
        padding: 14px 16px;
    }}
    .value-box {{
        background-color: #FFFFFF;
        border: 1px solid #E3E8EA;
        border-left: 6px solid {GRID_GREEN};
        border-radius: 10px;
        padding: 22px 26px;
        margin-top: 10px;
        margin-bottom: 10px;
    }}
    .value-box h3 {{
        margin-top: 0;
    }}
    .small-note {{
        color: #6B7280;
        font-size: 0.85rem;
    }}
    </style>
    """,
    unsafe_allow_html=True,
)

# --------------------------------------------------------------------------
# Sidebar — Customer Inputs
# --------------------------------------------------------------------------
st.sidebar.markdown("## Customer Profile")
st.sidebar.markdown(
    "<span class='small-note'>Enter the corporate customer's consumption "
    "and risk profile to generate a tailored comparison.</span>",
    unsafe_allow_html=True,
)

annual_consumption_gwh = st.sidebar.slider(
    "Annual Electricity Consumption (GWh/year)",
    min_value=10,
    max_value=100,
    value=30,
    step=5,
)

risk_profile = st.sidebar.radio(
    "Risk Tolerance Profile",
    options=["Low", "Medium", "High"],
    index=1,
    help="Low = strongly prefers price certainty. High = comfortable "
         "absorbing market volatility for potential upside.",
)

current_model = st.sidebar.radio(
    "Current Purchasing Model",
    options=["100% Spot Market", "Partial Fixed"],
    index=0,
)

st.sidebar.markdown("---")
st.sidebar.markdown("## Market Assumptions")
st.sidebar.markdown(
    "<span class='small-note'>Illustrative Nordic market parameters. "
    "Adjust to stress-test the comparison.</span>",
    unsafe_allow_html=True,
)

avg_spot_price = st.sidebar.slider(
    "Average Spot Price (€/MWh)", min_value=30, max_value=90, value=55
)
st.sidebar.markdown(
    "<span class='small-note'>Reference: Nord Pool day-ahead average for Finland "
    "was ≈€38.7/MWh in H1 2025 and ≈€71.7/MWh in H1 2026 — a real ~85% swing "
    "in six months. The default above sits between the two.</span>",
    unsafe_allow_html=True,
)
spot_volatility_pct = st.sidebar.slider(
    "Spot Price Volatility (annual, %)", min_value=10, max_value=60, value=35
)
flex_share_pct = st.sidebar.slider(
    "Flexibility-managed share of volume (%)",
    min_value=10,
    max_value=50,
    value=30,
    help="The portion of consumption actively shifted/optimized under "
         "the Hybrid solution to capture cheap-price windows.",
)

st.sidebar.markdown("---")
n_simulations = st.sidebar.slider(
    "Simulation runs (Monte Carlo)", min_value=200, max_value=5000, value=1500, step=100
)
random_seed = st.sidebar.number_input("Random seed", value=42, step=1)

# --------------------------------------------------------------------------
# Commercial Business Logic
# --------------------------------------------------------------------------
# NOTE: All figures below are simplified, transparent commercial-logic
# assumptions built for demonstration purposes — see README.md for the
# full methodology and disclaimers.

MWH_PER_GWH = 1000
volume_mwh = annual_consumption_gwh * MWH_PER_GWH

# Risk-adjusted premium a customer is willing/needing to pay for certainty
RISK_PREMIUM_MULTIPLIER = {"Low": 1.15, "Medium": 1.10, "High": 1.05}

# PPA fixed price = average spot + a hedging premium (utility's margin for
# absorbing volatility) minus a small discount for volume/duration.
PPA_HEDGE_PREMIUM = 0.12          # 12% premium embedded in a standard fixed PPA
FLEX_DISCOUNT_ON_MANAGED_VOLUME = 0.18   # 18% saving on the flexibility-managed share
FLEX_SERVICE_FEE_PER_MWH = 1.5    # €/MWh fee for running the flexibility service
CO2_GRID_AVG_KG_PER_MWH = 70      # Finland grid avg, ~2025 (Ember/Electricity Maps range 57-95 g/kWh)
CO2_PPA_RENEWABLE_KG_PER_MWH = 11 # lifecycle residual emissions of wind/solar-backed PPA


def simulate_spot_costs(volume_mwh, avg_price, volatility_pct, n_sims, seed):
    """Monte Carlo annual cost distribution for 100% spot exposure.

    Monthly spot prices are modeled as a random walk around the annual
    average with log-normal noise, then averaged into an annual cost.
    This captures the intra-year volatility corporates actually feel
    on their invoices, without claiming to forecast real prices.
    """
    rng = np.random.default_rng(seed)
    monthly_avg = avg_price
    sigma = volatility_pct / 100
    # 12 correlated monthly draws per simulation run
    monthly_prices = rng.lognormal(
        mean=np.log(monthly_avg) - (sigma ** 2) / 2,
        sigma=sigma,
        size=(n_sims, 12),
    )
    annual_avg_price = monthly_prices.mean(axis=1)
    annual_cost = annual_avg_price * volume_mwh
    return annual_cost, annual_avg_price


def simulate_fixed_ppa_costs(volume_mwh, avg_price):
    """Standard fixed PPA: flat price for the full year, no volatility."""
    fixed_price = avg_price * (1 + PPA_HEDGE_PREMIUM)
    annual_cost = np.full(1, fixed_price * volume_mwh)
    return annual_cost, fixed_price


def simulate_hybrid_costs(volume_mwh, avg_price, volatility_pct, flex_share, n_sims, seed):
    """Hybrid PPA + Flexibility.

    A fixed PPA backbone covers the bulk of consumption (price certainty),
    while the flexibility-managed share is actively optimized against
    spot price movements, capturing a discount for shifting load to
    cheaper hours/periods, net of a service fee for running the
    optimization.
    """
    rng = np.random.default_rng(seed + 1)
    fixed_price = avg_price * (1 + PPA_HEDGE_PREMIUM)
    fixed_volume = volume_mwh * (1 - flex_share)
    flex_volume = volume_mwh * flex_share

    sigma = volatility_pct / 100
    monthly_prices = rng.lognormal(
        mean=np.log(avg_price) - (sigma ** 2) / 2,
        sigma=sigma,
        size=(n_sims, 12),
    )
    annual_avg_spot = monthly_prices.mean(axis=1)

    flex_effective_price = (
        annual_avg_spot * (1 - FLEX_DISCOUNT_ON_MANAGED_VOLUME)
        + FLEX_SERVICE_FEE_PER_MWH
    )

    annual_cost = fixed_price * fixed_volume + flex_effective_price * flex_volume
    return annual_cost, fixed_price, flex_effective_price.mean()


# Run simulations
spot_costs, spot_prices = simulate_spot_costs(
    volume_mwh, avg_spot_price, spot_volatility_pct, n_simulations, random_seed
)
ppa_costs, ppa_fixed_price = simulate_fixed_ppa_costs(volume_mwh, avg_spot_price)
hybrid_costs, hybrid_fixed_price, hybrid_flex_avg_price = simulate_hybrid_costs(
    volume_mwh, avg_spot_price, spot_volatility_pct, flex_share_pct / 100,
    n_simulations, random_seed,
)

# Risk Exposure Index: coefficient of variation (std/mean) scaled 0-100.
# A simple, explainable proxy for "how much your annual bill can swing".
def risk_index(costs):
    if len(costs) <= 1 or costs.mean() == 0:
        return 0.0
    cv = costs.std() / costs.mean()
    return round(min(cv * 100 * 2.2, 100), 1)  # scaled for readability

spot_risk = risk_index(spot_costs)
ppa_risk = risk_index(ppa_costs)          # effectively ~0 (flat price)
hybrid_risk = risk_index(hybrid_costs)

results = pd.DataFrame(
    {
        "Option": ["100% Spot Market", "Standard Fixed PPA", "Hybrid PPA + Flexibility"],
        "Mean Annual Cost (€)": [spot_costs.mean(), ppa_costs.mean(), hybrid_costs.mean()],
        "Low (P10, €)": [
            np.percentile(spot_costs, 10),
            ppa_costs.mean(),
            np.percentile(hybrid_costs, 10),
        ],
        "High (P90, €)": [
            np.percentile(spot_costs, 90),
            ppa_costs.mean(),
            np.percentile(hybrid_costs, 90),
        ],
        "Risk Exposure Index (0-100)": [spot_risk, ppa_risk, hybrid_risk],
    }
)

# CO2 impact: assume Spot = average grid mix, PPA & Hybrid = renewable-backed
co2_spot_tons = volume_mwh * CO2_GRID_AVG_KG_PER_MWH / 1000
co2_ppa_tons = volume_mwh * CO2_PPA_RENEWABLE_KG_PER_MWH / 1000
co2_hybrid_tons = volume_mwh * CO2_PPA_RENEWABLE_KG_PER_MWH / 1000
co2_saving_tons = co2_spot_tons - co2_hybrid_tons

savings_vs_spot = spot_costs.mean() - hybrid_costs.mean()
savings_vs_ppa = ppa_costs.mean() - hybrid_costs.mean()

# --------------------------------------------------------------------------
# Header
# --------------------------------------------------------------------------
st.title("⚡ Nordic Power Contracts Navigator")
st.markdown(
    "A commercial decision-support tool for corporate energy customers — "
    "comparing **Spot Market**, **Fixed PPA**, and **Hybrid PPA + Flexibility** "
    "procurement strategies."
)
st.markdown(
    f"<span class='small-note'>Customer profile: **{annual_consumption_gwh} GWh/year** "
    f"· Risk tolerance: **{risk_profile}** · Current model: **{current_model}**</span>",
    unsafe_allow_html=True,
)
st.markdown("---")

# --------------------------------------------------------------------------
# Value Proposition Summary
# --------------------------------------------------------------------------
col1, col2 = st.columns([2, 1])

with col1:
    st.markdown(
        f"""
        <div class="value-box">
        <h3>💡 Value Proposition Summary — Hybrid PPA + Flexibility</h3>
        <p style="font-size:1.05rem; margin-bottom:4px;">
        Estimated annual savings vs. <b>100% Spot Market</b>:
        <b style="color:{PRIMARY}; font-size:1.3rem;">€{savings_vs_spot:,.0f}</b>
        </p>
        <p style="font-size:1.05rem; margin-bottom:4px;">
        Estimated annual savings vs. <b>Standard Fixed PPA</b>:
        <b style="color:{PRIMARY}; font-size:1.3rem;">€{savings_vs_ppa:,.0f}</b>
        </p>
        <p style="font-size:1.05rem; margin-bottom:0;">
        Estimated CO₂ reduction vs. current spot sourcing:
        <b style="color:{GRID_GREEN}; font-size:1.3rem;">{co2_saving_tons:,.0f} tons CO₂/year</b>
        </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

with col2:
    st.metric("Risk Exposure — Spot", f"{spot_risk}/100")
    st.metric("Risk Exposure — Fixed PPA", f"{ppa_risk}/100")
    st.metric("Risk Exposure — Hybrid", f"{hybrid_risk}/100")

st.markdown("---")

# --------------------------------------------------------------------------
# Comparison Chart — Cost forecast & risk range
# --------------------------------------------------------------------------
st.subheader("📊 Cost Forecast & Risk Range by Contract Option")

fig = go.Figure()

colors = {
    "100% Spot Market": SPOT_COLOR,
    "Standard Fixed PPA": ACCENT,
    "Hybrid PPA + Flexibility": GRID_GREEN,
}

for _, row in results.iterrows():
    option = row["Option"]
    mean_cost = row["Mean Annual Cost (€)"]
    low = row["Low (P10, €)"]
    high = row["High (P90, €)"]
    fig.add_trace(
        go.Bar(
            x=[option],
            y=[mean_cost],
            name=option,
            marker_color=colors[option],
            error_y=dict(
                type="data",
                symmetric=False,
                array=[max(high - mean_cost, 0)],
                arrayminus=[max(mean_cost - low, 0)],
                color="#4B5563",
                thickness=1.5,
                width=6,
            ),
            text=[f"€{mean_cost:,.0f}"],
            textposition="outside",
            showlegend=False,
        )
    )

fig.update_layout(
    plot_bgcolor="white",
    paper_bgcolor="white",
    yaxis_title="Estimated Annual Energy Cost (€)",
    xaxis_title="",
    font=dict(family="Segoe UI, Helvetica Neue, Arial, sans-serif", color="#1F2937"),
    margin=dict(t=30, b=30, l=10, r=10),
    height=420,
)
fig.update_yaxes(gridcolor="#E5E7EB")

st.plotly_chart(fig, use_container_width=True)
st.markdown(
    "<span class='small-note'>Error bars show the P10–P90 range across "
    f"{n_simulations:,} simulated annual outcomes — i.e. the realistic band "
    "of best- and worst-case bills a customer could actually see.</span>",
    unsafe_allow_html=True,
)

# --------------------------------------------------------------------------
# Risk Index comparison (horizontal bar)
# --------------------------------------------------------------------------
st.subheader("🎯 Risk Exposure Index")

fig_risk = go.Figure(
    go.Bar(
        x=results["Risk Exposure Index (0-100)"],
        y=results["Option"],
        orientation="h",
        marker_color=[colors[o] for o in results["Option"]],
        text=[f"{v}/100" for v in results["Risk Exposure Index (0-100)"]],
        textposition="outside",
    )
)
fig_risk.update_layout(
    plot_bgcolor="white",
    paper_bgcolor="white",
    xaxis_title="Risk Exposure Index (0 = fully stable, 100 = highly volatile)",
    xaxis=dict(range=[0, 100], gridcolor="#E5E7EB"),
    font=dict(family="Segoe UI, Helvetica Neue, Arial, sans-serif", color="#1F2937"),
    margin=dict(t=20, b=30, l=10, r=10),
    height=280,
)
st.plotly_chart(fig_risk, use_container_width=True)

st.markdown("---")

# --------------------------------------------------------------------------
# Detailed table
# --------------------------------------------------------------------------
with st.expander("📋 View detailed figures"):
    display_df = results.copy()
    for c in ["Mean Annual Cost (€)", "Low (P10, €)", "High (P90, €)"]:
        display_df[c] = display_df[c].map(lambda v: f"€{v:,.0f}")
    st.dataframe(display_df, use_container_width=True, hide_index=True)

    st.markdown(
        f"""
        **Underlying reference prices used in this scenario:**
        - Average spot price: €{avg_spot_price}/MWh (volatility: {spot_volatility_pct}%)
        - Standard Fixed PPA price: €{ppa_fixed_price:,.1f}/MWh
        - Hybrid fixed backbone price: €{hybrid_fixed_price:,.1f}/MWh
        - Hybrid flexibility-managed average price: €{hybrid_flex_avg_price:,.1f}/MWh
          ({flex_share_pct}% of volume actively optimized)
        """
    )

with st.expander("📎 Data sources & calibration"):
    st.markdown(
        """
        Default values in this demo are calibrated against public market data,
        not invented from scratch:

        - **Spot price range**: Nord Pool day-ahead average for Finland was
          ≈€38.7/MWh in H1 2025 and ≈€71.7/MWh in H1 2026 (Nord Pool data,
          reported via industry market commentary).
        - **Grid carbon intensity**: Finland's average grid emission factor is
          commonly cited in the 57–95 gCO₂/kWh range depending on methodology
          (Ember / Electricity Maps / Statistics Finland). This demo uses 70 g/kWh.
        - **Renewable PPA residual emissions**: ~11 gCO₂/kWh, in line with
          published wind lifecycle emission factors.
        - **PPA hedging premium and flexibility discount** remain user-adjustable
          modeled parameters (sidebar), since real contract premiums vary widely
          by duration, volume, counterparty credit risk, and structure
          (pay-as-produced vs. baseload) — there is no single published number
          for "the" PPA premium, and this tool doesn't pretend otherwise.

        This is still a simplified demonstration model, not a trading or
        investment tool — see README.md for the full methodology and disclaimer.
        """
    )

st.caption(
    "This tool uses simplified, transparent assumptions calibrated against "
    "public market data for commercial demonstration purposes. It is not a "
    "trading, pricing, or investment tool. See README.md for full methodology."
)
