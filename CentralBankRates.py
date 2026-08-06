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
    ANNUAL_CACHE, POLICY_CACHE, YIELD_CACHE, CB_RATES_CACHE, MMKT_CACHE,
    load_annual, load_policy_rates, load_teny_yields,
    load_cb_rates_direct, load_mmkt_rates,
    refresh_policy_rates, refresh_annual, refresh_teny_yields,
    refresh_cb_rates_direct, refresh_mmkt_rates,
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
        base = "color:#0f172a;"
        if "Hiking" in row["Trend"]:
            return [base + "background-color:#fecaca"] * len(row)
        if "Cutting" in row["Trend"]:
            return [base + "background-color:#bbf7d0"] * len(row)
        return [base] * len(row)

    st.dataframe(
        snap_disp[["Country", "Rate (%)", "Change 1Y (bp)", "Trend", "As of"]]
        .sort_values("Rate (%)", ascending=False)
        .style.apply(_style_row, axis=1),
        use_container_width=True, hide_index=True,
    )


# ── History chart ──────────────────────────────────────────────────────────────

def _history(df: pd.DataFrame, yld: pd.DataFrame, countries: list[str], yr_from: int) -> None:
    _section(
        "Policy Rate & 10Y Yield History",
        "Solid = policy rate · Dashed = 10Y government bond yield (FRED/OECD, where available)",
    )

    fdf = df[df["Country"].isin(countries) & (df["Date"].dt.year >= yr_from)]
    if fdf.empty:
        _no_data()
        return
    ydf = (
        yld[yld["Country"].isin(countries) & (yld["Date"].dt.year >= yr_from)]
        if not yld.empty else pd.DataFrame()
    )

    fig = go.Figure()
    for country in countries:
        color = COUNTRY_COLORS.get(country, "#888")
        cdf = fdf[fdf["Country"] == country].sort_values("Date")
        if cdf.empty:
            continue
        fig.add_trace(go.Scatter(
            x=cdf["Date"], y=cdf["Rate_Pct"],
            name=f"{country} (Policy)", mode="lines",
            line=dict(color=color, width=2),
            hovertemplate=f"<b>{country} Policy</b><br>%{{x|%b %Y}}: %{{y:.2f}}%<extra></extra>",
        ))
        if not ydf.empty:
            yc = ydf[ydf["Country"] == country].sort_values("Date")
            if not yc.empty:
                fig.add_trace(go.Scatter(
                    x=yc["Date"], y=yc["Yield_Pct"],
                    name=f"{country} (10Y)", mode="lines",
                    line=dict(color=color, width=1.5, dash="dash"),
                    opacity=0.7,
                    hovertemplate=f"<b>{country} 10Y</b><br>%{{x|%b %Y}}: %{{y:.2f}}%<extra></extra>",
                ))
    fig.update_layout(
        height=450,
        title=dict(text="Policy Rate vs 10Y Government Yield (%)",
                   font=dict(size=13, color=_T1), x=0),
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
        **_chart_layout(
            margin=dict(l=160, r=80, t=44, b=44),
            xaxis=dict(tickfont=dict(color=_T2), side="bottom",
                       gridcolor=_EDGE, showline=True, linecolor=_EDGE),
            yaxis=dict(tickfont=dict(color=_T1),
                       gridcolor=_EDGE, showline=True, linecolor=_EDGE),
        ),
    )
    st.plotly_chart(fig, use_container_width=True)


# ── Yield curve slope ─────────────────────────────────────────────────────────

def _yield_curve_slope(df: pd.DataFrame, yld: pd.DataFrame, countries: list[str], yr_from: int) -> None:
    _section(
        "Yield Curve Slope (10Y − Policy Rate)",
        "Positive = normal/upward-sloping · Negative = inverted — historically precedes recessions",
    )

    if yld.empty:
        _no_data("10Y yield data not loaded — click Refresh Data.")
        return

    pol = df[df["Country"].isin(countries)][["Country", "Date", "Rate_Pct"]].copy()
    pol["YearMonth"] = pol["Date"].dt.to_period("M")
    yf  = yld[yld["Country"].isin(countries)][["Country", "Date", "Yield_Pct"]].copy()
    yf["YearMonth"] = yf["Date"].dt.to_period("M")

    merged = pol.merge(yf[["Country", "YearMonth", "Yield_Pct"]], on=["Country", "YearMonth"], how="inner")
    merged["Slope"] = merged["Yield_Pct"] - merged["Rate_Pct"]
    merged = merged[merged["Date"].dt.year >= yr_from]

    if merged.empty:
        _no_data("No overlapping data for slope calculation (10Y yields only available for select DM countries).")
        return

    fig = go.Figure()
    for country in countries:
        cdf = merged[merged["Country"] == country].sort_values("Date")
        if cdf.empty:
            continue
        fig.add_trace(go.Scatter(
            x=cdf["Date"], y=cdf["Slope"],
            name=country, mode="lines",
            line=dict(color=COUNTRY_COLORS.get(country, "#888"), width=2),
            hovertemplate=f"<b>{country}</b><br>%{{x|%b %Y}}: %{{y:+.2f}}pp<extra></extra>",
        ))

    fig.add_hline(y=0, line=dict(color=_AMB, dash="dot", width=1.5),
                  annotation_text="Flat / Inversion threshold", annotation_font_color=_AMB)
    fig.update_layout(
        height=400,
        title=dict(text="Yield Curve Slope = 10Y Yield − Policy Rate (pp)",
                   font=dict(size=13, color=_T1), x=0),
        yaxis_title="Slope (pp)",
        **_chart_layout(),
    )
    st.plotly_chart(fig, use_container_width=True)
    st.markdown(
        "**Positive slope:** long rates above policy rate — normal conditions, markets expect future growth/inflation.  \n"
        "**Negative slope (inversion):** policy rate above 10Y yield — signals tight monetary conditions; "
        "a persistent inversion has historically preceded US recessions by 12–24 months."
    )


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

