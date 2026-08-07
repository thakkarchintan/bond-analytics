import streamlit as st

st.set_page_config(page_title="Bond Analytics", layout="wide")

from common import authenticator
from stream import home_page
from HeatmapTab import heatmap_tab
from portfolio_rebalance import portfolio_rebalance
from NewsSummary import *
from ChangelogTab import changelog_tab
from MacroDashboard import macro_dashboard
from CapitalMarkets import capital_markets
from YieldCurves import yield_curves
from BondCalculator import bond_calculator
from BondPortfolio import bond_portfolio
from BondInvestmentStrategies import bond_investment_strategies
from CreditSpreads import credit_spreads
from CentralBankRates import central_bank_rates
from CrossAsset import cross_asset
from LeadingIndicators import leading_indicators
from BondSimulator import bond_simulator
from GlobalBusinessCycle import global_business_cycle
from HistoricalShocks import historical_shocks
from FiscalScorecard import fiscal_scorecard
from InflationGrowth import inflation_growth
from FXCurrencies import fx_currencies
from DataSources import data_sources
from HomePage import home_page_cards
from data import load_data
from dotenv import load_dotenv
import os

# ── Global styles ────────────────────────────────────────────────────────────
_CSS = """
<style>
/* Hide branding */
#MainMenu { visibility: hidden; }
footer    { visibility: hidden; }

/* Compact sidebar header */
[data-testid="stSidebarHeader"] {
    padding: 0.5rem 1rem !important;
    min-height: unset !important;
}

/* Tighter content area */
.block-container {
    padding-top: 2rem;
    padding-bottom: 1rem;
}

/* Auto-dismiss login success banner */
@keyframes _alertFade {
    to { opacity: 0; max-height: 0; padding: 0; margin: 0; overflow: hidden; }
}
[data-testid="stAlert"] {
    animation: _alertFade 0.4s ease 2s forwards;
}

/* Dark sidebar */
[data-testid="stSidebar"] {
    background-color: #1e293b;
}
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] .stMarkdown p,
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3,
[data-testid="stSidebar"] span {
    color: #e2e8f0 !important;
}

/* Sidebar selectboxes */
[data-testid="stSidebar"] [data-baseweb="select"] > div:first-child {
    background-color: #334155 !important;
    border-color: #475569 !important;
}
[data-testid="stSidebar"] [data-baseweb="select"] * {
    color: #f1f5f9 !important;
    background-color: #334155 !important;
}

/* Sidebar date inputs */
[data-testid="stSidebar"] input[type="text"],
[data-testid="stSidebar"] input[type="number"] {
    background-color: #334155 !important;
    color: #f1f5f9 !important;
    border-color: #475569 !important;
}

/* Sidebar buttons */
[data-testid="stSidebar"] .stButton > button {
    width: 100%;
    background-color: #334155 !important;
    border: 1px solid #475569 !important;
    color: #f1f5f9 !important;
    border-radius: 6px;
    font-weight: 500;
}
[data-testid="stSidebar"] .stButton > button:hover {
    background-color: #475569 !important;
    border-color: #64748b !important;
}

/* Sidebar slider track */
[data-testid="stSidebar"] [data-testid="stSlider"] div[role="slider"] {
    background-color: #1e40af !important;
}

/* Main area button polish */
.stButton > button {
    border-radius: 6px;
    font-weight: 500;
}

/* Sidebar HR divider */
[data-testid="stSidebar"] hr {
    border-color: #334155;
}

/* Sidebar button height — matches selectbox height */
[data-testid="stSidebar"] .stButton > button {
    height: 2.4rem !important;
    min-height: 2.4rem !important;
}

/* Sidebar expand button (visible when sidebar is collapsed) */
[data-testid="collapsedControl"] {
    background-color: #1e293b !important;
    border-color: #334155 !important;
}
[data-testid="collapsedControl"] svg {
    fill: #22d3ee !important;
    color: #22d3ee !important;
}
</style>
"""

st.markdown(_CSS, unsafe_allow_html=True)

load_dotenv()

if "connected" not in st.session_state:
    st.session_state["connected"] = False

if "login_message_shown" not in st.session_state:
    st.session_state["login_message_shown"] = False

if not st.session_state["connected"]:
    st.markdown(
        """
        <div style="display:flex; justify-content:center; align-items:center; margin-top:200px;">
            <h1 style="color:#0f172a;">Bond Analytics</h1>
        </div>
        """,
        unsafe_allow_html=True,
    )

authenticator.check_auth()
authenticator.login()

if st.session_state["connected"]:
    APP_MAP = {
        "Bond Analytics": home_page,
        "Correlation Matrix": heatmap_tab,
        "Portfolio Rebalance": portfolio_rebalance,
        "News Summarizer": news_app,
        "Global Macro Dashboard": macro_dashboard,
        "Global Capital Markets": capital_markets,
        "Central Bank Rates": central_bank_rates,
        "Fiscal Scorecard": fiscal_scorecard,
        "Inflation & Growth": inflation_growth,
        "FX & Currencies": fx_currencies,
        "Global Yield Curves": yield_curves,
        "Bond Pricing & Calculator": bond_calculator,
        "Bond Portfolio": bond_portfolio,
        "Bond Investment Strategies": bond_investment_strategies,
        "Credit Spreads": credit_spreads,
        "Cross-Asset Dashboard": cross_asset,
        "Leading Indicators": leading_indicators,
        "Bond Simulator": bond_simulator,
        "Global Business Cycle": global_business_cycle,
        "Historical Shocks": historical_shocks,
        "Changelog": changelog_tab,
        "Data Sources": data_sources,
    }

    user_email = st.session_state["user_info"].get("email", "None")

    admins = [email.strip() for email in os.getenv("ADMINS", "").split(",")]
    if "admins" not in st.session_state:
        st.session_state["admins"] = admins

    restricted_apps = ["Changelog", "Data Sources"]
    visible_apps = {
        app_name: app_func
        for app_name, app_func in APP_MAP.items()
        if (app_name not in restricted_apps) or (user_email in admins)
    }

    if "selected_app" not in st.session_state:
        st.session_state["selected_app"] = "Home"

    nav_options = ["Home"] + list(visible_apps.keys())
    current_idx = nav_options.index(st.session_state["selected_app"]) if st.session_state["selected_app"] in nav_options else 0
    st.session_state["selected_app"] = st.sidebar.selectbox(
        "Navigate to", nav_options, index=current_idx
    )

    # Pre-warm data cache once per session — pays the Excel load cost here with
    # a spinner so sidebar controls are never frozen inside a tab function.
    if "data_warmed" not in st.session_state:
        with st.spinner("Loading market data..."):
            load_data()
        st.session_state["data_warmed"] = True

    if st.session_state["selected_app"] == "Home":
        home_page_cards(visible_apps)
    else:
        visible_apps[st.session_state["selected_app"]]()

    st.sidebar.markdown('<hr style="border:none;border-top:1px solid #475569;margin:1rem 0 0.5rem">', unsafe_allow_html=True)
    if st.sidebar.button("Logout", key="button1", use_container_width=True):
        authenticator.logout()
