"""
Global Capital Markets Dashboard
Teaches: equity vs bond markets, market size vs GDP, historical evolution,
         country financing models, interesting ratios.
"""
from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import streamlit as st

from datetime import datetime

from capital_markets_data import (
    load_capital_markets_data, refresh_capital_markets_data,
    CACHE_FILE, COUNTRY_COLORS, FINANCING_MODEL, YEARS
)

# ── Visual constants ───────────────────────────────────────────────────────────

_BG   = "#0f172a"
_CARD = "#1e293b"
_EDGE = "#334155"
_T1   = "#f1f5f9"
_T2   = "#94a3b8"
_T3   = "#475569"
_BLUE = "#3b82f6"
_GRN  = "#10b981"
_RED  = "#ef4444"
_AMB  = "#fbbf24"
_PRP  = "#a78bfa"

_EQ_COLOR  = "#3b82f6"   # equity — blue
_GB_COLOR  = "#10b981"   # govt bonds — green


# ── Helpers ────────────────────────────────────────────────────────────────────

def _chart_base(**kw) -> dict:
    base = dict(
        template="plotly_dark",
        paper_bgcolor=_CARD, plot_bgcolor=_BG,
        font=dict(color=_T1, size=12),
        margin=dict(l=64, r=20, t=44, b=44),
        xaxis=dict(gridcolor=_EDGE, tickfont=dict(color=_T2),
                   showline=True, linecolor=_EDGE),
        yaxis=dict(gridcolor=_EDGE, tickfont=dict(color=_T2),
                   showline=True, linecolor=_EDGE),
        hoverlabel=dict(bgcolor=_CARD, font_color=_T1, bordercolor=_EDGE),
        legend=dict(font=dict(color=_T1, size=11), bgcolor="rgba(0,0,0,0)"),
    )
    base.update(kw)
    return base


def _section(title: str, subtitle: str = "") -> None:
    sub_html = (
        f'<div style="font-size:12px;color:{_T2};margin-top:4px;">{subtitle}</div>'
        if subtitle else ""
    )
    st.markdown(
        f'<div style="background:{_CARD};border-left:4px solid {_BLUE};'
        f'padding:10px 16px;margin:28px 0 10px;border-radius:0 8px 8px 0;">'
        f'<span style="font-size:13px;font-weight:700;color:{_T1};'
        f'text-transform:uppercase;letter-spacing:.08em;">{title}</span>{sub_html}</div>',
        unsafe_allow_html=True,
    )


def _metric_card(label: str, value: str, sub: str = "", accent: str = _BLUE) -> str:
    return (
        f'<div style="background:{_CARD};border:1px solid {_EDGE};'
        f'border-left:3px solid {accent};border-radius:8px;padding:14px 12px;">'
        f'<div style="font-size:10px;color:{_T2};text-transform:uppercase;'
        f'letter-spacing:.1em;margin-bottom:5px;">{label}</div>'
        f'<div style="font-size:20px;font-weight:700;color:{_T1};">{value}</div>'
        f'<div style="font-size:10px;color:{_T2};margin-top:3px;">{sub}</div>'
        f'</div>'
    )


def _fmt_t(val: float) -> str:
    """Format a USD trillion value."""
    if pd.isna(val):
        return "N/A"
    if val >= 1:
        return f"${val:.2f}T"
    return f"${val*1000:.0f}B"


def _country_colors(countries: list[str]) -> list[str]:
    return [COUNTRY_COLORS.get(c, "#94a3b8") for c in countries]


# ── Section renderers ─────────────────────────────────────────────────────────

def _section1_snapshot(yr_df: pd.DataFrame, year: int) -> None:
    _section("Global Snapshot", f"Latest data — {year}")

    valid = yr_df.dropna(subset=["Equity_USD", "GovtBond_USD", "GDP_USD"])
    total_eq  = valid["Equity_USD"].sum()
    total_gb  = valid["GovtBond_USD"].sum()
    total_cap = total_eq + total_gb
    total_gdp = valid["GDP_USD"].sum()
    n         = len(valid)

    cards = [
        ("Global Equity Markets",  _fmt_t(total_eq),  f"{n} countries",         _EQ_COLOR),
        ("Global Govt Bond Mkts",  _fmt_t(total_gb),  "Gross govt debt proxy",  _GB_COLOR),
        ("Total Capital Markets",  _fmt_t(total_cap), "Equity + Govt Bonds",    _PRP),
        ("Combined GDP",           _fmt_t(total_gdp), f"{n} countries",         _AMB),
        ("Avg Equity/GDP",         f"{(valid['Equity_GDP_Pct'].mean()):.0f}%",
         "Market capitalisation",                                                _EQ_COLOR),
        ("Avg Govt Bond/GDP",      f"{(valid['GovtBond_GDP_Pct'].mean()):.0f}%",
         "Gross govt debt",                                                      _GB_COLOR),
    ]
    html = '<div style="display:grid;grid-template-columns:repeat(3,1fr);gap:10px;">'
    for lbl, val, sub, acc in cards:
        html += _metric_card(lbl, val, sub, acc)
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)