def _money_markets(mmkt: pd.DataFrame, yr_from: int) -> None:
    _section(
        "Money Market Rates",
        "SOFR · Fed Funds Effective Rate · daily from FRED",
    )

    if mmkt.empty:
        _no_data("No money market data — click Refresh Data.")
        return

    fdf = mmkt[mmkt["Date"].dt.year >= yr_from]
    if fdf.empty:
        _no_data()
        return

    MMKT_COLORS = {"SOFR": _BLUE, "Fed Funds (Eff.)": _GRN}

    fig = go.Figure()
    for series in [s for s in ["SOFR", "Fed Funds (Eff.)"] if s in fdf["Series"].unique()]:
        cdf = fdf[fdf["Series"] == series].sort_values("Date")
        fig.add_trace(go.Scatter(
            x=cdf["Date"], y=cdf["Rate_Pct"],
            name=series, mode="lines",
            line=dict(color=MMKT_COLORS.get(series, "#888"), width=2),
            hovertemplate=f"<b>{series}</b><br>%{{x|%d %b %Y}}: %{{y:.4f}}%<extra></extra>",
        ))

    fig.update_layout(
        height=380,
        title=dict(text="Money Market Rates (%)",
                   font=dict(size=13, color=_T1), x=0),
        yaxis_title="Rate (%)",
        **_chart_layout(),
    )
    st.plotly_chart(fig, use_container_width=True)
    st.markdown(
        "**SOFR** (Secured Overnight Financing Rate) is collateralised (tri-party repo) and replaced LIBOR "
        "as the benchmark US overnight rate from June 2023. "
        "**Fed Funds Effective** is the volume-weighted median of uncollateralised overnight interbank lending. "
        "SOFR typically trades a few basis points below Fed Funds. "
        "Source: FRED (SOFR, DFF)."
    )


def central_bank_rates() -> None:
    st.markdown(
        '<h2 style="color:#0f172a;margin:0 0 2px;">Central Bank Policy Rates</h2>'
        '<div style="font-size:12px;color:#475569;">'
        'Policy rates · SOFR · Fed Funds · Yield curve slope · Real rates</div>'
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
    from datetime import datetime
    for cache, label in [
        (POLICY_CACHE,   "Policy rates (BIS)"),
        (CB_RATES_CACHE, "Policy rates (direct)"),
        (MMKT_CACHE,     "Money market"),
        (YIELD_CACHE,    "10Y yields"),
        (ANNUAL_CACHE,   "Annual macro"),
    ]:
        if cache.exists():
            mtime = datetime.fromtimestamp(cache.stat().st_mtime)
            st.sidebar.caption(f"{label}: {mtime.strftime('%d %b %Y')}")
        else:
            st.sidebar.caption(f"{label}: not cached")

    refresh = st.sidebar.button("Refresh Data", key="cbr_refresh")

    # ── Load ──────────────────────────────────────────────────────────────────
    if refresh:
        with st.spinner("Fetching policy rates from BIS…"):
            df_bis = refresh_policy_rates()
        if df_bis.empty:
            with st.spinner("BIS unavailable — fetching from ECB/BoE/FRED…"):
                df = refresh_cb_rates_direct()
        else:
            df = df_bis
        with st.spinner("Fetching money market rates from FRED…"):
            mmkt = refresh_mmkt_rates()
        with st.spinner("Fetching 10Y yields from FRED…"):
            yld = refresh_teny_yields()
        with st.spinner("Fetching annual macro from IMF…"):
            ann = refresh_annual()
    else:
        df_bis = load_policy_rates()
        df     = df_bis if not df_bis.empty else load_cb_rates_direct()
        mmkt   = load_mmkt_rates()
        yld    = load_teny_yields()
        ann    = load_annual()

    # Source label for transparency
    if df_bis.empty and not df.empty:
        st.info(
            "ℹ️ BIS API unavailable — policy rates shown for **US, Euro Area, UK** "
            "via FRED / ECB SDW / Bank of England. Click **Refresh Data** to retry.",
            icon=None,
        )
    elif df.empty:
        st.warning(
            "No policy rate data loaded. Click **Refresh Data** in the sidebar.",
            icon="⚠️",
        )

    if not countries:
        st.info("Select at least one central bank in the sidebar.")
        return

    # Policy rate sections (show if any data available)
    if not df.empty:
        available = df["Country"].unique().tolist()
        sel = [c for c in countries if c in available]
        if sel:
            _snapshot(df, ann, sel)
            _history(df, yld, sel, yr_from)
            _yield_curve_slope(df, yld, sel, yr_from)
            _rate_cycles(df, sel)
            _real_rates(df, ann, sel, yr_from)
        else:
            st.info("Selected central banks have no data. Try Refresh Data.")

    # Money market rates always shown (FRED, independent of BIS)
    _money_markets(mmkt, yr_from)

    src = "BIS WS_CBPOL_M" if not df_bis.empty else "FRED (US Fed Funds), ECB SDW, Bank of England"
    st.markdown(
        f"**Policy rate source:** {src}. "
        "**10Y yields:** FRED/OECD IRLT series (developed markets). "
        "**Money market:** FRED SOFR, DFF. "
        "Real rate = nominal policy rate − IMF WEO CPI inflation (annual average)."
    )
