"""
Bond Investment Strategies  ·  Ladder · Bullet · Barbell
Build, compare and stress-test the three classic fixed-income portfolio strategies.
"""
from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from BondCalculator import (
    approx_price_change, bond_price,
    convexity, macaulay_duration, modified_duration,
)
from BondPortfolio import (
    BOND_UNIVERSE, BUCKETS,
    _scenario_builder, _impact_analysis,
)

# ── Palette ───────────────────────────────────────────────────────────────────
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
FACE  = 100_000

COUNTRY_COLORS = {
    "USA": "#60a5fa", "Germany": "#a78bfa", "United Kingdom": "#22d3ee",
    "Japan": "#34d399", "France": "#fbbf24", "Italy": "#fb923c",
    "Canada": "#818cf8", "Australia": "#f472b6",
    "India": "#f87171", "Brazil": "#a3e635", "China": "#e879f9",
}

_BOND_BY_ID = {b["id"]: b for b in BOND_UNIVERSE}

# ── Strategy metadata ─────────────────────────────────────────────────────────
_STRAT = {
    "Ladder": {
        "emoji": "🪜", "color": _BLUE,
        "tagline": "Equal allocation spread evenly across short, medium and long maturities.",
        "use_when": "Steady income · no strong rate view · want to reduce reinvestment risk",
        "mechanics": (
            "As each rung matures, proceeds roll into the long end — keeping the ladder intact. "
            "No single maturity dominates, so you're never fully exposed to one point on the curve."
        ),
        "watch": "Lower convexity than Barbell. Won't outperform in sharp rate moves.",
    },
    "Bullet": {
        "emoji": "🎯", "color": _AMB,
        "tagline": "All bonds concentrated around a single target maturity date.",
        "use_when": "Known future liability · pension payment · project funding in N years",
        "mechanics": (
            "All bonds mature near the same date, matching a specific obligation. "
            "Immunises price risk for that horizon — but coupons face high reinvestment risk."
        ),
        "watch": "Lowest convexity of the three. Underperforms in volatile rate environments.",
    },
    "Barbell": {
        "emoji": "🏋️", "color": _GRN,
        "tagline": "Short-end + long-end only — avoid the belly of the curve.",
        "use_when": "Rate volatility expected · curve flattener/steepener bet · maximise convexity",
        "mechanics": (
            "Short bonds provide liquidity; long bonds provide yield. Together they produce higher "
            "convexity than a Bullet of equal duration — so the portfolio benefits more from large "
            "rate moves in either direction."
        ),
        "watch": "Underperforms Bullet when the curve stays flat and volatility is low.",
    },
}


# ── Bond math ─────────────────────────────────────────────────────────────────

def _metrics(b: dict) -> dict:
    c, y = b["coupon"] / 100, b["ytm"] / 100
    px   = bond_price(b["face"], c, b["maturity"], y, b["freq"])
    mac  = macaulay_duration(b["face"], c, b["maturity"], y, b["freq"])
    mod  = modified_duration(b["face"], c, b["maturity"], y, b["freq"])
    cnv  = convexity(b["face"], c, b["maturity"], y, b["freq"])
    dv01 = mod * px * 0.0001
    return dict(price=px, mac_dur=mac, mod_dur=mod, conv=cnv, dv01=dv01)


def _cash_flows(positions: list[tuple[dict, int]]) -> pd.DataFrame:
    coupon_cf: dict[float, float]    = {}
    principal_cf: dict[float, float] = {}
    for b, qty in positions:
        cpn_per_period = b["coupon"] / 100 * b["face"] / b["freq"] * qty
        n = int(b["maturity"] * b["freq"])
        for p in range(1, n + 1):
            yr = round(p / b["freq"], 2)
            coupon_cf[yr] = coupon_cf.get(yr, 0) + cpn_per_period
        mat = float(b["maturity"])
        principal_cf[mat] = principal_cf.get(mat, 0) + b["face"] * qty
    all_yrs = sorted(set(coupon_cf) | set(principal_cf))
    rows = []
    for yr in all_yrs:
        princ = principal_cf.get(yr, 0)
        cpn   = coupon_cf.get(yr, 0) - princ   # coupon already includes principal at maturity
        rows.append({"year": yr, "coupon": cpn, "principal": princ})
    return pd.DataFrame(rows)


