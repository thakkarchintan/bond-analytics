"""
Credit Spreads
Source: ICE BofA Bond Indices via FRED — OAS across the full credit spectrum.
"""
from __future__ import annotations

from datetime import date

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from global_macro_data import (
    SPREADS_CACHE, SPREADS_SERIES,
    load_spreads, refresh_spreads,
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

# Colour per rating
SPREAD_COLORS: dict[str, str] = {
    "AAA": "#60a5fa",
    "AA":  "#34d399",
    "A":   "#a3e635",
    "BBB": "#fbbf24",
    "IG":  "#818cf8",
    "BB":  "#fb923c",
    "B":   "#f87171",
    "HY":  "#f472b6",
    "CCC": "#ef4444",
}

# Display order
RATING_ORDER = ["AAA", "AA", "A", "BBB", "IG", "BB", "B", "HY", "CCC"]

# NBER US recession bands
_RECESSIONS = [
    ("2001-03-01", "2001-11-01"),
    ("2007-12-01", "2009-06-01"),
    ("2020-02-01", "2020-04-01"),
]


def _section(title: str, subtitle: str = "") -> None:
    sub = (
        f'<div style="font-size:12px;color:{_T2};margin-top:4px;">{subtitle}</div>'
        if subtitle else ""
    )
    st.markdown(
        f'<div style="background:{_CARD};border-left:4px solid {_BLUE};'
        f'padding:10px 16px;margin:24px 0 10px;border-radius:0 8px 8px 0;">'
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


def _add_recessions(fig: go.Figure) -> None:
    for start, end in _RECESSIONS:
        fig.add_vrect(
            x0=start, x1=end,
            fillcolor="#334155", opacity=0.35,
            layer="below", line_width=0,
        )


def _snapshot_cards(df: pd.DataFrame) -> None:
    """Latest OAS snapshot for IG, HY, and key ratings."""
    latest = (
        df.sort_values("Date")
        .groupby("Series")
        .last()
        .reset_index()
    )
    rows_1y_ago = (
        df[df["Date"] <= (df["Date"].max() - pd.DateOffset(years=1))]
        .sort_values("Date")
        .groupby("Series")
        .last()
        .reset_index()
        .rename(columns={"OAS_Pct": "OAS_1Y"})
    )
    snap = latest.merge(rows_1y_ago[["Series", "OAS_1Y"]], on="Series", how="left")
    snap["Change"] = snap["OAS_Pct"] - snap["OAS_1Y"]

    html = '<div style="display:flex;gap:10px;flex-wrap:wrap;margin-bottom:16px;">'
    for rating in ["IG", "BBB", "HY", "BB", "B", "CCC"]:
        row = snap[snap["Series"] == rating]
        if row.empty:
            continue
        oas   = row.iloc[0]["OAS_Pct"]
        chg   = row.iloc[0]["Change"]
        clr   = SPREAD_COLORS.get(rating, "#888")
        chg_c = _GRN if chg <= 0 else _RED
        chg_s = f"{chg:+.0f} bp" if pd.notna(chg) else "—"
        html += (
            f'<div style="background:{_CARD};border:1px solid {_EDGE};border-radius:8px;'
            f'padding:10px 14px;text-align:center;min-width:90px;">'
            f'<div style="font-size:10px;color:{_T2};text-transform:uppercase;'
            f'letter-spacing:.08em;margin-bottom:4px;">{rating} OAS</div>'
            f'<div style="font-size:22px;font-weight:700;color:{clr};">{oas:.0f}</div>'
            f'<div style="font-size:11px;color:{_T2};">bp</div>'
            f'<div style="font-size:11px;color:{chg_c};margin-top:4px;">{chg_s} vs 1Y</div>'
            f'</div>'
        )
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)


def _time_series_tab(df: pd.DataFrame, selections: list[str], yr_from: int) -> None:
    _section(
        "Spread History",
        "OAS (option-adjusted spread) over US Treasuries — grey bands = NBER recessions",
    )

    fdf = df[df["Series"].isin(selections) & (df["Date"].dt.year >= yr_from)]
    if fdf.empty:
        st.info("No data in selected range.", icon="ℹ️")
        return

    fig = go.Figure()
    _add_recessions(fig)
    for s in [r for r in RATING_ORDER if r in selections]:
        sdf = fdf[fdf["Series"] == s].sort_values("Date")
        if sdf.empty:
            continue
        fig.add_trace(go.Scatter(
            x=sdf["Date"], y=sdf["OAS_Pct"], name=s,
            mode="lines",
            line=dict(color=SPREAD_COLORS.get(s, "#888"), width=2),
            hovertemplate=f"<b>{s}</b><br>%{{x|%d %b %Y}}: %{{y:.0f}} bp<extra></extra>",
        ))

    fig.update_layout(
        height=440,
        title=dict(text="Credit Spreads — OAS (basis points)",
                   font=dict(size=13, color=_T1), x=0),
        yaxis_title="OAS (bp)",
        **_chart_layout(),
    )
    st.plotly_chart(fig, use_container_width=True)
    st.markdown(
        "**Option-adjusted spread (OAS)** = yield of the bond index minus the equivalent-maturity "
        "Treasury yield, in basis points. A widening spread signals rising credit risk or risk-off sentiment."
    )


def _spectrum_tab(df: pd.DataFrame) -> None:
    _section(
        "Credit Risk Spectrum",
        "Current spread by rating — from investment grade (left) to high yield (right)",
    )

    latest = (
        df[df["Series"].isin(RATING_ORDER)]
        .sort_values("Date")
        .groupby("Series")
        .last()
        .reset_index()
    )
    ordered = [r for r in RATING_ORDER if r in latest["Series"].values]
    y_vals  = [latest.loc[latest["Series"] == r, "OAS_Pct"].iloc[0] for r in ordered]
    colors  = [SPREAD_COLORS.get(r, "#888") for r in ordered]

    c1, c2 = st.columns([2, 1])

    with c1:
        fig = go.Figure(go.Bar(
            x=ordered, y=y_vals,
            marker_color=colors,
            text=[f"{v:.0f} bp" for v in y_vals],
            textposition="outside",
            hovertemplate="<b>%{x}</b>: %{y:.0f} bp<extra></extra>",
        ))
        fig.add_shape(
            type="line", x0=-0.5, x1=3.5, y0=0, y1=0,
            line=dict(color=_AMB, dash="dot", width=1.5),
        )
        fig.add_annotation(x=3.5, y=0, text="IG / HY boundary",
                           font=dict(color=_AMB, size=10), showarrow=False, yshift=8)
        fig.update_layout(
            height=380,
            title=dict(text="Spread by Rating Bucket (latest, bp)",
                       font=dict(size=13, color=_T1), x=0),
            yaxis_title="OAS (bp)",
            showlegend=False,
            **_chart_layout(),
        )
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        # Table
        rows = [(r, v) for r, v in zip(ordered, y_vals)]
        rows_sorted = sorted(rows, key=lambda x: x[1])
        table_html = (
            f'<table style="width:100%;border-collapse:collapse;font-size:12px;">'
            f'<tr><th style="color:{_T2};text-align:left;padding:4px 8px;">Rating</th>'
            f'<th style="color:{_T2};text-align:right;padding:4px 8px;">OAS (bp)</th></tr>'
        )
        for r, v in rows:
            clr = SPREAD_COLORS.get(r, "#888")
            table_html += (
                f'<tr><td style="color:{clr};padding:4px 8px;font-weight:600;">{r}</td>'
                f'<td style="color:{_T1};text-align:right;padding:4px 8px;">{v:.0f}</td></tr>'
            )
        table_html += "</table>"
        st.markdown(table_html, unsafe_allow_html=True)

        ig_row  = latest[latest["Series"] == "IG"]
        hy_row  = latest[latest["Series"] == "HY"]
        if not ig_row.empty and not hy_row.empty:
            ig_oas = ig_row.iloc[0]["OAS_Pct"]
            hy_oas = hy_row.iloc[0]["OAS_Pct"]
            ratio  = hy_oas / ig_oas if ig_oas > 0 else float("nan")
            st.markdown(
                f'<div style="margin-top:16px;background:{_CARD};border:1px solid {_EDGE};'
                f'border-radius:8px;padding:10px 14px;">'
                f'<div style="font-size:10px;color:{_T2};text-transform:uppercase;">HY / IG Ratio</div>'
                f'<div style="font-size:24px;font-weight:700;color:{_AMB};">{ratio:.1f}×</div>'
                f'<div style="font-size:11px;color:{_T2};">IG={ig_oas:.0f} bp · HY={hy_oas:.0f} bp</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

    st.markdown(
        "**Investment grade (IG):** rated BBB/Baa and above — AAA, AA, A, BBB.  \n"
        "**High yield (HY):** rated BB/Ba and below — BB, B, CCC.  \n"
        "The HY/IG ratio measures relative risk appetite: above 4× indicates stressed credit conditions."
    )


def _ig_hy_tab(df: pd.DataFrame, yr_from: int) -> None:
    _section(
        "IG vs HY Comparison",
        "Investment-grade vs high-yield spread relationship over time",
    )

    ig_df = df[(df["Series"] == "IG") & (df["Date"].dt.year >= yr_from)].sort_values("Date")
    hy_df = df[(df["Series"] == "HY") & (df["Date"].dt.year >= yr_from)].sort_values("Date")

    if ig_df.empty or hy_df.empty:
        st.info("Insufficient data for comparison.", icon="ℹ️")
        return

    c1, c2 = st.columns(2)

    with c1:
        # Absolute levels
        fig = go.Figure()
        _add_recessions(fig)
        for sdf, name, clr in [(ig_df, "IG", SPREAD_COLORS["IG"]), (hy_df, "HY", SPREAD_COLORS["HY"])]:
            fig.add_trace(go.Scatter(
                x=sdf["Date"], y=sdf["OAS_Pct"], name=name,
                mode="lines", line=dict(color=clr, width=2),
                hovertemplate=f"<b>{name}</b><br>%{{x|%b %Y}}: %{{y:.0f}} bp<extra></extra>",
            ))
        fig.update_layout(
            height=340,
            title=dict(text="IG vs HY Spread Levels (bp)",
                       font=dict(size=13, color=_T1), x=0),
            yaxis_title="OAS (bp)",
            **_chart_layout(),
        )
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        # HY/IG ratio
        merged = ig_df[["Date", "OAS_Pct"]].merge(
            hy_df[["Date", "OAS_Pct"]], on="Date", suffixes=("_IG", "_HY")
        )
        merged["Ratio"] = merged["OAS_Pct_HY"] / merged["OAS_Pct_IG"]

        fig = go.Figure()
        _add_recessions(fig)
        fig.add_trace(go.Scatter(
            x=merged["Date"], y=merged["Ratio"],
            name="HY/IG Ratio", mode="lines",
            line=dict(color=_AMB, width=2),
            hovertemplate="HY/IG: <b>%{y:.2f}×</b><br>%{x|%b %Y}<extra></extra>",
        ))
        fig.add_hline(y=4, line=dict(color=_RED, dash="dot", width=1.5),
                      annotation_text="Stress threshold (4×)", annotation_font_color=_RED)
        fig.update_layout(
            height=340,
            title=dict(text="HY / IG Spread Ratio",
                       font=dict(size=13, color=_T1), x=0),
            yaxis_title="Ratio (×)",
            **_chart_layout(),
        )
        st.plotly_chart(fig, use_container_width=True)

    st.markdown(
        "When HY and IG spreads widen simultaneously, it signals a broad risk-off move. "
        "When HY widens but IG is stable, it reflects credit-specific stress in lower-quality issuers. "
        "The HY/IG ratio compresses during risk-on periods and blows out during crises (2008–09, Mar 2020)."
    )


def credit_spreads() -> None:
    st.markdown(
        '<h2 style="color:#0f172a;margin:0 0 2px;">Credit Spreads</h2>'
        '<div style="font-size:12px;color:#475569;">'
        'OAS across the credit spectrum (AAA → CCC) · Source: ICE BofA Bond Indices via FRED</div>'
        '<hr style="border:none;border-top:1px solid #e2e8f0;margin:10px 0 6px;">',
        unsafe_allow_html=True,
    )

    # ── Sidebar ────────────────────────────────────────────────────────────────
    st.sidebar.markdown(
        f'<div style="font-size:10px;color:{_T2};text-transform:uppercase;'
        f'letter-spacing:.1em;margin:16px 0 6px;padding-bottom:4px;'
        f'border-bottom:1px solid {_EDGE};">Filters</div>',
        unsafe_allow_html=True,
    )

    all_ratings = RATING_ORDER
    selections = st.sidebar.multiselect(
        "Ratings", all_ratings, default=["IG", "BBB", "HY", "BB"],
        key="cs_ratings",
    )
    yr_from = st.sidebar.slider("From year", 2000, 2023, 2008, key="cs_yr_from")

    st.sidebar.markdown(
        f'<div style="font-size:10px;color:{_T2};text-transform:uppercase;'
        f'letter-spacing:.1em;margin:14px 0 6px;padding-bottom:4px;'
        f'border-bottom:1px solid {_EDGE};">Data</div>',
        unsafe_allow_html=True,
    )
    if SPREADS_CACHE.exists():
        from datetime import datetime
        mtime = datetime.fromtimestamp(SPREADS_CACHE.stat().st_mtime)
        st.sidebar.caption(f"Cached: {mtime.strftime('%d %b %Y')}")
    else:
        st.sidebar.caption("Not cached")
    do_refresh = st.sidebar.button("Refresh Data", key="cs_refresh")

    # ── Load ──────────────────────────────────────────────────────────────────
    if do_refresh:
        with st.spinner("Fetching ICE BofA indices from FRED…"):
            df = refresh_spreads()
    else:
        df = load_spreads()

    if df.empty:
        st.warning(
            "No spread data loaded. Click **Refresh Data** in the sidebar "
            "(fetches 9 FRED series, takes ~20 seconds).",
            icon="⚠️",
        )
        return

    if not selections:
        st.info("Select at least one rating in the sidebar.")
        return

    # ── Snapshot cards ────────────────────────────────────────────────────────
    _snapshot_cards(df)

    # ── Tabs ──────────────────────────────────────────────────────────────────
    tab1, tab2, tab3 = st.tabs(["📈 Spread History", "📊 Credit Spectrum", "🔍 IG vs HY"])

    with tab1:
        _time_series_tab(df, selections, yr_from)
    with tab2:
        _spectrum_tab(df)
    with tab3:
        _ig_hy_tab(df, yr_from)

    st.markdown(
        "**Data:** ICE BofA US Corporate and High Yield OAS indices via FRED. "
        "IG = investment grade master (BAMLC0A0CM). "
        "HY = high yield master II (BAMLH0A0HYM2). "
        "Grey bands = NBER US recession periods."
    )
