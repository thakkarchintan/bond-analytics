"""
Yield Curve Trade Builder
Select a yield curve shape, apply a scenario (bear/bull steepen/flatten),
build 2- or 3-leg trades, see per-leg DV01s, P&L and DV01-neutral ratios.
"""
from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from BondCalculator import bond_price, modified_duration, convexity

# ── Palette (matches app dark theme) ─────────────────────────────────────────
_CARD = "#1e293b"
_BG   = "#0f172a"
_EDGE = "#334155"
_T1   = "#f1f5f9"
_T2   = "#94a3b8"
_BLUE = "#3b82f6"
_GRN  = "#10b981"
_RED  = "#ef4444"
_AMB  = "#fbbf24"
_PRP  = "#a78bfa"

# ── Constants ─────────────────────────────────────────────────────────────────
_TENOR_LABELS = ["2Y", "3Y", "5Y", "7Y", "10Y", "20Y", "30Y"]
_TENOR_MATS   = [2,    3,    5,    7,    10,    20,    30   ]

_SHAPES: dict[str, list[float]] = {
    "Normal (Upward Sloping)": [4.00, 4.20, 4.40, 4.55, 4.70, 4.90, 5.05],
    "Flat":                    [4.50, 4.50, 4.50, 4.50, 4.50, 4.50, 4.50],
    "Inverted":                [5.50, 5.30, 5.00, 4.80, 4.50, 4.30, 4.20],
    "Humped (Mid-Cycle)":      [4.00, 4.60, 5.00, 4.80, 4.50, 4.30, 4.20],
    "Custom":                  [4.50, 4.60, 4.70, 4.75, 4.80, 4.85, 4.90],
}

# Scenario shift profiles: fraction of total magnitude per tenor
# Positive = yield rises, negative = yield falls
_SCENARIO_PROFILES: dict[str, list[float]] = {
    "Bear Steepening":    [ 0.00,  0.10,  0.30,  0.50,  0.70,  0.85,  1.00],
    "Bull Steepening":    [-1.00, -0.85, -0.70, -0.50, -0.30, -0.10,  0.00],
    "Bear Flattening":    [ 1.00,  0.85,  0.70,  0.50,  0.30,  0.10,  0.00],
    "Bull Flattening":    [ 0.00, -0.10, -0.30, -0.50, -0.70, -0.85, -1.00],
    "Parallel Shift Up":  [ 1.00,  1.00,  1.00,  1.00,  1.00,  1.00,  1.00],
    "Parallel Shift Down":[-1.00, -1.00, -1.00, -1.00, -1.00, -1.00, -1.00],
    "Custom":             [ 0.00,  0.00,  0.00,  0.00,  0.00,  0.00,  0.00],
}

_SCENARIO_DESCRIPTIONS = {
    "Bear Steepening":    "Long-end yields rise faster than short end. Typical early-cycle / reflation trade or supply pressure on long bonds.",
    "Bull Steepening":    "Short-end yields fall faster than long end (front-end rally). Classic rate-cut expectation / recession trade.",
    "Bear Flattening":    "Short-end yields rise faster than long end. Classic central bank hiking cycle — front-end most affected.",
    "Bull Flattening":    "Long-end yields fall faster than short end. Deflationary growth scare or flight-to-quality in long bonds.",
    "Parallel Shift Up":  "All tenors rise by the same amount. Generalised rate sell-off / inflation surprise.",
    "Parallel Shift Down":"All tenors fall by the same amount. Generalised flight-to-quality or rate cut expectation.",
    "Custom":             "Set each tenor shift manually below.",
}


# ── Helpers ───────────────────────────────────────────────────────────────────

def _section(title: str, subtitle: str = "") -> None:
    sub = (
        f'<div style="font-size:12px;color:{_T2};margin-top:4px;">{subtitle}</div>'
        if subtitle else ""
    )
    st.markdown(
        f'<div style="background:{_CARD};border-left:4px solid {_BLUE};'
        f'padding:12px 16px;margin:24px 0 10px;border-radius:0 8px 8px 0;">'
        f'<span style="font-size:13px;font-weight:700;color:{_T1};'
        f'text-transform:uppercase;letter-spacing:.08em;">{title}</span>{sub}</div>',
        unsafe_allow_html=True,
    )