def _compute_portfolio(bond_ids: dict[str, int]) -> tuple[pd.DataFrame, dict]:
    rows = []
    for bid, qty in bond_ids.items():
        b = _BOND_BY_ID.get(bid)
        if b is None or qty == 0:
            continue
        m  = _metrics(b)
        mv = m["price"] * qty
        rows.append(dict(
            id=bid, name=b["name"], country=b["country"],
            maturity=b["maturity"], coupon=b["coupon"], ytm=b["ytm"],
            price=m["price"], mac_dur=m["mac_dur"], mod_dur=m["mod_dur"],
            conv=m["conv"], dv01=m["dv01"], qty=qty, mv=mv,
        ))
    if not rows:
        return pd.DataFrame(), {}
    df = pd.DataFrame(rows)
    total_mv = df["mv"].sum()
    df["weight"] = df["mv"] / total_mv
    port = dict(
        total_mv=total_mv,
        ytm=(df["ytm"]     * df["weight"]).sum(),
        mac_dur=(df["mac_dur"] * df["weight"]).sum(),
        mod_dur=(df["mod_dur"] * df["weight"]).sum(),
        conv=(df["conv"]   * df["weight"]).sum(),
        dv01=(df["dv01"]   * df["qty"]).sum(),
        avg_mat=(df["maturity"] * df["weight"]).sum(),
        n_bonds=int(df["qty"].sum()),
        n_isins=len(df),
    )
    return df, port


# ── Auto-build ────────────────────────────────────────────────────────────────

def _auto_ladder(investment: float, countries: list[str]) -> dict[str, int]:
    buckets = [(0, 2.5), (2.5, 7.0), (7.0, 15.0), (15.0, 50.0)]
    alloc   = investment / len(buckets)
    result  = {}
    for lo, hi in buckets:
        cands = [b for b in BOND_UNIVERSE if lo < b["maturity"] <= hi and b["country"] in countries]
        if not cands:
            continue
        b   = next((x for x in cands if x["country"] == "USA"), cands[0])
        qty = max(1, round(alloc / _metrics(b)["price"]))
        result[b["id"]] = qty
    return result


def _auto_bullet(investment: float, countries: list[str], target: float) -> dict[str, int]:
    if   target <= 2.5:  lo, hi = 0,    2.5
    elif target <= 7.0:  lo, hi = 2.5,  7.0
    elif target <= 15.0: lo, hi = 7.0,  15.0
    else:                lo, hi = 15.0, 50.0
    cands = [b for b in BOND_UNIVERSE if lo < b["maturity"] <= hi and b["country"] in countries]
    if not cands:
        return {}
    cands.sort(key=lambda b: (abs(b["maturity"] - target), b["country"] != "USA"))
    chosen  = cands[:min(3, len(cands))]
    per_bond = investment / len(chosen)
    return {b["id"]: max(1, round(per_bond / _metrics(b)["price"])) for b in chosen}


def _auto_barbell(investment: float, countries: list[str], short_pct: float) -> dict[str, int]:
    result = {}
    for lo, hi, alloc in [(0, 2.5, investment * short_pct), (15.0, 50.0, investment * (1 - short_pct))]:
        cands = [b for b in BOND_UNIVERSE if lo < b["maturity"] <= hi and b["country"] in countries]
        if not cands:
            continue
        b   = next((x for x in cands if x["country"] == "USA"), cands[0])
        qty = max(1, round(alloc / _metrics(b)["price"]))
        result[b["id"]] = qty
    return result


# ── UI helpers ────────────────────────────────────────────────────────────────

def _section(title: str, subtitle: str = "") -> None:
    sub = f'<div style="font-size:12px;color:{_T2};margin-top:4px;">{subtitle}</div>' if subtitle else ""
    st.markdown(
        f'<div style="background:{_CARD};border-left:4px solid {_BLUE};'
        f'padding:10px 16px;margin:20px 0 10px;border-radius:0 8px 8px 0;">'
        f'<span style="font-size:12px;font-weight:700;color:{_T1};'
        f'text-transform:uppercase;letter-spacing:.08em;">{title}</span>{sub}</div>',
        unsafe_allow_html=True,
    )


def _val_card(label: str, value: str, sub: str = "", accent: str = _BLUE) -> str:
    sub_html = f'<div style="font-size:10px;color:{_T2};margin-top:3px;">{sub}</div>' if sub else ""
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
        template="plotly_dark", paper_bgcolor=_CARD, plot_bgcolor=_BG,
        margin=dict(l=62, r=20, t=40, b=44),
        font=dict(color=_T1, size=12),
        xaxis=dict(gridcolor=_EDGE, tickfont=dict(color=_T2), showline=True, linecolor=_EDGE),
        yaxis=dict(gridcolor=_EDGE, tickfont=dict(color=_T2), showline=True, linecolor=_EDGE),
        hoverlabel=dict(bgcolor=_CARD, font_color=_T1, bordercolor=_EDGE),
        legend=dict(font=dict(color=_T1), bgcolor="rgba(0,0,0,0)"),
    )
    base.update(kw)
    return base


