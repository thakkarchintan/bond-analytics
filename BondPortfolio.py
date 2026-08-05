"""
Bond Portfolio Builder
One accordion, four maturity buckets in a row, check + qty per bond.
Face value = $100,000 per bond; qty = number of bonds.
"""
from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from BondCalculator import (
    approx_price_change, bond_price,
    convexity, macaulay_duration, modified_duration,
)

# ── Palette ────────────────────────────────────────────────────────────────────

COUNTRY_COLORS = {
    "USA":            "#60a5fa",
    "Germany":        "#a78bfa",
    "United Kingdom": "#22d3ee",
    "Japan":          "#34d399",
    "France":         "#fbbf24",
    "Italy":          "#fb923c",
    "Canada":         "#818cf8",
    "Australia":      "#f472b6",
    "India":          "#f87171",
    "Brazil":         "#a3e635",
    "China":          "#e879f9",
}

_CARD = "#1e293b"
_BG   = "#0f172a"
_EDGE = "#334155"
_T1   = "#f1f5f9"
_T2   = "#94a3b8"
_T3   = "#475569"
_BLUE = "#3b82f6"
_GRN  = "#10b981"
_RED  = "#ef4444"
_AMB  = "#fbbf24"

FACE = 100_000  # $100k face per bond

# Maturity buckets: (label, accent, lo_exclusive, hi_inclusive)
BUCKETS = [
    ("2Y",  _BLUE,    0.0,  2.5),
    ("5Y",  _AMB,     2.5,  7.0),
    ("10Y", _GRN,     7.0, 15.0),
    ("30Y", "#a78bfa", 15.0, 50.0),
]

# ── Bond universe (30 sovereign bonds, FV = $100k each) ───────────────────────

BOND_UNIVERSE: list[dict] = [
    # USA — semi-annual
    dict(id="US-2Y",  name="US Treasury 2Y",      country="USA",            coupon=4.625, maturity=2,  ytm=4.25, face=FACE, freq=2),
    dict(id="US-5Y",  name="US Treasury 5Y",       country="USA",            coupon=4.250, maturity=5,  ytm=4.10, face=FACE, freq=2),
    dict(id="US-10Y", name="US Treasury 10Y",      country="USA",            coupon=4.250, maturity=10, ytm=4.20, face=FACE, freq=2),
    dict(id="US-30Y", name="US Treasury 30Y",      country="USA",            coupon=4.625, maturity=30, ytm=4.50, face=FACE, freq=2),
    # Germany — annual
    dict(id="DE-2Y",  name="German Bund 2Y",       country="Germany",        coupon=2.500, maturity=2,  ytm=2.40, face=FACE, freq=1),
    dict(id="DE-5Y",  name="German Bund 5Y",       country="Germany",        coupon=2.250, maturity=5,  ytm=2.35, face=FACE, freq=1),
    dict(id="DE-10Y", name="German Bund 10Y",      country="Germany",        coupon=2.600, maturity=10, ytm=2.65, face=FACE, freq=1),
    dict(id="DE-30Y", name="German Bund 30Y",      country="Germany",        coupon=2.700, maturity=30, ytm=2.90, face=FACE, freq=1),
    # UK — semi-annual
    dict(id="UK-2Y",  name="UK Gilt 2Y",           country="United Kingdom", coupon=4.750, maturity=2,  ytm=4.35, face=FACE, freq=2),
    dict(id="UK-10Y", name="UK Gilt 10Y",          country="United Kingdom", coupon=4.250, maturity=10, ytm=4.45, face=FACE, freq=2),
    dict(id="UK-30Y", name="UK Gilt 30Y",          country="United Kingdom", coupon=4.125, maturity=30, ytm=4.70, face=FACE, freq=2),
    # Japan — semi-annual
    dict(id="JP-2Y",  name="Japan JGB 2Y",         country="Japan",          coupon=0.600, maturity=2,  ytm=0.65, face=FACE, freq=2),
    dict(id="JP-10Y", name="Japan JGB 10Y",        country="Japan",          coupon=1.100, maturity=10, ytm=1.00, face=FACE, freq=2),
    dict(id="JP-30Y", name="Japan JGB 30Y",        country="Japan",          coupon=1.800, maturity=30, ytm=2.00, face=FACE, freq=2),
    # France — annual
    dict(id="FR-5Y",  name="France OAT 5Y",        country="France",         coupon=2.750, maturity=5,  ytm=3.00, face=FACE, freq=1),
    dict(id="FR-10Y", name="France OAT 10Y",       country="France",         coupon=3.000, maturity=10, ytm=3.45, face=FACE, freq=1),
    # Italy — semi-annual
    dict(id="IT-3Y",  name="Italy BTP 3Y",         country="Italy",          coupon=3.500, maturity=3,  ytm=3.40, face=FACE, freq=2),
    dict(id="IT-10Y", name="Italy BTP 10Y",        country="Italy",          coupon=4.000, maturity=10, ytm=3.70, face=FACE, freq=2),
    dict(id="IT-30Y", name="Italy BTP 30Y",        country="Italy",          coupon=4.500, maturity=30, ytm=4.20, face=FACE, freq=2),
    # Canada — semi-annual
    dict(id="CA-2Y",  name="Canada GoC 2Y",        country="Canada",         coupon=3.750, maturity=2,  ytm=3.05, face=FACE, freq=2),
    dict(id="CA-10Y", name="Canada GoC 10Y",       country="Canada",         coupon=3.250, maturity=10, ytm=3.10, face=FACE, freq=2),
    # Australia — semi-annual
    dict(id="AU-3Y",  name="Australia ACGB 3Y",    country="Australia",      coupon=3.750, maturity=3,  ytm=3.85, face=FACE, freq=2),
    dict(id="AU-10Y", name="Australia ACGB 10Y",   country="Australia",      coupon=4.250, maturity=10, ytm=4.30, face=FACE, freq=2),
    # India — semi-annual
    dict(id="IN-5Y",  name="India G-Sec 5Y",       country="India",          coupon=7.000, maturity=5,  ytm=6.85, face=FACE, freq=2),
    dict(id="IN-10Y", name="India G-Sec 10Y",      country="India",          coupon=7.180, maturity=10, ytm=6.95, face=FACE, freq=2),
    # Brazil — semi-annual
    dict(id="BR-2Y",  name="Brazil NTN-F 2Y",      country="Brazil",         coupon=10.00, maturity=2,  ytm=12.00, face=FACE, freq=2),
    dict(id="BR-5Y",  name="Brazil NTN-F 5Y",      country="Brazil",         coupon=10.00, maturity=5,  ytm=12.50, face=FACE, freq=2),
    dict(id="BR-10Y", name="Brazil NTN-F 10Y",     country="Brazil",         coupon=10.00, maturity=10, ytm=12.90, face=FACE, freq=2),
    # China — semi-annual
    dict(id="CN-5Y",  name="China CGB 5Y",         country="China",          coupon=2.200, maturity=5,  ytm=2.00, face=FACE, freq=2),
    dict(id="CN-10Y", name="China CGB 10Y",        country="China",          coupon=2.400, maturity=10, ytm=2.20, face=FACE, freq=2),
]

