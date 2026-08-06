from __future__ import annotations

from datetime import date

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from data import load_data
from firebase_utils import get_instrument_metadata
from global_macro_data import (
    US_CURVE_CACHE, US_CURVE_MAT_YRS,
    load_us_curve, refresh_us_curve,
)

# Maturity label → decimal years (sovereign curves)
MATURITY_YEARS: dict[str, float] = {
    "1M":  1 / 12, "3M":  0.25,  "6M":  0.5,
    "1Y":  1.0,    "2Y":  2.0,   "3Y":  3.0,
    "5Y":  5.0,    "7Y":  7.0,   "10Y": 10.0,
    "15Y": 15.0,   "20Y": 20.0,  "30Y": 30.0,
}
_MAT_LABEL: dict[float, str] = {v: k for k, v in MATURITY_YEARS.items()}

_DATE_COLORS = [
    "#60a5fa", "#f87171", "#34d399", "#fbbf24", "#a78bfa",
    "#fb923c", "#22d3ee", "#f472b6", "#818cf8", "#a3e635",
]

_BG   = "#0f172a"
_CARD = "#1e293b"
_EDGE = "#334155"
_T1   = "#f1f5f9"
_T2   = "#94a3b8"


@st.cache_data(ttl=300)
def _metadata() -> dict:
    return get_instrument_metadata()


def _nearest_date(df: pd.DataFrame, target) -> tuple:
    dates = df["Date"].dt.date
    diffs = (dates - target).abs()
    idx = diffs.idxmin()
    return idx, dates.iloc[idx]


def _chart_base(height: int = 420) -> dict:
    return dict(
        template="plotly_dark",
        paper_bgcolor=_CARD, plot_bgcolor=_BG,
        height=height,
        margin=dict(l=62, r=20, t=54, b=44),
        font=dict(color=_T1, size=12),
        hoverlabel=dict(bgcolor=_CARD, font_color=_T1, bordercolor=_EDGE),
        legend=dict(
            orientation="h", yanchor="bottom", y=1.02,
            xanchor="right", x=1,
            font=dict(size=11, color=_T1),
            bgcolor="rgba(0,0,0,0)",
        ),
    )


# ── US Treasury Curve tab ─────────────────────────────────────────────────────

_US_MAT_ORDER = ["1M", "3M", "6M", "1Y", "2Y", "3Y", "5Y", "7Y", "10Y", "20Y", "30Y"]
_US_MAT_XS    = [US_CURVE_MAT_YRS[m] for m in _US_MAT_ORDER]


