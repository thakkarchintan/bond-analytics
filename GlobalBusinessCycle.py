"""
Global Business Cycle — OECD BCI, CCI, CLI
Source: DBnomics OECD/DP_LIVE. Data through Nov 2023 (OECD on DBnomics lag).
Index = Long-Term Trend Index: 100 = neutral, >100 = above trend (expansion).
"""
from __future__ import annotations

import os

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from dbnomics_data import (
    OECD_BC_CACHE,
    COUNTRY_NAMES,
    load_oecd_bc,
    refresh_oecd_bc,
)

_BG   = "#0f172a"
_CARD = "#1e293b"
_EDGE = "#334155"
_T1   = "#f1f5f9"
_T2   = "#94a3b8"
_BLUE = "#3b82f6"
_GRN  = "#10b981"
_RED  = "#ef4444"
_AMB  = "#fbbf24"

_INDICATOR_META = {
    "BCI": {
        "label": "Business Confidence Index",
        "desc":  "Surveys of industrial sentiment. Above 100 = businesses more optimistic than long-run average.",
        "color": _BLUE,
    },
    "CCI": {
        "label": "Consumer Confidence Index",
        "desc":  "Household economic expectations. Above 100 = consumers more confident than long-run average.",
        "color": _AMB,
    },
    "CLI": {
        "label": "Composite Leading Indicator",
        "desc":  "Aggregates multiple early-warning series. Designed to turn 6–9 months before the economy.",
        "color": _GRN,
    },
}

_COUNTRY_COLORS = [
    "#60a5fa","#f87171","#34d399","#fbbf24","#a78bfa",
    "#fb923c","#22d3ee","#f472b6","#818cf8","#a3e635",
    "#e879f9","#4ade80","#38bdf8","#facc15","#f472b6",
    "#94a3b8","#cbd5e1","#7dd3fc","#86efac","#fde68a",
]


def _chart_layout(**kw) -> dict:
    base = dict(
        paper_bgcolor=_CARD, plot_bgcolor=_BG,
        font=dict(family="Inter, sans-serif", color=_T1, size=12),
        margin=dict(l=55, r=20, t=44, b=36),
        legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color=_T1, size=11)),
        xaxis=dict(gridcolor=_EDGE, tickfont=dict(color=_T2), zerolinecolor=_EDGE),
        yaxis=dict(gridcolor=_EDGE, tickfont=dict(color=_T2), zerolinecolor=_EDGE),
    )
    base.update(kw)
    return base


def _latest_snapshot(df: pd.DataFrame, indicator: str) -> None:
    sub = df[df["Indicator"] == indicator].copy()
    if sub.empty:
        st.info(f"No {indicator} data available.")
        return

    latest = (
        sub.sort_values("Date")
        .groupby("Country")
        .last()
        .reset_index()
        .rename(columns={"Value": "Latest"})
        [["Country", "ISO", "Latest", "Date"]]
        .sort_values("Latest", ascending=False)
    )

    # Metric cards — 4 per row
    st.markdown(
        f'<div style="font-size:12px;color:{_T2};margin-bottom:6px;">'
        f'Latest available reading (most countries: Nov 2023). '
        f'Index = Long-Term Trend · 100 = neutral · '
        f'<span style="color:{_GRN}">green &gt;100 (above trend)</span> · '
        f'<span style="color:{_RED}">red &lt;100 (below trend)</span></div>',
        unsafe_allow_html=True,
    )

    cards_html = '<div style="display:flex;flex-wrap:wrap;gap:8px;">'
    for _, row in latest.iterrows():
        v = row["Latest"]
        clr = _GRN if v > 100 else _RED
        bg  = "rgba(16,185,129,0.08)" if v > 100 else "rgba(239,68,68,0.08)"
        cards_html += (
            f'<div style="background:{bg};border:1px solid {_EDGE};border-radius:8px;'
            f'padding:8px 12px;min-width:120px;">'
            f'<div style="font-size:10px;color:{_T2};margin-bottom:2px">{row["Country"]}</div>'
            f'<div style="font-size:1.25rem;font-weight:700;color:{clr}">{v:.1f}</div>'
            f'<div style="font-size:9px;color:{_T2}">{row["Date"].strftime("%b %Y") if pd.notna(row["Date"]) else ""}</div>'
            f'</div>'
        )
    cards_html += "</div>"
    st.markdown(cards_html, unsafe_allow_html=True)

    # Also a sortable table
    st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
    disp = latest.copy()
    disp["As of"] = disp["Date"].dt.strftime("%b %Y")
    disp["Signal"] = disp["Latest"].apply(lambda v: "🟢 Above trend" if v > 100 else "🔴 Below trend")
    disp = disp.rename(columns={"Latest": indicator})

    def _row_style(row):
        v = row[indicator]
        if v > 100:
            return ["background-color:#0e2e1a;color:#f1f5f9"] * len(row)
        return ["background-color:#3b1010;color:#f1f5f9"] * len(row)

    st.dataframe(
        disp[["Country", indicator, "As of", "Signal"]].style.apply(_row_style, axis=1),
        use_container_width=True, hide_index=True,
    )


