"""
Leading Economic Indicators & Recession Tracker
ISM PMI, Initial Jobless Claims, Consumer Sentiment, Housing Starts,
Unemployment, 2Y10Y spread — with NBER recession shading.
"""
from __future__ import annotations

import datetime as dt
import os

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from global_macro_data import (
    LEADING_CACHE,
    load_leading_indicators,
    refresh_leading_indicators,
)

_CARD = "#1e293b"
_BG   = "#0f172a"
_EDGE = "#334155"
_T1   = "#f1f5f9"
_T2   = "#94a3b8"
_BLUE = "#3b82f6"
_GRN  = "#10b981"
_RED  = "#ef4444"
_AMB  = "#fbbf24"
_CYAN = "#22d3ee"
_PURP = "#a78bfa"

# Colours and metadata for each indicator
_INDICATORS = {
    "Industrial Production": {
        "color":     _BLUE,
        "threshold": None,
        "inverted":  False,
        "unit":      "Index (2017=100)",
        "desc":      "Federal Reserve Industrial Production Index — measures real output of manufacturing, mining, and utilities. Turns down before recessions.",
    },
    "Initial Claims": {
        "color":     _RED,
        "threshold": None,
        "inverted":  True,
        "unit":      "Thousands (SA)",
        "desc":      "Initial jobless claims filed each week. Spikes precede recessions; the trend matters more than the level.",
    },
    "Consumer Sentiment": {
        "color":     _AMB,
        "threshold": None,
        "inverted":  False,
        "unit":      "Index (1966=100)",
        "desc":      "University of Michigan Consumer Sentiment. Sharp drops often precede spending slowdowns.",
    },
    "Housing Starts": {
        "color":     _GRN,
        "threshold": None,
        "inverted":  False,
        "unit":      "Thousands (SAAR)",
        "desc":      "New residential construction starts. A long leading indicator — typically turns 6-12 months before the economy.",
    },
    "Unemployment": {
        "color":     _CYAN,
        "threshold": None,
        "inverted":  True,
        "unit":      "%",
        "desc":      "Civilian unemployment rate. A lagging indicator — rises after the recession starts and falls after recovery.",
    },
    "2Y10Y Spread": {
        "color":     _PURP,
        "threshold": 0.0,
        "thresh_lbl": "0 = inversion (recession signal)",
        "inverted":  False,
        "unit":      "pp",
        "desc":      "10-Year minus 2-Year Treasury yield spread. Persistent inversion has preceded every US recession since 1970.",
    },
}


def _chart_layout(**kw) -> dict:
    base = dict(
        paper_bgcolor=_CARD, plot_bgcolor=_BG,
        font=dict(family="Inter, sans-serif", color=_T1, size=12),
        margin=dict(l=55, r=20, t=40, b=40),
        legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color=_T1, size=11)),
        xaxis=dict(gridcolor=_EDGE, tickfont=dict(color=_T2), zerolinecolor=_EDGE),
        yaxis=dict(gridcolor=_EDGE, tickfont=dict(color=_T2), zerolinecolor=_EDGE),
    )
    base.update(kw)
    return base


def _recession_periods(df_rec: pd.DataFrame) -> list[tuple[pd.Timestamp, pd.Timestamp]]:
    if df_rec.empty:
        return []
    df_rec = df_rec.sort_values("Date")
    periods: list[tuple] = []
    in_rec = False
    start: pd.Timestamp | None = None
    for _, row in df_rec.iterrows():
        val = int(row["Value"]) if not pd.isna(row["Value"]) else 0
        if val == 1 and not in_rec:
            in_rec = True
            start = row["Date"]
        elif val == 0 and in_rec:
            in_rec = False
            periods.append((start, row["Date"]))
    if in_rec and start is not None:
        periods.append((start, df_rec["Date"].iloc[-1]))
    return periods


def _add_rec_shading(fig: go.Figure, periods: list, yr_from: int) -> None:
    cutoff = pd.Timestamp(yr_from, 1, 1)
    for i, (s, e) in enumerate(periods):
        if e < cutoff:
            continue
        fig.add_vrect(
            x0=max(s, cutoff), x1=e,
            fillcolor="rgba(239,68,68,0.10)",
            line_width=0,
            annotation_text="Rec." if i == 0 else None,
            annotation_position="top left",
            annotation_font=dict(color="rgba(239,68,68,0.5)", size=9),
        )


def _signal_card(name: str, value: float, meta: dict) -> str:
    thresh = meta.get("threshold")
    inverted = meta.get("inverted", False)
    if thresh is not None:
        warning = value < thresh if not inverted else value > thresh
    else:
        warning = False

    bg    = "rgba(239,68,68,0.15)" if warning else "rgba(16,185,129,0.10)"
    dot   = _RED if warning else _GRN
    label = "⚠ Warning" if warning else "✓ Normal"

    return (
        f'<div style="background:{_CARD};border:1px solid {_EDGE};border-radius:8px;'
        f'padding:10px 14px">'
        f'<div style="font-size:11px;color:{_T2};margin-bottom:2px">{name}</div>'
        f'<div style="font-size:1.25rem;font-weight:700;color:{_T1}">{value:.2f}'
        f' <span style="font-size:10px;color:{_T2}">{meta["unit"]}</span></div>'
        f'<div style="font-size:10px;color:{dot};margin-top:3px">{label}</div>'
        f'</div>'
    )


