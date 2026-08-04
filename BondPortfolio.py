"""
Bond Portfolio Builder
One accordion, four maturity buckets in a row, check/uncheck + size per bond.
"""
from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from BondCalculator import (
    approx_price_change, bond_price,
    convexity, macaulay_duration, modified_duration,
)

# ── Colour palette ─────────────────────────────────────────────────────────────

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

# ── Maturity buckets ──────────────────────────────────────────────────────────
# (label, accent-colour, lo-exclusive, hi-inclusive)
BUCKETS = [
    ("2Y",  _BLUE,   0.0,  2.5),
    ("5Y",  _AMB,    2.5,  7.0),
    ("10Y", _GRN,    7.0, 15.0),
    ("30Y", "#a78bfa", 15.0, 50.0),
]

# ── Bond universe (30 sovereign bonds) ────────────────────────────────────────

BOND_UNIVERSE: list[dict] = [
    # USA — semi-annual
    dict(id="US-2Y",  name="US Treasury 2Y",      country="USA",            coupon=4.625, maturity=2,  ytm=4.25, face=1000, freq=2),
    dict(id="US-5Y",  name="US Treasury 5Y",      country="USA",            coupon=4.250, maturity=5,  ytm=4.10, face=1000, freq=2),
    dict(id="US-10Y", name="US Treasury 10Y",     country="USA",            coupon=4.250, maturity=10, ytm=4.20, face=1000, freq=2),
    dict(id="US-30Y", name="US Treasury 30Y",     country="USA",            coupon=4.625, maturity=30, ytm=4.50, face=1000, freq=2),
    # Germany — annual
    dict(id="DE-2Y",  name="German Bund 2Y",      country="Germany",        coupon=2.500, maturity=2,  ytm=2.40, face=1000, freq=1),
    dict(id="DE-5Y",  name="German Bund 5Y",      country="Germany",        coupon=2.250, maturity=5,  ytm=2.35, face=1000, freq=1),
    dict(id="DE-10Y", name="German Bund 10Y",     country="Germany",        coupon=2.600, maturity=10, ytm=2.65, face=1000, freq=1),
    dict(id="DE-30Y", name="German Bund 30Y",     country="Germany",        coupon=2.700, maturity=30, ytm=2.90, face=1000, freq=1),
    # United Kingdom — semi-annual
    dict(id="UK-2Y",  name="UK Gilt 2Y",          country="United Kingdom", coupon=4.750, maturity=2,  ytm=4.35, face=1000, freq=2),
    dict(id="UK-10Y", name="UK Gilt 10Y",         country="United Kingdom", coupon=4.250, maturity=10, ytm=4.45, face=1000, freq=2),
    dict(id="UK-30Y", name="UK Gilt 30Y",         country="United Kingdom", coupon=4.125, maturity=30, ytm=4.70, face=1000, freq=2),
    # Japan — semi-annual
    dict(id="JP-2Y",  name="Japan JGB 2Y",        country="Japan",          coupon=0.600, maturity=2,  ytm=0.65, face=1000, freq=2),
    dict(id="JP-10Y", name="Japan JGB 10Y",       country="Japan",          coupon=1.100, maturity=10, ytm=1.00, face=1000, freq=2),
    dict(id="JP-30Y", name="Japan JGB 30Y",       country="Japan",          coupon=1.800, maturity=30, ytm=2.00, face=1000, freq=2),
    # France — annual
    dict(id="FR-5Y",  name="France OAT 5Y",       country="France",         coupon=2.750, maturity=5,  ytm=3.00, face=1000, freq=1),
    dict(id="FR-10Y", name="France OAT 10Y",      country="France",         coupon=3.000, maturity=10, ytm=3.45, face=1000, freq=1),
    # Italy — semi-annual
    dict(id="IT-3Y",  name="Italy BTP 3Y",        country="Italy",          coupon=3.500, maturity=3,  ytm=3.40, face=1000, freq=2),
    dict(id="IT-10Y", name="Italy BTP 10Y",       country="Italy",          coupon=4.000, maturity=10, ytm=3.70, face=1000, freq=2),
    dict(id="IT-30Y", name="Italy BTP 30Y",       country="Italy",          coupon=4.500, maturity=30, ytm=4.20, face=1000, freq=2),
    # Canada — semi-annual
    dict(id="CA-2Y",  name="Canada GoC 2Y",       country="Canada",         coupon=3.750, maturity=2,  ytm=3.05, face=1000, freq=2),
    dict(id="CA-10Y", name="Canada GoC 10Y",      country="Canada",         coupon=3.250, maturity=10, ytm=3.10, face=1000, freq=2),
    # Australia — semi-annual
    dict(id="AU-3Y",  name="Australia ACGB 3Y",   country="Australia",      coupon=3.750, maturity=3,  ytm=3.85, face=1000, freq=2),
    dict(id="AU-10Y", name="Australia ACGB 10Y",  country="Australia",      coupon=4.250, maturity=10, ytm=4.30, face=1000, freq=2),
    # India — semi-annual
    dict(id="IN-5Y",  name="India G-Sec 5Y",      country="India",          coupon=7.000, maturity=5,  ytm=6.85, face=1000, freq=2),
    dict(id="IN-10Y", name="India G-Sec 10Y",     country="India",          coupon=7.180, maturity=10, ytm=6.95, face=1000, freq=2),
    # Brazil — semi-annual
    dict(id="BR-2Y",  name="Brazil NTN-F 2Y",     country="Brazil",         coupon=10.00, maturity=2,  ytm=12.00, face=1000, freq=2),
    dict(id="BR-5Y",  name="Brazil NTN-F 5Y",     country="Brazil",         coupon=10.00, maturity=5,  ytm=12.50, face=1000, freq=2),
    dict(id="BR-10Y", name="Brazil NTN-F 10Y",    country="Brazil",         coupon=10.00, maturity=10, ytm=12.90, face=1000, freq=2),
    # China — semi-annual
    dict(id="CN-5Y",  name="China CGB 5Y",        country="China",          coupon=2.200, maturity=5,  ytm=2.00, face=1000, freq=2),
    dict(id="CN-10Y", name="China CGB 10Y",       country="China",          coupon=2.400, maturity=10, ytm=2.20, face=1000, freq=2),
]