def _time_series_tab(df: pd.DataFrame, indicator: str, countries: list[str],
                     yr_from: int) -> None:
    meta = _INDICATOR_META[indicator]
    sub = df[
        (df["Indicator"] == indicator) &
        (df["Country"].isin(countries)) &
        (df["Date"].dt.year >= yr_from)
    ].copy()

    if sub.empty:
        st.info("No data for selected countries / indicator. Try Refresh Data.")
        return

    fig = go.Figure()
    country_list = sorted(sub["Country"].unique())
    for i, country in enumerate(country_list):
        cdf = sub[sub["Country"] == country].sort_values("Date")
        fig.add_trace(go.Scatter(
            x=cdf["Date"], y=cdf["Value"],
            name=country,
            line=dict(color=_COUNTRY_COLORS[i % len(_COUNTRY_COLORS)], width=1.8),
            hovertemplate=f"<b>{country}</b><br>%{{x|%b %Y}}: %{{y:.2f}}<extra></extra>",
        ))

    fig.add_hline(y=100, line=dict(color=_EDGE, dash="dot", width=1.5),
                  annotation_text="100 = neutral", annotation_font=dict(color=_T2, size=9),
                  annotation_position="top right")
    fig.update_layout(
        title=dict(text=f"{meta['label']} — country comparison", font=dict(size=13, color=_T1), x=0),
        height=480,
        yaxis_title="LTRENDIDX (100 = neutral)",
        **_chart_layout(),
    )
    st.plotly_chart(fig, use_container_width=True)
    st.caption(meta["desc"])


def _heatmap_tab(df: pd.DataFrame, indicator: str) -> None:
    meta = _INDICATOR_META[indicator]
    sub = df[df["Indicator"] == indicator].copy()
    if sub.empty:
        st.info("No data.")
        return

    # Latest 24 months per country
    sub["YearMonth"] = sub["Date"].dt.to_period("M").astype(str)
    pivot = sub.pivot_table(index="Country", columns="YearMonth", values="Value", aggfunc="last")
    if pivot.empty:
        st.info("Not enough data for heatmap.")
        return

    cols_sorted = sorted(pivot.columns)[-36:]
    pivot = pivot[cols_sorted].fillna(100)

    # Deviation from 100
    dev = pivot - 100

    fig = go.Figure(go.Heatmap(
        z=dev.values,
        x=list(dev.columns),
        y=list(dev.index),
        colorscale=[
            [0.0, "#ef4444"],
            [0.5, "#1e293b"],
            [1.0, "#10b981"],
        ],
        zmid=0,
        colorbar=dict(
            title="vs 100",
            tickfont=dict(color=_T1), titlefont=dict(color=_T1),
        ),
        hovertemplate="%{y}<br>%{x}: %{z:+.2f} vs 100<extra></extra>",
    ))
    fig.update_layout(
        title=dict(text=f"{meta['label']} — deviation from 100 (last 36 months)",
                   font=dict(size=13, color=_T1), x=0),
        height=max(300, len(dev) * 28 + 100),
        paper_bgcolor=_CARD, plot_bgcolor=_BG,
        font=dict(color=_T1, size=11),
        margin=dict(l=150, r=80, t=50, b=60),
        xaxis=dict(tickfont=dict(color=_T2), tickangle=-45),
        yaxis=dict(tickfont=dict(color=_T1)),
    )
    st.plotly_chart(fig, use_container_width=True)
    st.caption("Green = above long-run trend (expanding). Red = below trend (contracting).")


