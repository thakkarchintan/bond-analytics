from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from macro_data import ALL_COUNTRIES, YEARS, load_macro_data

# ── Palette ────────────────────────────────────────────────────────────────────

COUNTRY_COLORS: dict[str, str] = {
    "USA":            "#60a5fa",
    "China":          "#f87171",
    "Japan":          "#34d399",
    "Germany":        "#a78bfa",
    "France":         "#fbbf24",
    "Italy":          "#fb923c",
    "United Kingdom": "#22d3ee",
    "India":          "#f472b6",
    "Canada":         "#818cf8",
    "Brazil":         "#a3e635",
}

_BG   = "#0f172a"
_CARD = "#1e293b"
_EDGE = "#334155"
_T1   = "#f1f5f9"
_T2   = "#94a3b8"
_T3   = "#475569"
_BLUE = "#3b82f6"
_GRN  = "#10b981"
_RED  = "#ef4444"


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


def _pending(title: str, note: str = "Data not yet integrated.") -> None:
    _section(title)
    st.markdown(
        f'<div style="background:{_CARD};border:1px dashed {_EDGE};border-radius:8px;'
        f'padding:40px 24px;text-align:center;margin-bottom:8px;">'
        f'<div style="font-size:10px;font-weight:700;color:{_T2};'
        f'text-transform:uppercase;letter-spacing:.14em;margin-bottom:8px;">Data Pending</div>'
        f'<div style="font-size:13px;color:{_T3};">{note}</div>'
        f'<div style="font-size:11px;color:{_T3};margin-top:6px;">'
        f'Section auto-populates when data is integrated.</div></div>',
        unsafe_allow_html=True,
    )


def _metric_card(label: str, value: str) -> str:
    return (
        f'<div style="background:{_CARD};border:1px solid {_EDGE};border-radius:8px;'
        f'padding:16px 10px;text-align:center;height:88px;display:flex;'
        f'flex-direction:column;justify-content:center;">'
        f'<div style="font-size:10px;color:{_T2};text-transform:uppercase;'
        f'letter-spacing:.1em;margin-bottom:6px;">{label}</div>'
        f'<div style="font-size:21px;font-weight:700;color:{_T1};">{value}</div></div>'
    )


def _hex_rgba(h: str, a: float) -> str:
    h = h.lstrip("#")
    r, g, b = int(h[:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"rgba({r},{g},{b},{a})"


# ── Chart layout base ──────────────────────────────────────────────────────────

def _layout(**kw) -> dict:
    base = dict(
        template="plotly_dark",
        paper_bgcolor=_CARD,
        plot_bgcolor=_BG,
        margin=dict(l=62, r=20, t=44, b=44),
        font=dict(color=_T1, size=12),
        legend=dict(
            orientation="h", yanchor="bottom", y=1.02,
            xanchor="right", x=1, font=dict(size=11),
        ),
        xaxis=dict(gridcolor=_EDGE, tickfont=dict(color=_T2),
                   showline=True, linecolor=_EDGE),
        yaxis=dict(gridcolor=_EDGE, tickfont=dict(color=_T2),
                   showline=True, linecolor=_EDGE),
        hoverlabel=dict(bgcolor=_CARD, font_color=_T1, bordercolor=_EDGE),
    )
    base.update(kw)
    return base


# ── Reusable chart builders ────────────────────────────────────────────────────

def _line_compare(
    fdf: pd.DataFrame,
    col: str,
    title: str,
    yaxis_title: str,
    fmt: str = ".1f",
    height: int = 380,
    countries: list[str] | None = None,
) -> None:
    active = countries or ALL_COUNTRIES
    fig = go.Figure()
    for country in active:
        cdf = fdf[fdf["Country"] == country].sort_values("Year").dropna(subset=[col])
        if cdf.empty:
            continue
        fig.add_trace(go.Scatter(
            x=cdf["Year"], y=cdf[col],
            name=country,
            line=dict(color=COUNTRY_COLORS.get(country, "#888"), width=2.5),
            mode="lines+markers",
            marker=dict(size=5),
            hovertemplate=f"<b>{country}</b><br>%{{x}}: %{{y:{fmt}}}<extra></extra>",
        ))
    fig.update_layout(
        height=height,
        title=dict(text=title, font=dict(size=13, color=_T1), x=0),
        yaxis_title=yaxis_title,
        **_layout(),
    )
    st.plotly_chart(fig, use_container_width=True)


def _line_small_multiples(
    fdf: pd.DataFrame,
    col: str,
    yaxis_title: str,
    fmt: str = ".1f",
    countries: list[str] | None = None,
) -> None:
    active = countries or ALL_COUNTRIES
    chart_cols = st.columns(2)
    for i, country in enumerate(active):
        cdf = fdf[fdf["Country"] == country].sort_values("Year").dropna(subset=[col])
        clr = COUNTRY_COLORS.get(country, "#888")
        with chart_cols[i % 2]:
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=cdf["Year"], y=cdf[col],
                line=dict(color=clr, width=2),
                fill="tozeroy",
                fillcolor=_hex_rgba(clr, 0.12),
                mode="lines+markers",
                marker=dict(size=4),
                hovertemplate=f"<b>{country}</b><br>%{{x}}: %{{y:{fmt}}}<extra></extra>",
                showlegend=False,
            ))
            fig.update_layout(
                height=260,
                title=dict(text=country, font=dict(size=12, color=clr), x=0),
                yaxis_title=yaxis_title,
                **_layout(legend=dict(visible=False)),
            )
            st.plotly_chart(fig, use_container_width=True)