_BOND_BY_ID: dict[str, dict] = {b["id"]: b for b in BOND_UNIVERSE}

MATURITY_BUCKETS_CHART = [
    ("0–2Y",   0,   2),
    ("2–5Y",   2,   5),
    ("5–10Y",  5,  10),
    ("10–30Y", 10, 30),
]


# ── Pure bond math ─────────────────────────────────────────────────────────────

def _metrics(b: dict) -> dict:
    c, y, f, m, freq = b["coupon"] / 100, b["ytm"] / 100, b["face"], b["maturity"], b["freq"]
    px   = bond_price(f, c, m, y, freq)
    mac  = macaulay_duration(f, c, m, y, freq)
    mod  = modified_duration(f, c, m, y, freq)
    conv = convexity(f, c, m, y, freq)
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
        f'padding:12px 16px;margin:28px 0 10px;border-radius:0 8px 8px 0;">'
        f'<span style="font-size:13px;font-weight:700;color:{_T1};'
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
        f'border-left:3px solid {accent};border-radius:8px;padding:14px 12px;">'
        f'<div style="font-size:10px;color:{_T2};text-transform:uppercase;'
        f'letter-spacing:.1em;margin-bottom:5px;">{label}</div>'
        f'<div style="font-size:20px;font-weight:700;color:{_T1};">{value}</div>'
        f'{sub_html}</div>'
    )


def _layout(**kw) -> dict:
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
        legend=dict(font=dict(color=_T1), bgcolor="rgba(0,0,0,0)"),
    )
    base.update(kw)
    return base


# ── Bond item inside a bucket column ──────────────────────────────────────────

