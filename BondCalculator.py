"""
Bond Pricing & Calculator
Teaches: price ↔ yield, duration, modified duration, convexity, DV01, scenario P&L.
"""
from __future__ import annotations

import math

import plotly.graph_objects as go
import streamlit as st

_CARD = "#1e293b"
_BG   = "#0f172a"
_EDGE = "#334155"
_T1   = "#f1f5f9"
_T2   = "#94a3b8"
_BLUE = "#3b82f6"
_GRN  = "#10b981"
_RED  = "#ef4444"
_AMB  = "#fbbf24"


# ── Core bond math ─────────────────────────────────────────────────────────────

def _cashflows(face: float, coupon_rate: float, maturity: float,
               freq: int) -> list[tuple[float, float]]:
    """Return list of (time_in_years, cashflow) pairs."""
    periods = int(round(maturity * freq))
    coupon  = face * coupon_rate / freq
    cfs = [(t / freq, coupon) for t in range(1, periods)]
    cfs.append((maturity, coupon + face))
    return cfs


def bond_price(face: float, coupon_rate: float, maturity: float,
               ytm: float, freq: int) -> float:
    """Dirty price of a bond (full price, no accrued)."""
    cfs = _cashflows(face, coupon_rate, maturity, freq)
    r   = ytm / freq
    return sum(cf / (1 + r) ** (t * freq) for t, cf in cfs)


def macaulay_duration(face: float, coupon_rate: float, maturity: float,
                      ytm: float, freq: int) -> float:
    price = bond_price(face, coupon_rate, maturity, ytm, freq)
    if price == 0:
        return 0.0
    cfs = _cashflows(face, coupon_rate, maturity, freq)
    r   = ytm / freq
    return sum(t * cf / (1 + r) ** (t * freq) for t, cf in cfs) / price


def modified_duration(face: float, coupon_rate: float, maturity: float,
                      ytm: float, freq: int) -> float:
    mac = macaulay_duration(face, coupon_rate, maturity, ytm, freq)
    return mac / (1 + ytm / freq)


def convexity(face: float, coupon_rate: float, maturity: float,
              ytm: float, freq: int) -> float:
    price = bond_price(face, coupon_rate, maturity, ytm, freq)
    if price == 0:
        return 0.0
    cfs = _cashflows(face, coupon_rate, maturity, freq)
    r   = ytm / freq
    return (
        sum(t * (t + 1 / freq) * cf / (1 + r) ** (t * freq + 2)
            for t, cf in cfs)
        / price
    )


def ytm_from_price(face: float, coupon_rate: float, maturity: float,
                   price: float, freq: int,
                   tol: float = 1e-8, max_iter: int = 200) -> float:
    """Newton-Raphson YTM solve."""
    ytm = coupon_rate  # initial guess
    for _ in range(max_iter):
        p   = bond_price(face, coupon_rate, maturity, ytm, freq)
        dp  = -modified_duration(face, coupon_rate, maturity, ytm, freq) * p
        err = p - price
        if abs(err) < tol:
            break
        if dp == 0:
            break
        ytm -= err / dp
    return max(ytm, 1e-6)


def approx_price_change(mod_dur: float, conv: float,
                        price: float, dy: float) -> float:
    """First + second order approximation of ΔPrice for a yield change dy (decimal)."""
    return price * (-mod_dur * dy + 0.5 * conv * dy ** 2)


# ── Helpers ────────────────────────────────────────────────────────────────────

def _val_card(label: str, value: str, sub: str = "", accent: str = _BLUE) -> str:
    sub_html = (
        f'<div style="font-size:10px;color:{_T2};margin-top:3px;">{sub}</div>'
        if sub else ""
    )
    return (
        f'<div style="background:{_CARD};border:1px solid {_EDGE};border-left:3px solid {accent};'
        f'border-radius:8px;padding:14px 12px;">'
        f'<div style="font-size:10px;color:{_T2};text-transform:uppercase;'
        f'letter-spacing:.1em;margin-bottom:5px;">{label}</div>'
        f'<div style="font-size:20px;font-weight:700;color:{_T1};">{value}</div>'
        f'{sub_html}</div>'
    )