def _us_curve_tab(refresh: bool) -> None:
    if refresh:
        with st.spinner("Fetching US Treasury yields from FRED (11 series)…"):
            df = refresh_us_curve()
    else:
        df = load_us_curve()

    # Cache status
    from datetime import datetime
    if US_CURVE_CACHE.exists():
        mtime = datetime.fromtimestamp(US_CURVE_CACHE.stat().st_mtime)
        st.caption(f"Cached: {mtime.strftime('%d %b %Y %H:%M')} · Source: FRED daily constant-maturity Treasury yields")
    else:
        st.caption("Not yet cached — click Refresh to fetch from FRED")

    if df.empty:
        st.warning("No data. Click **Refresh US Curve** in the sidebar.", icon="⚠️")
        return

    all_dates = sorted(df["Date"].dt.date.unique())
    date_min, date_max = all_dates[0], all_dates[-1]

    # Date pickers inline (up to 5 comparison dates)
    if "yc_us_dates" not in st.session_state:
        st.session_state.yc_us_dates = [date_max]

    st.markdown(
        f'<div style="font-size:12px;color:{_T2};margin:4px 0 6px;">'
        'Select up to 5 dates to compare curve shapes:</div>',
        unsafe_allow_html=True,
    )

    to_remove: list[int] = []
    n = len(st.session_state.yc_us_dates)
    cols = st.columns(min(n, 5) + 1)
    for i, d in enumerate(st.session_state.yc_us_dates):
        with cols[i]:
            picked = st.date_input(
                f"Date {i+1}", value=d,
                min_value=date_min, max_value=date_max,
                key=f"yc_us_date_{i}", label_visibility="visible",
            )
            st.session_state.yc_us_dates[i] = picked
            if n > 1 and st.button("✕", key=f"yc_us_rm_{i}", help="Remove"):
                to_remove.append(i)
    with cols[min(n, 5)]:
        st.markdown("<div style='margin-top:24px'></div>", unsafe_allow_html=True)
        if n < 5 and st.button("＋ Add Date"):
            st.session_state.yc_us_dates.append(date_max)
            st.rerun()

    for i in reversed(to_remove):
        st.session_state.yc_us_dates.pop(i)
        st.rerun()

    selected_dates = list(dict.fromkeys(st.session_state.yc_us_dates))

    # Build chart
    fig = go.Figure()
    df["DateOnly"] = df["Date"].dt.date

    for i, target in enumerate(selected_dates):
        # Find closest available date
        available = sorted(df["DateOnly"].unique())
        actual = min(available, key=lambda d: abs((d - target).days))
        day_df = df[df["DateOnly"] == actual].copy()

        row = {r["Maturity"]: r["Yield_Pct"] for _, r in day_df.iterrows()}
        xs, ys, labels = [], [], []
        for mat in _US_MAT_ORDER:
            if mat in row and pd.notna(row[mat]):
                xs.append(US_CURVE_MAT_YRS[mat])
                ys.append(row[mat])
                labels.append(mat)

        if not xs:
            continue

        clr = _DATE_COLORS[i % len(_DATE_COLORS)]
        label = str(actual) if actual == target else f"{target} → {actual}"
        fig.add_trace(go.Scatter(
            x=xs, y=ys, name=label,
            mode="lines+markers",
            line=dict(color=clr, width=2.5),
            marker=dict(size=8, color=clr, line=dict(width=1.5, color=_BG)),
            customdata=labels,
            hovertemplate=(
                "<b>%{customdata}</b><br>"
                "Yield: <b>%{y:.3f}%</b><br>"
                f"<i>{label}</i><extra></extra>"
            ),
        ))

    fig.update_xaxes(
        tickvals=_US_MAT_XS,
        ticktext=_US_MAT_ORDER,
        title_text="Maturity",
        gridcolor=_EDGE, tickfont=dict(color=_T2),
        showline=True, linecolor=_EDGE,
    )
    fig.update_yaxes(
        title_text="Yield (%)",
        gridcolor=_EDGE, tickfont=dict(color=_T2),
        showline=True, linecolor=_EDGE,
    )
    fig.update_layout(
        title=dict(text="US Treasury Yield Curve — constant maturity",
                   font=dict(size=15, color=_T1), x=0),
        **_chart_base(),
    )
    st.plotly_chart(fig, use_container_width=True)

    # Spread metrics: 2Y10Y, 3M10Y
    spreads_html = '<div style="display:flex;gap:16px;margin-top:8px;">'
    for mat_short, mat_long, label in [("2Y", "10Y", "2Y10Y Spread"), ("3M", "10Y", "3M10Y Spread")]:
        last_date = sorted(df["DateOnly"].unique())[-1]
        row = {r["Maturity"]: r["Yield_Pct"] for _, r in df[df["DateOnly"] == last_date].iterrows()}
        s = row.get(mat_long, None)
        l = row.get(mat_short, None)
        if s is not None and l is not None:
            spread_bp = (s - l) * 100
            color = _CARD
            txt_color = "#34d399" if spread_bp >= 0 else "#f87171"
            spreads_html += (
                f'<div style="background:{color};border:1px solid {_EDGE};border-radius:8px;'
                f'padding:10px 16px;text-align:center;">'
                f'<div style="font-size:10px;color:{_T2};text-transform:uppercase;letter-spacing:.1em;">{label}</div>'
                f'<div style="font-size:20px;font-weight:700;color:{txt_color};">{spread_bp:+.0f} bp</div>'
                f'<div style="font-size:11px;color:{_T2};">as of {last_date}</div></div>'
            )
    spreads_html += "</div>"
    st.markdown(spreads_html, unsafe_allow_html=True)
    st.markdown(
        "<br>**Yield curve inversion** (negative spread) historically precedes US recessions by 12–24 months. "
        "The 3M10Y spread is the Fed's preferred recession indicator. "
        "Data: FRED daily constant-maturity Treasury yields (DGS series).",
        unsafe_allow_html=True,
    )


