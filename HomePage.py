import streamlit as st

_CARDS = [
    ("Bond Analytics",           "📊", "Bond spreads, flies and custom formula graphs. Your core fixed-income workbench."),
    ("Global Macro Dashboard",   "🌍", "IMF macro indicators — GDP, inflation, debt and current account across 16 countries."),
    ("Central Bank Rates",       "🏦", "Policy rate history with 10Y yield overlay. Track the rate cycle across major central banks."),
    ("Fiscal Scorecard",         "📋", "Government deficits, debt-to-GDP and fiscal trajectory for DM and EM economies."),
    ("Inflation & Growth",       "📈", "CPI and GDP growth trends side by side. See where each economy sits in the cycle."),
    ("FX & Currencies",          "💱", "Spot rates, REER and carry-trade differentials across major currency pairs."),
    ("Global Yield Curves",      "〰️", "Sovereign yield curves for G10 markets. Compare shapes and spot inversions instantly."),
    ("Bond Pricing & Calculator","🧮", "Price bonds, compute duration, DV01 and yield — all inputs update live."),
    ("Bond Portfolio",           "💼", "Build and stress-test a bond portfolio with P&L, DV01 hedging and short positions."),
    ("Bond Investment Strategies","📐", "Construct and compare Ladder, Bullet and Barbell strategies with rate shock simulation."),
    ("Credit Spreads",           "📉", "IG to CCC OAS spreads over time — credit risk spectrum, IG vs HY dynamics, recession context."),
    ("Cross-Asset Dashboard",    "📡", "VIX, Gold, Oil, S&P 500 and bond yields — normalized performance and correlation matrix."),
    ("Leading Indicators",       "🔭", "ISM PMI, jobless claims, housing starts, consumer sentiment — recession tracker with NBER shading."),
    ("Bond Simulator",           "🎯", "Interactive price-yield curve, duration vs convexity approximation, and rate shock analysis."),
    ("Global Business Cycle",    "🌐", "OECD BCI, CCI and CLI across 30 countries — latest snapshot, trend heatmap, country deep-dive."),
    ("Correlation Matrix",       "🔥", "Rolling cross-asset correlations. Spot diversification breakdowns and regime shifts."),
    ("Portfolio Rebalance",      "⚖️", "Optimise portfolio weights toward target allocations with rebalancing constraints."),
    ("Global Capital Markets",   "🏛️", "Capital markets overview — issuance, spreads and financing conditions."),
]

# Scoped with :has so styles only apply when home page is active
_HOME_CSS = """
<style>
/* Card wrapper: consistent border + hover glow */
body:has(#home-page-root) [data-testid="stVerticalBlockBorderWrapper"] {
    display: flex;
    flex-direction: column;
    border-radius: 8px !important;
    transition: border-color 0.15s ease, box-shadow 0.15s ease;
}
body:has(#home-page-root) [data-testid="stVerticalBlockBorderWrapper"]:hover {
    border-color: #60a5fa !important;
    box-shadow: 0 0 0 1px #60a5fa22 !important;
}

/* Inner content div — uniform padding on ALL sides */
body:has(#home-page-root) [data-testid="stVerticalBlockBorderWrapper"] > div:first-child {
    flex: 1 !important;
    display: flex !important;
    flex-direction: column !important;
    justify-content: flex-start !important;
    padding: 0.6rem 0.8rem 0.6rem !important;
    gap: 0.15rem !important;
    box-sizing: border-box !important;
}

/* Card title */
body:has(#home-page-root) [data-testid="stVerticalBlockBorderWrapper"] [data-testid="stMarkdownContainer"] p {
    font-size: 0.84rem !important;
    margin: 0 0 0.15rem !important;
    line-height: 1.3 !important;
}

/* Card description */
body:has(#home-page-root) [data-testid="stVerticalBlockBorderWrapper"] [data-testid="stCaptionContainer"] p {
    font-size: 0.72rem !important;
    line-height: 1.4 !important;
    margin: 0 !important;
}

/* Open button — full width within the padded content area */
body:has(#home-page-root) [data-testid="stVerticalBlockBorderWrapper"] .stButton {
    width: 100% !important;
    margin-top: 0.35rem !important;
}
body:has(#home-page-root) [data-testid="stVerticalBlockBorderWrapper"] .stButton > button {
    width: 100% !important;
    height: 1.8rem !important;
    min-height: unset !important;
    font-size: 0.75rem !important;
    padding: 0 0.5rem !important;
    margin: 0 !important;
}

/* Tighter column gaps */
body:has(#home-page-root) [data-testid="stHorizontalBlock"] {
    gap: 0.5rem !important;
}

/* Reduce vertical gap between card rows */
body:has(#home-page-root) [data-testid="stHorizontalBlock"] + [data-testid="stHorizontalBlock"] {
    margin-top: -0.6rem !important;
}
</style>
<div id="home-page-root"></div>
"""


def _render_card(col, app_name: str, emoji: str, desc: str):
    with col:
        with st.container(border=True):
            st.markdown(f"**{emoji} &nbsp;{app_name}**")
            st.caption(desc)
            if st.button("Open →", key=f"card_{app_name}"):
                st.session_state["selected_app"] = app_name
                st.rerun()


def home_page_cards(visible_apps: dict):
    st.markdown(_HOME_CSS, unsafe_allow_html=True)

    user_info = st.session_state.get("user_info", {})
    parts = (user_info.get("name", "") or "").split()
    first_name = parts[0] if parts else ""
    greeting = f"👋 Welcome back, **{first_name}**" if first_name else "👋 Welcome"

    st.markdown(
        f"<p style='font-size:0.95rem;margin:0 0 0.5rem'>{greeting}"
        f" &nbsp;·&nbsp; <span style='color:#94a3b8;font-weight:400'>"
        f"select a module to get started</span></p>",
        unsafe_allow_html=True,
    )

    # Build list of visible cards in defined order
    visible = [(n, e, d) for n, e, d in _CARDS if n in visible_apps]

    for i in range(0, len(visible), 4):
        row = visible[i:i + 4]
        n = len(row)
        if n == 4:
            cols = st.columns(4, gap="small")
            for j, (name, emoji, desc) in enumerate(row):
                _render_card(cols[j], name, emoji, desc)
        else:
            # Partial last row: center the cards
            pad = (4 - n) / 2
            col_widths = [pad] + [1.0] * n + [pad]
            cols = st.columns(col_widths, gap="small")
            for j, (name, emoji, desc) in enumerate(row):
                _render_card(cols[j + 1], name, emoji, desc)