def _section2_market_size(yr_df: pd.DataFrame, year: int) -> None:
    _section("Market Size Comparison",
             "Equity market capitalisation vs government bond market outstanding")

    df = yr_df.dropna(subset=["Equity_USD"]).sort_values("Total_Cap_USD", ascending=True)

    fig = go.Figure()
    fig.add_trace(go.Bar(
        name="Equity Market Cap", y=df["Country"], x=df["Equity_USD"],
        orientation="h", marker_color=_EQ_COLOR,
        hovertemplate="<b>%{y}</b><br>Equity: $%{x:.2f}T<extra></extra>",
    ))
    fig.add_trace(go.Bar(
        name="Govt Bond Market", y=df["Country"], x=df["GovtBond_USD"],
        orientation="h", marker_color=_GB_COLOR,
        hovertemplate="<b>%{y}</b><br>Govt Bonds: $%{x:.2f}T<extra></extra>",
    ))
    fig.update_layout(
        barmode="stack", height=420,
        title=dict(text=f"Capital Market Size by Country ({year})",
                   font=dict(size=13, color=_T1), x=0),
        xaxis_title="USD Trillions",
        **_chart_base(margin=dict(l=140, r=20, t=44, b=44)),
    )
    st.plotly_chart(fig, use_container_width=True)


def _section3_scatter(yr_df: pd.DataFrame, year: int) -> None:
    _section("Equity vs Bond Markets",
             "X = equity market cap · Y = govt bond market · bubble = GDP")

    df = yr_df.dropna(subset=["Equity_USD", "GovtBond_USD", "GDP_USD"])
    max_gdp = df["GDP_USD"].max()

    fig = go.Figure()
    for _, row in df.iterrows():
        fig.add_trace(go.Scatter(
            x=[row["Equity_USD"]], y=[row["GovtBond_USD"]],
            mode="markers+text",
            name=row["Country"],
            text=[row["Country"]],
            textposition="top center",
            textfont=dict(size=10, color=_T1),
            marker=dict(
                color=COUNTRY_COLORS.get(row["Country"], "#888"),
                size=max(8, row["GDP_USD"] / max_gdp * 60),
                opacity=0.85,
                line=dict(width=1.5, color=_BG),
            ),
            hovertemplate=(
                f"<b>{row['Country']}</b><br>"
                f"Equity: ${row['Equity_USD']:.2f}T<br>"
                f"Govt Bonds: ${row['GovtBond_USD']:.2f}T<br>"
                f"GDP: ${row['GDP_USD']:.2f}T<extra></extra>"
            ),
            showlegend=False,
        ))

    # 45° line (equal equity/bond)
    mx = max(df["Equity_USD"].max(), df["GovtBond_USD"].max()) * 1.05
    fig.add_trace(go.Scatter(
        x=[0, mx], y=[0, mx], mode="lines",
        line=dict(color=_T3, dash="dot", width=1),
        showlegend=True, name="Equal (Equity = Bonds)",
    ))
    fig.update_layout(
        height=480,
        title=dict(text=f"Equity vs Govt Bond Markets ({year}) — bubble ∝ GDP",
                   font=dict(size=13, color=_T1), x=0),
        xaxis_title="Equity Market Cap (USD T)",
        yaxis_title="Govt Bond Market (USD T)",
        **_chart_base(),
    )
    st.plotly_chart(fig, use_container_width=True)

    st.markdown(
        f'<div style="font-size:12px;color:{_T2};margin-top:-8px;padding:0 4px;">'
        f'Countries <b>above</b> the dotted line have larger bond markets than equity markets — '
        f'Japan is the signature case. Countries <b>below</b> are equity-dominant (USA, India).</div>',
        unsafe_allow_html=True,
    )


