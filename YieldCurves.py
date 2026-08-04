from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from data import load_data
from firebase_utils import get_instrument_metadata

# Maturity label → decimal years (for ordered x-axis)
MATURITY_YEARS: dict[str, float] = {
    "1M":  1 / 12,
    "3M":  0.25,
    "6M":  0.5,
    "1Y":  1.0,
    "2Y":  2.0,
    "3Y":  3.0,
    "5Y":  5.0,
    "7Y":  7.0,
    "10Y": 10.0,
    "15Y": 15.0,
    "20Y": 20.0,
    "30Y": 30.0,
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
    """Return (iloc_index, actual_date) closest to target date."""
    dates = df["Date"].dt.date
    diffs = (dates - target).abs()
    idx = diffs.idxmin()
    return idx, dates.iloc[idx]


def yield_curves() -> None:
    meta = _metadata()
    df = load_data()

    # Instruments tagged as Fixed Income Bonds with a recognised maturity
    bond_insts = {
        inst: m
        for inst, m in meta.items()
        if m.get("asset_class") == "Fixed Income Bonds"
        and m.get("maturity") in MATURITY_YEARS
        and m.get("country")
        and inst in df.columns
    }

    # ── Sidebar ────────────────────────────────────────────────────────────────
    st.sidebar.markdown(
        '<div style="font-size:10px;color:#94a3b8;text-transform:uppercase;'
        'letter-spacing:.1em;margin:20px 0 8px;padding-bottom:6px;'
        'border-bottom:1px solid #334155;">Yield Curve Filters</div>',
        unsafe_allow_html=True,
    )

    if not bond_insts:
        st.sidebar.info("No bond instruments tagged yet.")
        st.info(
            "No instruments have been tagged as **Fixed Income Bonds** yet.  \n"
            "Go to **Bond Analytics → Instrument Metadata** (admin only) and tag "
            "instruments with Country and Maturity to enable this dashboard."
        )
        return

    countries = sorted(set(m["country"] for m in bond_insts.values()))
    selected_countries = st.sidebar.multiselect(
        "Countries", countries, default=countries, key="yc_countries"
    )

    # Date pickers — up to 10
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

    selected_dates: list = list(dict.fromkeys(st.session_state.yc_dates))  # dedup, keep order

    if not selected_countries:
        st.warning("Select at least one country in the sidebar.")
        return

    # ── Page header ────────────────────────────────────────────────────────────
    st.markdown(
        '<h2 style="color:#0f172a;margin:0 0 2px;">Global Yield Curves</h2>'
        f'<div style="font-size:12px;color:#475569;">'
        f'{len(selected_countries)} countr{"ies" if len(selected_countries) != 1 else "y"} · '
        f'{len(selected_dates)} date{"s" if len(selected_dates) != 1 else ""} selected</div>'
        '<hr style="border:none;border-top:1px solid #e2e8f0;margin:12px 0 8px;">',
        unsafe_allow_html=True,
    )

    # ── One chart per country ──────────────────────────────────────────────────
    for country in selected_countries:
        country_insts = {
            inst: m for inst, m in bond_insts.items() if m["country"] == country
        }
        if not country_insts:
            st.info(f"No bond instruments tagged for {country}.")
            continue

        # All maturities available for this country (for x-axis ticks)
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
                x=xs, y=ys,
                name=trace_label,
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
            gridcolor=_EDGE,
            tickfont=dict(color=_T2),
            showline=True,
            linecolor=_EDGE,
        )
        fig.update_yaxes(
            title_text="Yield (%)",
            gridcolor=_EDGE,
            tickfont=dict(color=_T2),
            showline=True,
            linecolor=_EDGE,
        )
        fig.update_layout(
            template="plotly_dark",
            paper_bgcolor=_CARD,
            plot_bgcolor=_BG,
            height=420,
            title=dict(
                text=f"{country} — Government Yield Curve",
                font=dict(size=15, color=_T1), x=0,
            ),
            margin=dict(l=62, r=20, t=54, b=44),
            font=dict(color=_T1, size=12),
            legend=dict(
                orientation="h", yanchor="bottom", y=1.02,
                xanchor="right", x=1,
                font=dict(size=11, color=_T1),
                bgcolor="rgba(0,0,0,0)",
            ),
            hoverlabel=dict(bgcolor=_CARD, font_color=_T1, bordercolor=_EDGE),
        )
        st.plotly_chart(fig, use_container_width=True)