def _layout(**kw) -> dict:
    base = dict(
        template="plotly_dark",
        paper_bgcolor=_CARD,
        plot_bgcolor=_BG,
        margin=dict(l=60, r=20, t=44, b=44),
        font=dict(color=_T1, size=12),
        xaxis=dict(gridcolor=_EDGE, tickfont=dict(color=_T2),
                   showline=True, linecolor=_EDGE),
        yaxis=dict(gridcolor=_EDGE, tickfont=dict(color=_T2),
                   showline=True, linecolor=_EDGE),
        hoverlabel=dict(bgcolor=_CARD, font_color=_T1, bordercolor=_EDGE),
        legend=dict(font=dict(color=_T1, size=11), bgcolor="rgba(0,0,0,0)"),
    )
    base.update(kw)
    return base


def _metric_card(label: str, value: str, sub: str = "", accent: str = _BLUE) -> str:
    sub_html = (
        f'<div style="font-size:10px;color:{_T2};margin-top:3px;">{sub}</div>'
        if sub else ""
    )
    return (
        f'<div style="background:{_CARD};border:1px solid {_EDGE};border-left:3px solid {accent};'
        f'border-radius:8px;padding:12px 14px;">'
        f'<div style="font-size:10px;color:{_T2};text-transform:uppercase;'
        f'letter-spacing:.1em;margin-bottom:5px;">{label}</div>'
        f'<div style="font-size:18px;font-weight:700;color:{_T1};">{value}</div>'
        f'{sub_html}</div>'
    )


def _bond_metrics(yield_pct: float, maturity: float, face_m: float) -> dict:
    """Compute metrics for a par bond (coupon = yield) with face_m × $1M notional."""
    coupon = yield_pct / 100
    ytm    = yield_pct / 100
    price  = bond_price(100.0, coupon, maturity, ytm, 2)   # should ≈ 100
    md     = modified_duration(100.0, coupon, maturity, ytm, 2)
    cv     = convexity(100.0, coupon, maturity, ytm, 2)
    face_usd = face_m * 1_000_000.0
    # DV01: ModDur × (price/100) × face × 0.0001
    dv01   = md * (price / 100.0) * face_usd * 0.0001
    return {"price": price, "moddur": md, "convexity": cv, "dv01": dv01,
            "ytm": ytm, "coupon": coupon, "face_usd": face_usd}


def _new_price(coupon_pct: float, maturity: float, new_yield_pct: float) -> float:
    """Price of a par-issued bond when yield moves to new_yield_pct."""
    coupon = coupon_pct / 100
    ytm    = max(new_yield_pct, 0.01) / 100
    return bond_price(100.0, coupon, maturity, ytm, 2)


# ── Main page ─────────────────────────────────────────────────────────────────

