"""
Inflation & Growth Dashboard
Source: IMF WEO — CPI inflation, real GDP growth, unemployment.
Shows stagflation quadrant, Phillips curve, and country comparisons.
"""
from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from global_macro_data import (
    COUNTRY_COLORS, CORE_NAMES, ALL_NAMES,
    ANNUAL_CACHE, BREAKEVEN_CACHE,
    load_annual, refresh_annual,
    load_breakeven, refresh_breakeven,
)

_BG   = "#0f172a"
_CARD = "#1e293b"
_EDGE = "#334155"
_T1   = "#f1f5f9"
_T2   = "#94a3b8"
_T3   = "#475569"
_BLUE = "#3b82f6"
_GRN  = "#10b981"
_RED  = "#ef4444"
_AMB  = "#f59e0b"


def _section(title: str, subtitle: str = "") -> None:
    sub = (
        f'<div style="font-size:12px;color:{_T2};margin-top:4px;">{subtitle}</div>'
        if subtitle else ""
    )
    st.markdown(
        f'<div style="background:{_CARD};border-left:4px solid {_BLUE};'
        f'padding:10px 16px;margin:28px 0 10px;border-radius:0 8px 8px 0;">'
        f'<span style="font-size:13px;font-weight:700;color:{_T1};'
        f'text-transform:uppercase;letter-spacing:.08em;">{title}</span>{sub}</div>',
        unsafe_allow_html=True,
    )