def _strategy_banner(s: dict, color: str) -> None:
    st.markdown(
        f'<div style="background:{_CARD};border:1px solid {_EDGE};border-left:4px solid {color};'
        f'border-radius:8px;padding:14px 18px;margin-bottom:14px;">'
        f'<div style="font-size:13px;font-weight:600;color:{_T1};margin-bottom:6px;">{s["tagline"]}</div>'
        f'<div style="font-size:11px;color:{_T2};margin-bottom:3px;">'
        f'<strong style="color:{color};">Use when:</strong> {s["use_when"]}</div>'
        f'<div style="font-size:11px;color:{_T2};margin-bottom:3px;">'
        f'<strong style="color:{_T1};">How it works:</strong> {s["mechanics"]}</div>'
        f'<div style="font-size:11px;color:{_RED};">'
        f'<strong>Watch out:</strong> {s["watch"]}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )


# ── Charts ────────────────────────────────────────────────────────────────────

def _maturity_chart(df: pd.DataFrame, color: str) -> go.Figure:
    fig = go.Figure(go.Bar(
        x=df["maturity"], y=df["mv"],
        marker_color=color,
        text=df["name"].apply(lambda n: " ".join(n.split()[-2:])),
        textposition="outside", textfont=dict(color=_T1, size=9),
        hovertemplate="<b>%{text}</b><br>Maturity: %{x}Y<br>MV: $%{y:,.0f}<extra></extra>",
    ))
    fig.update_layout(
        height=280, showlegend=False,
        title=dict(text="Maturity Distribution", font=dict(size=13, color=_T1), x=0),
        xaxis_title="Maturity (years)", yaxis_title="Market Value ($)",
        **_chart_layout(margin=dict(l=70, r=20, t=40, b=50)),
    )
    return fig


def _cashflow_chart(positions: list[tuple[dict, int]], color: str) -> go.Figure:
    cf = _cash_flows(positions)
    if cf.empty:
        return go.Figure()
    fig = go.Figure()
    fig.add_trace(go.Bar(x=cf["year"], y=cf["coupon"],    name="Coupon",    marker_color=color, opacity=0.85))
    fig.add_trace(go.Bar(x=cf["year"], y=cf["principal"], name="Principal", marker_color=_AMB,  opacity=0.85))
    fig.update_layout(
        barmode="stack", height=280,
        title=dict(text="Cash Flow Waterfall", font=dict(size=13, color=_T1), x=0),
        xaxis_title="Year", yaxis_title="Cash Flow ($)",
        **_chart_layout(margin=dict(l=70, r=20, t=40, b=50)),
    )
    return fig


def _shock_table(df: pd.DataFrame, total_mv: float) -> None:
    rows = []
    for bp in [-200, -100, -50, -25, 25, 50, 100, 200]:
        dy  = bp / 10_000
        dmv = sum(
            approx_price_change(r["mod_dur"], r["conv"], r["price"], dy) * r["qty"]
            for _, r in df.iterrows()
        )
        rows.append({
            "Shock (bps)": f"{bp:+d}",
            "ΔMV ($)":     f"${dmv:+,.0f}",
            "ΔMV (%)":     f"{dmv / total_mv * 100:+.3f}%",
        })
    def _colour(row):
        bp  = int(row["Shock (bps)"].replace("+", ""))
        clr = "#d1fae5" if bp < 0 else "#fee2e2"
        return [f"background-color:{clr}"] * len(row)
    st.dataframe(pd.DataFrame(rows).style.apply(_colour, axis=1),
                 use_container_width=True, hide_index=True)


# ── Per-strategy tab ──────────────────────────────────────────────────────────

def _render_strategy(name: str, state_key: str, investment: float, countries: list[str]) -> None:
    s     = _STRAT[name]
    color = s["color"]
    ss    = f"strat_{state_key}_bonds"

    if ss not in st.session_state:
        st.session_state[ss] = {}

    _strategy_banner(s, color)

    # Controls row
    c1, c2, c3 = st.columns([2, 2, 1])

    if name == "Ladder":
        with c1:
            st.caption("Evenly distributes investment across 2Y · 5Y · 10Y · 30Y buckets.")
        with c3:
            if st.button("Auto-build", key=f"build_{state_key}", use_container_width=True):
                st.session_state[ss] = _auto_ladder(investment, countries)
                st.rerun()

    elif name == "Bullet":
        with c1:
            target_lbl = st.selectbox("Target maturity", ["2Y", "5Y", "10Y", "30Y"],
                                      index=2, key=f"bullet_tgt_{state_key}")
            target = float(target_lbl[:-1])
        with c3:
            if st.button("Auto-build", key=f"build_{state_key}", use_container_width=True):
                st.session_state[ss] = _auto_bullet(investment, countries, target)
                st.rerun()

    elif name == "Barbell":
        with c1:
            short_pct = st.slider("Short-end %", 20, 80, 50, 5,
                                  key=f"bb_split_{state_key}") / 100
        with c2:
            st.markdown(
                f'<div style="padding-top:26px;font-size:12px;color:{_T2};">'
                f'{int(short_pct*100)}% short-end (≤2Y) · {int((1-short_pct)*100)}% long-end (≥30Y)</div>',
                unsafe_allow_html=True,
            )
        with c3:
            if st.button("Auto-build", key=f"build_{state_key}", use_container_width=True):
                st.session_state[ss] = _auto_barbell(investment, countries, short_pct)
                st.rerun()

    # Manual override
    with st.expander("Manual Bond Selection / Override", expanded=not bool(st.session_state[ss])):
        available = [b for b in BOND_UNIVERSE if b["country"] in countries]
        id_to_label = {b["id"]: f"{b['name']}  ·  {b['coupon']}% cpn  ·  YTM {b['ytm']}%" for b in available}
        current = list(st.session_state[ss].keys())
        sel_ids = st.multiselect(
            "Add bonds", options=[b["id"] for b in available],
            default=[i for i in current if i in id_to_label],
            format_func=lambda bid: id_to_label.get(bid, bid),
            key=f"manual_{state_key}",
        )
        if sel_ids:
            qty_cols = st.columns(min(4, len(sel_ids)))
            new_qtys: dict[str, int] = {}
            for i, bid in enumerate(sel_ids):
                b = _BOND_BY_ID[bid]
                default_qty = st.session_state[ss].get(
                    bid, max(1, round(investment / len(sel_ids) / _metrics(b)["price"]))
                )
                with qty_cols[i % 4]:
                    new_qtys[bid] = st.number_input(
                        f"{b['name'].split()[-2]} {b['name'].split()[-1]}",
                        value=default_qty, min_value=1, step=1,
                        key=f"qty_{state_key}_{bid}",
                    )
            if st.button("Apply selection", key=f"apply_{state_key}"):
                st.session_state[ss] = new_qtys
                st.rerun()

    bond_ids = st.session_state[ss]
    if not bond_ids:
        st.info(f"Click **Auto-build** above to generate a {name} portfolio, or manually select bonds.")
        return

    df, port = _compute_portfolio(bond_ids)
    if df.empty:
        st.warning("No valid bonds in selection.")
        return

    # Metrics
    _section("Portfolio Metrics",
             f"{port['n_isins']} ISINs · {port['n_bonds']} bonds · "
             f"${port['total_mv']/1e6:.2f}M invested")

    cards = [
        ("Market Value",   f"${port['total_mv']/1e6:.2f}M",  f"{port['n_bonds']} bonds",       color),
        ("Wtd Avg YTM",    f"{port['ytm']:.3f}%",            "by market value",                 _AMB),
        ("Avg Maturity",   f"{port['avg_mat']:.1f} yrs",     "weighted by MV",                  _T2),
        ("Mac Duration",   f"{port['mac_dur']:.3f} yrs",     "avg cash-flow timing",            _AMB),
        ("Mod Duration",   f"{port['mod_dur']:.3f}",         "% Δpx per 1% Δyield",            _AMB),
        ("DV01",           f"${port['dv01']:,.0f}",          "$ per 1bp parallel shift",        _RED),
        ("Convexity",      f"{port['conv']:.2f}",            "higher = benefits from rate moves",_GRN),
    ]
    row1 = '<div style="display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin-bottom:8px;">'
    for lbl, val, sub, acc in cards[:4]:
        row1 += _val_card(lbl, val, sub, acc)
    row1 += "</div>"
    row2 = '<div style="display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin-bottom:14px;">'
    for lbl, val, sub, acc in cards[4:]:
        row2 += _val_card(lbl, val, sub, acc)
    row2 += "</div>"
    st.markdown(row1 + row2, unsafe_allow_html=True)

    # Charts
    _section("Strategy Shape & Cash Flows")
    positions = [(_BOND_BY_ID[bid], qty) for bid, qty in bond_ids.items() if bid in _BOND_BY_ID]
    ch1, ch2 = st.columns(2)
    with ch1:
        st.plotly_chart(_maturity_chart(df, color), use_container_width=True)
    with ch2:
        st.plotly_chart(_cashflow_chart(positions, color), use_container_width=True)

    # Quick parallel shock table
    _section("Quick Rate Shock",
             "Parallel yield curve shift · duration + convexity approximation")
    _shock_table(df, port["total_mv"])

    # Full scenario builder — per-economy, per-maturity shocks + impact analysis
    df_scen = df.copy()
    df_scen["units"] = df_scen["qty"]
    def _bucket(mat: float) -> str:
        for lbl, _, lo, hi in BUCKETS:
            if lo < mat <= hi:
                return lbl
        return "30Y"
    df_scen["bucket"] = df_scen["maturity"].apply(_bucket)
    _scenario_builder(set(bond_ids.keys()))
    _impact_analysis(df_scen, port["total_mv"])

    # Holdings detail
    with st.expander("Holdings Detail"):
        disp = df[["name", "country", "maturity", "coupon", "ytm",
                   "price", "qty", "mv", "weight", "mod_dur", "dv01"]].copy()
        disp.columns = ["Bond", "Country", "Maturity (Y)", "Coupon %", "YTM %",
                        "Price", "Qty", "MV ($)", "Weight", "Mod Dur", "DV01"]
        disp["Weight"] = (disp["Weight"] * 100).round(1).astype(str) + "%"
        disp["MV ($)"] = disp["MV ($)"].round(0).astype(int)
        disp["DV01"]   = disp["DV01"].round(0).astype(int)
        st.dataframe(disp, use_container_width=True, hide_index=True)


# ── Compare tab ───────────────────────────────────────────────────────────────

def _compare_tab(investment: float, countries: list[str]) -> None:
    st.markdown(
        f'<div style="font-size:13px;color:{_T2};margin-bottom:14px;">'
        'Auto-built defaults for each strategy at the selected investment amount. '
        'Customise individual strategies in their tabs, then return here to compare.</div>',
        unsafe_allow_html=True,
    )

    defaults = {
        "Ladder":  _auto_ladder(investment, countries),
        "Bullet":  _auto_bullet(investment, countries, 10.0),
        "Barbell": _auto_barbell(investment, countries, 0.5),
    }

    # Build portfolios
    portfolios: dict[str, tuple[pd.DataFrame, dict]] = {}
    for name, bond_ids in defaults.items():
        df, port = _compute_portfolio(bond_ids)
        if not df.empty:
            portfolios[name] = (df, port)

    if not portfolios:
        st.warning("No bonds available for selected countries.")
        return

    # Metrics table
    _section("Side-by-Side Metrics")
    metric_rows = []
    for name, (df, port) in portfolios.items():
        s = _STRAT[name]
        metric_rows.append({
            "Strategy":      f"{s['emoji']} {name}",
            "Market Value":  f"${port['total_mv']/1e6:.2f}M",
            "Wtd YTM":       f"{port['ytm']:.3f}%",
            "Avg Maturity":  f"{port['avg_mat']:.1f}Y",
            "Mac Duration":  f"{port['mac_dur']:.3f}",
            "Mod Duration":  f"{port['mod_dur']:.3f}",
            "Convexity":     f"{port['conv']:.2f}",
            "DV01 ($)":      f"${port['dv01']:,.0f}",
        })
    st.dataframe(pd.DataFrame(metric_rows).set_index("Strategy"), use_container_width=True)

    # Rate sensitivity comparison chart
    _section("Rate Sensitivity", "Parallel shift · % change in portfolio value")
    shock_bps = [-200, -100, -50, -25, 25, 50, 100, 200]
    fig = go.Figure()
    for name, (df, port) in portfolios.items():
        pcts = []
        for bp in shock_bps:
            dy  = bp / 10_000
            dmv = sum(
                approx_price_change(r["mod_dur"], r["conv"], r["price"], dy) * r["qty"]
                for _, r in df.iterrows()
            )
            pcts.append(dmv / port["total_mv"] * 100)
        fig.add_trace(go.Scatter(
            x=[f"{b:+d}bp" for b in shock_bps], y=pcts, name=name,
            mode="lines+markers",
            line=dict(color=_STRAT[name]["color"], width=2),
            marker=dict(size=7),
            hovertemplate=f"{name}<br>%{{x}}<br>ΔMV: %{{y:+.3f}}%<extra></extra>",
        ))
    fig.add_hline(y=0, line=dict(color=_T3, width=1, dash="dot"))
    fig.update_layout(
        height=340,
        title=dict(text="ΔMV (%) by Parallel Rate Shock", font=dict(size=13, color=_T1), x=0),
        xaxis_title="Parallel Shock", yaxis_title="ΔMV (%)",
        **_chart_layout(margin=dict(l=62, r=20, t=40, b=50)),
    )
    st.plotly_chart(fig, use_container_width=True)

    # Cash flow comparison
    _section("Cash Flow Comparison", "Coupon (solid) + principal (amber) flows per strategy")
    cf_cols = st.columns(3)
    for i, (name, (df, port)) in enumerate(portfolios.items()):
        s     = _STRAT[name]
        color = s["color"]
        positions = [(_BOND_BY_ID[bid], qty)
                     for bid, qty in defaults[name].items() if bid in _BOND_BY_ID]
        with cf_cols[i]:
            st.markdown(
                f'<div style="font-size:12px;font-weight:600;color:{color};'
                f'margin-bottom:6px;">{s["emoji"]} {name}</div>',
                unsafe_allow_html=True,
            )
            cf = _cash_flows(positions)
            if not cf.empty:
                fig = go.Figure()
                fig.add_trace(go.Bar(x=cf["year"], y=cf["coupon"],    name="Coupon",
                                     marker_color=color, opacity=0.85, showlegend=False))
                fig.add_trace(go.Bar(x=cf["year"], y=cf["principal"], name="Principal",
                                     marker_color=_AMB,  opacity=0.85, showlegend=False))
                fig.update_layout(
                    barmode="stack", height=240,
                    margin=dict(l=50, r=10, t=10, b=40),
                    paper_bgcolor=_CARD, plot_bgcolor=_BG,
                    font=dict(color=_T1, size=10),
                    xaxis=dict(gridcolor=_EDGE, tickfont=dict(color=_T2, size=9),
                               title="Year", title_font=dict(size=10)),
                    yaxis=dict(gridcolor=_EDGE, tickfont=dict(color=_T2, size=9)),
                )
                st.plotly_chart(fig, use_container_width=True)


# ── Main entry point ──────────────────────────────────────────────────────────

def bond_investment_strategies() -> None:
    st.markdown(
        '<h2 style="color:#0f172a;margin:0 0 2px;">Bond Investment Strategies</h2>'
        '<div style="font-size:12px;color:#475569;">'
        'Build, compare and stress-test Ladder · Bullet · Barbell portfolios · '
        '30 sovereign bonds · $100k face per bond</div>'
        '<hr style="border:none;border-top:1px solid #e2e8f0;margin:10px 0 6px;">',
        unsafe_allow_html=True,
    )

    # Sidebar
    st.sidebar.markdown(
        f'<div style="font-size:10px;color:{_T2};text-transform:uppercase;'
        f'letter-spacing:.1em;margin:8px 0 6px;padding-bottom:4px;'
        f'border-bottom:1px solid {_EDGE};">Strategy Settings</div>',
        unsafe_allow_html=True,
    )
    investment = st.sidebar.number_input(
        "Total Investment ($)", value=1_000_000, step=100_000,
        min_value=100_000, key="strat_investment",
    )
    all_countries = sorted({b["country"] for b in BOND_UNIVERSE})
    countries = st.sidebar.multiselect(
        "Countries", all_countries,
        default=["USA", "Germany", "United Kingdom", "Japan"],
        key="strat_countries",
    )
    if not countries:
        st.warning("Select at least one country in the sidebar to get started.")
        return

    tab1, tab2, tab3, tab4 = st.tabs(["🪜 Ladder", "🎯 Bullet", "🏋️ Barbell", "⚖️ Compare"])

    with tab1:
        _render_strategy("Ladder",  "ladder",  investment, countries)
    with tab2:
        _render_strategy("Bullet",  "bullet",  investment, countries)
    with tab3:
        _render_strategy("Barbell", "barbell", investment, countries)
    with tab4:
        _compare_tab(investment, countries)