# ── Sovereign curves tab (original content) ───────────────────────────────────

def _sovereign_tab(df: pd.DataFrame, bond_insts: dict, selected_countries: list[str],
                   selected_dates: list) -> None:
    if not selected_countries:
        st.warning("Select at least one country in the sidebar.")
        return

    for country in selected_countries:
        country_insts = {
            inst: m for inst, m in bond_insts.items() if m["country"] == country
        }
        if not country_insts:
            st.info(f"No bond instruments tagged for {country}.")
            continue

        all_mats_yrs = sorted(
            {MATURITY_YEARS[m["maturity"]] for m in country_insts.values()}
        )

        fig = go.Figure()
        any_trace = False

        for date_idx, target_date in enumerate(selected_dates):
            iloc_idx, actual_date = _nearest_date(df, target_date)
            row = df.iloc[iloc_idx]
            clr = _DATE_COLORS[date_idx % len(_DATE_COLORS)]

            points: list[tuple[float, float, str]] = []
            for inst, m in country_insts.items():
                mat_yrs = MATURITY_YEARS[m["maturity"]]
                val = row.get(inst, np.nan)
                if pd.notna(val):
                    points.append((mat_yrs, float(val), m["maturity"]))

            if not points:
                continue

            points.sort()
            xs     = [p[0] for p in points]
            ys     = [p[1] for p in points]
            labels = [p[2] for p in points]

            trace_label = (
                str(actual_date)
                if actual_date == target_date
                else f"{target_date} (→ {actual_date})"
            )

            fig.add_trace(go.Scatter(
                x=xs, y=ys, name=trace_label,
                mode="lines+markers",
                line=dict(color=clr, width=2.5),
                marker=dict(size=8, color=clr, line=dict(width=1.5, color=_BG)),
                customdata=labels,
                hovertemplate=(
                    "<b>%{customdata}</b><br>"
                    "Yield: <b>%{y:.3f}%</b><br>"
                    "<i>%{fullData.name}</i><extra></extra>"
                ),
            ))
            any_trace = True

        if not any_trace:
            st.warning(f"No data found for {country} on any of the selected dates.")
            continue

        fig.update_xaxes(
            tickvals=all_mats_yrs,
            ticktext=[_MAT_LABEL.get(m, str(m)) for m in all_mats_yrs],
            title_text="Maturity",
            gridcolor=_EDGE, tickfont=dict(color=_T2),
            showline=True, linecolor=_EDGE,
        )
        fig.update_yaxes(
            title_text="Yield (%)",
            gridcolor=_EDGE, tickfont=dict(color=_T2),
            showline=True, linecolor=_EDGE,
        )
        fig.update_layout(
            title=dict(text=f"{country} — Government Yield Curve",
                       font=dict(size=15, color=_T1), x=0),
            **_chart_base(),
        )
        st.plotly_chart(fig, use_container_width=True)


# ── Main entry point ──────────────────────────────────────────────────────────

