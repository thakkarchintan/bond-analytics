"""
Historical Global Shocks — yield and rates dynamics during 12 key market events.
"""
from __future__ import annotations

import pathlib

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from data import load_data
from global_macro_data import (
    BREAKEVEN_CACHE, CROSS_ASSET_CACHE, SPREADS_LONG_CACHE,
    load_breakeven, load_cross_asset, load_spreads_long, refresh_spreads_long,
)

_HERE = pathlib.Path(__file__).parent
_CBPOL_CACHE = _HERE / "dbn_cbpol_cache.parquet"

# ── Palette ───────────────────────────────────────────────────────────────────
_T1  = "#f1f5f9"
_T2  = "#94a3b8"
_GRD = "#1e293b"
_BG  = "rgba(0,0,0,0)"

_COLS = [
    "#60a5fa", "#f59e0b", "#34d399", "#f87171",
    "#a78bfa", "#fb923c", "#38bdf8", "#6ee7b7",
]

_DRIVER_STYLE: dict[str, tuple[str, str]] = {
    "Growth Shock":                     ("#1e3a5f", "#60a5fa"),
    "Inflation Shock":                  ("#3b1f00", "#fb923c"),
    "Central Bank Communication":       ("#2d1f4e", "#a78bfa"),
    "Sovereign Credit Risk":            ("#3b0f0f", "#f87171"),
    "Fiscal Policy & Market Structure": ("#2d2008", "#fbbf24"),
}

# ── Event catalogue ───────────────────────────────────────────────────────────