def _bond_item(b: dict) -> None:
    """Render one bond row: checkbox + (if ticked) units stepper."""
    clr   = COUNTRY_COLORS.get(b["country"], _T2)
    label = (
        f':{b["country"]}  '
        f'<span style="color:{_T2};font-size:11px;">'
        f'{b["coupon"]:.3f}%  ·  YTM {b["ytm"]:.2f}%</span>'
    )
    checked = st.checkbox(
        b["country"],
        key=f"chk_{b['id']}",
        help=f"{b['name']}  |  coupon {b['coupon']:.3f}%  |  YTM {b['ytm']:.2f}%  |  {b['freq']}× p.a.",
    )
    if checked:
        # Compact +/- stepper via session_state buttons
        unit_key = f"units_{b['id']}"
        if unit_key not in st.session_state:
            st.session_state[unit_key] = 100

        c_minus, c_val, c_plus = st.columns([1, 2, 1])
        with c_minus:
            if st.button("−", key=f"dec_{b['id']}",
                         help="−10 units", use_container_width=True):
                st.session_state[unit_key] = max(10, st.session_state[unit_key] - 10)
        with c_val:
            st.markdown(
                f'<div style="text-align:center;background:{_BG};border:1px solid {_EDGE};'
                f'border-radius:4px;padding:4px 0;font-weight:700;font-size:13px;'
                f'color:{_T1};line-height:32px;">'
                f'{st.session_state[unit_key]}</div>',
                unsafe_allow_html=True,
            )
        with c_plus:
            if st.button("+", key=f"inc_{b['id']}",
                         help="+10 units", use_container_width=True):
                st.session_state[unit_key] += 10

        # Show live position value
        m  = _metrics(b)
        mv = m["price"] * st.session_state[unit_key]
        st.markdown(
            f'<div style="font-size:10px;color:{_T3};text-align:center;'
            f'margin-bottom:6px;">${mv:,.0f}</div>',
            unsafe_allow_html=True,
        )

    # Thin divider between bonds
    st.markdown(
        f'<hr style="border:none;border-top:1px solid {_EDGE};margin:4px 0;">',
        unsafe_allow_html=True,
    )


# ── Main tab ───────────────────────────────────────────────────────────────────