def yield_curves() -> None:
    st.markdown(
        '<h2 style="color:#0f172a;margin:0 0 2px;">Global Yield Curves</h2>'
        '<div style="font-size:12px;color:#475569;">'
        'US Treasury full curve (FRED) · Sovereign curves from bond data</div>'
        '<hr style="border:none;border-top:1px solid #e2e8f0;margin:10px 0 6px;">',
        unsafe_allow_html=True,
    )

    # ── Sidebar ────────────────────────────────────────────────────────────────
    st.sidebar.markdown(
        '<div style="font-size:10px;color:#94a3b8;text-transform:uppercase;'
        'letter-spacing:.1em;margin:16px 0 6px;padding-bottom:4px;'
        'border-bottom:1px solid #334155;">US Treasury Curve</div>',
        unsafe_allow_html=True,
    )
    refresh_us = st.sidebar.button("Refresh US Curve", key="yc_us_refresh")

    st.sidebar.markdown(
        '<div style="font-size:10px;color:#94a3b8;text-transform:uppercase;'
        'letter-spacing:.1em;margin:16px 0 6px;padding-bottom:4px;'
        'border-bottom:1px solid #334155;">Sovereign Curves</div>',
        unsafe_allow_html=True,
    )

    meta = _metadata()
    df   = load_data()

    bond_insts = {
        inst: m
        for inst, m in meta.items()
        if m.get("asset_class") == "Fixed Income Bonds"
        and m.get("maturity") in MATURITY_YEARS
        and m.get("country")
        and inst in df.columns
    }

    countries = sorted(set(m["country"] for m in bond_insts.values()))
    selected_countries = st.sidebar.multiselect(
        "Countries", countries, default=countries, key="yc_countries",
    )

    all_dates = df["Date"].dropna().dt.date.tolist()
    date_min, date_max = min(all_dates), max(all_dates)

    if "yc_dates" not in st.session_state:
        st.session_state.yc_dates = [date_max]

    st.sidebar.markdown(
        f'<div style="font-size:12px;color:{_T2};margin:14px 0 6px;">'
        f'Dates <span style="color:{_T2};font-size:11px;">(max 10)</span></div>',
        unsafe_allow_html=True,
    )

    to_remove: list[int] = []
    for i, d in enumerate(st.session_state.yc_dates):
        c_date, c_del = st.sidebar.columns([5, 1])
        with c_date:
            picked = st.date_input(
                f"d{i}", value=d,
                min_value=date_min, max_value=date_max,
                key=f"yc_date_{i}", label_visibility="collapsed",
            )
            st.session_state.yc_dates[i] = picked
        with c_del:
            if (
                st.button("×", key=f"yc_rm_{i}", help="Remove this date")
                and len(st.session_state.yc_dates) > 1
            ):
                to_remove.append(i)

    for i in reversed(to_remove):
        st.session_state.yc_dates.pop(i)
        st.rerun()

    if len(st.session_state.yc_dates) < 10:
        if st.sidebar.button("＋  Add Date", key="yc_add"):
            st.session_state.yc_dates.append(date_max)
            st.rerun()

    selected_dates = list(dict.fromkeys(st.session_state.yc_dates))

    # ── Tabs ──────────────────────────────────────────────────────────────────
    tab_us, tab_sov = st.tabs(["🇺🇸 US Treasury Curve", "🌍 Sovereign Curves"])

    with tab_us:
        _us_curve_tab(refresh_us)

    with tab_sov:
        if not bond_insts:
            st.info(
                "No instruments have been tagged as **Fixed Income Bonds** yet.  \n"
                "Go to **Bond Analytics → Instrument Metadata** (admin only) and tag "
                "instruments with Country and Maturity to enable this dashboard."
            )
        else:
            st.markdown(
                f'<div style="font-size:12px;color:#475569;margin-bottom:8px;">'
                f'{len(selected_countries)} countr{"ies" if len(selected_countries) != 1 else "y"} · '
                f'{len(selected_dates)} date{"s" if len(selected_dates) != 1 else ""} selected</div>',
                unsafe_allow_html=True,
            )
            _sovereign_tab(df, bond_insts, selected_countries, selected_dates)
