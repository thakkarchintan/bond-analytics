"""
Fiscal Scorecard
Source: IMF World Economic Outlook — govt debt, fiscal balance, primary balance, current account.
"""
from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from global_macro_data import (
    COUNTRY_COLORS, CORE_NAMES, ALL_NAMES,
    ANNUAL_CACHE, load_annual, refresh_annual,
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


def _no_data(msg: str = "No data — click Refresh Data in the sidebar.") -> None:
    st.info(msg, icon="ℹ️")


# ── Snapshot ──────────────────────────────────────────────────────────────────

def _snapshot(df: pd.DataFrame, countries: list[str], year: int) -> None:
    _section("Fiscal Snapshot", f"Cross-country overview · {year}")

    snap = df[(df["Year"] == year) & (df["Country"].isin(countries))].copy()
    if snap.empty:
        _no_data()
        return

    def _pct(col: str) -> str:
        v = snap[col].mean() if col in snap.columns else float("nan")
        return f"{v:.1f}%" if pd.notna(v) else "—"

    def _pct_best(col: str, higher_better: bool = False) -> str:
        if col not in snap.columns:
            return "—"
        vals = snap.dropna(subset=[col])
        if vals.empty:
            return "—"
        idx = vals[col].idxmax() if higher_better else vals[col].idxmin()
        return vals.loc[idx, "Country"]

    html = '<div style="display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin-bottom:20px;">'
    for lbl, val, sub, acc in [
        ("Avg Govt Debt/GDP",   _pct("DebtGDP_Pct"),       "gross govt obligations",    _RED),
        ("Avg Fiscal Balance",  _pct("FiscalBal_Pct"),      "surplus(+) / deficit(−)",   _AMB),
        ("Most Indebted",       _pct_best("DebtGDP_Pct"),   "highest debt/GDP",          _T2),
        ("Best Fiscal Balance", _pct_best("FiscalBal_Pct", True), "smallest deficit",    _GRN),
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

    # Country scorecard table
    cols = {
        "DebtGDP_Pct":       "Debt/GDP %",
        "FiscalBal_Pct":     "Fiscal Bal %",
        "PrimaryBal_Pct":    "Primary Bal %",
        "CurrentAcct_Pct":   "Current Acct %",
        "RealGDP_Pct":       "Real GDP %",
    }
    avail = {k: v for k, v in cols.items() if k in snap.columns}
    rows = []
    for _, row in snap.set_index("Country").reindex(countries).iterrows():
        entry = {"Country": row.name}
        for k, v in avail.items():
            val = row.get(k, float("nan"))
            entry[v] = f"{val:.1f}%" if pd.notna(val) else "—"
        rows.append(entry)
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)


# ── Debt/GDP ──────────────────────────────────────────────────────────────────

def _debt(df: pd.DataFrame, countries: list[str], year: int, yr_from: int) -> None:
    _section("Government Debt / GDP", "Gross government obligations as % of GDP")

    c1, c2 = st.columns([3, 2])

    with c1:
        # Time series
        fdf = df[df["Country"].isin(countries) & (df["Year"] >= yr_from)].dropna(subset=["DebtGDP_Pct"])
        fig = go.Figure()
        for country in countries:
            cdf = fdf[fdf["Country"] == country].sort_values("Year")
            if cdf.empty:
                continue
            fig.add_trace(go.Scatter(
                x=cdf["Year"], y=cdf["DebtGDP_Pct"],
                name=country, mode="lines+markers",
                line=dict(color=COUNTRY_COLORS.get(country, "#888"), width=2),
                marker=dict(size=4),
                hovertemplate=f"<b>{country}</b><br>%{{x}}: %{{y:.1f}}%<extra></extra>",
            ))
        fig.add_hline(y=100, line=dict(color=_AMB, dash="dot", width=1.5),
                      annotation_text="100% threshold", annotation_font_color=_AMB)
        fig.update_layout(
            height=380,
            title=dict(text=f"Govt Debt / GDP — {yr_from}→{year}", font=dict(size=13, color=_T1), x=0),
            yaxis_title="Debt/GDP %",
            **_chart_layout(),
        )
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        # Ranking bar
        snap = (
            df[(df["Year"] == year) & (df["Country"].isin(countries))]
            .dropna(subset=["DebtGDP_Pct"])
            .sort_values("DebtGDP_Pct")
        )
        if not snap.empty:
            fig2 = go.Figure(go.Bar(
                x=snap["DebtGDP_Pct"], y=snap["Country"],
                orientation="h",
                marker_color=[COUNTRY_COLORS.get(c, "#888") for c in snap["Country"]],
                hovertemplate="%{y}: %{x:.1f}%<extra></extra>",
            ))
            fig2.add_vline(x=100, line=dict(color=_AMB, dash="dot", width=1))
            fig2.update_layout(
                height=380,
                title=dict(text=f"Ranking ({year})", font=dict(size=13, color=_T1), x=0),
                xaxis_title="Debt/GDP %", showlegend=False,
                **_chart_layout(margin=dict(l=130, r=20, t=44, b=44)),
            )
            st.plotly_chart(fig2, use_container_width=True)


# ── Fiscal balance ────────────────────────────────────────────────────────────

def _fiscal_balance(df: pd.DataFrame, countries: list[str], year: int, yr_from: int) -> None:
    _section(
        "Fiscal Balance",
        "General government net lending/borrowing as % of GDP — surplus (+) / deficit (−)",
    )

    c1, c2 = st.columns([3, 2])

    with c1:
        fdf = df[df["Country"].isin(countries) & (df["Year"] >= yr_from)].dropna(subset=["FiscalBal_Pct"])
        fig = go.Figure()
        for country in countries:
            cdf = fdf[fdf["Country"] == country].sort_values("Year")
            if cdf.empty:
                continue
            fig.add_trace(go.Scatter(
                x=cdf["Year"], y=cdf["FiscalBal_Pct"],
                name=country, mode="lines+markers",
                line=dict(color=COUNTRY_COLORS.get(country, "#888"), width=2),
                marker=dict(size=4),
                hovertemplate=f"<b>{country}</b><br>%{{x}}: %{{y:+.1f}}%<extra></extra>",
            ))
        fig.add_hline(y=0, line=dict(color=_T3, dash="dot", width=1))
        fig.add_hline(y=-3, line=dict(color=_AMB, dash="dot", width=1),
                      annotation_text="−3% (EU rule)", annotation_font_color=_AMB)
        fig.update_layout(
            height=380,
            title=dict(text=f"Fiscal Balance (% GDP) — {yr_from}→{year}",
                       font=dict(size=13, color=_T1), x=0),
            yaxis_title="% GDP",
            **_chart_layout(),
        )
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        snap = (
            df[(df["Year"] == year) & (df["Country"].isin(countries))]
            .dropna(subset=["FiscalBal_Pct"])
            .sort_values("FiscalBal_Pct")
        )
        if not snap.empty:
            colors = [_RED if v < 0 else _GRN for v in snap["FiscalBal_Pct"]]
            fig2 = go.Figure(go.Bar(
                x=snap["FiscalBal_Pct"], y=snap["Country"],
                orientation="h", marker_color=colors,
                hovertemplate="%{y}: %{x:+.1f}%<extra></extra>",
            ))
            fig2.add_vline(x=0, line=dict(color=_T3, width=1))
            fig2.update_layout(
                height=380,
                title=dict(text=f"Ranking ({year})", font=dict(size=13, color=_T1), x=0),
                xaxis_title="% GDP", showlegend=False,
                **_chart_layout(margin=dict(l=130, r=20, t=44, b=44)),
            )
            st.plotly_chart(fig2, use_container_width=True)


# ── Debt sustainability scatter ────────────────────────────────────────────────

def _sustainability(df: pd.DataFrame, countries: list[str], year: int) -> None:
    _section(
        "Debt Sustainability Matrix",
        "High debt + wide deficit (top-left) = most vulnerable · surplus + low debt (bottom-right) = strongest",
    )

    snap = df[(df["Year"] == year) & (df["Country"].isin(countries))].dropna(
        subset=["DebtGDP_Pct", "FiscalBal_Pct"]
    )
    if snap.empty:
        _no_data()
        return

    fig = go.Figure()
    for _, row in snap.iterrows():
        fig.add_trace(go.Scatter(
            x=[row["FiscalBal_Pct"]], y=[row["DebtGDP_Pct"]],
            mode="markers+text",
            name=row["Country"],
            text=[row["Country"]],
            textposition="top center",
            textfont=dict(size=10, color=_T1),
            marker=dict(
                color=COUNTRY_COLORS.get(row["Country"], "#888"),
                size=14, opacity=0.9,
                line=dict(width=1.5, color=_BG),
            ),
            hovertemplate=(
                f"<b>{row['Country']}</b><br>"
                f"Fiscal Balance: {row['FiscalBal_Pct']:+.1f}%<br>"
                f"Debt/GDP: {row['DebtGDP_Pct']:.1f}%<extra></extra>"
            ),
            showlegend=False,
        ))

    fig.add_vline(x=0, line=dict(color=_T3, dash="dot", width=1))
    fig.add_hline(y=100, line=dict(color=_AMB, dash="dot", width=1),
                  annotation_text="100% debt", annotation_font_color=_AMB)

    fig.update_layout(
        height=440,
        title=dict(text=f"Fiscal Balance (x) vs Debt/GDP (y) — {year}",
                   font=dict(size=13, color=_T1), x=0),
        xaxis_title="Fiscal Balance (% GDP)  ←deficit | surplus→",
        yaxis_title="Govt Debt / GDP (%)",
        **_chart_layout(margin=dict(l=72, r=20, t=44, b=60)),
    )
    st.plotly_chart(fig, use_container_width=True)

    st.markdown(
        "**Top-left quadrant** (high debt + deficit): most fiscally stressed — bond markets may demand "
        "higher yields as compensation for credit risk.  \n"
        "**Bottom-right quadrant** (low debt + surplus): strongest fiscal position — room to absorb shocks."
    )


# ── Main entry ────────────────────────────────────────────────────────────────

def fiscal_scorecard() -> None:
    st.markdown(
        '<h2 style="color:#0f172a;margin:0 0 2px;">Fiscal Scorecard</h2>'
        '<div style="font-size:12px;color:#475569;">'
        'Govt debt · fiscal balance · primary balance · current account · '
        'Source: IMF World Economic Outlook</div>'
        '<hr style="border:none;border-top:1px solid #e2e8f0;margin:10px 0 6px;">',
        unsafe_allow_html=True,
    )

    # ── Sidebar ───────────────────────────────────────────────────────────────
    st.sidebar.markdown(
        f'<div style="font-size:10px;color:{_T2};text-transform:uppercase;'
        f'letter-spacing:.1em;margin:16px 0 6px;padding-bottom:4px;'
        f'border-bottom:1px solid {_EDGE};">Countries</div>',
        unsafe_allow_html=True,
    )
    countries = st.sidebar.multiselect(
        "Countries", ALL_NAMES, default=CORE_NAMES,
        key="fs_countries", label_visibility="collapsed",
    )
    year    = st.sidebar.slider("Snapshot year", 2005, 2025, 2023, key="fs_year")
    yr_from = st.sidebar.slider("History from", 2000, year, 2010, key="fs_yr_from")

    st.sidebar.markdown(
        f'<div style="font-size:10px;color:{_T2};text-transform:uppercase;'
        f'letter-spacing:.1em;margin:14px 0 6px;padding-bottom:4px;'
        f'border-bottom:1px solid {_EDGE};">Data</div>',
        unsafe_allow_html=True,
    )
    if ANNUAL_CACHE.exists():
        from datetime import datetime
        mtime = datetime.fromtimestamp(ANNUAL_CACHE.stat().st_mtime)
        st.sidebar.caption(f"Cached: {mtime.strftime('%d %b %Y')}")
    else:
        st.sidebar.caption("Not cached yet")
    refresh = st.sidebar.button("Refresh Data", key="fs_refresh")

    if refresh:
        with st.spinner("Fetching fiscal data from IMF…"):
            df = refresh_annual()
    else:
        df = load_annual()

    if df.empty:
        st.warning(
            "No data loaded. Click **Refresh Data** to fetch from IMF (takes ~30s).",
            icon="⚠️",
        )
        return

    if not countries:
        st.info("Select at least one country in the sidebar.")
        return

    _snapshot(df, countries, year)
    _debt(df, countries, year, yr_from)
    _fiscal_balance(df, countries, year, yr_from)
    _sustainability(df, countries, year)

    st.markdown(
        "**Data source:** IMF World Economic Outlook (Datamapper API). "
        "Fiscal Balance = general government net lending/borrowing. "
        "Debt/GDP = gross government debt as % of GDP. "
        "Current account from IMF BCA_NGDPD indicator."
    )