def _section(title: str, subtitle: str = "") -> None:
    sub = (
        f'<div style="font-size:12px;color:{_T2};margin-top:4px;">{subtitle}</div>'
        if subtitle else ""
    )
    st.markdown(
        f'<div style="background:{_CARD};border-left:4px solid {_BLUE};'
        f'padding:12px 16px;margin:28px 0 10px;border-radius:0 8px 8px 0;">'
        f'<span style="font-size:13px;font-weight:700;color:{_T1};'
        f'text-transform:uppercase;letter-spacing:.08em;">{title}</span>{sub}</div>',
        unsafe_allow_html=True,
    )


def _layout(**kw) -> dict:
    base = dict(
        template="plotly_dark",
        paper_bgcolor=_CARD,
        plot_bgcolor=_BG,
        margin=dict(l=62, r=20, t=44, b=44),
        font=dict(color=_T1, size=12),
        xaxis=dict(gridcolor=_EDGE, tickfont=dict(color=_T2),
                   showline=True, linecolor=_EDGE),
        yaxis=dict(gridcolor=_EDGE, tickfont=dict(color=_T2),
                   showline=True, linecolor=_EDGE),
        hoverlabel=dict(bgcolor=_CARD, font_color=_T1, bordercolor=_EDGE),
        legend=dict(font=dict(color=_T1), bgcolor="rgba(0,0,0,0)"),
    )
    base.update(kw)
    return base


# ── Main tab ───────────────────────────────────────────────────────────────────

