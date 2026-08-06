"""
Cross-Asset Dashboard
VIX, Gold, WTI Crude, S&P 500 alongside US 10Y yield and credit spreads.
"""
from __future__ import annotations

import datetime as dt
import os

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from global_macro_data import (
    CROSS_ASSET_CACHE,
    load_cross_asset,
    load_spreads,
    load_teny_yields,
    refresh_cross_asset,
)

_CARD = "#1e293b"
_BG   = "#0f172a"
_EDGE = "#334155"
_T1   = "#f1f5f9"
_T2   = "#94a3b8"

ASSET_COLORS: dict[str, str] = {
    "VIX":       "#ef4444",
    "WTI Crude": "#f59e0b",
    "Gold":      "#fbbf24",
    "S&P 500":   "#34d399",
    "US 10Y":    "#60a5fa",
    "IG Spread": "#818cf8",
    "HY Spread": "#f472b6",
}

# Recession periods (NBER)
_RECESSIONS = [
    ("2001-03-01", "2001-11-01"),
    ("2007-12-01", "2009-06-01"),
    ("2020-02-01", "2020-04-01"),
]


def _chart_layout(**kw) -> dict:
    base = dict(
        paper_bgcolor=_CARD, plot_bgcolor=_BG,
        font=dict(family="Inter, sans-serif", color=_T2, size=12),
        margin=dict(l=55, r=20, t=40, b=40),
        legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color=_T1, size=11)),
        xaxis=dict(gridcolor=_EDGE, zerolinecolor=_EDGE),
        yaxis=dict(gridcolor=_EDGE, zerolinecolor=_EDGE),
    )
    base.update(kw)
    return base


def _add_recessions(fig: go.Figure, yr_from: int) -> None:
    for start, end in _RECESSIONS:
        if pd.Timestamp(end) < pd.Timestamp(yr_from, 1, 1):
            continue
        fig.add_vrect(
            x0=start, x1=end,
            fillcolor="rgba(255,100,100,0.08)",
            line_width=0,
            annotation_text="Rec.", annotation_position="top left",
            annotation_font=dict(color="#ef444477", size=9),
        )


def _load_all(yr_from: int) -> pd.DataFrame:
    frames = []

    df_ca = load_cross_asset()
    if not df_ca.empty:
        frames.append(df_ca[["Date", "Series", "Value"]])

    try:
        df_y = load_teny_yields()
        if not df_y.empty:
            us = df_y[df_y["Country"] == "United States"][["Date", "Rate"]].copy()
            us = us.rename(columns={"Rate": "Value"})
            us["Series"] = "US 10Y"
            frames.append(us)
    except Exception:
        pass

    try:
        df_sp = load_spreads()
        if not df_sp.empty:
            for label, col_name in [("IG", "IG Spread"), ("HY", "HY Spread")]:
                sub = df_sp[df_sp["Series"] == label][["Date", "Value"]].copy()
                sub["Series"] = col_name
                frames.append(sub)
    except Exception:
        pass

    if not frames:
        return pd.DataFrame()

    out = pd.concat(frames, ignore_index=True)
    out["Date"] = pd.to_datetime(out["Date"])
    cutoff = pd.Timestamp(yr_from, 1, 1)
    return out[out["Date"] >= cutoff].copy()