def _section4_equity_gdp(yr_df: pd.DataFrame, year: int) -> None:
    _section("Equity Market Cap / GDP",
             "How large is the stock market relative to the economy?")

    df = yr_df.dropna(subset=["Equity_GDP_Pct"]).sort_values("Equity_GDP_Pct")
    fig = go.Figure(go.Bar(
        x=df["Equity_GDP_Pct"], y=df["Country"],
        orientation="h",
        marker_color=_country_colors(df["Country"].tolist()),
        hovertemplate="<b>%{y}</b><br>Equity/GDP: %{x:.0f}%<extra></extra>",
    ))
    fig.add_vline(x=100, line=dict(color=_T3, dash="dot", width=1))
    fig.update_layout(
        height=360, showlegend=False,
        title=dict(text=f"Equity Market Cap / GDP ({year})",
                   font=dict(size=13, color=_T1), x=0),
        xaxis_title="Equity Market Cap as % of GDP",
        **_chart_base(margin=dict(l=140, r=20, t=44, b=44)),
    )
    st.plotly_chart(fig, use_container_width=True)


def _section5_govtbond_gdp(yr_df: pd.DataFrame, year: int) -> None:
    _section("Government Bond Market / GDP",
             "Japan's government bond market is larger than its entire annual GDP — twice over")

    df = yr_df.dropna(subset=["GovtBond_GDP_Pct"]).sort_values("GovtBond_GDP_Pct")
    fig = go.Figure(go.Bar(
        x=df["GovtBond_GDP_Pct"], y=df["Country"],
        orientation="h",
        marker_color=_country_colors(df["Country"].tolist()),
        hovertemplate="<b>%{y}</b><br>Govt Bond/GDP: %{x:.0f}%<extra></extra>",
    ))
    fig.add_vline(x=100, line=dict(color=_AMB, dash="dot", width=1.5),
                  annotation_text="100% of GDP", annotation_font_color=_AMB)
    fig.update_layout(
        height=360, showlegend=False,
        title=dict(text=f"Govt Bond Market / GDP ({year})",
                   font=dict(size=13, color=_T1), x=0),
        xaxis_title="Govt Bond Outstanding as % of GDP",
        **_chart_base(margin=dict(l=140, r=20, t=44, b=44)),
    )
    st.plotly_chart(fig, use_container_width=True)


def _section6_total_ranking(yr_df: pd.DataFrame, year: int) -> None:
    _section("Total Capital Market Ranking",
             "Equity + Government Bonds — who has the largest combined market?")

    df = yr_df.dropna(subset=["Total_Cap_USD"]).sort_values("Total_Cap_USD")
    fig = go.Figure()
    fig.add_trace(go.Bar(
        name="Equity", y=df["Country"], x=df["Equity_USD"],
        orientation="h", marker_color=_EQ_COLOR,
        hovertemplate="<b>%{y}</b><br>Equity: $%{x:.2f}T<extra></extra>",
    ))
    fig.add_trace(go.Bar(
        name="Govt Bonds", y=df["Country"], x=df["GovtBond_USD"],
        orientation="h", marker_color=_GB_COLOR,
        hovertemplate="<b>%{y}</b><br>Bonds: $%{x:.2f}T<extra></extra>",
    ))
    fig.update_layout(
        barmode="stack", height=380,
        title=dict(text=f"Total Capital Market Size — Ranked ({year})",
                   font=dict(size=13, color=_T1), x=0),
        xaxis_title="USD Trillions",
        **_chart_base(margin=dict(l=140, r=20, t=44, b=44)),
    )
    st.plotly_chart(fig, use_container_width=True)