_EVENTS: list[dict] = [
    {
        "id":     "dotcom",
        "label":  "1 · Dot-com Bust (2000–02)",
        "period": "March 2000 – October 2002",
        "driver": "Growth Shock",
        "lesson": (
            "Growth fears → bond prices rise → yields fall.  The 2Y10Y spread briefly "
            "inverted in mid-2000 ahead of the recession, then steepened sharply as the "
            "Fed cut rates 550 bp over 2001–03.  The equity crash did not spread to "
            "Treasuries — it pulled money into them."
        ),
        "window": ("1998-06-01", "2003-06-01"),
        "shade":  ("2000-03-10", "2002-10-09"),
        "keys":   [("2000-03-10", "NASDAQ peak"), ("2001-01-03", "Fed first cut")],
    },
    {
        "id":     "gfc",
        "label":  "2 · Global Financial Crisis (2008–09)",
        "period": "December 2007 – June 2009",
        "driver": "Growth Shock",
        "lesson": (
            "Flight-to-quality dominates everything.  Credit spreads exploded even while "
            "government yields collapsed.  The Fed cut rates to 0–0.25 % in two emergency "
            "moves and launched QE1.  The 10Y Treasury fell from ~5 % to ~2 %."
        ),
        "window": ("2006-01-01", "2010-12-01"),
        "shade":  ("2007-12-01", "2009-06-30"),
        "keys":   [("2008-09-15", "Lehman Brothers"), ("2008-12-16", "Fed → 0 %")],
    },
    {
        "id":     "eurozone",
        "label":  "3 · European Sovereign Debt Crisis (2010–12)",
        "period": "April 2010 – July 2012",
        "driver": "Sovereign Credit Risk",
        "lesson": (
            "Government bonds are not equally risk-free.  Italian and Greek spreads over "
            "Germany exploded, proving sovereign credit risk is real even inside a currency "
            "union.  German Bunds rallied hard as the safe-haven within Europe."
        ),
        "window": ("2009-01-01", "2013-06-01"),
        "shade":  ("2010-04-27", "2012-07-25"),
        "keys":   [("2010-04-27", "Greece junk"), ("2011-11-09", "Italy 10Y > 7 %")],
    },
    {
        "id":     "draghi",
        "label":  "4 · ECB 'Whatever It Takes' (2012)",
        "period": "July 26, 2012",
        "driver": "Central Bank Communication",
        "lesson": (
            "Sometimes central bank credibility alone moves yields more than actual bond "
            "purchases.  Draghi's three words on 26 July 2012 collapsed peripheral spreads "
            "within days — before a single bond was bought under OMT."
        ),
        "window": ("2012-01-01", "2013-06-01"),
        "shade":  None,
        "keys":   [("2012-07-26", "Draghi: 'whatever it takes'")],
    },
    {
        "id":     "taper",
        "label":  "5 · US Taper Tantrum (2013)",
        "period": "May – December 2013",
        "driver": "Central Bank Communication",
        "lesson": (
            "Expectations move markets before policy changes.  The Fed did not raise rates — "
            "Bernanke merely hinted at slowing QE.  US 10Y jumped ~100 bp in months.  "
            "Duration risk materialised for the first time since the 1990s."
        ),
        "window": ("2012-06-01", "2014-06-01"),
        "shade":  ("2013-05-22", "2013-12-31"),
        "keys":   [("2013-05-22", "Bernanke hints taper"), ("2013-12-18", "Taper begins")],
    },
    {
        "id":     "oil_deflation",
        "label":  "6 · Oil Crash & Deflation Scare (2014–16)",
        "period": "June 2014 – January 2016",
        "driver": "Growth Shock",
        "lesson": (
            "Falling inflation expectations can push nominal yields to historic lows.  "
            "German 10Y briefly went negative in 2016 — a reminder that yield is a "
            "market price, not a law of nature.  The ECB cut the deposit rate below zero."
        ),
        "window": ("2013-06-01", "2017-01-01"),
        "shade":  ("2014-06-01", "2016-01-31"),
        "keys":   [("2014-11-28", "OPEC keeps output"), ("2016-07-06", "German 10Y < 0")],
    },
    {
        "id":     "brexit",
        "label":  "7 · Brexit Referendum (2016)",
        "period": "June 23, 2016",
        "driver": "Fiscal Policy & Market Structure",
        "lesson": (
            "Political uncertainty creates immediate risk-off demand for high-quality bonds.  "
            "UK Gilt yields and US Treasuries both fell sharply on the vote result.  "
            "Sterling fell 10 % overnight and FTSE sold off before recovering."
        ),
        "window": ("2016-01-01", "2017-03-01"),
        "shade":  None,
        "keys":   [("2016-06-23", "Vote"), ("2016-06-24", "Result: Leave")],
    },
    {
        "id":     "covid",
        "label":  "8 · COVID-19 Pandemic (2020)",
        "period": "February – June 2020",
        "driver": "Growth Shock",
        "lesson": (
            "Extreme uncertainty + aggressive central bank intervention = record-low yields.  "
            "US 10Y briefly fell below 0.5 %.  The Fed cut to zero in two emergency sessions "
            "and launched unlimited QE.  The entire Treasury curve traded below 1 % for "
            "the first time in history."
        ),
        "window": ("2019-10-01", "2021-09-01"),
        "shade":  ("2020-02-01", "2021-04-30"),
        "keys":   [("2020-03-11", "WHO pandemic"), ("2020-03-15", "Fed → 0 % emergency")],
    },
    {
        "id":     "inflation_hike",
        "label":  "9 · Inflation Shock & Hiking Cycle (2022–23)",
        "period": "March 2022 – July 2023",
        "driver": "Inflation Shock",
        "lesson": (
            "Inflation — not growth — became the dominant driver.  The fastest hiking cycle "
            "in 40 years produced the biggest global bond bear market in decades.  "
            "US 10Y moved from ~1.5 % to above 4 %.  Duration risk returned with force "
            "and the 2Y10Y curve inverted deeply."
        ),
        "window": ("2021-01-01", "2024-06-01"),
        "shade":  ("2022-03-16", "2023-07-26"),
        "keys":   [("2022-03-16", "Fed first hike"), ("2023-07-26", "Last hike (+525 bp total)")],
    },
    {
        "id":     "uk_ldi",
        "label":  "10 · UK Mini-Budget & LDI Crisis (2022)",
        "period": "September – October 2022",
        "driver": "Fiscal Policy & Market Structure",
        "lesson": (
            "Bond markets can punish fiscal policy within days.  Long-dated gilt yields "
            "spiked over 100 bp in days, forcing the Bank of England to intervene.  "
            "Pension LDI (liability-driven investment) leverage amplified the move and "
            "created a self-reinforcing sell-off."
        ),
        "window": ("2022-07-01", "2023-03-01"),
        "shade":  ("2022-09-23", "2022-10-14"),
        "keys":   [("2022-09-23", "Mini-budget"), ("2022-10-14", "BoE emergency ends")],
    },
    {
        "id":     "trump_reflation",
        "label":  "✧ Trump Reflation Trade (2016)",
        "period": "November 2016",
        "driver": "Fiscal Policy & Market Structure",
        "lesson": (
            "Treasury yields jumped on expectations of fiscal stimulus, tax cuts and "
            "higher deficits.  A rare case of the 'Trump trade': equities and yields "
            "rose together, with the yield curve steepening sharply."
        ),
        "window": ("2016-09-01", "2017-06-01"),
        "shade":  None,
        "keys":   [("2016-11-08", "US Election")],
    },
    {
        "id":     "negative_yields",
        "label":  "✧ Negative Yield Era (2016–2021)",
        "period": "2016 – 2021",
        "driver": "Growth Shock",
        "lesson": (
            "Around $18 trillion of global bonds traded at negative yields at the "
            "2019 peak.  Yield is a market price set by supply and demand — it has "
            "no natural floor.  ECB and BoJ engineered this through negative deposit "
            "rates and large-scale asset purchases."
        ),
        "window": ("2014-01-01", "2022-03-01"),
        "shade":  ("2016-07-06", "2021-12-31"),
        "keys":   [("2016-07-06", "German 10Y < 0"), ("2019-08-01", "$17 T negative yield peak")],
    },
]