_BOND_BY_ID: dict[str, dict] = {b["id"]: b for b in BOND_UNIVERSE}

MAT_BUCKETS_CHART = [
    ("0–2Y",   0,  2),
    ("2–5Y",   2,  5),
    ("5–10Y",  5, 10),
    ("10–30Y", 10, 30),
]

# ── Scenario builder constants ────────────────────────────────────────────────

# Display columns: 2Y | 3Y | 5Y | 10Y | 30Y
_TENOR_LABELS = ["2Y", "3Y", "5Y", "10Y", "30Y"]

# Map bond maturity → column index (0=2Y, 1=3Y, 2=5Y, 3=10Y, 4=30Y)
def _tenor_col(mat: float) -> int:
    if mat <= 2.5: return 0
    if mat <= 4.0: return 1
    if mat <= 7.0: return 2
    if mat <= 15.0: return 3
    return 4

# (country, col_idx) → bond  (unique per country per tenor bucket)
_BOND_GRID: dict[tuple[str, int], dict] = {
    (b["country"], _tenor_col(b["maturity"])): b for b in BOND_UNIVERSE
}

_DISPLAY_COUNTRIES = [
    ("USA",            "USA"),
    ("Germany",        "Germany"),
    ("United Kingdom", "UK"),
    ("Japan",          "Japan"),
    ("France",         "France"),
    ("Italy",          "Italy"),
    ("Canada",         "Canada"),
    ("Australia",      "Australia"),
    ("India",          "India"),
    ("Brazil",         "Brazil"),
    ("China",          "China"),
]

# Preset shocks keyed by tenor column index
_PRESET_SHOCKS: dict[str, dict[int, int]] = {
    "+25bp":         {i: 25   for i in range(5)},
    "+50bp":         {i: 50   for i in range(5)},
    "+100bp":        {i: 100  for i in range(5)},
    "-25bp":         {i: -25  for i in range(5)},
    "-50bp":         {i: -50  for i in range(5)},
    "-100bp":        {i: -100 for i in range(5)},
    "Bear Steepen":  {0: 30, 1: 45, 2: 65, 3: 90, 4: 110},
    "Bull Flatten":  {0: -20, 1: -35, 2: -55, 3: -80, 4: -100},
    "Reset":         {i: 0   for i in range(5)},
}