def _section7_historical(full_df: pd.DataFrame) -> None:
    _section("Historical Evolution",
             "Use the Year slider in the sidebar to step through time — or explore the time series below")

    c1, c2 = st.columns(2)

    # Equity over time
    with c1:
        fig = go.Figure()
        for country in full_df["Country"].unique():
            cdf = full_df[full_df["Country"] == country].dropna(subset=["Equity_USD"])
            if cdf.empty:
                continue
            fig.add_trace(go.Scatter(
                x=cdf["Year"], y=cdf["Equity_USD"],
                name=country,
                mode="lines",
                line=dict(color=COUNTRY_COLORS.get(country, "#888"), width=2),
                hovertemplate=f"<b>{country}</b><br>%{{x}}: $%{{y:.2f}}T<extra></extra>",
            ))
        fig.update_layout(
            height=360,
            title=dict(text="Equity Market Cap — 2005 to 2023",
                       font=dict(size=13, color=_T1), x=0),
            yaxis_title="USD Trillions",
            **_chart_base(),
        )
        st.plotly_chart(fig, use_container_width=True)

    # Govt bonds over time
    with c2:
        fig = go.Figure()
        for country in full_df["Country"].unique():
            cdf = full_df[full_df["Country"] == country].dropna(subset=["GovtBond_USD"])
            if cdf.empty:
                continue
            fig.add_trace(go.Scatter(
                x=cdf["Year"], y=cdf["GovtBond_USD"],
                name=country,
                mode="lines",
                line=dict(color=COUNTRY_COLORS.get(country, "#888"), width=2),
                hovertemplate=f"<b>{country}</b><br>%{{x}}: $%{{y:.2f}}T<extra></extra>",
            ))
        fig.update_layout(
            height=360,
            title=dict(text="Govt Bond Market — 2005 to 2023",
                       font=dict(size=13, color=_T1), x=0),
            yaxis_title="USD Trillions",
            **_chart_base(),
        )
        st.plotly_chart(fig, use_container_width=True)

    # Total capital markets over time (full width)
    fig = go.Figure()
    for country in full_df["Country"].unique():
        cdf = full_df[full_df["Country"] == country].dropna(subset=["Total_Cap_USD"])
        if cdf.empty:
            continue
        fig.add_trace(go.Scatter(
            x=cdf["Year"], y=cdf["Total_Cap_USD"],
            name=country,
            mode="lines",
            line=dict(color=COUNTRY_COLORS.get(country, "#888"), width=2.5),
            hovertemplate=f"<b>{country}</b><br>%{{x}}: $%{{y:.2f}}T<extra></extra>",
        ))
    fig.update_layout(
        height=380,
        title=dict(text="Total Capital Markets (Equity + Govt Bonds) — 2005 to 2023",
                   font=dict(size=13, color=_T1), x=0),
        yaxis_title="USD Trillions",
        **_chart_base(),
    )
    st.plotly_chart(fig, use_container_width=True)


def _section8_ratios(yr_df: pd.DataFrame, year: int) -> None:
    _section("Interesting Ratios",
             "The Bond/Equity ratio tells you a country's financing model at a glance")

    df = yr_df.dropna(subset=["Bond_Equity_Ratio"]).sort_values("Bond_Equity_Ratio")

    c1, c2 = st.columns(2)

    # Bond/Equity ratio
    with c1:
        fig = go.Figure(go.Bar(
            x=df["Bond_Equity_Ratio"], y=df["Country"],
            orientation="h",
            marker_color=_country_colors(df["Country"].tolist()),
            hovertemplate="<b>%{y}</b><br>Bond/Equity: %{x:.2f}×<extra></extra>",
        ))
        fig.add_vline(x=1, line=dict(color=_AMB, dash="dot", width=1.5),
                      annotation_text="Bond = Equity", annotation_font_color=_AMB)
        fig.update_layout(
            height=340, showlegend=False,
            title=dict(text=f"Govt Bond / Equity Ratio ({year})",
                       font=dict(size=13, color=_T1), x=0),
            xaxis_title="Govt Bond Market ÷ Equity Market",
            **_chart_base(margin=dict(l=140, r=20, t=44, b=44)),
        )
        st.plotly_chart(fig, use_container_width=True)

    # Bubble: GDP vs Total Capital Market
    with c2:
        df2 = yr_df.dropna(subset=["GDP_USD", "Total_Cap_USD", "Population"])
        max_pop = df2["Population"].max()
        fig = go.Figure()
        for _, row in df2.iterrows():
            fig.add_trace(go.Scatter(
                x=[row["GDP_USD"]], y=[row["Total_Cap_USD"]],
                mode="markers+text",
                name=row["Country"],
                text=[row["Country"]],
                textposition="top center",
                textfont=dict(size=9, color=_T1),
                marker=dict(
                    color=COUNTRY_COLORS.get(row["Country"], "#888"),
                    size=max(8, row["Population"] / max_pop * 50),
                    opacity=0.85,
                    line=dict(width=1.5, color=_BG),
                ),
                showlegend=False,
                hovertemplate=(
                    f"<b>{row['Country']}</b><br>"
                    f"GDP: ${row['GDP_USD']:.2f}T<br>"
                    f"Total Capital: ${row['Total_Cap_USD']:.2f}T<br>"
                    f"Pop: {row['Population']/1e6:.0f}M<extra></extra>"
                ),
            ))
        # 45° line (capital market = GDP)
        mx = max(df2["GDP_USD"].max(), df2["Total_Cap_USD"].max()) * 1.05
        fig.add_trace(go.Scatter(
            x=[0, mx], y=[0, mx], mode="lines",
            line=dict(color=_T3, dash="dot", width=1),
            showlegend=False,
        ))
        fig.update_layout(
            height=340,
            title=dict(text=f"GDP vs Total Capital Market — bubble ∝ population ({year})",
                       font=dict(size=13, color=_T1), x=0),
            xaxis_title="GDP (USD T)",
            yaxis_title="Total Capital Market (USD T)",
            **_chart_base(),
        )
        st.plotly_chart(fig, use_container_width=True)