_EVENT_BY_ID = {e["id"]: e for e in _EVENTS}


# ── Chart helpers ─────────────────────────────────────────────────────────────

def _clip(df: pd.DataFrame, date_col: str, start: str, end: str) -> pd.DataFrame:
    return df[
        (df[date_col] >= pd.Timestamp(start)) &
        (df[date_col] <= pd.Timestamp(end))
    ].copy()


def _decorate(fig: go.Figure, ev: dict) -> go.Figure:
    """Add shade rectangle and vertical event markers."""
    if ev.get("shade"):
        fig.add_vrect(
            x0=ev["shade"][0], x1=ev["shade"][1],
            fillcolor="rgba(100,110,130,0.13)", line_width=0,
        )
    for date, label in (ev.get("keys") or []):
        fig.add_vline(
            x=date, line_dash="dot", line_color="#f59e0b", line_width=1.5,
            annotation_text=label, annotation_position="top right",
            annotation_font=dict(size=9, color="#f59e0b"),
        )
    return fig


def _base(title: str, y_label: str = "", h: int = 310) -> go.Figure:
    fig = go.Figure()
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor=_BG, plot_bgcolor=_BG,
        font=dict(size=11, color=_T2),
        title=dict(text=title, font=dict(size=13, color=_T1), x=0),
        xaxis=dict(gridcolor=_GRD, zeroline=False),
        yaxis=dict(gridcolor=_GRD, zeroline=False, title=y_label),
        margin=dict(l=0, r=0, t=38, b=0),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0,
                    font=dict(size=10), bgcolor="rgba(0,0,0,0)"),
        height=h,
        hovermode="x unified",
    )
    return fig


# ── Chart functions ───────────────────────────────────────────────────────────

def _yields(df: pd.DataFrame, ev: dict,
            cols: list[str], names: list[str],
            title: str, y_label: str = "Yield (%)") -> go.Figure:
    """Line chart for columns from Final.xlsx."""
    d = _clip(df, "Date", *ev["window"])
    fig = _base(title, y_label)
    for i, (col, name) in enumerate(zip(cols, names)):
        if col not in d.columns:
            continue
        s = d[["Date", col]].dropna()
        fig.add_trace(go.Scatter(
            x=s["Date"], y=s[col], name=name,
            line=dict(color=_COLS[i % len(_COLS)], width=1.8),
        ))
    return _decorate(fig, ev)