def _deep_dive_tab(df: pd.DataFrame, country: str, yr_from: int) -> None:
    sub = df[
        (df["Country"] == country) &
        (df["Date"].dt.year >= yr_from)
    ].copy()

    if sub.empty:
        st.info(f"No data for {country}.")
        return

    fig = go.Figure()
    colors = {"BCI": _BLUE, "CCI": _AMB, "CLI": _GRN}
    for ind in ["BCI", "CCI", "CLI"]:
        idf = sub[sub["Indicator"] == ind].sort_values("Date")
        if idf.empty:
            continue
        meta = _INDICATOR_META[ind]
        fig.add_trace(go.Scatter(
            x=idf["Date"], y=idf["Value"],
            name=meta["label"],
            line=dict(color=colors[ind], width=2),
            hovertemplate=f"<b>{meta['label']}</b><br>%{{x|%b %Y}}: %{{y:.2f}}<extra></extra>",
        ))

    fig.add_hline(y=100, line=dict(color=_EDGE, dash="dot", width=1.5),
                  annotation_text="100 = neutral", annotation_font=dict(color=_T2, size=9),
                  annotation_position="top right")
    fig.update_layout(
        title=dict(text=f"{country} — BCI · CCI · CLI", font=dict(size=13, color=_T1), x=0),
        height=440,
        yaxis_title="LTRENDIDX (100 = neutral)",
        **_chart_layout(),
    )
    st.plotly_chart(fig, use_container_width=True)

    # Latest table
    latest_rows = []
    for ind in ["BCI", "CCI", "CLI"]:
        idf = sub[sub["Indicator"] == ind].dropna(subset=["Value"]).sort_values("Date")
        if idf.empty:
            continue
        last = idf.iloc[-1]
        latest_rows.append({
            "Indicator": _INDICATOR_META[ind]["label"],
            "Latest Value": round(last["Value"], 2),
            "As of": last["Date"].strftime("%b %Y"),
            "Signal": "🟢 Above trend" if last["Value"] > 100 else "🔴 Below trend",
        })
    if latest_rows:
        st.dataframe(pd.DataFrame(latest_rows), use_container_width=True, hide_index=True)


def global_business_cycle() -> None:
    st.markdown("### 🌐 Global Business Cycle")
    st.caption(
        "OECD Business Confidence (BCI) · Consumer Confidence (CCI) · "
        "Composite Leading Indicator (CLI) · Long-Term Trend Index · "
        "Source: OECD via DBnomics · Data through Nov 2023"
    )

    # ── Sidebar ───────────────────────────────────────────────────────────────
    if st.sidebar.button("Refresh Data", key="gbc_refresh"):
        with st.spinner("Fetching OECD data from DBnomics (may take 60s)..."):
            refresh_oecd_bc()
        st.success("OECD business cycle data refreshed.")

    if OECD_BC_CACHE.exists():
        import datetime as _dt
        mtime = _dt.datetime.fromtimestamp(os.path.getmtime(OECD_BC_CACHE))
        st.sidebar.caption(f"Cache: {mtime.strftime('%d %b %Y %H:%M')}")
    else:
        st.sidebar.caption("No cache — click Refresh Data")

    indicator = st.sidebar.selectbox(
        "Indicator", ["CLI", "BCI", "CCI"],
        format_func=lambda x: _INDICATOR_META[x]["label"],
        key="gbc_indicator",
    )
    yr_from = st.sidebar.slider("From Year", 1990, 2020, 2005, key="gbc_yr_from")

    df = load_oecd_bc()
    if df.empty:
        st.warning("No data. Click **Refresh Data** in the sidebar.")
        return

    df["Date"] = pd.to_datetime(df["Date"])

    all_countries = sorted(df[df["Indicator"] == indicator]["Country"].unique())
    default_countries = [c for c in [
        "United States", "Euro Area", "China", "Germany", "Japan",
        "United Kingdom", "South Korea", "OECD Total",
    ] if c in all_countries][:8]

    countries = st.sidebar.multiselect(
        "Countries", all_countries, default=default_countries, key="gbc_countries",
    )

    deep_dive_country = st.sidebar.selectbox(
        "Deep-dive country", all_countries,
        index=all_countries.index("United States") if "United States" in all_countries else 0,
        key="gbc_deep",
    )

    # ── Tabs ──────────────────────────────────────────────────────────────────
    tab_snap, tab_ts, tab_heat, tab_deep = st.tabs([
        "📊 Latest Snapshot", "📈 Time Series", "🔥 Heatmap", "🔍 Country Deep-Dive"
    ])

    with tab_snap:
        _latest_snapshot(df, indicator)

    with tab_ts:
        if not countries:
            st.info("Select at least one country in the sidebar.")
        else:
            _time_series_tab(df, indicator, countries, yr_from)

    with tab_heat:
        _heatmap_tab(df, indicator)

    with tab_deep:
        _deep_dive_tab(df, deep_dive_country, yr_from)

    st.markdown(
        f"**Source:** OECD via DBnomics (`OECD/DP_LIVE`). "
        f"Long-Term Trend Index (LTRENDIDX): 100 = long-run average. "
        f"BCI = Business Confidence · CCI = Consumer Confidence · CLI = Composite Leading Indicator. "
        f"Data lag: OECD on DBnomics is approximately 2–3 years behind current date."
    )