def _section9_dna(yr_df: pd.DataFrame, year: int) -> None:
    _section("Capital Markets DNA",
             "Each country's financial structure at a glance — how do they finance themselves?")

    rows = []
    for _, row in yr_df.sort_values("Total_Cap_USD", ascending=False).iterrows():
        rows.append({
            "Country":          row["Country"],
            "GDP ($T)":         f"{row['GDP_USD']:.2f}" if pd.notna(row["GDP_USD"]) else "—",
            "Equity ($T)":      f"{row['Equity_USD']:.2f}" if pd.notna(row["Equity_USD"]) else "—",
            "Govt Bonds ($T)":  f"{row['GovtBond_USD']:.2f}" if pd.notna(row["GovtBond_USD"]) else "—",
            "Equity/GDP":       f"{row['Equity_GDP_Pct']:.0f}%" if pd.notna(row["Equity_GDP_Pct"]) else "—",
            "Bond/GDP":         f"{row['GovtBond_GDP_Pct']:.0f}%" if pd.notna(row["GovtBond_GDP_Pct"]) else "—",
            "Bond/Equity":      f"{row['Bond_Equity_Ratio']:.2f}×" if pd.notna(row["Bond_Equity_Ratio"]) else "—",
            "Financing Model":  FINANCING_MODEL.get(row["Country"], "—"),
        })
    dna_df = pd.DataFrame(rows)
    st.dataframe(dna_df, use_container_width=True, hide_index=True)



# ── Main entry point ──────────────────────────────────────────────────────────