def _spread(df: pd.DataFrame, ev: dict,
            c1: str, c2: str, name: str,
            title: str, y_label: str = "bp",
            color: str = "#f87171", scale: float = 100.0) -> go.Figure:
    """Single spread = (c1 - c2) * scale from Final.xlsx."""
    d = _clip(df, "Date", *ev["window"])
    fig = _base(title, y_label)
    if c1 in d.columns and c2 in d.columns:
        s = (d[c1] - d[c2]) * scale
        fig.add_trace(go.Scatter(
            x=d["Date"], y=s, name=name,
            line=dict(color=color, width=1.8),
        ))
        fig.add_hline(y=0, line_color="#475569", line_dash="dot", line_width=1)
    return _decorate(fig, ev)


def _multi_spreads(df: pd.DataFrame, ev: dict,
                   pairs: list[tuple[str, str, str, str]],
                   title: str, y_label: str = "bp") -> go.Figure:
    """Multiple spread lines on one chart. pairs = [(c1,c2,name,color),...]"""
    d = _clip(df, "Date", *ev["window"])
    fig = _base(title, y_label)
    for c1, c2, name, color in pairs:
        if c1 in d.columns and c2 in d.columns:
            s = (d[c1] - d[c2]) * 100
            fig.add_trace(go.Scatter(
                x=d["Date"], y=s, name=name,
                line=dict(color=color, width=1.8),
            ))
    fig.add_hline(y=0, line_color="#475569", line_dash="dot", line_width=1)
    return _decorate(fig, ev)


def _cb_rates(df_cbpol: pd.DataFrame, ev: dict,
              countries: list[str], names: list[str],
              title: str) -> go.Figure:
    """Step chart of CB policy rates."""
    fig = _base(title, "Rate (%)")
    start, end = ev["window"]
    for i, (country, name) in enumerate(zip(countries, names)):
        d = df_cbpol[df_cbpol["Country"] == country].copy()
        d = _clip(d, "Date", start, end).sort_values("Date")
        if d.empty:
            continue
        fig.add_trace(go.Scatter(
            x=d["Date"], y=d["Rate"], name=name,
            line=dict(color=_COLS[i % len(_COLS)], width=1.8, shape="hv"),
        ))
    return _decorate(fig, ev)


def _single_cross(df_cross: pd.DataFrame, ev: dict,
                  series: str, title: str,
                  y_label: str = "", color: str = "#60a5fa") -> go.Figure:
    """Single series from cross_asset_cache."""
    d = df_cross[df_cross["Series"] == series].copy()
    d = _clip(d, "Date", *ev["window"]).sort_values("Date")
    fig = _base(title, y_label)
    if not d.empty:
        fig.add_trace(go.Scatter(
            x=d["Date"], y=d["Value"], name=series,
            line=dict(color=color, width=1.8),
        ))
    return _decorate(fig, ev)


def _breakeven_chart(df_be: pd.DataFrame, ev: dict,
                     series: list[str], title: str) -> go.Figure:
    """Breakeven inflation series."""
    fig = _base(title, "Rate (%)")
    for i, s in enumerate(series):
        d = df_be[df_be["Series"] == s].copy()
        d = _clip(d, "Date", *ev["window"]).sort_values("Date")
        if d.empty:
            continue
        fig.add_trace(go.Scatter(
            x=d["Date"], y=d["Value"], name=s,
            line=dict(color=_COLS[i % len(_COLS)], width=1.8),
        ))
    fig.add_hline(y=2.0, line_color="#475569", line_dash="dot", line_width=1,
                  annotation_text="2% target", annotation_font=dict(size=9, color=_T2))
    return _decorate(fig, ev)