def _chart_layout(**kw) -> dict:
    base = dict(
        template="plotly_dark",
        paper_bgcolor=_CARD, plot_bgcolor=_BG,
        margin=dict(l=62, r=20, t=44, b=44),
        font=dict(color=_T1, size=12),
        xaxis=dict(gridcolor=_EDGE, tickfont=dict(color=_T2),
                   showline=True, linecolor=_EDGE),
        yaxis=dict(gridcolor=_EDGE, tickfont=dict(color=_T2),
                   showline=True, linecolor=_EDGE),
        hoverlabel=dict(bgcolor=_CARD, font_color=_T1, bordercolor=_EDGE),
        legend=dict(font=dict(color=_T1, size=11), bgcolor="rgba(0,0,0,0)",
                    orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    base.update(kw)
    return base


def _no_data(msg: str = "No data — click Refresh Data.") -> None:
    st.info(msg, icon="ℹ️")


# ── Snapshot ──────────────────────────────────────────────────────────────────

def _snapshot(df: pd.DataFrame, countries: list[str], year: int) -> None:
    _section("Macro Snapshot", f"Cross-country averages for selected countries · {year}")

    snap = df[(df["Year"] == year) & (df["Country"].isin(countries))].copy()
    if snap.empty:
        _no_data()
        return

    def _avg(col: str, fmt: str = ".1f") -> str:
        if col not in snap.columns:
            return "—"
        v = snap[col].mean()
        return (f"{v:{fmt}}%") if pd.notna(v) else "—"

    html = '<div style="display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin-bottom:20px;">'
    for lbl, val, sub, acc in [
        ("Avg CPI Inflation",  _avg("CPI_Pct"),         "year-on-year %",       _RED),
        ("Avg Real GDP Growth",_avg("RealGDP_Pct"),      "constant prices",      _GRN),
        ("Avg Unemployment",   _avg("Unemployment_Pct"), "% of labour force",    _AMB),
        ("Countries Surveyed", str(len(snap)),           f"of {len(countries)} selected", _BLUE),
    ]:
        html += (
            f'<div style="background:{_CARD};border:1px solid {_EDGE};border-radius:8px;'
            f'padding:14px 10px;text-align:center;">'
            f'<div style="font-size:10px;color:{_T2};text-transform:uppercase;'
            f'letter-spacing:.1em;margin-bottom:6px;">{lbl}</div>'
            f'<div style="font-size:22px;font-weight:700;color:{acc};">{val}</div>'
            f'<div style="font-size:11px;color:{_T3};margin-top:4px;">{sub}</div></div>'
        )
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)


# ── Stagflation quadrant ───────────────────────────────────────────────────────

def _stagflation(df: pd.DataFrame, countries: list[str], year: int) -> None:
    _section(
        "Stagflation Quadrant",
        "Each dot = one country · x = real GDP growth · y = CPI inflation · "
        "top-left = stagflation · bottom-right = goldilocks",
    )

    need = ["CPI_Pct", "RealGDP_Pct"]
    fdf  = df[df["Country"].isin(countries)].dropna(subset=need)
    if fdf.empty:
        _no_data()
        return

    snap = fdf[fdf["Year"] == year]

    c1, c2 = st.columns(2)

    for col, title, data in [
        (c1, f"Single Year — {year}", snap),
        (c2, "All Years (animated)", fdf),
    ]:
        with col:
            if data.empty:
                _no_data()
                continue
            fig = go.Figure()
            for country in countries:
                cdf = data[data["Country"] == country]
                if cdf.empty:
                    continue
                clr = COUNTRY_COLORS.get(country, "#888")
                fig.add_trace(go.Scatter(
                    x=cdf["RealGDP_Pct"], y=cdf["CPI_Pct"],
                    mode="markers+text" if len(cdf) == 1 else "markers",
                    name=country,
                    text=cdf["Country"] if len(cdf) == 1 else cdf["Year"].astype(str),
                    textposition="top center",
                    textfont=dict(size=9, color=_T1),
                    marker=dict(color=clr, size=9, opacity=0.85,
                                line=dict(width=1, color=_BG)),
                    hovertemplate=(
                        f"<b>{country}</b><br>"
                        "GDP Growth: %{x:.1f}%<br>"
                        "CPI: %{y:.1f}%<br>"
                        "Year: %{text}<extra></extra>"
                    ) if len(cdf) > 1 else (
                        f"<b>{country}</b><br>"
                        "GDP Growth: %{x:.1f}%<br>"
                        f"CPI: %{{y:.1f}}%<extra></extra>"
                    ),
                ))
            fig.add_vline(x=0, line=dict(color=_T3, dash="dot", width=1))
            fig.add_hline(y=2, line=dict(color=_T3, dash="dot", width=1),
                          annotation_text="2% target", annotation_font_color=_T3)
            # Quadrant labels
            fig.add_annotation(text="Stagflation", x=0.02, y=0.98, xref="paper", yref="paper",
                                showarrow=False, font=dict(color=_RED, size=10))
            fig.add_annotation(text="Goldilocks", x=0.98, y=0.02, xref="paper", yref="paper",
                                showarrow=False, font=dict(color=_GRN, size=10),
                                xanchor="right")
            fig.update_layout(
                height=360,
                title=dict(text=title, font=dict(size=13, color=_T1), x=0),
                xaxis_title="Real GDP Growth (%)  →",
                yaxis_title="CPI Inflation (%)  ↑",
                **_chart_layout(),
            )
            st.plotly_chart(fig, use_container_width=True)

    st.markdown(
        "**Top-left (high inflation + low/negative growth):** stagflation — hardest environment for central banks.  \n"
        "**Bottom-right (strong growth + low inflation):** goldilocks — ideal macro backdrop."
    )


# ── CPI time series ───────────────────────────────────────────────────────────

def _cpi_series(df: pd.DataFrame, countries: list[str], yr_from: int) -> None:
    _section("CPI Inflation", "Year-on-year consumer price inflation (%)")

    fdf = df[df["Country"].isin(countries) & (df["Year"] >= yr_from)].dropna(subset=["CPI_Pct"])
    if fdf.empty:
        _no_data()
        return

    c1, c2 = st.columns([3, 2])

    with c1:
        fig = go.Figure()
        for country in countries:
            cdf = fdf[fdf["Country"] == country].sort_values("Year")
            if cdf.empty:
                continue
            fig.add_trace(go.Scatter(
                x=cdf["Year"], y=cdf["CPI_Pct"],
                name=country, mode="lines+markers",
                line=dict(color=COUNTRY_COLORS.get(country, "#888"), width=2),
                marker=dict(size=4),
                hovertemplate=f"<b>{country}</b><br>%{{x}}: %{{y:.1f}}%<extra></extra>",
            ))
        fig.add_hline(y=2, line=dict(color=_T3, dash="dot", width=1),
                      annotation_text="2% target", annotation_font_color=_T3)
        fig.update_layout(
            height=380,
            title=dict(text="CPI Inflation (% YoY)", font=dict(size=13, color=_T1), x=0),
            yaxis_title="Inflation %",
            **_chart_layout(),
        )
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        # Latest year bar ranking
        latest_yr = fdf["Year"].max()
        snap = fdf[fdf["Year"] == latest_yr].sort_values("CPI_Pct")
        if not snap.empty:
            bar_colors = [_RED if v > 4 else _AMB if v > 2 else _GRN for v in snap["CPI_Pct"]]
            fig2 = go.Figure(go.Bar(
                x=snap["CPI_Pct"], y=snap["Country"],
                orientation="h", marker_color=bar_colors,
                hovertemplate="%{y}: %{x:.1f}%<extra></extra>",
            ))
            fig2.add_vline(x=2, line=dict(color=_T3, dash="dot", width=1))
            fig2.update_layout(
                height=380,
                title=dict(text=f"Ranking ({latest_yr})", font=dict(size=13, color=_T1), x=0),
                xaxis_title="CPI %", showlegend=False,
                **_chart_layout(margin=dict(l=130, r=20, t=44, b=44)),
            )
            st.plotly_chart(fig2, use_container_width=True)


# ── GDP growth time series ────────────────────────────────────────────────────

def _gdp_series(df: pd.DataFrame, countries: list[str], yr_from: int) -> None:
    _section("Real GDP Growth", "Annual % change in real (inflation-adjusted) GDP")

    fdf = df[df["Country"].isin(countries) & (df["Year"] >= yr_from)].dropna(subset=["RealGDP_Pct"])
    if fdf.empty:
        _no_data()
        return

    c1, c2 = st.columns([3, 2])

    with c1:
        fig = go.Figure()
        for country in countries:
            cdf = fdf[fdf["Country"] == country].sort_values("Year")
            if cdf.empty:
                continue
            fig.add_trace(go.Scatter(
                x=cdf["Year"], y=cdf["RealGDP_Pct"],
                name=country, mode="lines+markers",
                line=dict(color=COUNTRY_COLORS.get(country, "#888"), width=2),
                marker=dict(size=4),
                hovertemplate=f"<b>{country}</b><br>%{{x}}: %{{y:.1f}}%<extra></extra>",
            ))
        fig.add_hline(y=0, line=dict(color=_T3, dash="dot", width=1))
        fig.update_layout(
            height=380,
            title=dict(text="Real GDP Growth (% YoY)", font=dict(size=13, color=_T1), x=0),
            yaxis_title="Growth %",
            **_chart_layout(),
        )
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        latest_yr = fdf["Year"].max()
        snap = fdf[fdf["Year"] == latest_yr].sort_values("RealGDP_Pct")
        if not snap.empty:
            bar_colors = [_GRN if v >= 0 else _RED for v in snap["RealGDP_Pct"]]
            fig2 = go.Figure(go.Bar(
                x=snap["RealGDP_Pct"], y=snap["Country"],
                orientation="h", marker_color=bar_colors,
                hovertemplate="%{y}: %{x:.1f}%<extra></extra>",
            ))
            fig2.add_vline(x=0, line=dict(color=_T3, width=1))
            fig2.update_layout(
                height=380,
                title=dict(text=f"Ranking ({latest_yr})", font=dict(size=13, color=_T1), x=0),
                xaxis_title="Growth %", showlegend=False,
                **_chart_layout(margin=dict(l=130, r=20, t=44, b=44)),
            )
            st.plotly_chart(fig2, use_container_width=True)


# ── Phillips Curve ────────────────────────────────────────────────────────────

def _phillips(df: pd.DataFrame, countries: list[str], yr_from: int) -> None:
    _section(
        "Phillips Curve",
        "Unemployment (x) vs CPI inflation (y) — the classic macro trade-off · each dot = country × year",
    )

    need = ["Unemployment_Pct", "CPI_Pct"]
    fdf  = df[df["Country"].isin(countries) & (df["Year"] >= yr_from)].dropna(subset=need)
    if fdf.empty:
        _no_data("Unemployment data unavailable — refresh data.")
        return

    fig = go.Figure()
    for country in countries:
        cdf = fdf[fdf["Country"] == country]
        if cdf.empty:
            continue
        fig.add_trace(go.Scatter(
            x=cdf["Unemployment_Pct"], y=cdf["CPI_Pct"],
            mode="markers", name=country,
            marker=dict(color=COUNTRY_COLORS.get(country, "#888"), size=8, opacity=0.75,
                        line=dict(width=1, color=_BG)),
            text=cdf["Year"].astype(str),
            hovertemplate=(
                f"<b>{country}</b><br>"
                "Unemployment: %{x:.1f}%<br>"
                "Inflation: %{y:.1f}%<br>"
                "Year: %{text}<extra></extra>"
            ),
        ))
    fig.add_hline(y=2, line=dict(color=_T3, dash="dot", width=1),
                  annotation_text="2% inflation target", annotation_font_color=_T3)
    fig.update_layout(
        height=420,
        title=dict(text=f"Phillips Curve — {yr_from} to present · each dot = country × year",
                   font=dict(size=13, color=_T1), x=0),
        xaxis_title="Unemployment Rate (%)",
        yaxis_title="CPI Inflation (%)",
        **_chart_layout(),
    )
    st.plotly_chart(fig, use_container_width=True)
    st.markdown(
        "The **Phillips curve** posits an inverse relationship: lower unemployment → higher inflation. "
        "Post-2020 data shows this relationship has become more volatile — "
        "supply shocks can drive inflation up without a corresponding drop in unemployment."
    )


# ── Main entry ────────────────────────────────────────────────────────────────

def inflation_growth() -> None:
    st.markdown(
        '<h2 style="color:#0f172a;margin:0 0 2px;">Inflation &amp; Growth</h2>'
        '<div style="font-size:12px;color:#475569;">'
        'CPI inflation · real GDP growth · unemployment · stagflation quadrant · '
        'Source: IMF World Economic Outlook</div>'
        '<hr style="border:none;border-top:1px solid #e2e8f0;margin:10px 0 6px;">',
        unsafe_allow_html=True,
    )

    st.sidebar.markdown(
        f'<div style="font-size:10px;color:{_T2};text-transform:uppercase;'
        f'letter-spacing:.1em;margin:16px 0 6px;padding-bottom:4px;'
        f'border-bottom:1px solid {_EDGE};">Countries</div>',
        unsafe_allow_html=True,
    )
    countries = st.sidebar.multiselect(
        "Countries", ALL_NAMES, default=CORE_NAMES,
        key="ig_countries", label_visibility="collapsed",
    )
    year    = st.sidebar.slider("Snapshot year", 2005, 2025, 2023, key="ig_year")
    yr_from = st.sidebar.slider("History from", 2000, year, 2010, key="ig_yr_from")

    st.sidebar.markdown(
        f'<div style="font-size:10px;color:{_T2};text-transform:uppercase;'
        f'letter-spacing:.1em;margin:14px 0 6px;padding-bottom:4px;'
        f'border-bottom:1px solid {_EDGE};">Data</div>',
        unsafe_allow_html=True,
    )
    from datetime import datetime
    if ANNUAL_CACHE.exists():
        mtime = datetime.fromtimestamp(ANNUAL_CACHE.stat().st_mtime)
        st.sidebar.caption(f"IMF macro: {mtime.strftime('%d %b %Y')}")
    else:
        st.sidebar.caption("IMF macro: not cached")
    if BREAKEVEN_CACHE.exists():
        mtime = datetime.fromtimestamp(BREAKEVEN_CACHE.stat().st_mtime)
        st.sidebar.caption(f"Breakeven/TIPS: {mtime.strftime('%d %b %Y')}")
    else:
        st.sidebar.caption("Breakeven/TIPS: not cached")
    refresh    = st.sidebar.button("Refresh IMF Data",   key="ig_refresh")
    refresh_be = st.sidebar.button("Refresh Breakeven",  key="ig_refresh_be")

    if refresh:
        with st.spinner("Fetching from IMF…"):
            df = refresh_annual()
    else:
        df = load_annual()

    if df.empty:
        st.warning(
            "No data. Click **Refresh Data** to fetch from IMF (takes ~30s).", icon="⚠️"
        )
        return

    if not countries:
        st.info("Select at least one country in the sidebar.")
        return

    _snapshot(df, countries, year)
    _stagflation(df, countries, year)
    _cpi_series(df, countries, yr_from)
    _gdp_series(df, countries, yr_from)
    _phillips(df, countries, yr_from)

    st.markdown(
        "**Data source:** IMF World Economic Outlook Datamapper API. "
        "CPI = PCPIPCH (consumer prices, % change). "
        "Real GDP growth = NGDP_RPCH. Unemployment = LUR."
    )

    # ── Breakeven inflation & real yields ─────────────────────────────────────
    _breakeven_section(refresh_be, yr_from)


def _breakeven_section(refresh: bool, yr_from: int) -> None:
    """TIPS breakeven inflation and real yields from FRED."""
    _section(
        "Breakeven Inflation & Real Yields",
        "Market-implied inflation expectations and real yields from TIPS · Source: FRED",
    )

    if refresh:
        with st.spinner("Fetching TIPS data from FRED…"):
            df = refresh_breakeven()
    else:
        df = load_breakeven()

    if df.empty:
        st.info("No breakeven data — click **Refresh Data** in the sidebar.", icon="ℹ️")
        return

    # Filter to selected date range
    df = df[df["Date"].dt.year >= yr_from].copy()
    if df.empty:
        st.info("No data in selected date range.")
        return

    COLORS = {
        "5Y Breakeven":       "#60a5fa",
        "10Y Breakeven":      "#f87171",
        "5-10Y Fwd Breakeven":"#fbbf24",
        "5Y Real Yield":      "#34d399",
        "10Y Real Yield":     "#a78bfa",
    }

    # Two charts side by side: breakevenss | real yields
    c1, c2 = st.columns(2)

    with c1:
        fig = go.Figure()
        for s in ["5Y Breakeven", "10Y Breakeven", "5-10Y Fwd Breakeven"]:
            sdf = df[df["Series"] == s].sort_values("Date")
            if sdf.empty:
                continue
            fig.add_trace(go.Scatter(
                x=sdf["Date"], y=sdf["Value"], name=s,
                mode="lines",
                line=dict(color=COLORS[s], width=2),
                hovertemplate=f"<b>{s}</b><br>%{{x|%d %b %Y}}: %{{y:.2f}}%<extra></extra>",
            ))
        fig.add_hline(y=2, line=dict(color="#475569", dash="dot", width=1),
                      annotation_text="2% target", annotation_font_color="#475569")
        fig.update_layout(
            height=360,
            title=dict(text="Breakeven Inflation (%)", font=dict(size=13, color=_T1), x=0),
            yaxis_title="Breakeven (%)",
            template="plotly_dark",
            paper_bgcolor=_CARD, plot_bgcolor=_BG,
            margin=dict(l=54, r=12, t=44, b=36),
            font=dict(color=_T1, size=11),
            xaxis=dict(gridcolor=_EDGE, tickfont=dict(color=_T2)),
            yaxis=dict(gridcolor=_EDGE, tickfont=dict(color=_T2)),
            hoverlabel=dict(bgcolor=_CARD, font_color=_T1, bordercolor=_EDGE),
            legend=dict(font=dict(size=10, color=_T1), bgcolor="rgba(0,0,0,0)",
                        orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        )
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        fig = go.Figure()
        for s in ["5Y Real Yield", "10Y Real Yield"]:
            sdf = df[df["Series"] == s].sort_values("Date")
            if sdf.empty:
                continue
            fig.add_trace(go.Scatter(
                x=sdf["Date"], y=sdf["Value"], name=s,
                mode="lines",
                line=dict(color=COLORS[s], width=2),
                hovertemplate=f"<b>{s}</b><br>%{{x|%d %b %Y}}: %{{y:.2f}}%<extra></extra>",
            ))
        fig.add_hline(y=0, line=dict(color="#475569", dash="dot", width=1),
                      annotation_text="Zero real yield", annotation_font_color="#475569")
        fig.update_layout(
            height=360,
            title=dict(text="TIPS Real Yields (%)", font=dict(size=13, color=_T1), x=0),
            yaxis_title="Real Yield (%)",
            template="plotly_dark",
            paper_bgcolor=_CARD, plot_bgcolor=_BG,
            margin=dict(l=54, r=12, t=44, b=36),
            font=dict(color=_T1, size=11),
            xaxis=dict(gridcolor=_EDGE, tickfont=dict(color=_T2)),
            yaxis=dict(gridcolor=_EDGE, tickfont=dict(color=_T2)),
            hoverlabel=dict(bgcolor=_CARD, font_color=_T1, bordercolor=_EDGE),
            legend=dict(font=dict(size=10, color=_T1), bgcolor="rgba(0,0,0,0)",
                        orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        )
        st.plotly_chart(fig, use_container_width=True)

    # Latest values
    latest = df.groupby("Series").last().reset_index()
    vals = {r["Series"]: r["Value"] for _, r in latest.iterrows()}
    cards = [
        ("5Y Breakeven",        vals.get("5Y Breakeven"),        _BLUE),
        ("10Y Breakeven",       vals.get("10Y Breakeven"),        _RED),
        ("5-10Y Fwd Breakeven", vals.get("5-10Y Fwd Breakeven"), _AMB),
        ("5Y Real Yield",       vals.get("5Y Real Yield"),       _GRN),
        ("10Y Real Yield",      vals.get("10Y Real Yield"),      "#a78bfa"),
    ]
    html = '<div style="display:flex;gap:10px;margin-bottom:8px;">'
    for lbl, v, c in cards:
        if v is None:
            continue
        html += (
            f'<div style="background:{_CARD};border:1px solid {_EDGE};border-radius:8px;'
            f'padding:8px 12px;text-align:center;flex:1;">'
            f'<div style="font-size:9px;color:{_T2};text-transform:uppercase;letter-spacing:.08em;">{lbl}</div>'
            f'<div style="font-size:18px;font-weight:700;color:{c};">{v:.2f}%</div></div>'
        )
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)
    st.markdown(
        "**Breakeven inflation** = nominal Treasury yield − TIPS yield — the market's implied inflation expectation. "
        "**Real yield** (TIPS) = the inflation-adjusted return; negative real yields indicate financial repression. "
        "Data: FRED T5YIE, T10YIE, T5YIFR, DFII5, DFII10."
    )