def curve_trade_builder() -> None:
    st.markdown(
        f'<h2 style="color:#0f172a;margin:0 0 2px;">Yield Curve Trade Builder</h2>'
        f'<div style="font-size:12px;color:#475569;">'
        f'Scenario analysis · 2 &amp; 3-leg trades · DV01 attribution · P&amp;L · DV01-neutral ratios</div>'
        f'<hr style="border:none;border-top:1px solid #e2e8f0;margin:12px 0 8px;">',
        unsafe_allow_html=True,
    )

    # ═══════════════════════════════════════════════════════════════════════════
    # STEP 1 — Yield curve setup
    # ═══════════════════════════════════════════════════════════════════════════
    _section("Step 1 — Current Yield Curve", "Choose a preset shape or input yields manually")

    shape_choice = st.selectbox(
        "Curve shape preset",
        options=list(_SHAPES.keys()),
        index=0,
        key="ctb_shape",
    )

    # Seed default yields from preset; allow manual override
    preset_yields = _SHAPES[shape_choice]

    st.markdown(
        f'<div style="font-size:12px;color:{_T2};margin:6px 0 4px;">'
        f'Edit any yield below to override the preset:</div>',
        unsafe_allow_html=True,
    )
    cols_y = st.columns(7)
    current_yields: list[float] = []
    for i, (lbl, preset) in enumerate(zip(_TENOR_LABELS, preset_yields)):
        with cols_y[i]:
            y = st.number_input(
                lbl, value=float(preset), step=0.05,
                min_value=0.01, max_value=20.0, format="%.2f",
                key=f"ctb_y_{lbl}",
            )
            current_yields.append(y)

    # ═══════════════════════════════════════════════════════════════════════════
    # STEP 2 — Scenario
    # ═══════════════════════════════════════════════════════════════════════════
    _section("Step 2 — Scenario", "Define how the yield curve moves")

    sc1, sc2 = st.columns([2, 1])
    with sc1:
        scenario = st.selectbox(
            "Scenario type",
            options=list(_SCENARIO_PROFILES.keys()),
            index=0,
            key="ctb_scenario",
        )
        st.caption(_SCENARIO_DESCRIPTIONS[scenario])
    with sc2:
        magnitude = st.number_input(
            "Magnitude (bp)", value=50, step=5, min_value=1, max_value=500,
            key="ctb_mag",
            help="Maximum shift applied to the most-affected tenor",
        )

    profile = _SCENARIO_PROFILES[scenario]

    if scenario == "Custom":
        st.markdown(
            f'<div style="font-size:12px;color:{_T2};margin:6px 0 4px;">'
            f'Input the shift (bp) for each tenor:</div>',
            unsafe_allow_html=True,
        )
        cols_s = st.columns(7)
        shifts_bp: list[float] = []
        for i, lbl in enumerate(_TENOR_LABELS):
            with cols_s[i]:
                s = st.number_input(
                    f"{lbl} shift (bp)", value=0.0, step=5.0,
                    min_value=-500.0, max_value=500.0, format="%.0f",
                    key=f"ctb_shift_{lbl}",
                )
                shifts_bp.append(s)
    else:
        shifts_bp = [p * magnitude for p in profile]

    new_yields = [max(y + s / 100, 0.01) for y, s in zip(current_yields, shifts_bp)]

    # Show shift table
    with st.expander("Tenor-by-tenor shifts", expanded=False):
        shift_df = pd.DataFrame({
            "Tenor":         _TENOR_LABELS,
            "Current (%)":   [f"{y:.2f}" for y in current_yields],
            "Shift (bp)":    [f"{s:+.0f}" for s in shifts_bp],
            "New Yield (%)": [f"{y:.2f}" for y in new_yields],
        })
        st.dataframe(shift_df, use_container_width=True, hide_index=True)

    # ═══════════════════════════════════════════════════════════════════════════
    # STEP 3 — Trade legs
    # ═══════════════════════════════════════════════════════════════════════════
    _section("Step 3 — Trade Legs", "Build a 2- or 3-leg yield curve trade")

    n_legs = st.radio("Number of legs", [2, 3], horizontal=True, key="ctb_nlegs")

    leg_colors = [_BLUE, _AMB, _GRN]
    legs: list[dict] = []

    leg_cols = st.columns(n_legs)
    for i in range(n_legs):
        with leg_cols[i]:
            st.markdown(
                f'<div style="background:{_CARD};border:1px solid {_EDGE};'
                f'border-top:3px solid {leg_colors[i]};border-radius:8px;'
                f'padding:14px 14px 10px;margin-bottom:8px;">'
                f'<div style="font-size:12px;font-weight:700;color:{_T1};margin-bottom:10px;">'
                f'Leg {i+1}</div></div>',
                unsafe_allow_html=True,
            )
            tenor_sel = st.selectbox(
                "Tenor", _TENOR_LABELS,
                index=[0, 4, 2][i] if i < 3 else 0,
                key=f"ctb_leg{i}_tenor",
            )
            direction = st.radio(
                "Direction", ["Long", "Short"],
                horizontal=True,
                key=f"ctb_leg{i}_dir",
            )
            face_m = st.number_input(
                "Notional ($M)", value=10.0, step=5.0,
                min_value=0.1, max_value=10000.0, format="%.1f",
                key=f"ctb_leg{i}_face",
            )
            tenor_idx = _TENOR_LABELS.index(tenor_sel)
            mat       = _TENOR_MATS[tenor_idx]
            cur_yld   = current_yields[tenor_idx]
            new_yld   = new_yields[tenor_idx]
            shift     = shifts_bp[tenor_idx]
            metrics   = _bond_metrics(cur_yld, mat, face_m)
            dir_sign  = 1 if direction == "Long" else -1
            np_       = _new_price(cur_yld, mat, new_yld)
            pl_pts    = np_ - metrics["price"]           # price points
            pl_usd      = pl_pts / 100 * metrics["face_usd"] * dir_sign

            legs.append({
                "label":    f"Leg {i+1}: {direction} {face_m:.0f}M {tenor_sel}",
                "tenor":    tenor_sel,
                "maturity": mat,
                "direction": direction,
                "dir_sign": dir_sign,
                "face_m":   face_m,
                "face_usd":   metrics["face_usd"],
                "cur_yld":  cur_yld,
                "new_yld":  new_yld,
                "shift_bp": shift,
                "price":    metrics["price"],
                "new_price": np_,
                "moddur":   metrics["moddur"],
                "dv01":     metrics["dv01"] * dir_sign,
                "dv01_abs": metrics["dv01"],
                "pl_pts":   pl_pts * dir_sign,
                "pl_usd":     pl_usd,
                "color":    leg_colors[i],
            })

    # ═══════════════════════════════════════════════════════════════════════════
    # STEP 4 — Results
    # ═══════════════════════════════════════════════════════════════════════════
    _section("Step 4 — Results", "Yield curve shift · P&L · DV01 attribution · hedge ratios")

    # ── Yield curve chart ────────────────────────────────────────────────────
    fig_yc = go.Figure()

    fig_yc.add_trace(go.Scatter(
        x=_TENOR_MATS, y=current_yields, name="Current curve",
        line=dict(color=_BLUE, width=2.5),
        mode="lines+markers",
        marker=dict(size=7, color=_BLUE, line=dict(width=1, color=_BG)),
        hovertemplate="%{text}: %{y:.2f}%<extra>Current</extra>",
        text=_TENOR_LABELS,
    ))

    new_color = _RED if sum(shifts_bp) >= 0 else _GRN
    fig_yc.add_trace(go.Scatter(
        x=_TENOR_MATS, y=new_yields, name=f"After: {scenario}",
        line=dict(color=new_color, width=2.5, dash="dash"),
        mode="lines+markers",
        marker=dict(size=7, color=new_color, line=dict(width=1, color=_BG)),
        hovertemplate="%{text}: %{y:.2f}%<extra>New</extra>",
        text=_TENOR_LABELS,
    ))

    # Mark leg tenors
    for leg in legs:
        fig_yc.add_shape(
            type="line",
            x0=leg["maturity"], x1=leg["maturity"], y0=0, y1=1,
            xref="x", yref="paper",
            line=dict(color=leg["color"], width=1.5, dash="dot"),
        )
        fig_yc.add_annotation(
            x=leg["maturity"], y=0.97, xref="x", yref="paper",
            text=leg["tenor"], showarrow=False, xanchor="center",
            font=dict(size=9, color=leg["color"]),
        )

    fig_yc.update_layout(
        height=360,
        title=dict(text="Yield Curve — Before & After Scenario", font=dict(size=13, color=_T1), x=0),
        yaxis_title="Yield (%)",
        **_layout(),
    )
    fig_yc.update_xaxes(title="Maturity (years)", tickvals=_TENOR_MATS, ticktext=_TENOR_LABELS)
    st.plotly_chart(fig_yc, use_container_width=True)

    # ── Totals ────────────────────────────────────────────────────────────────
    total_pl   = sum(l["pl_usd"] for l in legs)
    total_dv01 = sum(l["dv01"]   for l in legs)
    pl_color   = _GRN if total_pl   >= 0 else _RED
    dv_color   = _GRN if total_dv01 >= 0 else _RED

    html_top = f'<div style="display:grid;grid-template-columns:repeat({2 + n_legs},1fr);gap:10px;margin-bottom:14px;">'
    html_top += _metric_card("Total P&L", f"${total_pl:+,.0f}", f"Scenario: {scenario}", pl_color)
    html_top += _metric_card("Net DV01", f"${total_dv01:+,.0f}", "$ per 1bp parallel shift", dv_color)
    for leg in legs:
        dv01_per_m = leg["dv01_abs"] / leg["face_m"]
        html_top += _metric_card(
            f"{leg['tenor']} DV01 / $1M",
            f"${dv01_per_m:,.0f}",
            f"{leg['direction']} · total ${leg['dv01_abs']:,.0f}",
            leg["color"],
        )
    html_top += '</div>'
    st.markdown(html_top, unsafe_allow_html=True)

    # ── Per-leg table (full width) ────────────────────────────────────────────
    leg_rows = []
    for leg in legs:
        dv01_per_m = leg["dv01_abs"] / leg["face_m"]
        leg_rows.append({
            "Leg":              leg["label"],
            "Notional ($M)":    f"{leg['face_m']:.1f}",
            "Cur Yield (%)":    f"{leg['cur_yld']:.2f}",
            "Shift (bp)":       f"{leg['shift_bp']:+.0f}",
            "New Yield (%)":    f"{leg['new_yld']:.2f}",
            "Price (cur)":      f"{leg['price']:.3f}",
            "Price (new)":      f"{leg['new_price']:.3f}",
            "Mod Dur":          f"{leg['moddur']:.3f}",
            "DV01/bp per $1M":  f"${dv01_per_m:,.0f}",
            "DV01/bp (total)":  f"${leg['dv01_abs']:,.0f}",
            "P&L ($)":          f"${leg['pl_usd']:+,.0f}",
        })
    leg_df = pd.DataFrame(leg_rows)

    def _color_leg(row):
        idx   = int(row.name)
        color = legs[idx]["color"]
        tints = {"#3b82f6": "#1e3a5f", "#fbbf24": "#3b2a00", "#10b981": "#052e16"}
        bg    = tints.get(color, _CARD)
        return [f"background-color:{bg};color:#f1f5f9" for _ in row]

    st.dataframe(
        leg_df.style.apply(_color_leg, axis=1),
        use_container_width=True, hide_index=True,
    )

    # ── Charts side by side, taller ───────────────────────────────────────────
    ch_left, ch_right = st.columns(2)

    with ch_left:
        fig_pl = go.Figure(go.Bar(
            x=[l["tenor"] for l in legs],
            y=[l["pl_usd"] for l in legs],
            marker_color=[l["color"] for l in legs],
            text=[f"${l['pl_usd']:+,.0f}" for l in legs],
            textposition="outside",
            textfont=dict(size=11, color=_T1),
            hovertemplate="Leg: %{x}<br>P&L: $%{y:+,.0f}<extra></extra>",
        ))
        fig_pl.add_hline(y=0, line_color=_EDGE, line_width=1)
        fig_pl.update_layout(
            height=340,
            title=dict(text="P&L per Leg ($)", font=dict(size=13, color=_T1), x=0),
            showlegend=False,
            xaxis_title="",
            yaxis_title="P&L ($)",
            **_layout(margin=dict(l=70, r=20, t=44, b=40)),
        )
        st.plotly_chart(fig_pl, use_container_width=True)

    with ch_right:
        dv_vals = [l["dv01"] for l in legs] + [total_dv01]
        dv_lbls = [f"{l['tenor']}\n({l['direction']})" for l in legs] + ["Net"]
        dv_clrs = [l["color"] for l in legs] + [_GRN if total_dv01 >= 0 else _RED]

        fig_dv = go.Figure(go.Bar(
            x=dv_lbls, y=dv_vals,
            marker_color=dv_clrs,
            text=[f"${v:+,.0f}" for v in dv_vals],
            textposition="outside",
            textfont=dict(size=11, color=_T1),
            hovertemplate="%{x}<br>DV01: $%{y:+,.0f}<extra></extra>",
        ))
        fig_dv.add_hline(y=0, line_color=_EDGE, line_width=1)
        fig_dv.update_layout(
            height=340,
            title=dict(text="DV01 Attribution — $ per 1bp (signed by direction)", font=dict(size=13, color=_T1), x=0),
            xaxis_title="",
            yaxis_title="DV01 ($)",
            showlegend=False,
            **_layout(margin=dict(l=70, r=20, t=44, b=40)),
        )
        st.plotly_chart(fig_dv, use_container_width=True)

    # ── DV01-neutral ratios ───────────────────────────────────────────────────
    _section(
        "DV01-Neutral Hedge Ratios",
        "Notional ratios that make the trade DV01-flat — useful when you want pure curve exposure with no parallel-rate risk",
    )

    def _parallel_pl(leg_list: list[dict], shift_bp: float) -> float:
        """P&L of a set of legs under a uniform parallel yield shift."""
        total = 0.0
        for leg in leg_list:
            new_y = max(leg["cur_yld"] + shift_bp / 100, 0.01)
            np_   = _new_price(leg["cur_yld"], leg["maturity"], new_y)
            total += (np_ - leg["price"]) / 100 * leg["face_usd"] * leg["dir_sign"]
        return total

    if n_legs == 2:
        leg_a, leg_b = legs[0], legs[1]
        dv_per_m_a = leg_a["dv01_abs"] / leg_a["face_m"]   # $ per 1bp per $1M
        dv_per_m_b = leg_b["dv01_abs"] / leg_b["face_m"]

        # DV01-neutral: fix leg A notional, solve for leg B notional
        neutral_face_b = leg_a["face_m"] * (dv_per_m_a / dv_per_m_b) if dv_per_m_b else 0.0
        ratio = dv_per_m_a / dv_per_m_b if dv_per_m_b else 0.0

        # Build neutral legs for verification
        neutral_legs = [
            {**leg_a},
            {**leg_b,
             "face_m":   neutral_face_b,
             "face_usd": neutral_face_b * 1_000_000,
             "dv01":     -leg_a["dv01"] / leg_a["face_m"] * neutral_face_b * leg_b["dir_sign"],
            },
        ]
        verify_pl_up   = _parallel_pl(neutral_legs, +50)
        verify_pl_down = _parallel_pl(neutral_legs, -50)

        html_r = '<div style="display:grid;grid-template-columns:1fr 1fr 1fr 1fr;gap:10px;margin-bottom:14px;">'
        html_r += _metric_card(f"DV01/bp per $1M — {leg_a['tenor']}", f"${dv_per_m_a:,.0f}", f"{leg_a['direction']}", _BLUE)
        html_r += _metric_card(f"DV01/bp per $1M — {leg_b['tenor']}", f"${dv_per_m_b:,.0f}", f"{leg_b['direction']}", _AMB)
        html_r += _metric_card("Hedge Ratio", f"{ratio:.4f}×", f"$M of {leg_b['tenor']} per $1M of {leg_a['tenor']}", _GRN)
        html_r += _metric_card(f"Neutral size — {leg_b['tenor']}", f"${neutral_face_b:.2f}M", f"Given ${leg_a['face_m']:.0f}M of {leg_a['tenor']}", _PRP)
        html_r += '</div>'
        st.markdown(html_r, unsafe_allow_html=True)

        vfy_color_up   = _GRN if abs(verify_pl_up)   < 50 else _AMB
        vfy_color_down = _GRN if abs(verify_pl_down) < 50 else _AMB
        st.markdown(
            f'<div style="background:{_CARD};border:1px solid {_EDGE};border-radius:8px;'
            f'padding:16px 18px;font-size:13px;color:{_T2};line-height:1.9;">'
            f'<b style="color:{_T1};">DV01-neutral construction</b><br>'
            f'For every <b style="color:{_BLUE};">${leg_a["face_m"]:.0f}M</b> of '
            f'<b>{leg_a["tenor"]}</b> ({leg_a["direction"]}), '
            f'trade <b style="color:{_AMB};">${neutral_face_b:.2f}M</b> of '
            f'<b>{leg_b["tenor"]}</b> in the opposite direction.<br>'
            f'DV01 per $1M: {leg_a["tenor"]} = <b style="color:{_BLUE};">${dv_per_m_a:,.0f}</b> &nbsp;·&nbsp; '
            f'{leg_b["tenor"]} = <b style="color:{_AMB};">${dv_per_m_b:,.0f}</b> &nbsp;·&nbsp; '
            f'Ratio = <b style="color:{_GRN};">{ratio:.4f}×</b><br><br>'
            f'<b style="color:{_T1};">✓ Parallel shift verification (at neutral sizes)</b><br>'
            f'Parallel <b>+50bp</b>: P&L = <b style="color:{vfy_color_up};">${verify_pl_up:+,.0f}</b> &nbsp;·&nbsp; '
            f'Parallel <b>−50bp</b>: P&L = <b style="color:{vfy_color_down};">${verify_pl_down:+,.0f}</b><br>'
            f'<span style="font-size:11px;">Small residual (~$0) is convexity — duration-hedged trades are not '
            f'perfectly convexity-neutral. A larger negative residual means additional convexity hedging is needed.</span>'
            f'</div>',
            unsafe_allow_html=True,
        )

    elif n_legs == 3:
        leg_a, leg_b, leg_c = legs
        dv_per_m_a = leg_a["dv01_abs"] / leg_a["face_m"]
        dv_per_m_b = leg_b["dv01_abs"] / leg_b["face_m"]
        dv_per_m_c = leg_c["dv01_abs"] / leg_c["face_m"]

        # Fix belly (leg_b), size wings so combined wing DV01 = belly DV01
        # Each wing gets half the belly DV01 (equal-weighted butterfly)
        neutral_face_a = (leg_b["face_m"] * dv_per_m_b / 2) / dv_per_m_a if dv_per_m_a else 0
        neutral_face_c = (leg_b["face_m"] * dv_per_m_b / 2) / dv_per_m_c if dv_per_m_c else 0

        neutral_legs = [
            {**leg_a, "face_m": neutral_face_a, "face_usd": neutral_face_a * 1_000_000},
            {**leg_b},
            {**leg_c, "face_m": neutral_face_c, "face_usd": neutral_face_c * 1_000_000},
        ]
        verify_pl_up   = _parallel_pl(neutral_legs, +50)
        verify_pl_down = _parallel_pl(neutral_legs, -50)

        html_r = '<div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:10px;margin-bottom:14px;">'
        html_r += _metric_card(f"DV01/bp per $1M — {leg_a['tenor']}", f"${dv_per_m_a:,.0f}", leg_a['direction'], _BLUE)
        html_r += _metric_card(f"DV01/bp per $1M — {leg_b['tenor']}", f"${dv_per_m_b:,.0f}", leg_b['direction'], _AMB)
        html_r += _metric_card(f"DV01/bp per $1M — {leg_c['tenor']}", f"${dv_per_m_c:,.0f}", leg_c['direction'], _GRN)
        html_r += '</div>'
        st.markdown(html_r, unsafe_allow_html=True)

        vfy_color_up   = _GRN if abs(verify_pl_up)   < 100 else _AMB
        vfy_color_down = _GRN if abs(verify_pl_down) < 100 else _AMB
        st.markdown(
            f'<div style="background:{_CARD};border:1px solid {_EDGE};border-radius:8px;'
            f'padding:16px 18px;font-size:13px;color:{_T2};line-height:1.9;">'
            f'<b style="color:{_T1};">DV01-neutral butterfly (fix {leg_b["tenor"]} belly at ${leg_b["face_m"]:.0f}M)</b><br>'
            f'{leg_a["tenor"]}: <b style="color:{_BLUE};">${neutral_face_a:.2f}M</b> ({leg_a["direction"]}) &nbsp;|&nbsp; '
            f'{leg_b["tenor"]}: <b style="color:{_AMB};">${leg_b["face_m"]:.0f}M</b> ({leg_b["direction"]}) &nbsp;|&nbsp; '
            f'{leg_c["tenor"]}: <b style="color:{_GRN};">${neutral_face_c:.2f}M</b> ({leg_c["direction"]})<br>'
            f'Each wing carries half the belly DV01 → net DV01 = $0 per 1bp parallel shift.<br><br>'
            f'<b style="color:{_T1};">✓ Parallel shift verification (at neutral sizes)</b><br>'
            f'Parallel <b>+50bp</b>: P&L = <b style="color:{vfy_color_up};">${verify_pl_up:+,.0f}</b> &nbsp;·&nbsp; '
            f'Parallel <b>−50bp</b>: P&L = <b style="color:{vfy_color_down};">${verify_pl_down:+,.0f}</b>'
            f'</div>',
            unsafe_allow_html=True,
        )

    # ── Trade summary expander ────────────────────────────────────────────────
    with st.expander("Full trade summary", expanded=False):
        summary_rows = []
        for leg in legs:
            summary_rows.append({
                "Leg":             leg["label"],
                "Tenor":           leg["tenor"],
                "Direction":       leg["direction"],
                "Notional ($M)":   f"{leg['face_m']:.1f}",
                "Current YTM (%)": f"{leg['cur_yld']:.2f}",
                "New YTM (%)":     f"{leg['new_yld']:.2f}",
                "Shift (bp)":      f"{leg['shift_bp']:+.0f}",
                "Entry Price":     f"{leg['price']:.4f}",
                "Exit Price":      f"{leg['new_price']:.4f}",
                "Mod Duration":    f"{leg['moddur']:.3f}",
                "DV01 ($, signed)":f"${leg['dv01']:+,.0f}",
                "P&L ($)":         f"${leg['pl_usd']:+,.0f}",
            })
        summary_rows.append({
            "Leg": "─── TOTAL ───", "Tenor": "", "Direction": "",
            "Notional ($M)": "", "Current YTM (%)": "", "New YTM (%)": "",
            "Shift (bp)": "", "Entry Price": "", "Exit Price": "",
            "Mod Duration": "",
            "DV01 ($, signed)": f"${total_dv01:+,.0f}",
            "P&L ($)": f"${total_pl:+,.0f}",
        })
        st.dataframe(pd.DataFrame(summary_rows), use_container_width=True, hide_index=True)