def _oas_chart(df_sl: pd.DataFrame, ev: dict,
               series: list[str], title: str) -> go.Figure:
    """Historical OAS credit spreads."""
    fig = _base(title, "OAS (%)")
    for i, s in enumerate(series):
        d = df_sl[df_sl["Series"] == s].copy()
        d = _clip(d, "Date", *ev["window"]).sort_values("Date")
        if d.empty:
            continue
        fig.add_trace(go.Scatter(
            x=d["Date"], y=d["OAS_Pct"], name=s,
            line=dict(color=_COLS[i % len(_COLS)], width=1.8),
        ))
    return _decorate(fig, ev)


# ── Event renderers ───────────────────────────────────────────────────────────

def _render_dotcom(ev, df, cbpol, cross, be, sl):
    c1, c2, c3 = st.columns(3)
    with c1:
        st.plotly_chart(_yields(df, ev,
            ["US2Y", "US10Y", "US30Y"], ["US 2Y", "US 10Y", "US 30Y"],
            "US Treasury Yields"), use_container_width=True)
    with c2:
        st.plotly_chart(_spread(df, ev, "US10Y", "US2Y", "2Y10Y",
            "US 2Y10Y Spread", color="#34d399"), use_container_width=True)
    with c3:
        st.plotly_chart(_single_cross(cross, ev, "S&P 500",
            "S&P 500 Index", "Level", "#34d399"), use_container_width=True)


def _render_gfc(ev, df, cbpol, cross, be, sl):
    has_spreads = not sl.empty
    n = 4 if has_spreads else 3
    cols = st.columns(n)
    with cols[0]:
        st.plotly_chart(_yields(df, ev,
            ["US2Y", "US10Y"], ["US 2Y", "US 10Y"],
            "US Treasury Yields"), use_container_width=True)
    with cols[1]:
        st.plotly_chart(_cb_rates(cbpol, ev,
            ["United States", "Euro Area", "United Kingdom", "Japan"],
            ["Fed", "ECB", "BoE", "BoJ"],
            "Central Bank Policy Rates"), use_container_width=True)
    with cols[2]:
        st.plotly_chart(_single_cross(cross, ev, "VIX",
            "VIX Volatility Index", "", "#f87171"), use_container_width=True)
    if has_spreads:
        with cols[3]:
            st.plotly_chart(_oas_chart(sl, ev, ["HY", "BBB"],
                "US Credit Spreads (OAS %)"), use_container_width=True)


def _render_eurozone(ev, df, cbpol, cross, be, sl):
    c1, c2, c3 = st.columns(3)
    with c1:
        st.plotly_chart(_spread(df, ev, "FBTPY", "FGBLY", "Italy–Germany 10Y",
            "Italy–Germany 10Y Spread", color="#f87171"), use_container_width=True)
    with c2:
        st.plotly_chart(_multi_spreads(df, ev,
            [("FOATY", "FGBLY", "France–Germany 10Y", "#c084fc"),
             ("UK10Y",  "FGBLY", "UK–Germany 10Y",     "#fb923c")],
            "Other Spreads vs Germany"), use_container_width=True)
    with c3:
        st.plotly_chart(_yields(df, ev,
            ["FGBLY"], ["German 10Y (Bund)"],
            "German 10Y — Flight to Quality"), use_container_width=True)


def _render_draghi(ev, df, cbpol, cross, be, sl):
    c1, c2, c3 = st.columns(3)
    with c1:
        st.plotly_chart(_spread(df, ev, "FBTPY", "FGBLY", "Italy–Germany 10Y",
            "Italy–Germany 10Y Spread", color="#f87171"), use_container_width=True)
    with c2:
        st.plotly_chart(_multi_spreads(df, ev,
            [("FOATY", "FGBLY", "France–Germany 10Y", "#c084fc"),
             ("FBTSY", "FGBSY", "Italy–Germany 2Y",   "#f87171")],
            "Contagion Spreads vs Germany"), use_container_width=True)
    with c3:
        st.plotly_chart(_cb_rates(cbpol, ev,
            ["Euro Area"], ["ECB"],
            "ECB Policy Rate"), use_container_width=True)