def _bar_latest(
    fdf: pd.DataFrame,
    col: str,
    yaxis_title: str,
    year: int,
    countries: list[str],
) -> None:
    snap = (
        fdf[(fdf["Year"] == year) & (fdf["Country"].isin(countries))]
        .dropna(subset=[col])
        .sort_values(col, ascending=False)
    )
    if snap.empty:
        return
    fig = go.Figure(go.Bar(
        x=snap["Country"],
        y=snap[col],
        marker_color=[COUNTRY_COLORS.get(c, "#888") for c in snap["Country"]],
        hovertemplate="%{x}: %{y:.1f}<extra></extra>",
    ))
    fig.update_layout(
        height=300,
        title=dict(text=f"Latest ({year})", font=dict(size=12, color=_T1), x=0),
        yaxis_title=yaxis_title,
        showlegend=False,
        **_layout(legend=dict(visible=False)),
    )
    st.plotly_chart(fig, use_container_width=True)


def _render_section(
    fdf: pd.DataFrame,
    col: str,
    title: str,
    section_title: str,
    subtitle: str,
    yaxis_title: str,
    fmt: str = ".1f",
    height: int = 380,
    countries: list[str] | None = None,
    compare: bool = True,
    show_bar: bool = False,
    year_to: int = 2024,
) -> None:
    _section(section_title, subtitle)
    active = countries or ALL_COUNTRIES

    if compare:
        if show_bar:
            c1, c2 = st.columns([5, 2])
            with c1:
                _line_compare(fdf, col, title, yaxis_title, fmt, height, active)
            with c2:
                _bar_latest(fdf, col, yaxis_title, year_to, active)
        else:
            _line_compare(fdf, col, title, yaxis_title, fmt, height, active)
    else:
        _line_small_multiples(fdf, col, yaxis_title, fmt, active)
        if show_bar:
            _bar_latest(fdf, col, yaxis_title, year_to, active)


# ── Snapshot section ───────────────────────────────────────────────────────────