def leading_indicators() -> None:
    st.markdown("### 🔭 Leading Indicators & Recession Tracker")
    st.caption(
        "ISM PMI · Jobless Claims · Consumer Sentiment · Housing Starts · "
        "Unemployment · 2Y10Y Spread — with NBER recession shading"
    )

    # ── Sidebar ───────────────────────────────────────────────────────────────
    if st.sidebar.button("Refresh Data", key="li_refresh"):
        with st.spinner("Fetching from FRED..."):
            refresh_leading_indicators()
        st.success("Leading indicator data refreshed.")

    if LEADING_CACHE.exists():
        mtime = os.path.getmtime(LEADING_CACHE)
        ts = dt.datetime.fromtimestamp(mtime).strftime("%d %b %Y %H:%M")
        st.sidebar.caption(f"Cache: {ts}")
    else:
        st.sidebar.caption("No cache — click Refresh Data")

    yr_from = st.sidebar.slider("From Year", 1970, 2024, 2000, key="li_yr_from")

    df_all = load_leading_indicators()
    if df_all.empty:
        st.warning("No data available. Click **Refresh Data** in the sidebar.")
        return

    df_all["Date"] = pd.to_datetime(df_all["Date"])
    cutoff = pd.Timestamp(yr_from, 1, 1)
    df_plot = df_all[df_all["Date"] >= cutoff].copy()

    # Extract recession data
    rec_df = df_all[df_all["Series"] == "Recession"].copy()
    rec_periods = _recession_periods(rec_df)

    # ── Latest signal dashboard ───────────────────────────────────────────────
    latest: dict[str, float] = {}
    for name in _INDICATORS:
        sub = df_all[df_all["Series"] == name].dropna(subset=["Value"])
        if not sub.empty:
            latest[name] = sub.sort_values("Date")["Value"].iloc[-1]

    if latest:
        st.markdown("**Latest Readings**")
        n = len(latest)
        cols = st.columns(n)
        for col, (name, val) in zip(cols, latest.items()):
            col.markdown(_signal_card(name, val, _INDICATORS[name]), unsafe_allow_html=True)

        # Recession signal count
        warnings = 0
        for name, val in latest.items():
            meta = _INDICATORS[name]
            thresh = meta.get("threshold")
            if thresh is not None:
                if (not meta["inverted"] and val < thresh) or (meta["inverted"] and val > thresh):
                    warnings += 1

        signal_color = _GRN if warnings <= 1 else (_AMB if warnings == 2 else _RED)
        signal_text  = (
            "Low recession risk" if warnings <= 1
            else "Elevated recession risk" if warnings == 2
            else "High recession risk"
        )
        st.markdown(
            f'<div style="margin:0.6rem 0 0.2rem;padding:8px 16px;background:{_CARD};'
            f'border:1px solid {signal_color};border-radius:8px;display:inline-block">'
            f'<span style="color:{signal_color};font-weight:600">{signal_text}</span>'
            f' &nbsp;<span style="color:{_T2};font-size:12px">— {warnings} of {len(latest)} signals in warning territory</span>'
            f'</div>',
            unsafe_allow_html=True,
        )
        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

    # ── Individual charts ─────────────────────────────────────────────────────
    available = [n for n in _INDICATORS if n in df_plot["Series"].unique()]
    selected = st.multiselect(
        "Indicators to display", available, default=available, key="li_sel"
    )
    if not selected:
        st.info("Select at least one indicator above.")
        return

    for name in selected:
        meta = _INDICATORS[name]
        sub  = df_plot[df_plot["Series"] == name].sort_values("Date").dropna(subset=["Value"])
        if sub.empty:
            continue

        fig = go.Figure()
        _add_rec_shading(fig, rec_periods, yr_from)

        fig.add_trace(go.Scatter(
            x=sub["Date"], y=sub["Value"],
            name=name,
            line=dict(color=meta["color"], width=1.8),
            hovertemplate=f"<b>{name}</b><br>%{{x|%Y-%m-%d}}<br>%{{y:.2f}} {meta['unit']}<extra></extra>",
        ))

        thresh = meta.get("threshold")
        if thresh is not None:
            fig.add_hline(
                y=thresh,
                line=dict(color=_RED, dash="dash", width=1),
                annotation_text=meta.get("thresh_lbl", f"{thresh}"),
                annotation_font=dict(color=_RED, size=10),
                annotation_position="top right",
            )

        # 12-month rolling average
        if len(sub) > 12:
            sub = sub.copy()
            sub["MA12"] = sub["Value"].rolling(12, min_periods=6).mean()
            fig.add_trace(go.Scatter(
                x=sub["Date"], y=sub["MA12"],
                name="12M avg",
                line=dict(color=_T2, width=1.2, dash="dot"),
                hoverinfo="skip",
            ))

        fig.update_layout(
            title=dict(
                text=f"{name}  ({meta['unit']})",
                font=dict(size=13, color=_T1), x=0,
            ),
            height=310,
            **_chart_layout(
                margin=dict(l=55, r=20, t=45, b=20),
                xaxis=dict(gridcolor=_EDGE, tickfont=dict(color=_T2), zerolinecolor=_EDGE),
                yaxis=dict(gridcolor=_EDGE, tickfont=dict(color=_T2), zerolinecolor=_EDGE),
            ),
        )
        st.plotly_chart(fig, use_container_width=True)
        st.caption(meta["desc"])
        st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)