def capital_markets() -> None:
    st.markdown(
        '<h2 style="color:#0f172a;margin:0 0 2px;">Global Capital Markets Dashboard</h2>'
        '<div style="font-size:12px;color:#475569;">'
        '10 countries · equity vs bond markets · market size vs GDP · '
        'historical evolution 2005–2023</div>'
        '<hr style="border:none;border-top:1px solid #e2e8f0;margin:10px 0 6px;">',
        unsafe_allow_html=True,
    )

    # ── Sidebar ───────────────────────────────────────────────────────────────
    st.sidebar.markdown(
        f'<div style="font-size:10px;color:{_T2};text-transform:uppercase;'
        f'letter-spacing:.1em;margin:16px 0 8px;padding-bottom:4px;'
        f'border-bottom:1px solid {_EDGE};">Year</div>',
        unsafe_allow_html=True,
    )
    year = st.sidebar.slider(
        "Year", min_value=2005, max_value=2023, value=2023, step=1,
        key="cm_year", label_visibility="collapsed",
    )

    st.sidebar.markdown(
        f'<div style="font-size:10px;color:{_T2};text-transform:uppercase;'
        f'letter-spacing:.1em;margin:12px 0 6px;padding-bottom:4px;'
        f'border-bottom:1px solid {_EDGE};">Sections</div>',
        unsafe_allow_html=True,
    )
    show = {
        "snapshot":   st.sidebar.checkbox("Global Snapshot",          value=True, key="cm_s1"),
        "size":       st.sidebar.checkbox("Market Size Comparison",   value=True, key="cm_s2"),
        "scatter":    st.sidebar.checkbox("Equity vs Bond Scatter",   value=True, key="cm_s3"),
        "eq_gdp":     st.sidebar.checkbox("Equity/GDP",               value=True, key="cm_s4"),
        "gb_gdp":     st.sidebar.checkbox("Govt Bond/GDP",            value=True, key="cm_s5"),
        "ranking":    st.sidebar.checkbox("Total Market Ranking",     value=True, key="cm_s6"),
        "history":    st.sidebar.checkbox("Historical Evolution",     value=True, key="cm_s7"),
        "ratios":     st.sidebar.checkbox("Interesting Ratios",       value=True, key="cm_s8"),
        "dna":        st.sidebar.checkbox("Capital Markets DNA",      value=True, key="cm_s9"),
    }

    # ── Data freshness + refresh ──────────────────────────────────────────────
    st.sidebar.markdown(
        f'<div style="font-size:10px;color:{_T2};text-transform:uppercase;'
        f'letter-spacing:.1em;margin:16px 0 6px;padding-bottom:4px;'
        f'border-bottom:1px solid {_EDGE};">Data</div>',
        unsafe_allow_html=True,
    )
    if CACHE_FILE.exists():
        mtime = datetime.fromtimestamp(CACHE_FILE.stat().st_mtime)
        st.sidebar.caption(f"Last refreshed: {mtime.strftime('%d %b %Y, %H:%M')}")
    else:
        st.sidebar.caption("No local cache — will fetch from APIs")

    refresh_clicked = st.sidebar.button("Refresh Data", key="cm_refresh")

    # ── Load data ─────────────────────────────────────────────────────────────
    # If refresh was clicked: show current data immediately (fast from cache),
    # then fetch new data in the background and swap in when ready.
    if refresh_clicked:
        full_df = load_capital_markets_data()   # serve stale data while we fetch
        refresh_banner = st.info(
            "Refreshing data from World Bank & IMF — current data shown below…",
            icon="🔄",
        )
        yr_df = full_df[full_df["Year"] == year].copy()
    else:
        full_df = load_capital_markets_data()
        if full_df.empty:
            st.error("Failed to load data. Please try again later.")
            return
        yr_df = full_df[full_df["Year"] == year].copy()

    # ── Sections ──────────────────────────────────────────────────────────────
    if show["snapshot"]:
        _section1_snapshot(yr_df, year)

    if show["size"]:
        _section2_market_size(yr_df, year)

    if show["scatter"]:
        _section3_scatter(yr_df, year)

    c1, c2 = st.columns(2)
    with c1:
        if show["eq_gdp"]:
            _section4_equity_gdp(yr_df, year)
    with c2:
        if show["gb_gdp"]:
            _section5_govtbond_gdp(yr_df, year)

    if show["ranking"]:
        _section6_total_ranking(yr_df, year)

    if show["history"]:
        _section7_historical(full_df)

    if show["ratios"]:
        _section8_ratios(yr_df, year)

    if show["dna"]:
        _section9_dna(yr_df, year)
        st.markdown(
            "**Market-based** (USA, UK, Canada, Australia): companies raise money primarily through equity and bond markets.  \n"
            "**Bank-based** (Germany): companies rely heavily on bank loans; listed equity market is relatively small.  \n"
            "**Government debt-heavy** (Japan): the govt bond market dwarfs everything else; bond/equity > 2×.  \n"
            "**State-led** (China): large markets but government-directed; rapid growth from a low base in 2005.  \n"
            "**Mixed / developing** (India, Brazil): growing equity markets, high govt debt, capital markets deepening over time."
        )

    # Footer note
    st.markdown(
        f'<div style="font-size:11px;color:#ffffff;margin-top:24px;padding:12px;'
        f'background:{_CARD};border-radius:6px;border:1px solid {_EDGE};">'
        f'<b>Data sources:</b> Equity market capitalisation — World Bank (CM.MKT.LCAP.CD). '
        f'Government bond market size — IMF Gross Government Debt (% GDP) × GDP (USD). '
        f'This is a good proxy for traded government bonds outstanding; '
        f'it includes all forms of central government obligations. '
        f'Corporate bond data (BIS Debt Securities Statistics) is not yet integrated — '
        f'the BIS SDMX API is inaccessible from this environment; '
        f'it will be added when an alternative feed is identified. '
        f'GDP data — IMF World Economic Outlook.</div>',
        unsafe_allow_html=True,
    )

    # ── Execute deferred refresh after page has rendered ─────────────────────
    if refresh_clicked:
        with st.spinner("Fetching fresh data from World Bank & IMF…"):
            refresh_capital_markets_data()
        refresh_banner.empty()
        st.rerun()