def _snapshot(fdf: pd.DataFrame, year_to: int, countries: list[str]) -> None:
    _section("Global Snapshot", f"Cross-country averages for selected countries · {year_to}")

    snap = fdf[(fdf["Year"] == year_to) & (fdf["Country"].isin(countries))]

    def _fmt_gdp(v: float) -> str:
        return f"${v / 1000:.1f}tn" if not pd.isna(v) else "—"

    def _fmt_pct(v: float, dp: int = 1) -> str:
        return f"{v:.{dp}f}%" if not pd.isna(v) else "—"

    metrics = [
        ("Avg GDP", _fmt_gdp(snap["GDP_USD"].mean())),
        ("GDP Growth", _fmt_pct(snap["Real_GDP_Growth"].mean())),
        ("Inflation", _fmt_pct(snap["CPI_Inflation"].mean())),
        ("Debt/GDP", _fmt_pct(snap["Debt_GDP"].mean(), 0)),
        ("Fiscal Balance", _fmt_pct(snap["Fiscal_Balance_GDP"].mean())),
    ]

    html = '<div style="display:grid;grid-template-columns:repeat(5,1fr);gap:10px;margin-bottom:20px;">'
    for label, val in metrics:
        html += _metric_card(label, val)
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)

    # Country scorecard
    score_cols = {
        "GDP_USD":             f"GDP USD bn",
        "Real_GDP_Growth":     "Growth %",
        "CPI_Inflation":       "Inflation %",
        "Debt_GDP":            "Debt/GDP %",
        "Fiscal_Balance_GDP":  "Fiscal Bal %",
        "Govt_Debt_Outstanding": "Debt USD bn",
    }
    available = {k: v for k, v in score_cols.items() if k in snap.columns}
    display = (
        snap.set_index("Country")[list(available.keys())]
        .reindex(countries)
        .rename(columns=available)
        .round(1)
    )
    st.dataframe(display, use_container_width=True)


# ── Main entry point ───────────────────────────────────────────────────────────

