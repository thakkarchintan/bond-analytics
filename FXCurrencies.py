"""
FX & Currencies Dashboard
Sources: FRED (spot rates vs USD) · IMF (policy rate differentials).
Shows currency performance, USD index, carry trade indicators.
"""
from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from global_macro_data import (
    COUNTRY_COLORS, CORE_NAMES, ALL_NAMES, FX_SERIES,
    FX_CACHE, POLICY_CACHE, REER_CACHE,
    load_fx, load_policy_rates, load_reer,
    refresh_fx, refresh_policy_rates, refresh_reer,
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

# Default countries with FX data
_FX_COUNTRIES = [meta["country"] for meta in FX_SERIES.values()]
_CORE_FX      = [c for c in [
    "Japan", "Euro Area", "United Kingdom", "China",
    "India", "Canada", "Australia", "Brazil", "South Korea",
] if c in _FX_COUNTRIES]


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

def _snapshot(df: pd.DataFrame, countries: list[str]) -> None:
    _section("FX Snapshot", "Latest available rates — local currency units per 1 USD")

    # Build ccy map
    ccy_map = {meta["country"]: meta["ccy"] for meta in FX_SERIES.values()}

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

    # 1-year change
    one_yr_ago = latest["Date"].max() - pd.DateOffset(years=1)
    prev = (
        df[df["Country"].isin(countries) & (df["Date"] <= one_yr_ago)]
        .sort_values("Date")
        .groupby("Country")
        .last()
        .reset_index()
        .rename(columns={"LocalPerUSD": "Prev"})
        [["Country", "Prev"]]
    )
    snap = latest.merge(prev, on="Country", how="left")
    snap["Chg1Y_Pct"] = (snap["LocalPerUSD"] / snap["Prev"] - 1) * 100
    snap["Currency"]  = snap["Country"].map(ccy_map)
    snap["As of"]     = snap["Date"].dt.strftime("%b %Y")

    snap_disp = snap[["Country", "Currency", "LocalPerUSD", "Chg1Y_Pct", "As of"]].copy()
    snap_disp["Rate (local/USD)"]  = snap_disp["LocalPerUSD"].round(4)
    snap_disp["YoY Change (%)"]    = snap_disp["Chg1Y_Pct"].round(2)

    def _style(row):
        v = row["YoY Change (%)"]
        if isinstance(v, float) and v > 3:
            return ["background-color:#1e1010"] * len(row)  # weakened vs USD
        if isinstance(v, float) and v < -3:
            return ["background-color:#0e1e14"] * len(row)  # strengthened vs USD
        return [""] * len(row)

    st.dataframe(
        snap_disp[["Country", "Currency", "Rate (local/USD)", "YoY Change (%)", "As of"]]
        .sort_values("Country")
        .style.apply(_style, axis=1),
        use_container_width=True, hide_index=True,
    )
    st.caption(
        "Rate = local currency units per 1 USD. "
        "YoY Change > 0 = local currency weakened vs USD (took more units to buy 1 USD)."
    )


# ── Indexed performance chart ─────────────────────────────────────────────────

def _indexed(df: pd.DataFrame, countries: list[str], base_year: int) -> None:
    _section(
        "Currency Performance vs USD",
        f"Indexed to 100 at Jan {base_year} · above 100 = local currency weakened vs USD",
    )

    fdf = df[df["Country"].isin(countries) & (df["Date"].dt.year >= base_year)].copy()
    if fdf.empty:
        _no_data()
        return

    fig = go.Figure()
    for country in countries:
        cdf = fdf[fdf["Country"] == country].sort_values("Date")
        if cdf.empty:
            continue
        base_rows = cdf[cdf["Date"].dt.year == base_year]
        if base_rows.empty:
            continue
        base_val = base_rows["LocalPerUSD"].mean()
        if base_val == 0 or pd.isna(base_val):
            continue
        cdf = cdf.copy()
        cdf["Indexed"] = cdf["LocalPerUSD"] / base_val * 100
        ccy = next((m["ccy"] for m in FX_SERIES.values() if m["country"] == country), "")
        fig.add_trace(go.Scatter(
            x=cdf["Date"], y=cdf["Indexed"],
            name=f"{country} ({ccy})", mode="lines",
            line=dict(color=COUNTRY_COLORS.get(country, "#888"), width=2),
            hovertemplate=f"<b>{country}</b><br>%{{x|%b %Y}}: %{{y:.1f}}<extra></extra>",
        ))
    fig.add_hline(y=100, line=dict(color=_T3, dash="dot", width=1.5),
                  annotation_text=f"Base ({base_year}=100)", annotation_font_color=_T3)
    fig.update_layout(
        height=420,
        title=dict(text=f"FX Performance vs USD — indexed to Jan {base_year} (100 = base)",
                   font=dict(size=13, color=_T1), x=0),
        yaxis_title="Index (100 = base year)",
        **_chart_layout(),
    )
    st.plotly_chart(fig, use_container_width=True)
    st.markdown(
        f"**Above 100:** local currency has weakened vs USD since {base_year} (more units per dollar).  \n"
        f"**Below 100:** local currency has strengthened vs USD."
    )


# ── YoY returns heatmap ───────────────────────────────────────────────────────

def _returns_heatmap(df: pd.DataFrame, countries: list[str]) -> None:
    _section("Annual FX Returns vs USD", "% change in local/USD rate per year · green = local strengthened")

    fdf = df[df["Country"].isin(countries)].copy()
    fdf["Year"] = fdf["Date"].dt.year
    annual = fdf.groupby(["Country", "Year"])["LocalPerUSD"].mean().reset_index()

    pivot = annual.pivot(index="Country", columns="Year", values="LocalPerUSD")
    # YoY % change (positive = local weakened = bad for local holders)
    pct = pivot.pct_change(axis=1) * 100
    pct = pct.dropna(how="all", axis=1)
    if pct.empty:
        _no_data()
        return

    years = sorted(pct.columns)

    fig = go.Figure(go.Heatmap(
        z=pct.values,
        x=[str(y) for y in years],
        y=pct.index.tolist(),
        colorscale=[
            [0.0, "#10b981"],   # green = strengthened (rate fell)
            [0.5, "#1e293b"],   # neutral
            [1.0, "#ef4444"],   # red = weakened (rate rose)
        ],
        zmid=0,
        hovertemplate="%{y}<br>%{x}: %{z:.1f}%<extra></extra>",
        colorbar=dict(
            title="% chg",
            tickfont=dict(color=_T1), titlefont=dict(color=_T1),
        ),
    ))
    fig.update_layout(
        height=max(280, len(pct) * 32 + 80),
        title=dict(text="Annual FX Return vs USD (% change in local/USD rate)",
                   font=dict(size=13, color=_T1), x=0),
        xaxis=dict(tickfont=dict(color=_T2), side="bottom"),
        yaxis=dict(tickfont=dict(color=_T1)),
        **_chart_layout(margin=dict(l=150, r=80, t=44, b=44)),
    )
    st.plotly_chart(fig, use_container_width=True)
    st.caption("Green = local currency strengthened vs USD. Red = weakened.")


# ── REER ─────────────────────────────────────────────────────────────────────

def _reer(reer: pd.DataFrame, countries: list[str], yr_from: int) -> None:
    _section(
        "Real Effective Exchange Rate (REER)",
        "BIS broad REER · 2020=100 · above 100 = real appreciation vs trading partners",
    )

    if reer.empty:
        _no_data("REER data not loaded — click Refresh Data.")
        return

    fdf = reer[reer["Country"].isin(countries) & (reer["Date"].dt.year >= yr_from)]
    if fdf.empty:
        _no_data()
        return

    fig = go.Figure()
    for country in countries:
        cdf = fdf[fdf["Country"] == country].sort_values("Date")
        if cdf.empty:
            continue
        fig.add_trace(go.Scatter(
            x=cdf["Date"], y=cdf["REER"],
            name=country, mode="lines",
            line=dict(color=COUNTRY_COLORS.get(country, "#888"), width=2),
            hovertemplate=f"<b>{country}</b><br>%{{x|%b %Y}}: %{{y:.1f}}<extra></extra>",
        ))

    fig.add_hline(y=100, line=dict(color=_T3, dash="dot", width=1.5),
                  annotation_text="2020=100", annotation_font_color=_T3)
    fig.update_layout(
        height=420,
        title=dict(text="Real Effective Exchange Rate (2020=100)",
                   font=dict(size=13, color=_T1), x=0),
        yaxis_title="REER Index (2020=100)",
        **_chart_layout(),
    )
    st.plotly_chart(fig, use_container_width=True)
    st.markdown(
        "**Above 100:** currency has appreciated in real terms since 2020 vs trading partners "
        "— potential loss of export competitiveness.  \n"
        "**Below 100:** real depreciation — exports more competitive. "
        "Source: BIS Effective Exchange Rates, broad basket, monthly."
    )


# ── Rate differential vs FX ───────────────────────────────────────────────────

def _carry_scatter(fx: pd.DataFrame, pol: pd.DataFrame, countries: list[str], year: int) -> None:
    _section(
        "Rate Differential vs FX Performance",
        f"Policy rate vs US ({year}) · carry: higher-rate currencies tend to attract capital inflows",
    )

    if pol.empty:
        _no_data("Policy rate data not loaded — click Refresh Data.")
        return

    # Annual average FX change
    fdf = fx[fx["Country"].isin(countries)].copy()
    fdf["Year"] = fdf["Date"].dt.year
    fx_ann = fdf.groupby(["Country", "Year"])["LocalPerUSD"].mean().reset_index()
    fx_chg = fx_ann.copy()
    fx_chg["FX_Chg"] = fx_chg.groupby("Country")["LocalPerUSD"].pct_change() * 100
    snap_fx = fx_chg[fx_chg["Year"] == year][["Country", "FX_Chg"]]

    # Annual average policy rate from BIS
    pol_copy = pol.copy()
    pol_copy["Year"] = pol_copy["Date"].dt.year
    pol_ann  = pol_copy.groupby(["Country", "Year"])["Rate_Pct"].mean().reset_index()
    snap_pol = pol_ann[pol_ann["Year"] == year][["Country", "Rate_Pct"]].copy()

    us = snap_pol[snap_pol["Country"] == "United States"]["Rate_Pct"]
    us_rate = float(us.values[0]) if len(us) > 0 else 0.0
    snap_pol["RateDiff"] = snap_pol["Rate_Pct"] - us_rate

    merged = snap_fx.merge(snap_pol, on="Country", how="inner").dropna(subset=["FX_Chg", "RateDiff"])
    if merged.empty:
        _no_data()
        return

    fig = go.Figure()
    for _, row in merged.iterrows():
        fig.add_trace(go.Scatter(
            x=[row["RateDiff"]], y=[-row["FX_Chg"]],  # flip: positive = strengthened
            mode="markers+text",
            name=row["Country"],
            text=[row["Country"]],
            textposition="top center",
            textfont=dict(size=9, color=_T1),
            marker=dict(
                color=COUNTRY_COLORS.get(row["Country"], "#888"),
                size=14, opacity=0.9,
                line=dict(width=1.5, color=_BG),
            ),
            showlegend=False,
            hovertemplate=(
                f"<b>{row['Country']}</b><br>"
                f"Rate vs US: {row['RateDiff']:+.2f}pp  (Policy: {row['Rate_Pct']:.2f}%)<br>"
                f"FX vs USD: {-row['FX_Chg']:.1f}% ({'strengthened' if row['FX_Chg'] < 0 else 'weakened'})"
                "<extra></extra>"
            ),
        ))

    fig.add_vline(x=0, line=dict(color=_T3, dash="dot", width=1))
    fig.add_hline(y=0, line=dict(color=_T3, dash="dot", width=1))
    fig.update_layout(
        height=420,
        title=dict(text=f"Policy Rate Differential vs US (x) · FX vs USD (y) — {year}",
                   font=dict(size=13, color=_T1), x=0),
        xaxis_title="Policy Rate vs US (pp)  ←lower | higher→",
        yaxis_title="FX vs USD (% — positive = local strengthened)",
        **_chart_layout(margin=dict(l=72, r=20, t=44, b=60)),
    )
    st.plotly_chart(fig, use_container_width=True)
    st.markdown(
        "**Carry trade logic:** countries with higher policy rates vs the US should theoretically attract "
        "capital inflows and see currency strength (upper-right). In practice, high-inflation EMs often "
        "offset carry with depreciation — uncovered interest rate parity."
    )


# ── Main entry ────────────────────────────────────────────────────────────────

def fx_currencies() -> None:
    st.markdown(
        '<h2 style="color:#0f172a;margin:0 0 2px;">FX &amp; Currencies</h2>'
        '<div style="font-size:12px;color:#475569;">'
        'Spot rates vs USD · REER indices (BIS) · rate differential · '
        'Source: FRED (spot) · BIS (REER) · BIS (policy rates)</div>'
        '<hr style="border:none;border-top:1px solid #e2e8f0;margin:10px 0 6px;">',
        unsafe_allow_html=True,
    )

    st.sidebar.markdown(
        f'<div style="font-size:10px;color:{_T2};text-transform:uppercase;'
        f'letter-spacing:.1em;margin:16px 0 6px;padding-bottom:4px;'
        f'border-bottom:1px solid {_EDGE};">Currencies</div>',
        unsafe_allow_html=True,
    )
    countries = st.sidebar.multiselect(
        "Countries", _FX_COUNTRIES, default=_CORE_FX,
        key="fx_countries", label_visibility="collapsed",
    )
    base_year = st.sidebar.slider("Index base year", 2005, 2020, 2015, key="fx_base_year")
    snap_year = st.sidebar.slider("Snapshot year",   2005, 2025, 2023, key="fx_snap_year")

    st.sidebar.markdown(
        f'<div style="font-size:10px;color:{_T2};text-transform:uppercase;'
        f'letter-spacing:.1em;margin:14px 0 6px;padding-bottom:4px;'
        f'border-bottom:1px solid {_EDGE};">Data</div>',
        unsafe_allow_html=True,
    )
    for cache, label in [
        (FX_CACHE,     "FX spot rates"),
        (REER_CACHE,   "REER (BIS)"),
        (POLICY_CACHE, "Policy rates"),
    ]:
        if cache.exists():
            from datetime import datetime
            mtime = datetime.fromtimestamp(cache.stat().st_mtime)
            st.sidebar.caption(f"{label}: {mtime.strftime('%d %b %Y')}")
        else:
            st.sidebar.caption(f"{label}: not cached")
    refresh = st.sidebar.button("Refresh Data", key="fx_refresh")

    if refresh:
        with st.spinner("Fetching FX rates from FRED…"):
            df = refresh_fx()
        with st.spinner("Fetching REER from BIS…"):
            reer = refresh_reer()
        with st.spinner("Fetching policy rates from BIS…"):
            pol = refresh_policy_rates()
    else:
        df   = load_fx()
        reer = load_reer()
        pol  = load_policy_rates()

    if df.empty:
        st.warning(
            "No FX data loaded. Click **Refresh Data** to fetch from FRED (takes ~15 seconds).",
            icon="⚠️",
        )
        return

    if not countries:
        st.info("Select at least one currency in the sidebar.")
        return

    available = df["Country"].unique().tolist()
    countries  = [c for c in countries if c in available]
    if not countries:
        st.info("Selected currencies have no data yet. Try Refresh Data.")
        return

    _snapshot(df, countries)
    _indexed(df, countries, base_year)
    _reer(reer, countries, base_year)
    _returns_heatmap(df, countries)
    _carry_scatter(df, pol, countries, snap_year)

    st.markdown(
        "**Data sources:** FRED (spot bilateral rates, daily → monthly avg). "
        "BIS WS_EER_M (broad real effective exchange rates, 2020=100). "
        "BIS WS_CBPOL_M (policy rates for rate differential calculation)."
    )