def _render_taper(ev, df, cbpol, cross, be, sl):
    c1, c2, c3 = st.columns(3)
    with c1:
        st.plotly_chart(_yields(df, ev,
            ["US10Y", "US30Y"], ["US 10Y", "US 30Y"],
            "US Treasury Yields — The Tantrum"), use_container_width=True)
    with c2:
        st.plotly_chart(_spread(df, ev, "US10Y", "US2Y", "2Y10Y",
            "US 2Y10Y Slope (Steepening)", color="#34d399"), use_container_width=True)
    with c3:
        st.plotly_chart(_cb_rates(cbpol, ev,
            ["United States"], ["Fed Funds"],
            "Fed Policy Rate — Held at 0 %"), use_container_width=True)


def _render_oil_deflation(ev, df, cbpol, cross, be, sl):
    c1, c2, c3 = st.columns(3)
    with c1:
        st.plotly_chart(_single_cross(cross, ev, "WTI Crude",
            "WTI Crude Oil (USD/bbl)", "USD / bbl", "#fb923c"), use_container_width=True)
    with c2:
        fig_be = _breakeven_chart(be, ev, ["5Y Breakeven", "10Y Breakeven"],
            "US Inflation Expectations (Breakeven %)")
        st.plotly_chart(fig_be, use_container_width=True)
    with c3:
        st.plotly_chart(_yields(df, ev,
            ["FGBLY", "US10Y"], ["German 10Y (Bund)", "US 10Y"],
            "German 10Y Goes Negative"), use_container_width=True)


def _render_brexit(ev, df, cbpol, cross, be, sl):
    c1, c2, c3 = st.columns(3)
    with c1:
        st.plotly_chart(_yields(df, ev,
            ["UK10Y", "FGBLY", "US10Y"],
            ["UK 10Y (Gilt)", "German 10Y (Bund)", "US 10Y"],
            "10Y Government Yields"), use_container_width=True)
    with c2:
        st.plotly_chart(_multi_spreads(df, ev,
            [("UK10Y", "FGBLY", "UK–Germany 10Y", "#fb923c"),
             ("US10Y", "FGBLY", "US–Germany 10Y", "#60a5fa")],
            "Spreads vs Germany"), use_container_width=True)
    with c3:
        st.plotly_chart(_single_cross(cross, ev, "S&P 500",
            "S&P 500 Index", "Level", "#34d399"), use_container_width=True)


def _render_covid(ev, df, cbpol, cross, be, sl):
    c1, c2, c3 = st.columns(3)
    with c1:
        st.plotly_chart(_yields(df, ev,
            ["US2Y", "US10Y", "US30Y"], ["US 2Y", "US 10Y", "US 30Y"],
            "US Treasury Yields — Historic Low"), use_container_width=True)
    with c2:
        st.plotly_chart(_cb_rates(cbpol, ev,
            ["United States", "Euro Area", "United Kingdom", "Japan"],
            ["Fed", "ECB", "BoE", "BoJ"],
            "Central Bank Policy Rates"), use_container_width=True)
    with c3:
        st.plotly_chart(_single_cross(cross, ev, "VIX",
            "VIX Volatility Index", "", "#f87171"), use_container_width=True)


def _render_inflation_hike(ev, df, cbpol, cross, be, sl):
    r1c1, r1c2 = st.columns(2)
    r2c1, r2c2 = st.columns(2)
    with r1c1:
        st.plotly_chart(_cb_rates(cbpol, ev,
            ["United States", "Euro Area", "United Kingdom", "Japan", "Canada"],
            ["Fed", "ECB", "BoE", "BoJ", "BoC"],
            "Central Bank Policy Rates — Fastest Hike in 40 Years"), use_container_width=True)
    with r1c2:
        st.plotly_chart(_yields(df, ev,
            ["US2Y", "US10Y", "US30Y"], ["US 2Y", "US 10Y", "US 30Y"],
            "US Treasury Yields — Bear Market"), use_container_width=True)
    with r2c1:
        st.plotly_chart(_spread(df, ev, "US10Y", "US2Y", "2Y10Y",
            "US 2Y10Y Spread — Deep Inversion", color="#f87171"), use_container_width=True)
    with r2c2:
        fig_be = _breakeven_chart(be, ev, ["5Y Breakeven", "10Y Breakeven", "5Y Real Yield"],
            "Inflation Expectations & Real Yields")
        st.plotly_chart(fig_be, use_container_width=True)