def macro_dashboard() -> None:
    df = load_macro_data()

    # ── Sidebar controls ───────────────────────────────────────────────────────
    st.sidebar.markdown(
        f'<div style="font-size:10px;color:{_T2};text-transform:uppercase;'
        f'letter-spacing:.1em;margin:20px 0 8px;padding-bottom:6px;'
        f'border-bottom:1px solid {_EDGE};">Dashboard Filters</div>',
        unsafe_allow_html=True,
    )

    # Display names keep the canonical country order with short labels
    display_order = [
        "USA", "China", "Japan", "Germany", "France",
        "Italy", "United Kingdom", "India", "Canada", "Brazil",
    ]
    selected = st.sidebar.multiselect(
        "Countries",
        options=display_order,
        default=display_order,
        key="macro_countries",
    )

    year_from, year_to = st.sidebar.slider(
        "Year range",
        min_value=min(YEARS),
        max_value=max(YEARS),
        value=(min(YEARS), max(YEARS)),
        key="macro_years",
    )

    compare = st.sidebar.checkbox(
        "Compare (one chart per metric)",
        value=True,
        key="macro_compare",
    )

    if not selected:
        st.warning("Select at least one country in the sidebar.")
        return

    fdf = df[df["Country"].isin(selected) & df["Year"].between(year_from, year_to)].copy()

    # ── Page header ────────────────────────────────────────────────────────────
    st.markdown(
        f'<h2 style="color:{_T1};margin:0 0 2px;">Global Macro Dashboard</h2>'
        f'<div style="font-size:12px;color:{_T2};">'
        f'{len(selected)} countries · {year_from}–{year_to} · '
        f'{"Compare mode" if compare else "Small multiples"} · '
        f'Source: IMF WEO &amp; GDD</div>'
        f'<hr style="border:none;border-top:1px solid {_EDGE};margin:14px 0 4px;">',
        unsafe_allow_html=True,
    )

    # ── 1. Snapshot ────────────────────────────────────────────────────────────
    _snapshot(fdf, year_to, selected)

    # ── 2. GDP ────────────────────────────────────────────────────────────────
    _render_section(
        fdf, "GDP_USD",
        title="GDP — USD Billions",
        section_title="GDP",
        subtitle="Gross Domestic Product, current prices (USD billions) · IMF WEO",
        yaxis_title="USD bn",
        fmt=".0f",
        height=400,
        countries=selected,
        compare=compare,
        show_bar=True,
        year_to=year_to,
    )

    # ── 3. Real GDP Growth ────────────────────────────────────────────────────
    _render_section(
        fdf, "Real_GDP_Growth",
        title="Real GDP Growth %",
        section_title="Real GDP Growth",
        subtitle="% change, constant prices · IMF WEO (NGDP_RPCH)",
        yaxis_title="%",
        fmt=".1f",
        height=360,
        countries=selected,
        compare=compare,
    )

    # ── 4. Government Debt Outstanding ────────────────────────────────────────
    _render_section(
        fdf, "Govt_Debt_Outstanding",
        title="Government Debt Outstanding — USD Billions",
        section_title="Government Debt Outstanding",
        subtitle="Calculated: General Govt Gross Debt/GDP × GDP USD (approx.) · IMF GDD × WEO",
        yaxis_title="USD bn",
        fmt=".0f",
        height=400,
        countries=selected,
        compare=compare,
        show_bar=True,
        year_to=year_to,
    )

    # ── 5. Debt / GDP ─────────────────────────────────────────────────────────
    _render_section(
        fdf, "Debt_GDP",
        title="Government Debt / GDP %",
        section_title="Government Debt / GDP",
        subtitle="General Government Gross Debt as % of GDP · IMF Global Debt Database (GDD)",
        yaxis_title="%",
        fmt=".1f",
        height=400,
        countries=selected,
        compare=compare,
        show_bar=True,
        year_to=year_to,
    )

    # ── 6. Fiscal Balance ─────────────────────────────────────────────────────
    _section(
        "Fiscal Balance",
        "General Government Net Lending (+) / Net Borrowing (−) · IMF WEO",
    )
    if compare:
        c1, c2 = st.columns(2)
        with c1:
            _line_compare(fdf, "Fiscal_Balance_GDP", "Fiscal Balance % GDP",
                          "%", ".1f", 360, selected)
        with c2:
            _line_compare(fdf, "Primary_Balance_GDP", "Primary Balance % GDP",
                          "%", ".1f", 360, selected)
    else:
        st.markdown(
            f'<div style="font-size:12px;color:{_T2};margin-bottom:6px;">Fiscal Balance</div>',
            unsafe_allow_html=True,
        )
        _line_small_multiples(fdf, "Fiscal_Balance_GDP", "%", ".1f", selected)
        st.markdown(
            f'<div style="font-size:12px;color:{_T2};margin:12px 0 6px;">Primary Balance</div>',
            unsafe_allow_html=True,
        )
        _line_small_multiples(fdf, "Primary_Balance_GDP", "%", ".1f", selected)

    # ── 7. CPI Inflation ──────────────────────────────────────────────────────
    _render_section(
        fdf, "CPI_Inflation",
        title="CPI Inflation %",
        section_title="CPI Inflation",
        subtitle="Consumer Price Index, period average % change · IMF WEO (PCPIPCH)",
        yaxis_title="%",
        fmt=".1f",
        height=360,
        countries=selected,
        compare=compare,
        show_bar=True,
        year_to=year_to,
    )

    # ── 8–12. Pending sections ─────────────────────────────────────────────────
    _pending(
        "10Y Government Yield",
        "10-year benchmark government bond yield data not yet integrated.",
    )
    _pending(
        "Policy Rate",
        "Central bank policy rate data not yet integrated.",
    )
    _pending(
        "Government Bond Issuance",
        "Gross government bond issuance (USD bn) data not yet integrated.",
    )
    _pending(
        "Bond Issuance / GDP",
        "Requires gross bond issuance data — will calculate automatically once integrated.",
    )
    _pending(
        "Correlation: Debt/GDP vs 10Y Yield",
        "10-year government yield data required for this scatter analysis.",
    )
    _pending(
        "Correlation: Fiscal Balance vs 10Y Yield",
        "10-year government yield data required for this scatter analysis.",
    )

    # ── 13. Download ──────────────────────────────────────────────────────────
    _section("Download Data", "Filtered dataset as CSV")
    dl_cols = [
        "Country", "Year", "GDP_USD", "Real_GDP_Growth", "CPI_Inflation",
        "Debt_GDP", "Fiscal_Balance_GDP", "Primary_Balance_GDP",
        "Govt_Debt_Outstanding",
    ]
    dl_df = fdf[[c for c in dl_cols if c in fdf.columns]].copy()
    dl_df.columns = [c.replace("_", " ") for c in dl_df.columns]
    csv_bytes = dl_df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="⬇  Download CSV",
        data=csv_bytes,
        file_name=f"global_macro_{year_from}_{year_to}.csv",
        mime="text/csv",
    )
