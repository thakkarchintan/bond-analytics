"""
Bond Price / Yield Simulator
Interactive exploration of price-yield relationship, duration, and convexity.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from BondCalculator import (
    _cashflows,
    approx_price_change,
    bond_price,
    convexity,
    macaulay_duration,
    modified_duration,
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

_FREQ_MAP = {"Annual": 1, "Semi-annual": 2, "Quarterly": 4}


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


def _metric_html(label: str, value: str, sub: str = "") -> str:
    sub_html = (
        f'<div style="font-size:10px;color:{_T2};margin-top:2px">{sub}</div>'
        if sub else ""
    )
    return (
        f'<div style="background:{_CARD};border:1px solid {_EDGE};border-radius:8px;'
        f'padding:10px 14px;text-align:center">'
        f'<div style="font-size:11px;color:{_T2};margin-bottom:4px">{label}</div>'
        f'<div style="font-size:1.3rem;font-weight:700;color:{_T1}">{value}</div>'
        f'{sub_html}</div>'
    )


def bond_simulator() -> None:
    st.markdown("### 🎯 Bond Price / Yield Simulator")
    st.caption(
        "Explore the price-yield relationship · duration · convexity · cash flow timeline"
    )

    # ── Sidebar ───────────────────────────────────────────────────────────────
    st.sidebar.markdown("### Bond Parameters")
    face     = st.sidebar.number_input("Face Value ($)", 100.0, 10_000.0, 1_000.0, 100.0, key="bsim_face")
    coupon   = st.sidebar.slider("Coupon Rate (%)", 0.0, 15.0, 5.0, 0.25, key="bsim_coupon")
    maturity = st.sidebar.slider("Years to Maturity", 1, 30, 10, 1, key="bsim_mat")
    ytm_pct  = st.sidebar.slider("Current YTM (%)", 0.25, 20.0, 5.0, 0.25, key="bsim_ytm")
    freq_lbl = st.sidebar.selectbox("Payment Frequency", list(_FREQ_MAP), index=1, key="bsim_freq")

    freq = _FREQ_MAP[freq_lbl]
    cr   = coupon / 100
    ytm  = ytm_pct / 100

    price    = bond_price(face, cr, maturity, ytm, freq)
    mac_dur  = macaulay_duration(face, cr, maturity, ytm, freq)
    mod_dur  = modified_duration(face, cr, maturity, ytm, freq)
    conv_val = convexity(face, cr, maturity, ytm, freq)
    dv01     = mod_dur * price * 0.0001

    # ── Metrics ───────────────────────────────────────────────────────────────
    if abs(price - face) < 0.5:
        premium = "at par"
    elif price > face:
        premium = f"premium (+{price - face:.2f})"
    else:
        premium = f"discount ({price - face:.2f})"

    cols = st.columns(5)
    for col, (lbl, val, sub) in zip(cols, [
        ("Price",         f"${price:,.2f}",   premium),
        ("Macaulay Dur.", f"{mac_dur:.2f}y",  "weighted avg time"),
        ("Modified Dur.", f"{mod_dur:.2f}",   "price sensitivity / 1%"),
        ("Convexity",     f"{conv_val:.2f}",  "2nd-order curvature"),
        ("DV01",          f"${dv01:,.2f}",    f"per $1M = ${dv01*1000:,.0f}"),
    ]):
        col.markdown(_metric_html(lbl, val, sub), unsafe_allow_html=True)

    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

    # ── Tabs ──────────────────────────────────────────────────────────────────
    tab_curve, tab_cf, tab_shock = st.tabs(
        ["📈 Price-Yield Curve", "💰 Cash Flows", "⚡ Rate Shock Analysis"]
    )

    # ── Tab 1: Price-Yield Curve ───────────────────────────────────────────────
    with tab_curve:
        y_lo   = max(0.001, ytm - 0.10)
        y_hi   = min(0.30, ytm + 0.12)
        yields = np.linspace(y_lo, y_hi, 300)
        prices = [bond_price(face, cr, maturity, y, freq) for y in yields]
        dy_arr = yields - ytm

        dur_line  = price + price * (-mod_dur * dy_arr)
        conv_line = [price + approx_price_change(mod_dur, conv_val, price, dy) for dy in dy_arr]

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=yields * 100, y=prices, name="Actual Price",
            line=dict(color=_BLUE, width=2.5),
        ))
        fig.add_trace(go.Scatter(
            x=yields * 100, y=dur_line, name="Duration Estimate",
            line=dict(color=_AMB, width=1.5, dash="dash"),
        ))
        fig.add_trace(go.Scatter(
            x=yields * 100, y=conv_line, name="Convexity-Adjusted",
            line=dict(color=_GRN, width=1.5, dash="dot"),
        ))
        fig.add_trace(go.Scatter(
            x=[ytm_pct], y=[price], name="Current",
            mode="markers", marker=dict(color=_RED, size=10, symbol="circle"),
        ))

        # Annotate convexity gain at +200bp
        dy_200     = 0.02
        actual_200 = bond_price(face, cr, maturity, ytm + dy_200, freq)
        dur_200    = price + price * (-mod_dur * dy_200)
        gain_200   = actual_200 - dur_200
        if gain_200 > 0.01:
            fig.add_annotation(
                x=(ytm + dy_200) * 100, y=actual_200,
                text=f"Convexity gain<br>+${gain_200:.2f} at +200bp",
                showarrow=True, arrowhead=2, arrowcolor=_GRN,
                font=dict(color=_GRN, size=10), bgcolor=_CARD,
                bordercolor=_EDGE, borderwidth=1,
            )

        fig.update_layout(
            title="Price-Yield Relationship",
            **_chart_layout(
                xaxis=dict(title="YTM (%)", gridcolor=_EDGE, zerolinecolor=_EDGE),
                yaxis=dict(title="Price ($)", gridcolor=_EDGE, zerolinecolor=_EDGE),
            ),
        )
        st.plotly_chart(fig, use_container_width=True)
        st.caption(
            "The yellow dashed line (duration) is a straight-line approximation — it underestimates "
            "price when yields rise and overestimates when yields fall. Convexity (green dotted) "
            "adds the curvature correction. Bonds with higher convexity outperform in both directions."
        )

    # ── Tab 2: Cash Flows ─────────────────────────────────────────────────────
    with tab_cf:
        cfs     = _cashflows(face, cr, maturity, freq)
        r_per   = ytm / freq
        periods = [(t, cf, cf / (1 + r_per) ** (t * freq)) for t, cf in cfs]

        t_vals      = [t for t, _, _ in periods]
        coupon_amt  = face * cr / freq
        coupon_bars = [coupon_amt] * len(periods)
        princ_bars  = [face if t == maturity else 0.0 for t, _, _ in periods]
        pv_vals     = [pv for _, _, pv in periods]

        fig2 = go.Figure()
        fig2.add_trace(go.Bar(
            x=t_vals, y=coupon_bars, name="Coupon",
            marker_color=_BLUE, opacity=0.85,
        ))
        fig2.add_trace(go.Bar(
            x=t_vals, y=princ_bars, name="Principal",
            marker_color=_AMB, opacity=0.85,
        ))
        fig2.add_trace(go.Scatter(
            x=t_vals, y=pv_vals, name="Present Value",
            mode="lines+markers",
            line=dict(color=_GRN, width=2),
            marker=dict(size=6),
        ))
        fig2.update_layout(
            title="Cash Flows & Present Values",
            barmode="stack",
            **_chart_layout(
                xaxis=dict(title="Time (years)", gridcolor=_EDGE, zerolinecolor=_EDGE),
                yaxis=dict(title="Amount ($)", gridcolor=_EDGE, zerolinecolor=_EDGE),
            ),
        )
        st.plotly_chart(fig2, use_container_width=True)

        table_rows = []
        for t, cf, pv in periods:
            table_rows.append({
                "Period (yr)":    f"{t:.2f}",
                "Cash Flow ($)":  f"{cf:,.2f}",
                "Disc. Factor":   f"{pv / cf:.6f}",
                "PV ($)":         f"{pv:,.2f}",
                "% of Price":     f"{pv / price * 100:.2f}%",
                "Cum. Duration":  f"{t * pv / price:.4f}",
            })
        st.dataframe(pd.DataFrame(table_rows), use_container_width=True, hide_index=True)
        st.caption(
            "Macaulay duration is the sum of (time × PV weight) across all cash flows — "
            f"here it equals {mac_dur:.2f} years. The last row dominates duration for long-maturity bonds."
        )

    # ── Tab 3: Rate Shock Analysis ─────────────────────────────────────────────
    with tab_shock:
        shocks = list(range(-300, 325, 25))
        data = []
        for bp in shocks:
            dy      = bp / 10_000
            new_ytm = max(0.0001, ytm + dy)
            actual  = bond_price(face, cr, maturity, new_ytm, freq)
            d_act   = actual - price
            d_dur   = price * (-mod_dur * dy)
            d_conv  = approx_price_change(mod_dur, conv_val, price, dy)
            data.append({
                "Shock (bp)":   f"{bp:+d}",
                "New YTM (%)":  f"{new_ytm * 100:.2f}",
                "Actual Price": f"{actual:,.2f}",
                "ΔP Actual":    f"{d_act:+.2f}",
                "ΔP Duration":  f"{d_dur:+.2f}",
                "ΔP Conv.Adj.": f"{d_conv:+.2f}",
                "Dur. Error":   f"{d_act - d_dur:+.2f}",
                "_shock":    bp,
                "_actual":   actual,
                "_dur_px":   price + d_dur,
                "_conv_px":  price + d_conv,
            })

        df_s = pd.DataFrame(data)

        fig3 = go.Figure()
        fig3.add_trace(go.Scatter(
            x=df_s["_shock"], y=df_s["_actual"], name="Actual Price",
            line=dict(color=_BLUE, width=2.5),
        ))
        fig3.add_trace(go.Scatter(
            x=df_s["_shock"], y=df_s["_dur_px"], name="Duration Estimate",
            line=dict(color=_AMB, width=1.5, dash="dash"),
        ))
        fig3.add_trace(go.Scatter(
            x=df_s["_shock"], y=df_s["_conv_px"], name="Convexity-Adjusted",
            line=dict(color=_GRN, width=1.5, dash="dot"),
        ))
        fig3.add_vline(x=0, line=dict(color=_EDGE, dash="dot", width=1))
        fig3.update_layout(
            title="Price Impact: Actual vs Approximations",
            **_chart_layout(
                xaxis=dict(title="Yield Shock (bp)", gridcolor=_EDGE, zerolinecolor=_EDGE),
                yaxis=dict(title="Price ($)", gridcolor=_EDGE, zerolinecolor=_EDGE),
            ),
        )
        st.plotly_chart(fig3, use_container_width=True)

        display_cols = [
            "Shock (bp)", "New YTM (%)", "Actual Price",
            "ΔP Actual", "ΔP Duration", "ΔP Conv.Adj.", "Dur. Error",
        ]
        st.dataframe(df_s[display_cols], use_container_width=True, hide_index=True)
        st.caption(
            "Duration error = Actual ΔP − Duration ΔP. It is always positive (bonds outperform the "
            "linear estimate) because of convexity — the larger the shock, the bigger the error."
        )