# ── Bond math ─────────────────────────────────────────────────────────────────

def _metrics(b: dict) -> dict:
    c, y = b["coupon"] / 100, b["ytm"] / 100
    px   = bond_price(b["face"], c, b["maturity"], y, b["freq"])
    mac  = macaulay_duration(b["face"], c, b["maturity"], y, b["freq"])
    mod  = modified_duration(b["face"], c, b["maturity"], y, b["freq"])
    conv = convexity(b["face"], c, b["maturity"], y, b["freq"])
    dv01 = mod * px * 0.0001
    return dict(price=px, mac_dur=mac, mod_dur=mod, conv=conv, dv01=dv01)


# ── UI helpers ─────────────────────────────────────────────────────────────────

def _section(title: str, subtitle: str = "") -> None:
    sub = (
        f'<div style="font-size:12px;color:{_T2};margin-top:4px;">{subtitle}</div>'
        if subtitle else ""
    )
    st.markdown(
        f'<div style="background:{_CARD};border-left:4px solid {_BLUE};'
        f'padding:10px 16px;margin:24px 0 10px;border-radius:0 8px 8px 0;">'
        f'<span style="font-size:12px;font-weight:700;color:{_T1};'
        f'text-transform:uppercase;letter-spacing:.08em;">{title}</span>{sub}</div>',
        unsafe_allow_html=True,
    )


def _val_card(label: str, value: str, sub: str = "", accent: str = _BLUE) -> str:
    sub_html = (
        f'<div style="font-size:10px;color:{_T2};margin-top:3px;">{sub}</div>'
        if sub else ""
    )
    return (
        f'<div style="background:{_CARD};border:1px solid {_EDGE};'
        f'border-left:3px solid {accent};border-radius:8px;padding:12px;">'
        f'<div style="font-size:10px;color:{_T2};text-transform:uppercase;'
        f'letter-spacing:.1em;margin-bottom:4px;">{label}</div>'
        f'<div style="font-size:18px;font-weight:700;color:{_T1};">{value}</div>'
        f'{sub_html}</div>'
    )