def bond_portfolio() -> None:
    st.markdown(
        '<h2 style="color:#0f172a;margin:0 0 2px;">Bond Portfolio Builder</h2>'
        '<div style="font-size:12px;color:#475569;">'
        '30 sovereign bonds · check to add · +/− to size · metrics update live</div>'
        '<hr style="border:none;border-top:1px solid #e2e8f0;margin:12px 0 8px;">',
        unsafe_allow_html=True,
    )

    # ── Sidebar country filter ────────────────────────────────────────────────
    st.sidebar.markdown(
        f'<div style="font-size:10px;color:{_T2};text-transform:uppercase;'
        f'letter-spacing:.1em;margin:20px 0 8px;padding-bottom:6px;'
        f'border-bottom:1px solid {_EDGE};">Show Countries</div>',
        unsafe_allow_html=True,
    )
    all_countries = sorted({b["country"] for b in BOND_UNIVERSE})
    country_filter = st.sidebar.multiselect(
        "Countries", all_countries, default=all_countries, key="bp_country_filter",
        label_visibility="collapsed",
    )
    visible = [b for b in BOND_UNIVERSE if b["country"] in country_filter]

    # ── Single accordion: 4 maturity boxes in one row ─────────────────────────
    with st.expander("Bond Universe — check bonds to add, use +/− to size positions",
                     expanded=True):

        bucket_cols = st.columns(4)

        for col, (blabel, bcolor, lo, hi) in zip(bucket_cols, BUCKETS):
            bonds_in_bucket = [b for b in visible if lo < b["maturity"] <= hi]
            with col:
                # Bucket header card
                st.markdown(
                    f'<div style="background:{_BG};border-top:3px solid {bcolor};'
                    f'border-radius:6px 6px 0 0;padding:8px 0;text-align:center;'
                    f'margin-bottom:10px;">'
                    f'<span style="font-size:18px;font-weight:800;color:{_T1};">'
                    f'{blabel}</span>'
                    f'<span style="font-size:10px;color:{_T2};display:block;'
                    f'margin-top:1px;">{len(bonds_in_bucket)} bonds</span></div>',
                    unsafe_allow_html=True,
                )
                if not bonds_in_bucket:
                    st.markdown(
                        f'<div style="color:{_T3};font-size:11px;text-align:center;">'
                        f'No bonds visible<br>(adjust country filter)</div>',
                        unsafe_allow_html=True,
                    )
                else:
                    for b in bonds_in_bucket:
                        _bond_item(b)

    # ── Collect selected bonds from session_state ─────────────────────────────
    selected_bonds = [b for b in BOND_UNIVERSE
                      if st.session_state.get(f"chk_{b['id']}", False)]

    if not selected_bonds:
        st.info("Check one or more bonds above to build your portfolio.")
        return

    units: dict[str, int] = {
        b["id"]: st.session_state.get(f"units_{b['id']}", 100)
        for b in selected_bonds
    }

    # ── Portfolio computation ─────────────────────────────────────────────────
    rows = []
    for b in selected_bonds:
        m  = _metrics(b)
        u  = units[b["id"]]
        mv = m["price"] * u
        rows.append({
            "id":       b["id"],
            "name":     b["name"],
            "country":  b["country"],
            "maturity": b["maturity"],
            "ytm":      b["ytm"] / 100,
            "coupon":   b["coupon"] / 100,
            "price":    m["price"],
            "mac_dur":  m["mac_dur"],
            "mod_dur":  m["mod_dur"],
            "conv":     m["conv"],
            "dv01_u":   m["dv01"],
            "units":    u,
            "mv":       mv,
        })

    df = pd.DataFrame(rows)
    total_mv = df["mv"].sum()

    if total_mv == 0:
        st.warning("All positions are zero — use + to add units.")
        return

    df["weight"]    = df["mv"] / total_mv
    port_ytm        = (df["ytm"]     * df["weight"]).sum()
    port_mac_dur    = (df["mac_dur"] * df["weight"]).sum()
    port_mod_dur    = (df["mod_dur"] * df["weight"]).sum()
    port_conv       = (df["conv"]    * df["weight"]).sum()
    port_dv01       = (df["dv01_u"]  * df["units"]).sum()
    n_bonds         = len(df)

    # ── Portfolio summary ─────────────────────────────────────────────────────
    _section(
        "Portfolio Summary",
        f"{n_bonds} bond{'s' if n_bonds != 1 else ''} · "
        f"Total market value ${total_mv:,.2f}",
    )
    cards = [
        ("Total Market Value", f"${total_mv:,.2f}",   "",                   _BLUE),
        ("Wtd Avg YTM",        f"{port_ytm*100:.3f}%", "by market value",   _AMB),
        ("Macaulay Duration",  f"{port_mac_dur:.3f} yrs", "avg cashflow timing", _AMB),
        ("Modified Duration",  f"{port_mod_dur:.3f}",  "% Δpx / 1% Δyield", _AMB),
        ("Convexity",          f"{port_conv:.3f}",     "portfolio avg",      _T2),
        ("Portfolio DV01",     f"${port_dv01:,.2f}",   "$ per 1bp total",   _GRN),
    ]
    html = '<div style="display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin-bottom:8px;">'
    for lbl, val, sub, acc in cards:
        html += _val_card(lbl, val, sub, acc)
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)

    # Rate shock scenarios
    st.markdown(
        f'<div style="font-size:12px;color:{_T2};margin:18px 0 6px;">'
        f'Rate shock scenarios — portfolio ΔMV (duration + convexity approx.)</div>',
        unsafe_allow_html=True,
    )
    shocks = [-200, -100, -50, -25, 25, 50, 100, 200]
    scen_rows = []
    for bp in shocks:
        dy  = bp / 10000
        dmv = sum(
            approx_price_change(r["mod_dur"], r["conv"], r["price"], dy) * r["units"]
            for _, r in df.iterrows()
        )
        scen_rows.append({
            "Shock (bps)": f"{bp:+d}",
            "ΔMV ($)":     f"${dmv:+,.2f}",
            "ΔMV (%)":     f"{dmv / total_mv * 100:+.3f}%",
        })

    def _colour(row):
        bp  = int(row["Shock (bps)"].replace("+", ""))
        col = "#d1fae5" if bp < 0 else "#fee2e2"
        return [f"background-color:{col}" for _ in row]

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
            hovertemplate="%{label}<br>$%{value:,.2f} (%{percent})<extra></extra>",
        ))
        fig.update_layout(
            height=320,
            title=dict(text="Country Allocation", font=dict(size=13, color=_T1), x=0),
            **_layout(margin=dict(l=20, r=20, t=44, b=20)),
        )
        st.plotly_chart(fig, use_container_width=True)

    # Maturity profile
    with r1c2:
        lbls  = [b[0] for b in MATURITY_BUCKETS_CHART]
        bmv   = [
            df[(df["maturity"] > lo) & (df["maturity"] <= hi)]["mv"].sum()
            for _, lo, hi in MATURITY_BUCKETS_CHART
        ]
        fig = go.Figure(go.Bar(
            x=lbls, y=bmv,
            marker_color=[_BLUE, _AMB, _GRN, "#a78bfa"],
            hovertemplate="%{x}<br>$%{y:,.2f}<extra></extra>",
        ))
        fig.update_layout(
            height=320,
            title=dict(text="Maturity Profile (Market Value)",
                       font=dict(size=13, color=_T1), x=0),
            yaxis_title="Market Value ($)", showlegend=False,
            **_layout(margin=dict(l=62, r=20, t=44, b=44)),
        )
        st.plotly_chart(fig, use_container_width=True)

    r2c1, r2c2 = st.columns(2)

    # DV01 contribution
    with r2c1:
        ddf = df.assign(dv01_total=df["dv01_u"] * df["units"]).sort_values("dv01_total")
        fig = go.Figure(go.Bar(
            y=ddf["name"], x=ddf["dv01_total"], orientation="h",
            marker_color=[COUNTRY_COLORS.get(c, "#888") for c in ddf["country"]],
            hovertemplate="%{y}<br>DV01: $%{x:,.2f}<extra></extra>",
        ))
        fig.update_layout(
            height=320,
            title=dict(text="DV01 Contribution by Bond",
                       font=dict(size=13, color=_T1), x=0),
            xaxis_title="DV01 ($)", showlegend=False,
            **_layout(margin=dict(l=160, r=20, t=44, b=44)),
        )
        st.plotly_chart(fig, use_container_width=True)

    # Yield positioning scatter
    with r2c2:
        fig = go.Figure()
        for country in df["country"].unique():
            cdf = df[df["country"] == country]
            fig.add_trace(go.Scatter(
                x=cdf["maturity"], y=cdf["ytm"] * 100,
                mode="markers", name=country,
                marker=dict(
                    color=COUNTRY_COLORS.get(country, "#888"),
                    size=cdf["mv"] / cdf["mv"].max() * 30 + 8,
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
            height=320,
            title=dict(text="Yield Positioning (bubble ∝ market value)",
                       font=dict(size=13, color=_T1), x=0),
            xaxis_title="Maturity (years)", yaxis_title="YTM (%)",
            **_layout(margin=dict(l=62, r=20, t=44, b=44)),
        )
        st.plotly_chart(fig, use_container_width=True)

    # ── Holdings table ────────────────────────────────────────────────────────
    _section("Holdings Summary")
    disp = df[[
        "name", "country", "coupon", "maturity", "ytm",
        "price", "units", "mv", "weight", "mod_dur", "dv01_u",
    ]].copy()
    disp.columns = [
        "Bond", "Country", "Coupon %", "Maturity (Y)", "YTM %",
        "Price", "Units", "Market Value", "Weight", "Mod Dur", "DV01/unit",
    ]
    disp["Coupon %"]     = (disp["Coupon %"] * 100).round(3)
    disp["YTM %"]        = (disp["YTM %"] * 100).round(3)
    disp["Price"]        = disp["Price"].round(4)
    disp["Market Value"] = disp["Market Value"].round(2)
    disp["Weight"]       = (disp["Weight"] * 100).round(2).astype(str) + "%"
    disp["Mod Dur"]      = disp["Mod Dur"].round(3)
    disp["DV01/unit"]    = disp["DV01/unit"].round(4)
    st.dataframe(disp, use_container_width=True, hide_index=True)

    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button(
        "⬇  Download Portfolio CSV", csv,
        file_name="bond_portfolio.csv", mime="text/csv",
    )