def _render_uk_ldi(ev, df, cbpol, cross, be, sl):
    c1, c2, c3 = st.columns(3)
    with c1:
        st.plotly_chart(_yields(df, ev,
            ["UK10Y", "FGBXY"], ["UK 10Y (Gilt)", "German 30Y (Buxl)"],
            "Long-End Yields — The LDI Spike"), use_container_width=True)
    with c2:
        st.plotly_chart(_multi_spreads(df, ev,
            [("UK10Y", "FGBLY", "UK–Germany 10Y",  "#fb923c"),
             ("UK10Y", "US10Y", "UK–US 10Y",        "#a78bfa")],
            "UK Gilt Spreads"), use_container_width=True)
    with c3:
        st.plotly_chart(_cb_rates(cbpol, ev,
            ["United Kingdom", "United States", "Euro Area"],
            ["BoE", "Fed", "ECB"],
            "Policy Rates During LDI Crisis"), use_container_width=True)


def _render_trump_reflation(ev, df, cbpol, cross, be, sl):
    c1, c2, c3 = st.columns(3)
    with c1:
        st.plotly_chart(_yields(df, ev,
            ["US2Y", "US10Y", "US30Y"], ["US 2Y", "US 10Y", "US 30Y"],
            "US Treasury Yields — Reflation Jump"), use_container_width=True)
    with c2:
        st.plotly_chart(_spread(df, ev, "US10Y", "US2Y", "2Y10Y",
            "US Curve — Steepening on Fiscal Expectations", color="#34d399"),
            use_container_width=True)
    with c3:
        st.plotly_chart(_single_cross(cross, ev, "S&P 500",
            "S&P 500 Index", "Level", "#34d399"), use_container_width=True)


def _render_negative_yields(ev, df, cbpol, cross, be, sl):
    c1, c2, c3 = st.columns(3)
    with c1:
        st.plotly_chart(_yields(df, ev,
            ["FGBLY", "FGBMY", "FGBXY"], ["German 10Y", "German 5Y", "German 30Y"],
            "German Bund Yields Go Negative"), use_container_width=True)
    with c2:
        st.plotly_chart(_cb_rates(cbpol, ev,
            ["Euro Area", "Japan"], ["ECB", "BoJ"],
            "Negative Rate Pioneers"), use_container_width=True)
    with c3:
        fig_be = _breakeven_chart(be, ev, ["5Y Breakeven", "10Y Breakeven"],
            "US Inflation Expectations")
        st.plotly_chart(fig_be, use_container_width=True)


_RENDERERS = {
    "dotcom":          _render_dotcom,
    "gfc":             _render_gfc,
    "eurozone":        _render_eurozone,
    "draghi":          _render_draghi,
    "taper":           _render_taper,
    "oil_deflation":   _render_oil_deflation,
    "brexit":          _render_brexit,
    "covid":           _render_covid,
    "inflation_hike":  _render_inflation_hike,
    "uk_ldi":          _render_uk_ldi,
    "trump_reflation": _render_trump_reflation,
    "negative_yields": _render_negative_yields,
}


# ── Event metadata card ───────────────────────────────────────────────────────

_CARD_CSS = """
<style>
.shock-header { font-size:22px; font-weight:700; color:#f1f5f9; margin-bottom:2px; }
.shock-sub    { font-size:13px; color:#64748b; margin-bottom:18px; }
.shock-card   { border:1px solid #1e293b; border-radius:10px; padding:14px 18px;
                margin-bottom:16px; background:#0f172a; }
.shock-period { font-size:12px; color:#94a3b8; margin-bottom:6px; }
.shock-badge  { display:inline-block; padding:2px 10px; border-radius:4px;
                font-size:11px; font-weight:600; margin-bottom:8px; }
.shock-lesson { font-size:13px; color:#cbd5e1; line-height:1.65; }
.shock-fw     { font-size:10px; font-weight:700; color:#64748b; letter-spacing:.08em;
                text-transform:uppercase; margin-top:10px; margin-bottom:4px; }
</style>
"""