def _chart_layout(**kw) -> dict:
    base = dict(
        template="plotly_dark",
        paper_bgcolor=_CARD, plot_bgcolor=_BG,
        margin=dict(l=62, r=20, t=40, b=44),
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


# ── Compact bond row inside a bucket column ────────────────────────────────────

def _bond_row(b: dict) -> None:
    """Checkbox + small detail + qty stepper if selected."""
    checked = st.checkbox(
        b["country"],
        key=f"chk_{b['id']}",
        help=f"{b['name']}",
    )
    # Small detail line always visible
    st.markdown(
        f'<div style="font-size:10px;color:{_T3};margin:-6px 0 4px 24px;">'
        f'{b["coupon"]:.2f}% · YTM {b["ytm"]:.2f}%</div>',
        unsafe_allow_html=True,
    )

    if checked:
        unit_key = f"units_{b['id']}"
        if unit_key not in st.session_state:
            st.session_state[unit_key] = 1

        qty = st.session_state[unit_key]
        mv  = _metrics(b)["price"] * qty

        # Compact inline stepper: [−] qty [+]  $xM
        c1, c2, c3, c4 = st.columns([1, 1, 1, 3])
        with c1:
            if st.button("−", key=f"dec_{b['id']}"):
                st.session_state[unit_key] = max(1, qty - 1)
        with c2:
            st.markdown(
                f'<div style="text-align:center;font-size:12px;font-weight:600;'
                f'color:{_T1};padding-top:6px;">{qty}</div>',
                unsafe_allow_html=True,
            )
        with c3:
            if st.button("+", key=f"inc_{b['id']}"):
                st.session_state[unit_key] = qty + 1
        with c4:
            st.markdown(
                f'<div style="font-size:10px;color:{_T3};padding-top:7px;">'
                f'${mv/1e6:.2f}M</div>',
                unsafe_allow_html=True,
            )


# ── Scenario builder ──────────────────────────────────────────────────────────

def _apply_preset(name: str) -> None:
    col_shocks = _PRESET_SHOCKS[name]
    for b in BOND_UNIVERSE:
        st.session_state[f"shock_{b['id']}"] = col_shocks[_tenor_col(b["maturity"])]


def _scenario_builder(portfolio_ids: set[str]) -> None:
    _section(
        "Yield Shock Scenario",
        "Set basis-point changes per economy and maturity — impact analysis updates below",
    )

    # Preset buttons — row 1: parallel, row 2: curve + reset
    row1 = ["+25bp", "+50bp", "+100bp", "-25bp", "-50bp", "-100bp"]
    row2 = ["Bear Steepen", "Bull Flatten", "Reset"]

    c1s = st.columns(len(row1))
    for col, name in zip(c1s, row1):
        with col:
            if st.button(name, key=f"pbtn_{name}", use_container_width=True):
                _apply_preset(name)
                st.rerun()

    c2s = st.columns(len(row2))
    for col, name in zip(c2s, row2):
        with col:
            if st.button(name, key=f"pbtn_{name}", use_container_width=True):
                _apply_preset(name)
                st.rerun()

    st.markdown('<div style="height:8px"></div>', unsafe_allow_html=True)

    # Initialise all shock keys to 0 on first render
    for b in BOND_UNIVERSE:
        if f"shock_{b['id']}" not in st.session_state:
            st.session_state[f"shock_{b['id']}"] = 0

    # Header row
    widths = [1.8] + [0.85] * 5
    hcols = st.columns(widths)
    hcols[0].markdown(
        f'<div style="font-size:10px;font-weight:600;color:{_T2};'
        f'text-transform:uppercase;letter-spacing:.08em;">Economy</div>',
        unsafe_allow_html=True,
    )
    for i, lbl in enumerate(_TENOR_LABELS):
        hcols[i + 1].markdown(
            f'<div style="font-size:10px;font-weight:600;color:{_T2};'
            f'text-transform:uppercase;letter-spacing:.08em;text-align:center;">{lbl}</div>',
            unsafe_allow_html=True,
        )

    # One row per economy
    for country_full, country_short in _DISPLAY_COUNTRIES:
        in_portfolio = any(
            b["id"] in portfolio_ids
            for b in BOND_UNIVERSE if b["country"] == country_full
        )
        color  = _T1 if in_portfolio else _T3
        weight = "600" if in_portfolio else "400"
        rcols  = st.columns(widths)
        with rcols[0]:
            st.markdown(
                f'<div style="font-size:11px;color:{color};font-weight:{weight};'
                f'padding-top:9px;">{country_short}</div>',
                unsafe_allow_html=True,
            )
        for i in range(5):
            bond = _BOND_GRID.get((country_full, i))
            with rcols[i + 1]:
                if bond:
                    st.number_input(
                        "bps",
                        key=f"shock_{bond['id']}",
                        min_value=-1000,
                        max_value=1000,
                        step=1,
                        label_visibility="collapsed",
                    )
                else:
                    st.markdown(
                        f'<div style="height:38px;display:flex;align-items:center;'
                        f'justify-content:center;font-size:12px;color:{_EDGE};">—</div>',
                        unsafe_allow_html=True,
                    )

    st.markdown(
        f'<div style="font-size:11px;color:{_T3};margin-top:6px;">'
        f'Bold economies have bonds in your portfolio. '
        f'Shocks for economies not in your portfolio have no P&L impact.</div>',
        unsafe_allow_html=True,
    )


# ── Impact analysis ────────────────────────────────────────────────────────────

def _impact_analysis(df: pd.DataFrame, total_mv: float) -> None:
    # Collect per-bond shocks and compute new prices
    shock_rows = []
    for _, row in df.iterrows():
        bid       = row["id"]
        shock_bps = int(st.session_state.get(f"shock_{bid}", 0))
        b         = _BOND_BY_ID[bid]
        new_ytm   = max(b["ytm"] / 100 + shock_bps / 10_000, 0.0001)
        new_px    = bond_price(b["face"], b["coupon"] / 100, b["maturity"], new_ytm, b["freq"])
        delta_mv  = (new_px - row["price"]) * row["units"]
        shock_rows.append(dict(
            id=bid, name=row["name"], country=row["country"], bucket=row["bucket"],
            shock_bps=shock_bps,
            old_ytm=b["ytm"],
            new_ytm=new_ytm * 100,
            old_price=row["price"], new_price=new_px,
            old_mv=row["mv"], new_mv=new_px * row["units"],
            delta_mv=delta_mv, units=row["units"],
        ))

    sdf         = pd.DataFrame(shock_rows)
    total_delta = sdf["delta_mv"].sum()
    has_shock   = sdf["shock_bps"].ne(0).any()

    if not has_shock:
        _section(
            "Risk & Impact Analysis",
            "Set yield shocks above — portfolio P&L will appear here",
        )
        st.info("All yield shocks are zero. Adjust basis points in the scenario builder to see impact.")
        return

    pct = total_delta / total_mv * 100
    _section(
        "Risk & Impact Analysis",
        f"Scenario total  {'+' if total_delta >= 0 else ''}${total_delta:,.0f}  "
        f"({'+'if pct >= 0 else ''}{pct:.3f}% of portfolio)",
    )

    # ── Summary cards ─────────────────────────────────────────────────────────
    worst = sdf.loc[sdf["delta_mv"].idxmin()]
    best  = sdf.loc[sdf["delta_mv"].idxmax()]
    n_moved = sdf["shock_bps"].ne(0).sum()
    cards = [
        ("Total ΔMV",
         f"${total_delta:+,.0f}",
         f"{pct:+.3f}% of portfolio",
         _GRN if total_delta >= 0 else _RED),
        ("Biggest gain",
         f"${best['delta_mv']:+,.0f}",
         best["name"],
         _GRN),
        ("Biggest loss",
         f"${worst['delta_mv']:+,.0f}",
         worst["name"],
         _RED),
        ("Bonds impacted",
         str(n_moved),
         f"of {len(sdf)} in portfolio",
         _T2),
    ]
    html = '<div style="display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin-bottom:16px;">'
    for lbl, val, sub, acc in cards:
        html += _val_card(lbl, val, sub, acc)
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)

    # ── Charts ────────────────────────────────────────────────────────────────
    c1, c2 = st.columns(2)

    with c1:
        cdf = sdf.groupby("country")["delta_mv"].sum().reset_index().sort_values("delta_mv")
        fig = go.Figure(go.Bar(
            x=cdf["delta_mv"], y=cdf["country"], orientation="h",
            marker_color=[_GRN if v >= 0 else _RED for v in cdf["delta_mv"]],
            hovertemplate="<b>%{y}</b><br>ΔMV: $%{x:+,.0f}<extra></extra>",
        ))
        fig.add_vline(x=0, line=dict(color=_T3, width=1))
        fig.update_layout(
            height=300,
            title=dict(text="P&L by country", font=dict(size=13, color=_T1), x=0),
            xaxis_title="ΔMV ($)", showlegend=False,
            **_chart_layout(margin=dict(l=130, r=20, t=40, b=44)),
        )
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        bucket_order = [b[0] for b in BUCKETS]
        bdf = (
            sdf.groupby("bucket")["delta_mv"]
            .sum()
            .reindex(bucket_order)
            .fillna(0)
            .reset_index()
        )
        fig = go.Figure(go.Bar(
            x=bdf["bucket"], y=bdf["delta_mv"],
            marker_color=[_GRN if v >= 0 else _RED for v in bdf["delta_mv"]],
            hovertemplate="%{x}<br>ΔMV: $%{y:+,.0f}<extra></extra>",
        ))
        fig.add_hline(y=0, line=dict(color=_T3, width=1))
        fig.update_layout(
            height=300,
            title=dict(text="P&L by maturity bucket", font=dict(size=13, color=_T1), x=0),
            yaxis_title="ΔMV ($)", showlegend=False,
            **_chart_layout(margin=dict(l=72, r=20, t=40, b=44)),
        )
        st.plotly_chart(fig, use_container_width=True)

    # Waterfall: P&L attribution per bond (sorted worst → best)
    wdf = sdf.sort_values("delta_mv")
    x_labels  = wdf["name"].tolist() + ["Total"]
    y_values  = wdf["delta_mv"].tolist() + [total_delta]
    measures  = ["relative"] * len(wdf) + ["total"]
    text_vals = [f"${v:+,.0f}" for v in y_values]

    fig = go.Figure(go.Waterfall(
        x=x_labels, y=y_values, measure=measures,
        connector=dict(line=dict(color=_EDGE, width=1, dash="dot")),
        increasing=dict(marker_color=_GRN),
        decreasing=dict(marker_color=_RED),
        totals=dict(marker_color=_BLUE),
        text=text_vals, textposition="outside",
        textfont=dict(color=_T1, size=9),
        hovertemplate="%{x}<br>ΔMV: $%{y:+,.0f}<extra></extra>",
    ))
    fig.update_layout(
        height=320,
        title=dict(text="P&L attribution — by bond", font=dict(size=13, color=_T1), x=0),
        yaxis_title="ΔMV ($)", showlegend=False,
        **_chart_layout(margin=dict(l=72, r=20, t=40, b=90)),
    )
    st.plotly_chart(fig, use_container_width=True)

    # ── Detail table ──────────────────────────────────────────────────────────
    disp = sdf[[
        "name", "country", "shock_bps", "old_ytm", "new_ytm",
        "old_price", "new_price", "units", "old_mv", "new_mv", "delta_mv",
    ]].copy()
    disp.columns = [
        "Bond", "Country", "Shock (bps)", "Old YTM (%)", "New YTM (%)",
        "Old Price", "New Price", "Qty", "Old MV ($)", "New MV ($)", "ΔMV ($)",
    ]
    disp["Old YTM (%)"]  = disp["Old YTM (%)"].round(3)
    disp["New YTM (%)"]  = disp["New YTM (%)"].round(3)
    disp["Old Price"]    = disp["Old Price"].round(2)
    disp["New Price"]    = disp["New Price"].round(2)
    disp["Old MV ($)"]   = disp["Old MV ($)"].round(0).astype(int)
    disp["New MV ($)"]   = disp["New MV ($)"].round(0).astype(int)
    disp["ΔMV ($)"]      = disp["ΔMV ($)"].round(0).astype(int)

    def _row_color(row):
        clr = "#d1fae5" if row["ΔMV ($)"] >= 0 else "#fee2e2"
        return [f"background-color:{clr}"] * len(row)

    st.dataframe(
        disp.style.apply(_row_color, axis=1),
        use_container_width=True, hide_index=True,
    )