def cross_asset() -> None:
    st.markdown("### 📡 Cross-Asset Dashboard")
    st.caption(
        "VIX · WTI Crude · S&P 500 · US 10Y yield · IG and HY spreads — "
        "risk-on / risk-off dynamics in one view"
    )

    # ── Sidebar ───────────────────────────────────────────────────────────────
    if st.sidebar.button("Refresh Data", key="ca_refresh"):
        with st.spinner("Fetching from FRED..."):
            refresh_cross_asset()
        st.success("Cross-asset data refreshed.")

    if CROSS_ASSET_CACHE.exists():
        mtime = os.path.getmtime(CROSS_ASSET_CACHE)
        ts = dt.datetime.fromtimestamp(mtime).strftime("%d %b %Y %H:%M")
        st.sidebar.caption(f"Cache: {ts}")
    else:
        st.sidebar.caption("No cache — click Refresh Data")

    yr_from = st.sidebar.slider("From Year", 2000, 2024, 2010, key="ca_yr_from")

    df_all = _load_all(yr_from)
    if df_all.empty:
        st.warning("No data available. Click **Refresh Data** in the sidebar.")
        return

    all_series = sorted(df_all["Series"].unique())
    default_sel = [s for s in ["VIX", "Gold", "WTI Crude", "S&P 500", "US 10Y"] if s in all_series]
    selected = st.sidebar.multiselect("Assets", all_series, default=default_sel, key="ca_sel")

    if not selected:
        st.info("Select at least one asset in the sidebar.")
        return

    df = df_all[df_all["Series"].isin(selected)].copy()

    # ── Tabs ──────────────────────────────────────────────────────────────────
    tab_norm, tab_raw, tab_corr = st.tabs(
        ["📊 Normalized Performance", "📈 Raw Values", "🔗 Correlation Matrix"]
    )

    with tab_norm:
        st.caption("Each series re-indexed to 100 at the start of the selected period. Recession shading in red.")
        fig = go.Figure()
        _add_recessions(fig, yr_from)
        for s in selected:
            sub = df[df["Series"] == s].sort_values("Date").dropna(subset=["Value"])
            if sub.empty or sub["Value"].iloc[0] == 0:
                continue
            normed = sub["Value"] / sub["Value"].iloc[0] * 100
            fig.add_trace(go.Scatter(
                x=sub["Date"], y=normed, name=s,
                line=dict(color=ASSET_COLORS.get(s, _T2), width=1.8),
                hovertemplate=(
                    f"<b>{s}</b><br>%{{x|%Y-%m-%d}}<br>Index: %{{y:.1f}}<extra></extra>"
                ),
            ))
        fig.add_hline(y=100, line=dict(color=_EDGE, dash="dot", width=1))
        fig.update_layout(
            title="Cross-Asset Performance (indexed to 100)",
            **_chart_layout(
                xaxis=dict(gridcolor=_EDGE, zerolinecolor=_EDGE),
                yaxis=dict(gridcolor=_EDGE, zerolinecolor=_EDGE),
            ),
        )
        st.plotly_chart(fig, use_container_width=True)

    with tab_raw:
        st.caption("Raw values — each asset on its own scale.")
        for s in selected:
            sub = df[df["Series"] == s].sort_values("Date").dropna(subset=["Value"])
            if sub.empty:
                continue
            color = ASSET_COLORS.get(s, _T2)
            fig_r = go.Figure()
            _add_recessions(fig_r, yr_from)
            fig_r.add_trace(go.Scatter(
                x=sub["Date"], y=sub["Value"], name=s,
                line=dict(color=color, width=1.5),
                fill="tozeroy", fillcolor="rgba(59,130,246,0.06)",
                hovertemplate=f"<b>{s}</b><br>%{{x|%Y-%m-%d}}<br>%{{y:.2f}}<extra></extra>",
            ))
            fig_r.update_layout(
                title=s, height=230,
                **_chart_layout(
                    margin=dict(l=55, r=20, t=35, b=20),
                    xaxis=dict(gridcolor=_EDGE, zerolinecolor=_EDGE),
                    yaxis=dict(gridcolor=_EDGE, zerolinecolor=_EDGE),
                ),
            )
            st.plotly_chart(fig_r, use_container_width=True)

    with tab_corr:
        wide = (
            df.pivot_table(index="Date", columns="Series", values="Value", aggfunc="last")
            .resample("ME").last()
        )
        valid = [s for s in selected if s in wide.columns]
        wide = wide[valid].dropna()

        if wide.shape[0] < 12 or wide.shape[1] < 2:
            st.info(
                "Need at least 2 assets with 12+ overlapping monthly observations. "
                "Try extending the date range."
            )
        else:
            corr = wide.pct_change().dropna().corr()
            fig_c = px.imshow(
                corr,
                text_auto=".2f",
                color_continuous_scale="RdBu",
                zmin=-1, zmax=1,
                aspect="auto",
                color_continuous_midpoint=0,
            )
            fig_c.update_layout(
                title="Monthly Return Correlation Matrix",
                paper_bgcolor=_CARD, plot_bgcolor=_BG,
                font=dict(color=_T1, size=11),
                margin=dict(l=80, r=20, t=40, b=40),
                coloraxis_colorbar=dict(tickfont=dict(color=_T2)),
            )
            st.plotly_chart(fig_c, use_container_width=True)
            st.caption(
                "Computed on monthly % returns. Red = strong positive correlation (assets move together), "
                "blue = negative (diversification). During stress events, most correlations spike toward +1."
            )
