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
    ("Correlation Matrix",       "🔥", "Rolling cross-asset correlations. Spot diversification breakdowns and regime shifts."),
    ("Portfolio Rebalance",      "⚖️", "Optimise portfolio weights toward target allocations with rebalancing constraints."),
    ("News Summarizer",          "📰", "AI-summarised financial news filtered by theme. Stay on top of market narratives."),
    ("Global Capital Markets",   "🏛️", "Capital markets overview — issuance, spreads and financing conditions."),
]


def home_page_cards(visible_apps: dict):
    user_info = st.session_state.get("user_info", {})
    first_name = (user_info.get("name", "") or "").split()[0]
    greeting = f"Welcome back, {first_name}!" if first_name else "Welcome!"

    st.markdown(f"## {greeting}")
    st.caption("Select a module below or use the sidebar to navigate.")
    st.divider()

    cols = st.columns(3, gap="medium")
    col_idx = 0
    for app_name, emoji, desc in _CARDS:
        if app_name not in visible_apps:
            continue
        with cols[col_idx % 3]:
            with st.container(border=True):
                st.markdown(f"**{emoji} &nbsp; {app_name}**")
                st.caption(desc)
                if st.button("Open →", key=f"card_{app_name}", use_container_width=True):
                    st.session_state["selected_app"] = app_name
                    st.rerun()
        col_idx += 1