def bond_calculator() -> None:
    st.markdown(
        '<h2 style="color:#0f172a;margin:0 0 2px;">Bond Pricing & Calculator</h2>'
        '<div style="font-size:12px;color:#475569;">'
        'Price ↔ Yield · Duration · Convexity · DV01 · Scenario P&amp;L</div>'
        '<hr style="border:none;border-top:1px solid #e2e8f0;margin:12px 0 8px;">',
        unsafe_allow_html=True,
    )

    # ── Inputs ────────────────────────────────────────────────────────────────
    _section("Bond Parameters")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        face      = st.number_input("Face Value", value=1000.0, step=100.0, min_value=1.0)
    with c2:
        coupon_pct = st.number_input("Coupon Rate (%)", value=5.0, step=0.25,
                                     min_value=0.0, max_value=30.0)
    with c3:
        maturity  = st.number_input("Maturity (years)", value=10.0, step=1.0,
                                    min_value=0.25, max_value=50.0)
    with c4:
        freq      = st.selectbox("Payment Frequency", [1, 2, 4, 12],
                                 index=1,
                                 format_func=lambda x: {1:"Annual",2:"Semi-annual",
                                                        4:"Quarterly",12:"Monthly"}[x])

    coupon_rate = coupon_pct / 100

    # ── Solve mode: enter YTM → get price, or enter price → get YTM ──────────
    _section("Pricing", "Enter either YTM or Price — the other is solved automatically")
    col_ytm, col_px, col_solve = st.columns([2, 2, 1])
    with col_ytm:
        ytm_pct = st.number_input("YTM (%)", value=5.0, step=0.1,
                                  min_value=0.01, max_value=50.0,
                                  key="ytm_input")
    with col_px:
        price_input = st.number_input("Price", value=round(bond_price(face, coupon_rate, maturity, ytm_pct / 100, freq), 4),
                                      step=0.01, min_value=0.01, key="price_input")
    with col_solve:
        st.markdown("<br>", unsafe_allow_html=True)
        solve_from_price = st.checkbox("Solve YTM from Price", value=False)

    if solve_from_price:
        ytm = ytm_from_price(face, coupon_rate, maturity, price_input, freq)
        price = price_input
    else:
        ytm   = ytm_pct / 100
        price = bond_price(face, coupon_rate, maturity, ytm, freq)

    mac_dur = macaulay_duration(face, coupon_rate, maturity, ytm, freq)
    mod_dur = modified_duration(face, coupon_rate, maturity, ytm, freq)
    conv    = convexity(face, coupon_rate, maturity, ytm, freq)
    dv01    = mod_dur * price * 0.0001   # $ change per 1bp move per unit face

    premium_discount = price - face
    pd_pct = premium_discount / face * 100

    # ── Key metrics ───────────────────────────────────────────────────────────
    _section("Key Metrics")

    accent_price = _GRN if price >= face else _RED
    cards = [
        ("Price",           f"${price:,.4f}",
         f"{'Premium' if price > face else 'Discount' if price < face else 'Par'} "
         f"({pd_pct:+.2f}% of face)", accent_price),
        ("YTM",             f"{ytm*100:.4f}%",          "", _BLUE),
        ("Macaulay Duration",f"{mac_dur:.3f} yrs",      "Weighted avg time to cashflow", _AMB),
        ("Modified Duration",f"{mod_dur:.3f}",           "% price change per 1% yield move", _AMB),
        ("Convexity",        f"{conv:.3f}",              "Second-order price sensitivity", _T2),
        ("DV01",             f"${dv01:,.4f}",            "$ change per 1bp per unit face", _GRN),
    ]

    html = '<div style="display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin-bottom:8px;">'
    for label, val, sub, acc in cards:
        html += _val_card(label, val, sub, acc)
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)

    # ── Price–Yield curve ─────────────────────────────────────────────────────
    _section("Price–Yield Relationship",
             "Full convexity curve with duration tangent line at current YTM")
    ytm_range = [y / 1000 for y in range(max(1, int(ytm * 1000) - 400),
                                          int(ytm * 1000) + 401)]
    prices = [bond_price(face, coupon_rate, maturity, y, freq) for y in ytm_range]
    # Duration tangent
    tangent = [price + approx_price_change(mod_dur, 0, price, y - ytm)
               for y in ytm_range]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=[y * 100 for y in ytm_range], y=prices,
        name="Actual price", line=dict(color=_BLUE, width=2.5),
        hovertemplate="YTM: %{x:.2f}%<br>Price: $%{y:,.2f}<extra></extra>",
    ))
    fig.add_trace(go.Scatter(
        x=[y * 100 for y in ytm_range], y=tangent,
        name="Duration approx.", line=dict(color=_AMB, width=1.5, dash="dash"),
        hovertemplate="YTM: %{x:.2f}%<br>Duration est.: $%{y:,.2f}<extra></extra>",
    ))
    fig.add_trace(go.Scatter(
        x=[ytm * 100], y=[price],
        name="Current", mode="markers",
        marker=dict(color=_GRN, size=12, symbol="circle",
                    line=dict(width=2, color=_BG)),
        hovertemplate=f"YTM: {ytm*100:.3f}%<br>Price: ${price:,.4f}<extra></extra>",
    ))
    fig.update_layout(
        height=400,
        xaxis_title="YTM (%)",
        yaxis_title=f"Price (face = ${face:,.0f})",
        **_layout(),
    )
    st.plotly_chart(fig, use_container_width=True)

    # ── Scenario P&L ──────────────────────────────────────────────────────────
    _section("Rate Shock Scenarios",
             "Estimated price change using duration + convexity approximation")

    shocks_bp = [-200, -100, -50, -25, +25, +50, +100, +200]
    rows = []
    for bp in shocks_bp:
        dy      = bp / 10000
        new_ytm = max(ytm + dy, 1e-4)
        exact   = bond_price(face, coupon_rate, maturity, new_ytm, freq)
        approx  = price + approx_price_change(mod_dur, conv, price, dy)
        rows.append({
            "Shock (bps)":     f"{bp:+d}",
            "New YTM (%)":     f"{new_ytm*100:.3f}",
            "Exact Price":     f"${exact:,.4f}",
            "Approx Price":    f"${approx:,.4f}",
            "ΔPrice (exact)":  f"${exact - price:+,.4f}",
            "ΔPrice %":        f"{(exact - price) / price * 100:+.3f}%",
        })

    import pandas as pd
    scenario_df = pd.DataFrame(rows)

    # Colour code the ΔPrice column
    def _colour_row(row):
        bp = int(row["Shock (bps)"].replace("+", ""))
        clr = "#d1fae5" if bp < 0 else "#fee2e2" if bp > 0 else ""
        return [f"background-color:{clr}" if clr else "" for _ in row]

    st.dataframe(
        scenario_df.style.apply(_colour_row, axis=1),
        use_container_width=True,
        hide_index=True,
    )

    # Scenario bar chart
    exact_changes = []
    for bp in shocks_bp:
        dy      = bp / 10000
        new_ytm = max(ytm + dy, 1e-4)
        exact_changes.append(bond_price(face, coupon_rate, maturity, new_ytm, freq) - price)

    bar_colors = [_GRN if v >= 0 else _RED for v in exact_changes]
    fig2 = go.Figure(go.Bar(
        x=[f"{b:+d}bp" for b in shocks_bp],
        y=exact_changes,
        marker_color=bar_colors,
        hovertemplate="Shock: %{x}<br>ΔPrice: $%{y:+,.4f}<extra></extra>",
    ))
    fig2.update_layout(
        height=300,
        title=dict(text="ΔPrice by Rate Shock", font=dict(size=13, color=_T1), x=0),
        xaxis_title="Rate shock",
        yaxis_title=f"ΔPrice ($)",
        showlegend=False,
        **_layout(legend=dict(visible=False)),
    )
    st.plotly_chart(fig2, use_container_width=True)

    # ── Cashflow timeline ─────────────────────────────────────────────────────
    _section("Cashflow Timeline", "Each coupon and the final principal repayment")
    cfs = _cashflows(face, coupon_rate, maturity, freq)
    cf_times  = [t for t, _ in cfs]
    cf_values = [v for _, v in cfs]
    cf_colors = [_BLUE if v < face else _GRN for v in cf_values]

    fig3 = go.Figure(go.Bar(
        x=cf_times, y=cf_values,
        marker_color=cf_colors,
        hovertemplate="t = %{x:.2f} yrs<br>Cashflow: $%{y:,.2f}<extra></extra>",
    ))
    fig3.update_layout(
        height=300,
        title=dict(text="Bond Cashflows", font=dict(size=13, color=_T1), x=0),
        xaxis_title="Time (years)",
        yaxis_title="Cashflow ($)",
        showlegend=False,
        **_layout(legend=dict(visible=False)),
    )
    st.plotly_chart(fig3, use_container_width=True)

    # ── Concept explainer ─────────────────────────────────────────────────────
    with st.expander("Concept guide — What do these numbers mean?"):
        st.markdown(f"""
**Price** (${price:,.4f}) — The present value of all future cashflows discounted at the YTM.
A price **above face** ({face:,.0f}) means the bond trades at a **premium** (coupon > market rate).
A price **below face** means it trades at a **discount** (coupon < market rate).

**Yield to Maturity (YTM)** ({ytm*100:.3f}%) — The single discount rate that equates the bond's
price to its present value of cashflows. It is the bond's implied return if held to maturity.

**Macaulay Duration** ({mac_dur:.3f} yrs) — The weighted-average time to receive the bond's
cashflows. A zero-coupon bond's duration equals its maturity; coupon bonds are shorter.

**Modified Duration** ({mod_dur:.3f}) — Measures **price sensitivity to yield**:
a 1% rise in yield changes price by approximately −{mod_dur:.2f}%.
Formula: ModDur = MacDur / (1 + YTM/frequency).

**Convexity** ({conv:.3f}) — The curvature in the price–yield relationship.
Duration *underestimates* price gains and *overestimates* price losses for large yield moves.
Convexity corrects for this: investors pay a premium for high-convexity bonds.

**DV01** (${dv01:,.4f}) — Dollar Value of 1 basis point.
The dollar change in price for a 1bp (0.01%) move in yield for this bond.
Portfolio risk managers aggregate DV01 across all positions.

**Approximation formula:**
ΔPrice ≈ −ModDur × Price × Δy + ½ × Convexity × Price × Δy²
        """)

    # ── Hold-to-maturity: risk evolution over time ────────────────────────────
    _section(
        "Rate Scenario — Risk Evolution Over Time",
        "How Price, Modified Duration and DV01 change as you hold this bond to maturity under different rate regimes",
    )

    st.sidebar.markdown("---")
    st.sidebar.markdown(
        f'<div style="font-size:11px;font-weight:700;color:#94a3b8;'
        f'text-transform:uppercase;letter-spacing:.08em;margin-bottom:6px;">'
        f'Rate Evolution</div>',
        unsafe_allow_html=True,
    )
    sel_shocks = st.sidebar.multiselect(
        "Scenarios (bp shift)",
        options=[-200, -100, -50, 0, +50, +100, +200],
        default=[-100, 0, +100],
        key="evo_shocks",
    )
    pos_face = st.sidebar.number_input(
        "Position size ($)",
        value=1_000_000.0,
        step=500_000.0,
        min_value=1.0,
        format="%,.0f",
        key="evo_face",
        help="Used for DV01 dollar display only",
    )

    if not sel_shocks:
        st.info("Select at least one rate scenario in the sidebar.")
    else:
        # colour map: blue spectrum for cuts, grey for 0, red spectrum for hikes
        _SHOCK_COLORS = {
            -200: "#1d4ed8", -100: "#3b82f6", -50: "#93c5fd",
            0:    "#94a3b8",
            +50:  "#fca5a5", +100: "#ef4444", +200: "#991b1b",
        }

        # time axis — quarterly steps
        n_steps = max(int(maturity * 4), 1)
        t_axis  = [i / 4 for i in range(n_steps + 1)]

        # compute series per scenario
        series: dict[int, dict] = {}
        for shock in sorted(sel_shocks):
            s_ytm = max(ytm + shock / 10000, 0.0001)
            px_s, md_s, dv_s = [], [], []
            for t in t_axis:
                rem = maturity - t
                if rem < 1 / freq / 2:
                    px_s.append(face); md_s.append(0.0); dv_s.append(0.0)
                else:
                    p_  = bond_price(face, coupon_rate, rem, s_ytm, freq)
                    md_ = modified_duration(face, coupon_rate, rem, s_ytm, freq)
                    dv_ = md_ * (p_ / face) * pos_face * 0.0001
                    px_s.append(p_); md_s.append(md_); dv_s.append(dv_)
            series[shock] = {"price": px_s, "moddur": md_s, "dv01": dv_s, "ytm": s_ytm}

        col_a, col_b, col_c = st.columns(3)

        # Chart 1 — Price pull-to-par
        fig_px = go.Figure()
        fig_px.add_hline(y=face, line_color=_EDGE, line_dash="dot", line_width=1,
                         annotation_text="Par", annotation_font=dict(size=9, color=_T2))
        for shock in sorted(sel_shocks):
            clr   = _SHOCK_COLORS.get(shock, _BLUE)
            lbl   = f"{shock:+d} bp"
            fig_px.add_trace(go.Scatter(
                x=t_axis, y=series[shock]["price"], name=lbl,
                line=dict(color=clr, width=1.8),
                hovertemplate=f"t=%{{x:.2f}} yr | {lbl}<br>Price: $%{{y:,.2f}}<extra></extra>",
            ))
        fig_px.update_layout(
            height=320,
            title=dict(text="Price — Pull to Par", font=dict(size=12, color=_T1), x=0),
            xaxis_title="Years held",
            yaxis_title=f"Price ($)",
            **_layout(),
        )
        with col_a:
            st.plotly_chart(fig_px, use_container_width=True)
            st.caption(
                "All paths converge to face value at maturity regardless of rate level. "
                "A rate shock shifts the starting price but the pull-to-par effect is "
                "inexorable — guaranteeing par if held to maturity."
            )

        # Chart 2 — Modified Duration decline
        fig_md = go.Figure()
        for shock in sorted(sel_shocks):
            clr = _SHOCK_COLORS.get(shock, _BLUE)
            fig_md.add_trace(go.Scatter(
                x=t_axis, y=series[shock]["moddur"], name=f"{shock:+d} bp",
                line=dict(color=clr, width=1.8),
                hovertemplate=f"t=%{{x:.2f}} yr<br>ModDur: %{{y:.3f}}<extra></extra>",
            ))
        fig_md.update_layout(
            height=320,
            title=dict(text="Modified Duration — Declining as Bond Ages", font=dict(size=12, color=_T1), x=0),
            xaxis_title="Years held",
            yaxis_title="ModDur (years)",
            **_layout(),
        )
        with col_b:
            st.plotly_chart(fig_md, use_container_width=True)
            st.caption(
                "Duration falls as remaining maturity shrinks — the bond becomes less "
                "interest-rate sensitive over time. Higher-YTM scenarios show slightly "
                "lower duration because cashflows are discounted more heavily."
            )

        # Chart 3 — DV01 dollar risk
        fig_dv = go.Figure()
        for shock in sorted(sel_shocks):
            clr = _SHOCK_COLORS.get(shock, _BLUE)
            fig_dv.add_trace(go.Scatter(
                x=t_axis, y=series[shock]["dv01"], name=f"{shock:+d} bp",
                line=dict(color=clr, width=1.8),
                hovertemplate=f"t=%{{x:.2f}} yr<br>DV01: $%{{y:,.1f}}<extra></extra>",
            ))
        fig_dv.update_layout(
            height=320,
            title=dict(text=f"DV01 — Dollar Risk per 1bp (${pos_face:,.0f} position)", font=dict(size=12, color=_T1), x=0),
            xaxis_title="Years held",
            yaxis_title="DV01 ($)",
            **_layout(),
        )
        with col_c:
            st.plotly_chart(fig_dv, use_container_width=True)
            st.caption(
                "DV01 combines price and duration — it is the actual dollar P&L per 1bp "
                "move in yield for this position. Both decline toward zero at maturity, "
                "showing risk naturally reduces as a bond ages."
            )

        # Math detail table at t=0
        with st.expander("Scenario snapshot at purchase (t = 0)"):
            detail_rows = []
            base_price = series.get(0, {}).get("price", [price])[0] if 0 in series else price
            for shock in sorted(sel_shocks):
                s   = series[shock]
                p0  = s["price"][0]
                md0 = s["moddur"][0]
                dv0 = s["dv01"][0]
                pl_vs_base = (p0 - price) / face * pos_face
                detail_rows.append({
                    "Scenario":         f"{shock:+d} bp",
                    "YTM (%)":          f"{s['ytm']*100:.4f}",
                    "Price ($)":        f"${p0:,.4f}",
                    "vs Face":          f"{(p0-face)/face*100:+.2f}%",
                    "Mod Duration":     f"{md0:.3f}",
                    "DV01 ($)":         f"${dv0:,.1f}",
                    "P&L vs 0bp ($)":   f"${pl_vs_base:+,.0f}",
                })
            st.dataframe(pd.DataFrame(detail_rows), use_container_width=True, hide_index=True)
            st.caption(
                f"P&L vs 0bp shows the mark-to-market gain/loss on a ${pos_face:,.0f} position "
                "if rates move by the scenario amount on the day of purchase."
            )