# ── Main tab ───────────────────────────────────────────────────────────────────

def bond_portfolio() -> None:
    st.markdown(
        '<h2 style="color:#0f172a;margin:0 0 2px;">Bond Portfolio Builder</h2>'
        '<div style="font-size:12px;color:#475569;">'
        '30 sovereign bonds · $100k face per bond · check to add · qty = number of bonds</div>'
        '<hr style="border:none;border-top:1px solid #e2e8f0;margin:10px 0 6px;">',
        unsafe_allow_html=True,
    )

    # Sidebar country filter
    st.sidebar.markdown(
        f'<div style="font-size:10px;color:{_T2};text-transform:uppercase;'
        f'letter-spacing:.1em;margin:20px 0 6px;padding-bottom:4px;'
        f'border-bottom:1px solid {_EDGE};">Show Countries</div>',
        unsafe_allow_html=True,
    )
    all_countries = sorted({b["country"] for b in BOND_UNIVERSE})
    country_filter = st.sidebar.multiselect(
        "Countries", all_countries, default=all_countries,
        key="bp_country_filter", label_visibility="collapsed",
    )
    visible = [b for b in BOND_UNIVERSE if b["country"] in country_filter]

    # ── Single accordion: 4 maturity boxes in one row ─────────────────────────
    with st.expander("Bond Universe — select & size positions", expanded=True):
        cols = st.columns(4)
        for col, (blabel, bcolor, lo, hi) in zip(cols, BUCKETS):
            bucket_bonds = [b for b in visible if lo < b["maturity"] <= hi]
            with col:
                # Compact bucket header — coloured underline only
                st.markdown(
                    f'<div style="border-bottom:2px solid {bcolor};'
                    f'padding-bottom:4px;margin-bottom:8px;">'
                    f'<span style="font-size:14px;font-weight:700;color:{_T1};">'
                    f'{blabel}</span>'
                    f'<span style="font-size:10px;color:{_T2};margin-left:6px;">'
                    f'{len(bucket_bonds)} bonds</span></div>',
                    unsafe_allow_html=True,
                )
                if not bucket_bonds:
                    st.markdown(
                        f'<div style="color:{_T3};font-size:11px;">'
                        f'No bonds (adjust country filter)</div>',
                        unsafe_allow_html=True,
                    )
                for b in bucket_bonds:
                    _bond_row(b)

    # ── Collect selections ────────────────────────────────────────────────────
    selected = [b for b in BOND_UNIVERSE
                if st.session_state.get(f"chk_{b['id']}", False)]

    if not selected:
        st.info("Check one or more bonds above to build your portfolio.")
        return

    units: dict[str, int] = {
        b["id"]: st.session_state.get(f"units_{b['id']}", 1)
        for b in selected
    }

    # ── Portfolio computation ─────────────────────────────────────────────────
    rows = []
    for b in selected:
        m  = _metrics(b)
        u  = units[b["id"]]
        mv = m["price"] * u
        # Bucket label for this bond
        bucket = next(
            lbl for lbl, bcolor, lo, hi in BUCKETS
            if lo < b["maturity"] <= hi
        )
        rows.append(dict(
            id=b["id"], name=b["name"], country=b["country"],
            maturity=b["maturity"], bucket=bucket,
            ytm=b["ytm"] / 100, coupon=b["coupon"] / 100,
            price=m["price"], mac_dur=m["mac_dur"], mod_dur=m["mod_dur"],
            conv=m["conv"], dv01_u=m["dv01"],
            units=u, mv=mv,
        ))

    df = pd.DataFrame(rows)
    total_mv = df["mv"].sum()

    if total_mv == 0:
        st.warning("All quantities are zero — use + to add bonds.")
        return

    df["weight"]  = df["mv"] / total_mv
    port_ytm      = (df["ytm"]     * df["weight"]).sum()
    port_mac_dur  = (df["mac_dur"] * df["weight"]).sum()
    port_mod_dur  = (df["mod_dur"] * df["weight"]).sum()
    port_conv     = (df["conv"]    * df["weight"]).sum()
    port_dv01     = (df["dv01_u"]  * df["units"]).sum()
    n_bonds       = int(df["units"].sum())
    n_lines       = len(df)

    # ── Portfolio summary ─────────────────────────────────────────────────────
    _section(
        "Portfolio Summary",
        f"{n_lines} ISIN{'s' if n_lines != 1 else ''} · "
        f"{n_bonds} bonds · Total market value ${total_mv/1e6:.3f}M",
    )
    cards = [
        ("Total Market Value",  f"${total_mv/1e6:.3f}M",    f"{n_bonds} bonds × avg ${total_mv/n_bonds/1e3:.1f}k", _BLUE),
        ("Wtd Avg YTM",         f"{port_ytm*100:.3f}%",      "by market value",         _AMB),
        ("Macaulay Duration",   f"{port_mac_dur:.3f} yrs",   "avg cashflow timing",      _AMB),
        ("Modified Duration",   f"{port_mod_dur:.3f}",       "% Δpx / 1% Δyield",       _AMB),
        ("Convexity",           f"{port_conv:.3f}",          "portfolio avg",            _T2),
        ("Portfolio DV01",      f"${port_dv01:,.0f}",        "$ per 1bp move, total",    _GRN),
    ]
    html = '<div style="display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin-bottom:8px;">'
    for lbl, val, sub, acc in cards:
        html += _val_card(lbl, val, sub, acc)
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)

    # Rate shock table
    st.markdown(
        f'<div style="font-size:12px;color:{_T2};margin:16px 0 6px;">'
        f'Rate shock scenarios — portfolio ΔMV (duration + convexity approx.)</div>',
        unsafe_allow_html=True,
    )
    scen_rows = []
    for bp in [-200, -100, -50, -25, 25, 50, 100, 200]:
        dy  = bp / 10000
        dmv = sum(
            approx_price_change(r["mod_dur"], r["conv"], r["price"], dy) * r["units"]
            for _, r in df.iterrows()
        )
        scen_rows.append({
            "Shock (bps)": f"{bp:+d}",
            "ΔMV ($)":     f"${dmv:+,.0f}",
            "ΔMV (%)":     f"{dmv / total_mv * 100:+.3f}%",
        })

    def _colour(row):
        bp  = int(row["Shock (bps)"].replace("+", ""))
        clr = "#d1fae5" if bp < 0 else "#fee2e2"
        return [f"background-color:{clr}" for _ in row]

    st.dataframe(
        pd.DataFrame(scen_rows).style.apply(_colour, axis=1),
        use_container_width=True, hide_index=True,
    )

    # ── Analytics ─────────────────────────────────────────────────────────────
    _section("Portfolio Analytics")

    r1c1, r1c2 = st.columns(2)

    # Country allocation donut
    with r1c1:
        cmv = df.groupby("country")["mv"].sum().reset_index()
        fig = go.Figure(go.Pie(
            labels=cmv["country"], values=cmv["mv"], hole=0.55,
            marker_colors=[COUNTRY_COLORS.get(c, "#888") for c in cmv["country"]],
            textfont=dict(color=_T1, size=11),
            hovertemplate="%{label}<br>$%{value:,.0f} (%{percent})<extra></extra>",
        ))
        fig.update_layout(
            height=300,
            title=dict(text="Country Allocation", font=dict(size=13, color=_T1), x=0),
            **_chart_layout(margin=dict(l=20, r=20, t=40, b=20)),
        )
        st.plotly_chart(fig, use_container_width=True)

    # Maturity profile (market value)
    with r1c2:
        bucket_colors = [_BLUE, _AMB, _GRN, "#a78bfa"]
        bmv = [
            df[(df["maturity"] > lo) & (df["maturity"] <= hi)]["mv"].sum()
            for _, lo, hi in MAT_BUCKETS_CHART
        ]
        fig = go.Figure(go.Bar(
            x=[b[0] for b in MAT_BUCKETS_CHART], y=bmv,
            marker_color=bucket_colors,
            hovertemplate="%{x}<br>$%{y:,.0f}<extra></extra>",
        ))
        fig.update_layout(
            height=300,
            title=dict(text="Maturity Profile — Market Value",
                       font=dict(size=13, color=_T1), x=0),
            yaxis_title="Market Value ($)", showlegend=False,
            **_chart_layout(margin=dict(l=62, r=20, t=40, b=44)),
        )
        st.plotly_chart(fig, use_container_width=True)

    r2c1, r2c2 = st.columns(2)

    # DV01 by individual bond
    with r2c1:
        ddf = df.assign(dv01_total=df["dv01_u"] * df["units"]).sort_values("dv01_total")
        fig = go.Figure(go.Bar(
            y=ddf["name"], x=ddf["dv01_total"], orientation="h",
            marker_color=[COUNTRY_COLORS.get(c, "#888") for c in ddf["country"]],
            hovertemplate="%{y}<br>DV01: $%{x:,.0f}<extra></extra>",
        ))
        fig.update_layout(
            height=300,
            title=dict(text="DV01 by Bond",
                       font=dict(size=13, color=_T1), x=0),
            xaxis_title="DV01 ($)", showlegend=False,
            **_chart_layout(margin=dict(l=160, r=20, t=40, b=44)),
        )
        st.plotly_chart(fig, use_container_width=True)

    # DV01 by maturity bucket
    with r2c2:
        dv01_bucket = (
            df.assign(dv01_total=df["dv01_u"] * df["units"])
            .groupby("bucket")["dv01_total"]
            .sum()
            .reindex([b[0] for b in BUCKETS])
            .fillna(0)
            .reset_index()
        )
        fig = go.Figure(go.Bar(
            x=dv01_bucket["bucket"],
            y=dv01_bucket["dv01_total"],
            marker_color=bucket_colors,
            hovertemplate="%{x}<br>DV01: $%{y:,.0f}<extra></extra>",
        ))
        fig.update_layout(
            height=300,
            title=dict(text="DV01 by Maturity Bucket",
                       font=dict(size=13, color=_T1), x=0),
            xaxis_title="Maturity Bucket",
            yaxis_title="DV01 ($)",
            showlegend=False,
            **_chart_layout(margin=dict(l=62, r=20, t=40, b=44)),
        )
        st.plotly_chart(fig, use_container_width=True)

    # Yield positioning scatter (full width)
    fig = go.Figure()
    for country in df["country"].unique():
        cdf = df[df["country"] == country]
        max_mv = df["mv"].max()
        fig.add_trace(go.Scatter(
            x=cdf["maturity"], y=cdf["ytm"] * 100,
            mode="markers", name=country,
            marker=dict(
                color=COUNTRY_COLORS.get(country, "#888"),
                size=cdf["mv"] / max_mv * 30 + 8,
                opacity=0.85,
                line=dict(width=1.5, color=_BG),
            ),
            text=cdf["name"],
            hovertemplate=(
                "<b>%{text}</b><br>Maturity: %{x}Y<br>"
                "YTM: %{y:.2f}%<extra></extra>"
            ),
        ))
    fig.update_layout(
        height=300,
        title=dict(text="Yield Positioning — bubble size ∝ market value",
                   font=dict(size=13, color=_T1), x=0),
        xaxis_title="Maturity (years)", yaxis_title="YTM (%)",
        **_chart_layout(margin=dict(l=62, r=20, t=40, b=44)),
    )
    st.plotly_chart(fig, use_container_width=True)

    # ── Holdings table ────────────────────────────────────────────────────────
    _section("Holdings Summary")
    disp = df[["name", "country", "bucket", "coupon", "ytm",
               "price", "units", "mv", "weight", "mod_dur", "dv01_u"]].copy()
    disp.columns = ["Bond", "Country", "Bucket", "Coupon %", "YTM %",
                    "Price", "Qty", "Market Value ($)", "Weight", "Mod Dur", "DV01/bond"]
    disp["Coupon %"]        = (disp["Coupon %"] * 100).round(3)
    disp["YTM %"]           = (disp["YTM %"] * 100).round(3)
    disp["Price"]           = disp["Price"].round(2)
    disp["Market Value ($)"] = disp["Market Value ($)"].round(0).astype(int)
    disp["Weight"]          = (disp["Weight"] * 100).round(2).astype(str) + "%"
    disp["Mod Dur"]         = disp["Mod Dur"].round(3)
    disp["DV01/bond"]       = disp["DV01/bond"].round(0).astype(int)
    st.dataframe(disp, use_container_width=True, hide_index=True)

    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button(
        "⬇  Download Portfolio CSV", csv,
        file_name="bond_portfolio.csv", mime="text/csv",
    )

    # ── Yield shock scenario + impact analysis ────────────────────────────────
    portfolio_ids = {b["id"] for b in selected}
    _scenario_builder(portfolio_ids)
    _impact_analysis(df, total_mv)