def _event_card(ev: dict) -> None:
    bg, fg = _DRIVER_STYLE.get(ev["driver"], ("#1e293b", "#94a3b8"))
    st.markdown(
        f"""
        <div class="shock-card">
          <div class="shock-period">📅 {ev["period"]}</div>
          <span class="shock-badge" style="background:{bg};color:{fg};">
            {ev["driver"]}
          </span>
          <div class="shock-lesson">{ev["lesson"]}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ── Main entry point ──────────────────────────────────────────────────────────

def historical_shocks() -> None:
    st.markdown(_CARD_CSS, unsafe_allow_html=True)
    st.markdown('<div class="shock-header">Historical Global Shocks</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="shock-sub">Yield and rates dynamics around 12 key market events · '
        'Data: Final.xlsx · BIS/FRED/DBnomics caches</div>',
        unsafe_allow_html=True,
    )

    # ── Sidebar controls ──────────────────────────────────────────────────────
    ev_labels = [e["label"] for e in _EVENTS]
    sel_label = st.sidebar.selectbox("Select event", ev_labels, key="shock_event")
    ev = next(e for e in _EVENTS if e["label"] == sel_label)

    st.sidebar.markdown("---")
    refresh_oas = st.sidebar.button("🔄 Refresh Credit Spreads", key="shock_refresh_oas",
                                     help="Fetch HY/BBB OAS history from FRED (1996–present)")
    st.sidebar.caption(
        "Credit spread data (HY/BBB OAS) covers GFC & Dot-com events.\n"
        "Click Refresh if not yet loaded."
    )

    # ── Load data ─────────────────────────────────────────────────────────────
    df_bond = load_data()

    cbpol_path = _CBPOL_CACHE
    if cbpol_path.exists():
        df_cbpol = pd.read_parquet(cbpol_path)
        df_cbpol["Date"] = pd.to_datetime(df_cbpol["Date"])
    else:
        df_cbpol = pd.DataFrame(columns=["Date", "Country", "Rate"])

    df_cross = load_cross_asset() if CROSS_ASSET_CACHE.exists() else pd.DataFrame()
    if not df_cross.empty:
        df_cross["Date"] = pd.to_datetime(df_cross["Date"])

    df_be = load_breakeven() if BREAKEVEN_CACHE.exists() else pd.DataFrame()
    if not df_be.empty:
        df_be["Date"] = pd.to_datetime(df_be["Date"])

    if refresh_oas:
        with st.spinner("Fetching historical OAS from FRED…"):
            df_sl = refresh_spreads_long()
    else:
        df_sl = load_spreads_long() if SPREADS_LONG_CACHE.exists() else pd.DataFrame()
    if not df_sl.empty:
        df_sl["Date"] = pd.to_datetime(df_sl["Date"])

    # ── Event metadata card ───────────────────────────────────────────────────
    _event_card(ev)

    # ── Charts ────────────────────────────────────────────────────────────────
    render_fn = _RENDERERS.get(ev["id"])
    if render_fn:
        render_fn(ev, df_bond, df_cbpol, df_cross, df_be, df_sl)
    else:
        st.info("Renderer not yet defined for this event.")

    # ── Data availability note ────────────────────────────────────────────────
    with st.expander("Data availability", expanded=False):
        notes = [
            ("Yield curves (bond data)", "Final.xlsx — daily from April 1994"),
            ("CB policy rates", "BIS WS_CBPOL via DBnomics — daily from 1946"),
            ("VIX · WTI · S&P 500", "FRED — daily from 2000"),
            ("TIPS breakeven / real yields", "FRED — daily from 2003"),
            ("Historical credit spreads (HY/BBB OAS)", "FRED OAS series — daily from 1996–97 (click Refresh)"),
        ]
        for src, detail in notes:
            st.markdown(f"**{src}** — {detail}")
