"""
Bond Portfolio Builder
Select from a universe of 30 sovereign bonds, size positions,
and analyse portfolio-level risk metrics and analytics.
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

# ── Bond universe (30 sovereign bonds) ────────────────────────────────────────
# ytm and coupon are % values; maturity in years; freq = coupon payments/year

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

MATURITY_BUCKETS = [
    ("0–2Y",   0,   2),
    ("2–5Y",   2,   5),
    ("5–10Y",  5,  10),
    ("10–30Y", 10, 30),
]


# ── Pure bond math helpers ─────────────────────────────────────────────────────

def _metrics(b: dict) -> dict:
    """Pre-compute all metrics for one bond at its reference YTM."""
    c = b["coupon"] / 100
    y = b["ytm"] / 100
    f, m, freq = b["face"], b["maturity"], b["freq"]
    px    = bond_price(f, c, m, y, freq)
    mac   = macaulay_duration(f, c, m, y, freq)
    mod   = modified_duration(f, c, m, y, freq)
    conv  = convexity(f, c, m, y, freq)
    dv01  = mod * px * 0.0001
    prem  = (px - f) / f * 100
    return dict(price=px, mac_dur=mac, mod_dur=mod, conv=conv, dv01=dv01,
                prem_disc=prem)


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
        f'<div style="background:{_CARD};border:1px solid {_EDGE};border-left:3px solid {accent};'
        f'border-radius:8px;padding:14px 12px;">'
        f'<div style="font-size:10px;color:{_T2};text-transform:uppercase;'
        f'letter-spacing:.1em;margin-bottom:5px;">{label}</div>'
        f'<div style="font-size:20px;font-weight:700;color:{_T1};">{value}</div>'
        f'{sub_html}</div>'
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

def bond_portfolio() -> None:
    st.markdown(
        '<h2 style="color:#0f172a;margin:0 0 2px;">Bond Portfolio Builder</h2>'
        '<div style="font-size:12px;color:#475569;">'
        '30 sovereign bonds · select, size positions, analyse portfolio risk</div>'
        '<hr style="border:none;border-top:1px solid #e2e8f0;margin:12px 0 8px;">',
        unsafe_allow_html=True,
    )

    # ── Sidebar ───────────────────────────────────────────────────────────────
    st.sidebar.markdown(
        f'<div style="font-size:10px;color:{_T2};text-transform:uppercase;'
        f'letter-spacing:.1em;margin:20px 0 8px;padding-bottom:6px;'
        f'border-bottom:1px solid {_EDGE};">Portfolio Filters</div>',
        unsafe_allow_html=True,
    )
    all_countries = sorted({b["country"] for b in BOND_UNIVERSE})
    country_filter = st.sidebar.multiselect(
        "Filter by country", all_countries, default=all_countries,
        key="bp_country_filter",
    )

    # ── Bond Selection ────────────────────────────────────────────────────────
    _section("Select Bonds", "Choose bonds from the universe; size each position below")
    filtered = [b for b in BOND_UNIVERSE if b["country"] in country_filter]
    bond_options = {b["id"]: f"{b['name']}  —  {b['coupon']:.3f}% coupon · {b['ytm']:.2f}% YTM"
                   for b in filtered}

    selected_ids: list[str] = st.multiselect(
        "Bonds",
        options=list(bond_options.keys()),
        format_func=lambda bid: bond_options[bid],
        default=[],
        key="bp_selected",
        label_visibility="collapsed",
    )

    if not selected_ids:
        st.info("Select one or more bonds above to build your portfolio.")
        return

    selected_bonds = [_BOND_BY_ID[bid] for bid in selected_ids]

    # ── Position sizing + individual detail accordions ─────────────────────────
    _section("Position Details", "Expand each bond to set units and view individual metrics")

    units: dict[str, int] = {}
    bond_calcs: dict[str, dict] = {}

    for b in selected_bonds:
        m = _metrics(b)
        bond_calcs[b["id"]] = m
        clr = COUNTRY_COLORS.get(b["country"], _T2)
        prem_label = "Premium" if m["prem_disc"] > 0.01 else "Discount" if m["prem_disc"] < -0.01 else "Par"
        accent_clr = _GRN if m["prem_disc"] >= 0 else _RED

        with st.expander(
            f"**{b['name']}**  ·  {b['country']}  ·  {b['coupon']:.3f}% coupon  ·  "
            f"YTM {b['ytm']:.2f}%  ·  Price ${m['price']:,.2f}",
            expanded=False,
        ):
            col_u, col_i = st.columns([1, 3])
            with col_u:
                u = st.number_input(
                    "Units (× face)",
                    min_value=0, max_value=100_000, value=100, step=10,
                    key=f"units_{b['id']}",
                    help=f"Each unit = ${b['face']:,.0f} face value",
                )
                units[b["id"]] = u
                mv = m["price"] * u
                st.markdown(
                    f'<div style="margin-top:8px;font-size:12px;color:{_T2};">'
                    f'Market value: <b style="color:{_T1}">${mv:,.2f}</b></div>',
                    unsafe_allow_html=True,
                )

            with col_i:
                cards_html = (
                    f'<div style="display:grid;grid-template-columns:repeat(3,1fr);gap:8px;">'
                    + _val_card("Price", f"${m['price']:,.4f}", prem_label, accent_clr)
                    + _val_card("Mac Duration", f"{m['mac_dur']:.3f} yrs", "Avg cashflow timing", _AMB)
                    + _val_card("Mod Duration", f"{m['mod_dur']:.3f}", "% Δprice / 1% Δyield", _AMB)
                    + _val_card("Convexity", f"{m['conv']:.3f}", "2nd-order sensitivity", _T2)
                    + _val_card("DV01 / unit", f"${m['dv01']:,.4f}", "$ per 1bp per unit", _GRN)
                    + _val_card("DV01 total", f"${m['dv01']*u:,.2f}", f"for {u} units", _GRN)
                    + '</div>'
                )
                st.markdown(cards_html, unsafe_allow_html=True)

            # Mini price-yield snippet
            ytm_c = b["ytm"] / 100
            y_range = [y / 10000 for y in range(
                max(1, int(ytm_c * 10000) - 200),
                int(ytm_c * 10000) + 201, 5
            )]
            px_curve = [
                bond_price(b["face"], b["coupon"] / 100, b["maturity"], y, b["freq"])
                for y in y_range
            ]
            fig_mini = go.Figure()
            fig_mini.add_trace(go.Scatter(
                x=[y * 100 for y in y_range], y=px_curve,
                line=dict(color=clr, width=2), showlegend=False,
                hovertemplate="YTM %{x:.2f}% → $%{y:,.2f}<extra></extra>",
            ))
            fig_mini.add_trace(go.Scatter(
                x=[b["ytm"]], y=[m["price"]],
                mode="markers", showlegend=False,
                marker=dict(color=_GRN, size=10, line=dict(width=2, color=_BG)),
                hovertemplate=f"Current: YTM {b['ytm']}% → ${m['price']:,.4f}<extra></extra>",
            ))
            fig_mini.update_layout(
                height=200,
                title=dict(text="Price–Yield", font=dict(size=11, color=_T2), x=0),
                xaxis_title="YTM (%)",
                yaxis_title="Price",
                **_layout(margin=dict(l=50, r=10, t=30, b=30)),
            )
            st.plotly_chart(fig_mini, use_container_width=True)

    # Ensure units populated for any bond with no expander interaction yet
    for b in selected_bonds:
        if b["id"] not in units:
            units[b["id"]] = st.session_state.get(f"units_{b['id']}", 100)

    # ── Portfolio computation ─────────────────────────────────────────────────
    rows = []
    for b in selected_bonds:
        m  = bond_calcs[b["id"]]
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
        st.warning("All positions are zero units — set units in the expanders above.")
        return

    df["weight"] = df["mv"] / total_mv
    port_ytm     = (df["ytm"]     * df["weight"]).sum()
    port_mac_dur = (df["mac_dur"] * df["weight"]).sum()
    port_mod_dur = (df["mod_dur"] * df["weight"]).sum()
    port_conv    = (df["conv"]    * df["weight"]).sum()
    port_dv01    = (df["dv01_u"]  * df["units"]).sum()
    n_bonds      = len(df)

    # ── Portfolio summary ─────────────────────────────────────────────────────
    _section(
        "Portfolio Summary",
        f"{n_bonds} bond{'s' if n_bonds != 1 else ''} · "
        f"Total market value ${total_mv:,.2f}",
    )
    summary_cards = [
        ("Total Market Value", f"${total_mv:,.2f}", "",            _BLUE),
        ("Wtd Avg YTM",        f"{port_ytm*100:.3f}%", "by market value", _AMB),
        ("Macaulay Duration",  f"{port_mac_dur:.3f} yrs", "portfolio avg", _AMB),
        ("Modified Duration",  f"{port_mod_dur:.3f}", "% Δpx / 1% Δyield", _AMB),
        ("Convexity",          f"{port_conv:.3f}", "portfolio avg",  _T2),
        ("Portfolio DV01",     f"${port_dv01:,.2f}", "$ per 1bp move total", _GRN),
    ]
    html = '<div style="display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin-bottom:8px;">'
    for lbl, val, sub, acc in summary_cards:
        html += _val_card(lbl, val, sub, acc)
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)

    # Scenario P&L
    st.markdown(
        f'<div style="font-size:12px;color:{_T2};margin:16px 0 6px;">'
        f'Rate shock scenarios (portfolio-level ΔMV)</div>',
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
    scen_df = pd.DataFrame(scen_rows)
    def _colour(row):
        bp = int(row["Shock (bps)"].replace("+", ""))
        c = "#d1fae5" if bp < 0 else "#fee2e2" if bp > 0 else ""
        return [f"background-color:{c}" if c else "" for _ in row]
    st.dataframe(scen_df.style.apply(_colour, axis=1),
                 use_container_width=True, hide_index=True)

    # ── Analytics ─────────────────────────────────────────────────────────────
    _section("Portfolio Analytics")

    row1_c1, row1_c2 = st.columns(2)

    # 1. Country allocation donut
    with row1_c1:
        country_mv = df.groupby("country")["mv"].sum().reset_index()
        fig_pie = go.Figure(go.Pie(
            labels=country_mv["country"],
            values=country_mv["mv"],
            hole=0.55,
            marker_colors=[COUNTRY_COLORS.get(c, "#888") for c in country_mv["country"]],
            textfont=dict(color=_T1, size=11),
            hovertemplate="%{label}<br>$%{value:,.2f} (%{percent})<extra></extra>",
        ))
        fig_pie.update_layout(
            height=320,
            title=dict(text="Country Allocation", font=dict(size=13, color=_T1), x=0),
            **_layout(margin=dict(l=20, r=20, t=44, b=20),
                      legend=dict(font=dict(size=10, color=_T1), bgcolor="rgba(0,0,0,0)")),
        )
        st.plotly_chart(fig_pie, use_container_width=True)

    # 2. Maturity profile
    with row1_c2:
        bucket_labels = [b[0] for b in MATURITY_BUCKETS]
        bucket_mv = []
        for lbl, lo, hi in MATURITY_BUCKETS:
            mv_sum = df[(df["maturity"] > lo) & (df["maturity"] <= hi)]["mv"].sum()
            bucket_mv.append(mv_sum)
        fig_mat = go.Figure(go.Bar(
            x=bucket_labels, y=bucket_mv,
            marker_color=[_BLUE, _AMB, _GRN, _RED],
            hovertemplate="%{x}<br>$%{y:,.2f}<extra></extra>",
        ))
        fig_mat.update_layout(
            height=320,
            title=dict(text="Maturity Profile (Market Value)", font=dict(size=13, color=_T1), x=0),
            yaxis_title="Market Value ($)",
            showlegend=False,
            **_layout(legend=dict(visible=False), margin=dict(l=62, r=20, t=44, b=44)),
        )
        st.plotly_chart(fig_mat, use_container_width=True)

    row2_c1, row2_c2 = st.columns(2)

    # 3. DV01 contribution by bond
    with row2_c1:
        df_dv = df.assign(dv01_total=df["dv01_u"] * df["units"]).sort_values("dv01_total")
        fig_dv = go.Figure(go.Bar(
            y=df_dv["name"],
            x=df_dv["dv01_total"],
            orientation="h",
            marker_color=[COUNTRY_COLORS.get(c, "#888") for c in df_dv["country"]],
            hovertemplate="%{y}<br>DV01: $%{x:,.2f}<extra></extra>",
        ))
        fig_dv.update_layout(
            height=320,
            title=dict(text="DV01 Contribution by Bond", font=dict(size=13, color=_T1), x=0),
            xaxis_title="DV01 ($)",
            showlegend=False,
            **_layout(legend=dict(visible=False),
                      margin=dict(l=160, r=20, t=44, b=44)),
        )
        st.plotly_chart(fig_dv, use_container_width=True)

    # 4. Yield positioning scatter (maturity vs YTM, bubble = market value)
    with row2_c2:
        fig_yc = go.Figure()
        for country in df["country"].unique():
            cdf = df[df["country"] == country]
            fig_yc.add_trace(go.Scatter(
                x=cdf["maturity"],
                y=cdf["ytm"] * 100,
                mode="markers",
                name=country,
                marker=dict(
                    color=COUNTRY_COLORS.get(country, "#888"),
                    size=cdf["mv"] / cdf["mv"].max() * 30 + 8,
                    opacity=0.85,
                    line=dict(width=1.5, color=_BG),
                ),
                text=cdf["name"],
                hovertemplate=(
                    "<b>%{text}</b><br>"
                    "Maturity: %{x}Y<br>"
                    "YTM: %{y:.2f}%<extra></extra>"
                ),
            ))
        fig_yc.update_layout(
            height=320,
            title=dict(text="Yield Positioning (bubble ∝ market value)",
                       font=dict(size=13, color=_T1), x=0),
            xaxis_title="Maturity (years)",
            yaxis_title="YTM (%)",
            **_layout(margin=dict(l=62, r=20, t=44, b=44)),
        )
        st.plotly_chart(fig_yc, use_container_width=True)

    # ── Holdings table ────────────────────────────────────────────────────────
    _section("Holdings Summary")
    display_df = df[[
        "name", "country", "coupon", "maturity", "ytm",
        "price", "units", "mv", "weight", "mod_dur", "dv01_u",
    ]].copy()
    display_df.columns = [
        "Bond", "Country", "Coupon %", "Maturity (Y)", "YTM %",
        "Price", "Units", "Market Value", "Weight", "Mod Dur", "DV01/unit",
    ]
    display_df["Coupon %"]    = (display_df["Coupon %"] * 100).round(3)
    display_df["YTM %"]       = (display_df["YTM %"] * 100).round(3)
    display_df["Price"]       = display_df["Price"].round(4)
    display_df["Market Value"] = display_df["Market Value"].round(2)
    display_df["Weight"]      = (display_df["Weight"] * 100).round(2).astype(str) + "%"
    display_df["Mod Dur"]     = display_df["Mod Dur"].round(3)
    display_df["DV01/unit"]   = display_df["DV01/unit"].round(4)
    st.dataframe(display_df, use_container_width=True, hide_index=True)

    # Download
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button(
        "⬇  Download Portfolio CSV", csv,
        file_name="bond_portfolio.csv", mime="text/csv",
    )
