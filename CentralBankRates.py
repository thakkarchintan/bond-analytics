"""
Central Bank Policy Rates
Source: BIS WS_CBPOL_M — 40+ central banks, monthly, back to 2000.
"""
from __future__ import annotations

from datetime import date

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from global_macro_data import (
    COUNTRY_COLORS, CORE_NAMES, ALL_NAMES,
    ANNUAL_CACHE, POLICY_CACHE,
    load_annual, load_policy_rates,
    refresh_policy_rates, refresh_annual,
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


def _no_data(msg: str = "No data — click Refresh Data in the sidebar.") -> None:
    st.info(msg, icon="ℹ️")


# ── Snapshot section ───────────────────────────────────────────────────────────

def _snapshot(df: pd.DataFrame, ann: pd.DataFrame, countries: list[str]) -> None:
    _section("Policy Rate Snapshot", "Latest available rate per central bank")

    latest = (
        df[df["Country"].isin(countries)]
        .sort_values("Date")
        .groupby("Country")
        .last()
        .reset_index()
    )
    if latest.empty:
        _no_data()
        return

    # Compute 1-year change
    one_yr_ago = latest["Date"].max() - pd.DateOffset(years=1)
    prev = (
        df[df["Country"].isin(countries) & (df["Date"] <= one_yr_ago)]
        .sort_values("Date")
        .groupby("Country")
        .last()
        .reset_index()
        .rename(columns={"Rate_Pct": "Rate_Prev"})
        [["Country", "Rate_Prev"]]
    )
    snap = latest.merge(prev, on="Country", how="left")
    snap["Change_1Y"] = snap["Rate_Pct"] - snap["Rate_Prev"]

    # Scalar summary cards
    avg_rate  = snap["Rate_Pct"].mean()
    n_hiking  = (snap["Change_1Y"] > 0.01).sum()
    n_cutting = (snap["Change_1Y"] < -0.01).sum()
    n_hold    = len(snap) - n_hiking - n_cutting
    hi_cb     = snap.loc[snap["Rate_Pct"].idxmax(), "Country"] if not snap.empty else "—"
    hi_rate   = snap["Rate_Pct"].max()

    cards_html = (
        f'<div style="display:grid;grid-template-columns:repeat(5,1fr);gap:10px;margin-bottom:20px;">'
    )
    for lbl, val, sub, acc in [
        ("Avg Policy Rate",    f"{avg_rate:.2f}%",             f"{len(snap)} CBs tracked",   _BLUE),
        ("Hiking",             str(n_hiking),                   "vs 1 year ago",              _RED),
        ("Cutting",            str(n_cutting),                  "vs 1 year ago",              _GRN),
        ("On Hold",            str(n_hold),                     "change < ±10bps",            _AMB),
        ("Highest Rate",       f"{hi_rate:.2f}%",               hi_cb,                        _T2),
    ]:
        cards_html += (
            f'<div style="background:{_CARD};border:1px solid {_EDGE};border-radius:8px;'
            f'padding:14px 10px;text-align:center;">'
            f'<div style="font-size:10px;color:{_T2};text-transform:uppercase;'
            f'letter-spacing:.1em;margin-bottom:6px;">{lbl}</div>'
            f'<div style="font-size:22px;font-weight:700;color:{acc};">{val}</div>'
            f'<div style="font-size:11px;color:{_T3};margin-top:4px;">{sub}</div></div>'
        )
    cards_html += "</div>"
    st.markdown(cards_html, unsafe_allow_html=True)

    # Rates table
    snap_disp = snap[["Country", "Rate_Pct", "Change_1Y", "Date"]].copy()
    snap_disp["Rate (%)"]      = snap_disp["Rate_Pct"].round(2)
    snap_disp["Change 1Y (bp)"]= (snap_disp["Change_1Y"] * 100).round(0).astype("Int64")
    snap_disp["As of"]         = snap_disp["Date"].dt.strftime("%b %Y")
    snap_disp["Trend"]         = snap_disp["Change_1Y"].apply(
        lambda x: "▲ Hiking" if x > 0.01 else ("▼ Cutting" if x < -0.01 else "● Hold")
    )

    def _style_row(row):
        if "Hiking" in row["Trend"]:
            return [f"background-color:#1e1010"] * len(row)
        if "Cutting" in row["Trend"]:
            return [f"background-color:#0e1e14"] * len(row)
        return [""] * len(row)

    st.dataframe(
        snap_disp[["Country", "Rate (%)", "Change 1Y (bp)", "Trend", "As of"]]
        .sort_values("Rate (%)", ascending=False)
        .style.apply(_style_row, axis=1),
        use_container_width=True, hide_index=True,
    )


# ── History chart ──────────────────────────────────────────────────────────────

def _history(df: pd.DataFrame, countries: list[str], yr_from: int) -> None:
    _section("Policy Rate History", "Monthly rates since selected start year")

    fdf = df[df["Country"].isin(countries) & (df["Date"].dt.year >= yr_from)]
    if fdf.empty:
        _no_data()
        return

    fig = go.Figure()
    for country in countries:
        cdf = fdf[fdf["Country"] == country].sort_values("Date")
        if cdf.empty:
            continue
        fig.add_trace(go.Scatter(
            x=cdf["Date"], y=cdf["Rate_Pct"],
            name=country, mode="lines",
            line=dict(color=COUNTRY_COLORS.get(country, "#888"), width=2),
            hovertemplate=f"<b>{country}</b><br>%{{x|%b %Y}}: %{{y:.2f}}%<extra></extra>",
        ))
    fig.update_layout(
        height=420,
        title=dict(text="Central Bank Policy Rates (%)", font=dict(size=13, color=_T1), x=0),
        yaxis_title="Rate (%)",
        **_chart_layout(),
    )
    st.plotly_chart(fig, use_container_width=True)


# ── Rate cycle heatmap ────────────────────────────────────────────────────────

def _rate_cycles(df: pd.DataFrame, countries: list[str]) -> None:
    _section("Rate Cycle Overview", "Annual average rate per central bank — colour shows level")

    fdf = df[df["Country"].isin(countries)].copy()
    fdf["Year"] = fdf["Date"].dt.year
    pivot = (
        fdf.groupby(["Country", "Year"])["Rate_Pct"]
        .mean()
        .unstack("Year")
    )
    if pivot.empty:
        _no_data()
        return

    pivot = pivot.loc[pivot.index.isin(countries)]
    years = sorted(pivot.columns)

    fig = go.Figure(go.Heatmap(
        z=pivot.values,
        x=[str(y) for y in years],
        y=pivot.index.tolist(),
        colorscale=[
            [0.0,  "#1d4ed8"],
            [0.3,  "#2dd4bf"],
            [0.6,  "#f59e0b"],
            [1.0,  "#ef4444"],
        ],
        hovertemplate="%{y}<br>%{x}: %{z:.2f}%<extra></extra>",
        colorbar=dict(title="Rate %", tickfont=dict(color=_T1), titlefont=dict(color=_T1)),
    ))
    fig.update_layout(
        height=max(300, len(pivot) * 34 + 80),
        title=dict(text="Annual Average Policy Rate (%) by Country & Year",
                   font=dict(size=13, color=_T1), x=0),
        xaxis=dict(tickfont=dict(color=_T2), side="bottom"),
        yaxis=dict(tickfont=dict(color=_T1)),
        **_chart_layout(margin=dict(l=160, r=80, t=44, b=44)),
    )
    st.plotly_chart(fig, use_container_width=True)


# ── Real policy rate ───────────────────────────────────────────────────────────

def _real_rates(df: pd.DataFrame, ann: pd.DataFrame, countries: list[str], yr_from: int) -> None:
    _section(
        "Real Policy Rate",
        "Nominal policy rate − CPI inflation · negative = accommodative, positive = restrictive",
    )

    if ann.empty or "CPI_Pct" not in ann.columns:
        _no_data("Annual IMF data unavailable — refresh all data.")
        return

    # Annual average of monthly policy rate
    fdf = df[df["Country"].isin(countries)].copy()
    fdf["Year"] = fdf["Date"].dt.year
    ann_rate = (
        fdf.groupby(["Country", "Year"])["Rate_Pct"].mean().reset_index()
        .rename(columns={"Rate_Pct": "Nominal_Rate"})
    )

    merged = ann_rate.merge(
        ann[ann["Country"].isin(countries)][["Country", "Year", "CPI_Pct"]],
        on=["Country", "Year"], how="inner",
    )
    merged["Real_Rate"] = merged["Nominal_Rate"] - merged["CPI_Pct"]
    merged = merged[merged["Year"] >= yr_from]

    if merged.empty:
        _no_data()
        return

    fig = go.Figure()
    for country in countries:
        cdf = merged[merged["Country"] == country].sort_values("Year")
        if cdf.empty:
            continue
        fig.add_trace(go.Scatter(
            x=cdf["Year"], y=cdf["Real_Rate"],
            name=country, mode="lines+markers",
            line=dict(color=COUNTRY_COLORS.get(country, "#888"), width=2),
            marker=dict(size=5),
            hovertemplate=f"<b>{country}</b><br>%{{x}}: %{{y:.2f}}%<extra></extra>",
        ))
    fig.add_hline(y=0, line=dict(color=_T3, dash="dot", width=1.5))
    fig.update_layout(
        height=400,
        title=dict(text="Real Policy Rate = Nominal − CPI (%)",
                   font=dict(size=13, color=_T1), x=0),
        yaxis_title="Real Rate (%)",
        **_chart_layout(),
    )
    st.plotly_chart(fig, use_container_width=True)
    st.markdown(
        "**Above zero** — real rates are positive (restrictive). "
        "**Below zero** — real rates are negative (accommodative / financial repression).",
    )


# ── Main entry point ───────────────────────────────────────────────────────────

def central_bank_rates() -> None:
    st.markdown(
        '<h2 style="color:#0f172a;margin:0 0 2px;">Central Bank Policy Rates</h2>'
        '<div style="font-size:12px;color:#475569;">'
        'Source: BIS WS_CBPOL_M · 40+ central banks · monthly data · back to 2000</div>'
        '<hr style="border:none;border-top:1px solid #e2e8f0;margin:10px 0 6px;">',
        unsafe_allow_html=True,
    )

    # ── Sidebar ───────────────────────────────────────────────────────────────
    st.sidebar.markdown(
        f'<div style="font-size:10px;color:{_T2};text-transform:uppercase;'
        f'letter-spacing:.1em;margin:16px 0 6px;padding-bottom:4px;'
        f'border-bottom:1px solid {_EDGE};">Central Banks</div>',
        unsafe_allow_html=True,
    )
    countries = st.sidebar.multiselect(
        "Countries", ALL_NAMES, default=CORE_NAMES,
        key="cbr_countries", label_visibility="collapsed",
    )
    yr_from = st.sidebar.slider("From year", 2000, 2023, 2008, key="cbr_yr_from")

    st.sidebar.markdown(
        f'<div style="font-size:10px;color:{_T2};text-transform:uppercase;'
        f'letter-spacing:.1em;margin:14px 0 6px;padding-bottom:4px;'
        f'border-bottom:1px solid {_EDGE};">Data</div>',
        unsafe_allow_html=True,
    )
    for cache, label in [(POLICY_CACHE, "Policy rates"), (ANNUAL_CACHE, "Annual macro")]:
        if cache.exists():
            from datetime import datetime
            mtime = datetime.fromtimestamp(cache.stat().st_mtime)
            st.sidebar.caption(f"{label}: {mtime.strftime('%d %b %Y')}")
        else:
            st.sidebar.caption(f"{label}: not cached")

    refresh = st.sidebar.button("Refresh Data", key="cbr_refresh")

    # ── Load ──────────────────────────────────────────────────────────────────
    if refresh:
        with st.spinner("Fetching policy rates from BIS…"):
            df = refresh_policy_rates()
        with st.spinner("Fetching annual macro from IMF…"):
            ann = refresh_annual()
    else:
        df  = load_policy_rates()
        ann = load_annual()

    if df.empty:
        st.warning(
            "No policy rate data loaded yet. Click **Refresh Data** in the sidebar "
            "to fetch from BIS (first load takes ~30 seconds).",
            icon="⚠️",
        )
        return

    if not countries:
        st.info("Select at least one central bank in the sidebar.")
        return

    # Filter to countries that actually exist in the data
    available = df["Country"].unique().tolist()
    countries = [c for c in countries if c in available]
    if not countries:
        st.info("Selected central banks have no data yet. Try Refresh Data.")
        return

    _snapshot(df, ann, countries)
    _history(df, countries, yr_from)
    _rate_cycles(df, countries)
    _real_rates(df, ann, countries, yr_from)

    st.markdown(
        "**Data source:** BIS Central Bank Policy Rates (WS_CBPOL_M). "
        "Covers 40+ central banks at monthly frequency. "
        "Real rate = nominal policy rate − IMF WEO CPI inflation (annual average)."
    )
