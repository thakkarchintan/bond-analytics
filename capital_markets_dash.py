"""
Global Capital Markets Dashboard — Dash prototype (light theme)
Run standalone:  python capital_markets_dash.py  →  http://localhost:8051

Light-themed counterpart to the Credit Spreads dark prototype.
All Plotly charts show the full toolbar (zoom, pan, download, fullscreen).
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

import dash
from dash import dcc, html, Input, Output, callback, dash_table
import dash_bootstrap_components as dbc

# ── Light palette ──────────────────────────────────────────────────────────────
_PAGE   = "#f0f4f8"       # outer page background
_SIDE   = "#ffffff"       # sidebar background
_CARD   = "#ffffff"       # card / chart background
_PLOT   = "#f8fafc"       # plot area inside chart
_BORDER = "#e2e8f0"       # borders & grid lines
_T1     = "#0f172a"       # primary text
_T2     = "#475569"       # secondary text
_T3     = "#94a3b8"       # muted text
_BLUE   = "#2563eb"       # accent
_GRN    = "#059669"
_RED    = "#dc2626"
_AMB    = "#d97706"
_PRP    = "#7c3aed"

# Data colours (same as Streamlit version for consistency)
COUNTRY_COLORS = {
    "United States":  "#2563eb",
    "China":          "#dc2626",
    "Japan":          "#059669",
    "India":          "#db2777",
    "United Kingdom": "#0891b2",
    "France":         "#d97706",
    "Germany":        "#7c3aed",
    "Canada":         "#4f46e5",
    "Brazil":         "#65a30d",
    "Australia":      "#ea580c",
}

FINANCING_MODEL = {
    "United States":  "Market-based",
    "China":          "State-led",
    "Japan":          "Government debt-heavy",
    "India":          "Mixed / developing",
    "United Kingdom": "Market-based",
    "France":         "Mixed / bank-based",
    "Germany":        "Bank-based",
    "Canada":         "Market-based",
    "Brazil":         "Mixed / developing",
    "Australia":      "Market-based",
}

HERE  = Path(__file__).parent
CACHE = HERE / "capital_markets_cache.parquet"

# Plotly toolbar config — show all tools, allow scroll zoom, hide logo
_CHART_CONFIG = {
    "displayModeBar":  True,
    "scrollZoom":      True,
    "displaylogo":     False,
    "modeBarButtonsToRemove": ["select2d", "lasso2d"],
    "toImageButtonOptions": {
        "format": "png",
        "filename": "bond_analytics_chart",
        "scale": 2,
    },
}


# ── Helpers ────────────────────────────────────────────────────────────────────

def _fmt_t(val) -> str:
    if pd.isna(val):
        return "N/A"
    if val >= 1:
        return f"${val:.2f}T"
    return f"${val * 1000:.0f}B"


def _country_colors(countries: list[str]) -> list[str]:
    return [COUNTRY_COLORS.get(c, "#94a3b8") for c in countries]


def load_df() -> pd.DataFrame:
    if not CACHE.exists():
        return pd.DataFrame()
    return pd.read_parquet(CACHE)


def _chart_layout(**kw) -> dict:
    base = dict(
        paper_bgcolor=_CARD,
        plot_bgcolor=_PLOT,
        font=dict(family="Inter, system-ui, sans-serif", color=_T1, size=12),
        margin=dict(l=60, r=24, t=48, b=90),
        xaxis=dict(
            gridcolor=_BORDER, tickfont=dict(color=_T2),
            showline=True, linecolor=_BORDER, zerolinecolor=_BORDER,
        ),
        yaxis=dict(
            gridcolor=_BORDER, tickfont=dict(color=_T2),
            showline=True, linecolor=_BORDER, zerolinecolor=_BORDER,
        ),
        hoverlabel=dict(bgcolor=_CARD, font_color=_T1, bordercolor=_BORDER),
        legend=dict(
            orientation="h",
            yanchor="top",
            y=-0.18,
            xanchor="center",
            x=0.5,
            font=dict(color=_T2, size=11),
            bgcolor="rgba(255,255,255,0.8)",
            bordercolor=_BORDER, borderwidth=1,
        ),
    )
    base.update(kw)
    return base


def _card_wrap(children, style: dict | None = None) -> html.Div:
    s = {
        "background": _CARD,
        "border": f"1px solid {_BORDER}",
        "borderRadius": "12px",
        "padding": "20px 24px",
        "marginBottom": "20px",
        "boxShadow": "0 1px 3px rgba(0,0,0,0.06)",
    }
    if style:
        s.update(style)
    return html.Div(children, style=s)


def _section_label(title: str, subtitle: str = "") -> html.Div:
    return html.Div([
        html.Div(title, style={
            "fontSize": "13px", "fontWeight": "700", "color": _T1,
            "textTransform": "uppercase", "letterSpacing": ".07em",
        }),
        html.Div(subtitle, style={
            "fontSize": "12px", "color": _T2, "marginTop": "3px",
        }) if subtitle else None,
    ], style={
        "borderLeft": f"3px solid {_BLUE}",
        "paddingLeft": "12px",
        "marginBottom": "16px",
    })


# ── App ────────────────────────────────────────────────────────────────────────

app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    title="Capital Markets — Dash | Bond Analytics",
    suppress_callback_exceptions=True,
)

# ── Sidebar ────────────────────────────────────────────────────────────────────

_sidebar_style = {
    "position":    "fixed",
    "top":         0,
    "left":        0,
    "bottom":      0,
    "width":       "260px",
    "padding":     "24px 18px",
    "background":  _SIDE,
    "borderRight": f"1px solid {_BORDER}",
    "overflowY":   "auto",
    "zIndex":      1000,
    "boxShadow":   "2px 0 8px rgba(0,0,0,0.06)",
}

_content_style = {
    "marginLeft": "260px",
    "padding":    "28px 32px",
    "background": _PAGE,
    "minHeight":  "100vh",
}

sidebar = html.Div([

    # Brand
    html.Div([
        html.Div("Bond Analytics", style={
            "fontSize": "11px", "fontWeight": "700", "color": _BLUE,
            "letterSpacing": ".1em", "textTransform": "uppercase",
        }),
        html.Div("Capital Markets", style={
            "fontSize": "20px", "fontWeight": "700", "color": _T1, "marginTop": "2px",
        }),
        html.Div("10 countries · equity & govt bonds · 2005–2023", style={
            "fontSize": "11px", "color": _T3, "marginTop": "3px", "lineHeight": "1.4",
        }),
    ], style={"marginBottom": "28px"}),

    html.Hr(style={"borderColor": _BORDER, "margin": "0 0 20px"}),

    # Year slider
    html.Div("YEAR", style={
        "fontSize": "10px", "fontWeight": "700", "color": _T3,
        "textTransform": "uppercase", "letterSpacing": ".1em", "marginBottom": "12px",
    }),
    dcc.Slider(
        id="cm-year",
        min=2005, max=2023, step=1, value=2023,
        marks={y: {"label": str(y), "style": {"color": _T3, "fontSize": "10px"}}
               for y in [2005, 2010, 2015, 2020, 2023]},
        tooltip={"placement": "bottom", "always_visible": True},
    ),

    html.Hr(style={"borderColor": _BORDER, "margin": "20px 0"}),

    # Country filter
    html.Div("COUNTRIES", style={
        "fontSize": "10px", "fontWeight": "700", "color": _T3,
        "textTransform": "uppercase", "letterSpacing": ".1em", "marginBottom": "10px",
    }),
    dcc.Checklist(
        id="cm-countries",
        options=[
            {"label": html.Span(c, style={"color": COUNTRY_COLORS.get(c, _T1),
                                           "fontWeight": "600", "fontSize": "12px",
                                           "marginLeft": "6px"}),
             "value": c}
            for c in [
                "United States", "China", "Japan", "India", "United Kingdom",
                "France", "Germany", "Canada", "Brazil", "Australia",
            ]
        ],
        value=[
            "United States", "China", "Japan", "India", "United Kingdom",
            "France", "Germany", "Canada", "Brazil", "Australia",
        ],
        style={"display": "flex", "flexDirection": "column", "gap": "7px"},
        inputStyle={"accentColor": _BLUE},
    ),

    html.Hr(style={"borderColor": _BORDER, "margin": "20px 0"}),

    # Sections toggle
    html.Div("SECTIONS", style={
        "fontSize": "10px", "fontWeight": "700", "color": _T3,
        "textTransform": "uppercase", "letterSpacing": ".1em", "marginBottom": "10px",
    }),
    dcc.Checklist(
        id="cm-sections",
        options=[
            {"label": html.Span(label, style={"fontSize": "12px", "color": _T2, "marginLeft": "6px"}),
             "value": val}
            for label, val in [
                ("Global Snapshot",          "snapshot"),
                ("Market Size",              "size"),
                ("Equity vs Bond Scatter",   "scatter"),
                ("Equity / GDP",             "eq_gdp"),
                ("Govt Bond / GDP",          "gb_gdp"),
                ("Total Ranking",            "ranking"),
                ("Historical Evolution",     "history"),
                ("Ratios & Bubbles",         "ratios"),
                ("Capital Markets DNA",      "dna"),
            ]
        ],
        value=["snapshot", "size", "scatter", "eq_gdp", "gb_gdp",
               "ranking", "history", "ratios", "dna"],
        style={"display": "flex", "flexDirection": "column", "gap": "7px"},
        inputStyle={"accentColor": _BLUE},
    ),

    html.Hr(style={"borderColor": _BORDER, "margin": "20px 0"}),

    html.Div("💡 Tip: use the toolbar to zoom / pan / download PNG. Use the ⤢ button on each chart to go fullscreen.",
             style={"fontSize": "11px", "color": _T3, "lineHeight": "1.5"}),

], style=_sidebar_style)


content = html.Div([

    # Page header
    html.Div([
        html.H2("Global Capital Markets Dashboard", style={
            "color": _T1, "fontWeight": "700", "fontSize": "22px", "marginBottom": "2px",
        }),
        html.Div(
            "10 countries · equity vs government bond markets · market size vs GDP · "
            "historical evolution 2005–2023",
            style={"fontSize": "12px", "color": _T2, "marginBottom": "24px"},
        ),
    ]),

    html.Div(id="cm-page-content"),

    # Footer
    html.Div([
        html.Hr(style={"borderColor": _BORDER}),
        html.Div([
            html.Strong("Data sources: "),
            "Equity market capitalisation — World Bank (CM.MKT.LCAP.CD). ",
            "Government bond market size — IMF Gross Government Debt (% GDP) × GDP (USD). ",
            "GDP data — IMF World Economic Outlook. ",
            "Corporate bond data (BIS) not yet integrated.",
        ], style={"fontSize": "11px", "color": _T3}),
    ], style={"marginTop": "40px"}),

], style=_content_style)


app.layout = html.Div(
    [sidebar, content],
    style={"fontFamily": "Inter, system-ui, sans-serif", "background": _PAGE},
)


# ── Main callback ──────────────────────────────────────────────────────────────

@callback(
    Output("cm-page-content", "children"),
    Input("cm-year",      "value"),
    Input("cm-countries", "value"),
    Input("cm-sections",  "value"),
)
def render_page(year: int, selected_countries: list[str], sections: list[str]):
    full_df = load_df()
    if full_df.empty:
        return html.Div("No data available.", style={"color": _T2, "padding": "40px 0"})

    selected_countries = selected_countries or []
    sections = sections or []

    yr_df   = full_df[
        (full_df["Year"] == year) &
        (full_df["Country"].isin(selected_countries))
    ].copy()
    hist_df = full_df[full_df["Country"].isin(selected_countries)].copy()

    blocks = []

    if "snapshot" in sections:
        blocks.append(_kpi_snapshot(yr_df, year))

    if "size" in sections:
        blocks.append(_market_size(yr_df, year))

    if "scatter" in sections:
        blocks.append(_scatter_eq_bond(yr_df, year))

    row_charts = []
    if "eq_gdp" in sections:
        row_charts.append(dbc.Col(_equity_gdp(yr_df, year), width=6))
    if "gb_gdp" in sections:
        row_charts.append(dbc.Col(_govtbond_gdp(yr_df, year), width=6))
    if row_charts:
        blocks.append(dbc.Row(row_charts, style={"marginBottom": "0"}))

    if "ranking" in sections:
        blocks.append(_total_ranking(yr_df, year))

    if "history" in sections:
        blocks.append(_historical(hist_df))

    if "ratios" in sections:
        blocks.append(_ratios_and_bubble(yr_df, year))

    if "dna" in sections:
        blocks.append(_dna_table(yr_df))

    return html.Div(blocks)


# ── Section renderers ──────────────────────────────────────────────────────────

def _kpi_snapshot(yr_df: pd.DataFrame, year: int) -> html.Div:
    valid = yr_df.dropna(subset=["Equity_USD", "GovtBond_USD", "GDP_USD"])

    total_eq  = valid["Equity_USD"].sum()
    total_gb  = valid["GovtBond_USD"].sum()
    total_cap = total_eq + total_gb
    total_gdp = valid["GDP_USD"].sum()
    n         = len(valid)
    avg_eq_gdp = valid["Equity_GDP_Pct"].mean()
    avg_gb_gdp = valid["GovtBond_GDP_Pct"].mean()

    kpis = [
        ("Global Equity Markets", _fmt_t(total_eq), f"{n} countries", _BLUE),
        ("Global Govt Bond Mkts", _fmt_t(total_gb), "Gross govt debt proxy", _GRN),
        ("Total Capital Markets", _fmt_t(total_cap), "Equity + Govt Bonds", _PRP),
        ("Combined GDP", _fmt_t(total_gdp), f"{n} countries", _AMB),
        ("Avg Equity/GDP", f"{avg_eq_gdp:.0f}%", "Market capitalisation", _BLUE),
        ("Avg Govt Bond/GDP", f"{avg_gb_gdp:.0f}%", "Gross govt debt", _GRN),
    ]

    tiles = []
    for label, val, sub, clr in kpis:
        tiles.append(html.Div([
            html.Div(label, style={
                "fontSize": "10px", "color": _T2, "textTransform": "uppercase",
                "letterSpacing": ".08em", "marginBottom": "6px",
            }),
            html.Div(val, style={
                "fontSize": "24px", "fontWeight": "700", "color": clr, "lineHeight": "1",
            }),
            html.Div(sub, style={"fontSize": "11px", "color": _T3, "marginTop": "4px"}),
        ], style={
            "background": _CARD, "border": f"1px solid {_BORDER}",
            "borderTop": f"3px solid {clr}",
            "borderRadius": "10px", "padding": "16px 18px",
            "flex": "1", "minWidth": "140px",
            "boxShadow": "0 1px 3px rgba(0,0,0,0.04)",
        }))

    return _card_wrap([
        _section_label("Global Snapshot", f"Latest data — {year}"),
        html.Div(tiles, style={"display": "flex", "gap": "12px", "flexWrap": "wrap"}),
    ])


def _market_size(yr_df: pd.DataFrame, year: int) -> html.Div:
    df = yr_df.dropna(subset=["Equity_USD"]).sort_values("Total_Cap_USD", ascending=True)

    fig = go.Figure()
    fig.add_trace(go.Bar(
        name="Equity Market Cap", y=df["Country"], x=df["Equity_USD"],
        orientation="h", marker_color=_BLUE,
        hovertemplate="<b>%{y}</b><br>Equity: $%{x:.2f}T<extra></extra>",
    ))
    fig.add_trace(go.Bar(
        name="Govt Bond Market", y=df["Country"], x=df["GovtBond_USD"],
        orientation="h", marker_color=_GRN,
        hovertemplate="<b>%{y}</b><br>Govt Bonds: $%{x:.2f}T<extra></extra>",
    ))
    fig.update_layout(
        barmode="stack", height=400,
        title=dict(text=f"Capital Market Size by Country ({year})",
                   font=dict(size=14, color=_T1, weight="bold"), x=0),
        xaxis_title="USD Trillions",
        **_chart_layout(margin=dict(l=150, r=24, t=48, b=90)),
    )

    return _card_wrap([
        _section_label("Market Size Comparison",
                       "Equity market capitalisation vs government bond market outstanding"),
        dcc.Graph(figure=fig, config=_CHART_CONFIG, style={"borderRadius": "8px"}),
    ])


def _scatter_eq_bond(yr_df: pd.DataFrame, year: int) -> html.Div:
    df = yr_df.dropna(subset=["Equity_USD", "GovtBond_USD", "GDP_USD"])
    max_gdp = df["GDP_USD"].max()

    fig = go.Figure()
    for _, row in df.iterrows():
        fig.add_trace(go.Scatter(
            x=[row["Equity_USD"]], y=[row["GovtBond_USD"]],
            mode="markers+text",
            name=row["Country"],
            text=[row["Country"]],
            textposition="top center",
            textfont=dict(size=11, color=_T1),
            marker=dict(
                color=COUNTRY_COLORS.get(row["Country"], "#888"),
                size=max(10, row["GDP_USD"] / max_gdp * 65),
                opacity=0.8,
                line=dict(width=2, color=_CARD),
            ),
            showlegend=False,
            hovertemplate=(
                f"<b>{row['Country']}</b><br>"
                f"Equity: ${row['Equity_USD']:.2f}T<br>"
                f"Govt Bonds: ${row['GovtBond_USD']:.2f}T<br>"
                f"GDP: ${row['GDP_USD']:.2f}T<extra></extra>"
            ),
        ))

    mx = max(df["Equity_USD"].max(), df["GovtBond_USD"].max()) * 1.1
    fig.add_trace(go.Scatter(
        x=[0, mx], y=[0, mx], mode="lines",
        line=dict(color=_BORDER, dash="dot", width=1.5),
        showlegend=True, name="Equal (Equity = Bonds)",
    ))
    fig.update_layout(
        height=480,
        title=dict(text=f"Equity vs Govt Bond Markets ({year}) — bubble ∝ GDP",
                   font=dict(size=14, color=_T1, weight="bold"), x=0),
        xaxis_title="Equity Market Cap (USD T)",
        yaxis_title="Govt Bond Market (USD T)",
        **_chart_layout(),
    )

    return _card_wrap([
        _section_label("Equity vs Bond Markets",
                       "X = equity market cap · Y = govt bond market · bubble size = GDP"),
        dcc.Graph(figure=fig, config=_CHART_CONFIG),
        html.Div(
            "Countries above the dotted line have larger bond markets than equity markets — "
            "Japan is the signature case. Countries below are equity-dominant (USA, India).",
            style={"fontSize": "12px", "color": _T2, "marginTop": "10px",
                   "background": _PLOT, "padding": "10px 14px", "borderRadius": "6px",
                   "border": f"1px solid {_BORDER}"},
        ),
    ])


def _equity_gdp(yr_df: pd.DataFrame, year: int) -> html.Div:
    df = yr_df.dropna(subset=["Equity_GDP_Pct"]).sort_values("Equity_GDP_Pct")
    fig = go.Figure(go.Bar(
        x=df["Equity_GDP_Pct"], y=df["Country"],
        orientation="h",
        marker_color=_country_colors(df["Country"].tolist()),
        hovertemplate="<b>%{y}</b><br>Equity/GDP: %{x:.0f}%<extra></extra>",
    ))
    fig.add_vline(x=100, line=dict(color=_T3, dash="dot", width=1.5),
                  annotation_text="100% of GDP",
                  annotation_font=dict(color=_T3, size=10))
    fig.update_layout(
        height=340, showlegend=False,
        title=dict(text=f"Equity Market Cap / GDP ({year})",
                   font=dict(size=13, color=_T1, weight="bold"), x=0),
        xaxis_title="Equity Market Cap as % of GDP",
        **_chart_layout(margin=dict(l=140, r=24, t=48, b=44)),
    )
    return _card_wrap([
        _section_label("Equity / GDP", "How large is the stock market vs the economy?"),
        dcc.Graph(figure=fig, config=_CHART_CONFIG),
    ])


def _govtbond_gdp(yr_df: pd.DataFrame, year: int) -> html.Div:
    df = yr_df.dropna(subset=["GovtBond_GDP_Pct"]).sort_values("GovtBond_GDP_Pct")
    fig = go.Figure(go.Bar(
        x=df["GovtBond_GDP_Pct"], y=df["Country"],
        orientation="h",
        marker_color=_country_colors(df["Country"].tolist()),
        hovertemplate="<b>%{y}</b><br>Govt Bond/GDP: %{x:.0f}%<extra></extra>",
    ))
    fig.add_vline(x=100, line=dict(color=_AMB, dash="dot", width=1.5),
                  annotation_text="100% of GDP",
                  annotation_font=dict(color=_AMB, size=10))
    fig.update_layout(
        height=340, showlegend=False,
        title=dict(text=f"Govt Bond Market / GDP ({year})",
                   font=dict(size=13, color=_T1, weight="bold"), x=0),
        xaxis_title="Govt Bond Outstanding as % of GDP",
        **_chart_layout(margin=dict(l=140, r=24, t=48, b=44)),
    )
    return _card_wrap([
        _section_label("Govt Bond / GDP",
                       "Japan's government bond market is larger than its GDP — twice over"),
        dcc.Graph(figure=fig, config=_CHART_CONFIG),
    ])


def _total_ranking(yr_df: pd.DataFrame, year: int) -> html.Div:
    df = yr_df.dropna(subset=["Total_Cap_USD"]).sort_values("Total_Cap_USD")
    fig = go.Figure()
    fig.add_trace(go.Bar(
        name="Equity", y=df["Country"], x=df["Equity_USD"],
        orientation="h", marker_color=_BLUE,
        hovertemplate="<b>%{y}</b><br>Equity: $%{x:.2f}T<extra></extra>",
    ))
    fig.add_trace(go.Bar(
        name="Govt Bonds", y=df["Country"], x=df["GovtBond_USD"],
        orientation="h", marker_color=_GRN,
        hovertemplate="<b>%{y}</b><br>Bonds: $%{x:.2f}T<extra></extra>",
    ))
    fig.update_layout(
        barmode="stack", height=380,
        title=dict(text=f"Total Capital Market Size — Ranked ({year})",
                   font=dict(size=14, color=_T1, weight="bold"), x=0),
        xaxis_title="USD Trillions",
        **_chart_layout(margin=dict(l=150, r=24, t=48, b=90)),
    )
    return _card_wrap([
        _section_label("Total Capital Market Ranking",
                       "Equity + Government Bonds — who has the largest combined market?"),
        dcc.Graph(figure=fig, config=_CHART_CONFIG),
    ])


def _historical(hist_df: pd.DataFrame) -> html.Div:
    charts = []

    for title, col, ylab in [
        ("Equity Market Cap — 2005 to 2023",              "Equity_USD",   "USD Trillions"),
        ("Govt Bond Market — 2005 to 2023",               "GovtBond_USD", "USD Trillions"),
    ]:
        fig = go.Figure()
        for country in hist_df["Country"].unique():
            cdf = hist_df[hist_df["Country"] == country].dropna(subset=[col])
            if cdf.empty:
                continue
            fig.add_trace(go.Scatter(
                x=cdf["Year"], y=cdf[col], name=country, mode="lines+markers",
                marker=dict(size=5),
                line=dict(color=COUNTRY_COLORS.get(country, "#888"), width=2),
                hovertemplate=f"<b>{country}</b><br>%{{x}}: $%{{y:.2f}}T<extra></extra>",
            ))
        fig.update_layout(
            height=340,
            title=dict(text=title, font=dict(size=13, color=_T1, weight="bold"), x=0),
            yaxis_title=ylab,
            **_chart_layout(margin=dict(l=60, r=24, t=48, b=130)),
        )
        charts.append(dbc.Col(dcc.Graph(figure=fig, config=_CHART_CONFIG), width=6))

    # Total capital markets — full width
    fig_total = go.Figure()
    for country in hist_df["Country"].unique():
        cdf = hist_df[hist_df["Country"] == country].dropna(subset=["Total_Cap_USD"])
        if cdf.empty:
            continue
        fig_total.add_trace(go.Scatter(
            x=cdf["Year"], y=cdf["Total_Cap_USD"], name=country, mode="lines+markers",
            marker=dict(size=6),
            line=dict(color=COUNTRY_COLORS.get(country, "#888"), width=2.5),
            hovertemplate=f"<b>{country}</b><br>%{{x}}: $%{{y:.2f}}T<extra></extra>",
        ))
    fig_total.update_layout(
        height=380,
        title=dict(
            text="Total Capital Markets (Equity + Govt Bonds) — 2005 to 2023",
            font=dict(size=14, color=_T1, weight="bold"), x=0,
        ),
        yaxis_title="USD Trillions",
        **_chart_layout(margin=dict(l=60, r=24, t=48, b=130)),
    )

    return _card_wrap([
        _section_label("Historical Evolution",
                       "Use the Year slider to explore a specific snapshot, or track trends below"),
        dbc.Row(charts, style={"marginBottom": "16px"}),
        dcc.Graph(figure=fig_total, config=_CHART_CONFIG),
    ])


def _ratios_and_bubble(yr_df: pd.DataFrame, year: int) -> html.Div:
    df = yr_df.dropna(subset=["Bond_Equity_Ratio"]).sort_values("Bond_Equity_Ratio")
    fig_ratio = go.Figure(go.Bar(
        x=df["Bond_Equity_Ratio"], y=df["Country"],
        orientation="h",
        marker_color=_country_colors(df["Country"].tolist()),
        hovertemplate="<b>%{y}</b><br>Bond/Equity: %{x:.2f}×<extra></extra>",
    ))
    fig_ratio.add_vline(x=1, line=dict(color=_AMB, dash="dot", width=1.5),
                        annotation_text="Bond = Equity",
                        annotation_font=dict(color=_AMB, size=10))
    fig_ratio.update_layout(
        height=340, showlegend=False,
        title=dict(text=f"Govt Bond / Equity Ratio ({year})",
                   font=dict(size=13, color=_T1, weight="bold"), x=0),
        xaxis_title="Govt Bond Market ÷ Equity Market",
        **_chart_layout(margin=dict(l=150, r=24, t=48, b=44)),
    )

    df2 = yr_df.dropna(subset=["GDP_USD", "Total_Cap_USD", "Population"])
    max_pop = df2["Population"].max()
    fig_bubble = go.Figure()
    for _, row in df2.iterrows():
        fig_bubble.add_trace(go.Scatter(
            x=[row["GDP_USD"]], y=[row["Total_Cap_USD"]],
            mode="markers+text", name=row["Country"],
            text=[row["Country"]], textposition="top center",
            textfont=dict(size=10, color=_T1),
            marker=dict(
                color=COUNTRY_COLORS.get(row["Country"], "#888"),
                size=max(10, row["Population"] / max_pop * 55),
                opacity=0.8, line=dict(width=2, color=_CARD),
            ),
            showlegend=False,
            hovertemplate=(
                f"<b>{row['Country']}</b><br>"
                f"GDP: ${row['GDP_USD']:.2f}T<br>"
                f"Total Capital: ${row['Total_Cap_USD']:.2f}T<br>"
                f"Pop: {row['Population']/1e6:.0f}M<extra></extra>"
            ),
        ))
    mx = max(df2["GDP_USD"].max(), df2["Total_Cap_USD"].max()) * 1.1
    fig_bubble.add_trace(go.Scatter(
        x=[0, mx], y=[0, mx], mode="lines",
        line=dict(color=_BORDER, dash="dot", width=1.5), showlegend=False,
    ))
    fig_bubble.update_layout(
        height=340,
        title=dict(
            text=f"GDP vs Total Capital Market — bubble ∝ population ({year})",
            font=dict(size=13, color=_T1, weight="bold"), x=0,
        ),
        xaxis_title="GDP (USD T)",
        yaxis_title="Total Capital Market (USD T)",
        **_chart_layout(),
    )

    return _card_wrap([
        _section_label("Ratios & Bubbles",
                       "The Bond/Equity ratio reveals a country's financing model at a glance"),
        dbc.Row([
            dbc.Col(dcc.Graph(figure=fig_ratio,  config=_CHART_CONFIG), width=6),
            dbc.Col(dcc.Graph(figure=fig_bubble, config=_CHART_CONFIG), width=6),
        ]),
    ])


def _dna_table(yr_df: pd.DataFrame) -> html.Div:
    rows = []
    for _, row in yr_df.sort_values("Total_Cap_USD", ascending=False).iterrows():
        rows.append({
            "Country":         row["Country"],
            "GDP ($T)":        f"{row['GDP_USD']:.2f}" if pd.notna(row["GDP_USD"]) else "—",
            "Equity ($T)":     f"{row['Equity_USD']:.2f}" if pd.notna(row["Equity_USD"]) else "—",
            "Govt Bonds ($T)": f"{row['GovtBond_USD']:.2f}" if pd.notna(row["GovtBond_USD"]) else "—",
            "Equity/GDP":      f"{row['Equity_GDP_Pct']:.0f}%" if pd.notna(row["Equity_GDP_Pct"]) else "—",
            "Bond/GDP":        f"{row['GovtBond_GDP_Pct']:.0f}%" if pd.notna(row["GovtBond_GDP_Pct"]) else "—",
            "Bond/Equity":     f"{row['Bond_Equity_Ratio']:.2f}×" if pd.notna(row["Bond_Equity_Ratio"]) else "—",
            "Financing Model": FINANCING_MODEL.get(row["Country"], "—"),
        })

    cols = ["Country", "GDP ($T)", "Equity ($T)", "Govt Bonds ($T)",
            "Equity/GDP", "Bond/GDP", "Bond/Equity", "Financing Model"]

    table = dash_table.DataTable(
        data=rows,
        columns=[{"name": c, "id": c} for c in cols],
        sort_action="native",
        filter_action="native",
        style_table={"overflowX": "auto", "borderRadius": "8px", "border": f"1px solid {_BORDER}"},
        style_header={
            "background":   "#f1f5f9",
            "color":        _T1,
            "fontWeight":   "600",
            "fontSize":     "12px",
            "border":       f"1px solid {_BORDER}",
            "textAlign":    "left",
            "padding":      "8px 14px",
        },
        style_cell={
            "background":  _CARD,
            "color":        _T1,
            "fontSize":     "12px",
            "border":       f"1px solid {_BORDER}",
            "padding":      "8px 14px",
            "textAlign":    "left",
        },
        style_data_conditional=[
            {"if": {"row_index": "odd"}, "background": "#f8fafc"},
        ],
        page_size=12,
    )

    notes = [
        ("Market-based", "USA, UK, Canada, Australia — companies raise money through markets, not banks."),
        ("Bank-based",   "Germany — companies rely on bank loans; listed equity market is relatively small."),
        ("Govt debt-heavy", "Japan — govt bond market dwarfs everything else; bond/equity > 2×."),
        ("State-led",    "China — large markets but government-directed; rapid growth from 2005 base."),
        ("Mixed / developing", "India, Brazil, France — growing equity markets, high govt debt, deepening."),
    ]
    note_divs = [
        html.Div([
            html.Strong(label + ": ", style={"color": _T1}),
            html.Span(desc, style={"color": _T2}),
        ], style={"fontSize": "12px", "marginBottom": "4px"})
        for label, desc in notes
    ]

    return _card_wrap([
        _section_label("Capital Markets DNA",
                       "Each country's financial structure — sortable and filterable"),
        table,
        html.Div(note_divs, style={
            "marginTop": "16px", "background": _PLOT, "padding": "14px 16px",
            "borderRadius": "6px", "border": f"1px solid {_BORDER}",
        }),
    ])


# ── Run ────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("\n  Bond Analytics — Global Capital Markets (Dash / Light theme)")
    print("  ─────────────────────────────────────────────────────────────")
    print("  http://localhost:8051\n")
    print("  Chart toolbar: zoom · pan · box-zoom · scroll-zoom · download PNG · reset\n")
    app.run(debug=False, port=8051)
