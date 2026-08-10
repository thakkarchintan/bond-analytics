"""
Credit Spreads — Dash prototype
Run alongside the Streamlit app to compare frameworks:
    python credit_spreads_dash.py   →  http://localhost:8050

Reads from the same gmacro_spreads_cache.parquet the Streamlit app uses.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

import dash
from dash import dcc, html, Input, Output, callback, dash_table
import dash_bootstrap_components as dbc

# ── Palette ────────────────────────────────────────────────────────────────────
_BG   = "#0f172a"
_CARD = "#1e293b"
_EDGE = "#334155"
_T1   = "#f1f5f9"
_T2   = "#94a3b8"
_T3   = "#475569"
_BLUE = "#3b82f6"
_GRN  = "#10b981"
_RED  = "#ef4444"
_AMB  = "#f59e0b"
_PRP  = "#8b5cf6"

SPREAD_COLORS: dict[str, str] = {
    "AAA": "#60a5fa", "AA":  "#34d399", "A":   "#a3e635",
    "BBB": "#fbbf24", "IG":  "#818cf8", "BB":  "#fb923c",
    "B":   "#f87171", "HY":  "#f472b6", "CCC": "#ef4444",
}
RATING_ORDER = ["AAA", "AA", "A", "BBB", "IG", "BB", "B", "HY", "CCC"]

_RECESSIONS = [
    ("2001-03-01", "2001-11-01"),
    ("2007-12-01", "2009-06-01"),
    ("2020-02-01", "2020-04-01"),
]

HERE  = Path(__file__).parent
CACHE = HERE / "gmacro_spreads_cache.parquet"

# ── Data ───────────────────────────────────────────────────────────────────────

def load_df() -> pd.DataFrame:
    if not CACHE.exists():
        return pd.DataFrame(columns=["Date", "Series", "OAS_Pct"])
    df = pd.read_parquet(CACHE)
    df["Date"] = pd.to_datetime(df["Date"])
    return df


def get_snapshot(df: pd.DataFrame) -> pd.DataFrame:
    latest = df.sort_values("Date").groupby("Series").last().reset_index()
    one_yr_ago = (
        df[df["Date"] <= df["Date"].max() - pd.DateOffset(years=1)]
        .sort_values("Date")
        .groupby("Series")
        .last()
        .reset_index()
        .rename(columns={"OAS_Pct": "OAS_1Y"})
    )
    snap = latest.merge(one_yr_ago[["Series", "OAS_1Y"]], on="Series", how="left")
    snap["Change"] = snap["OAS_Pct"] - snap["OAS_1Y"]
    return snap


# ── Chart helpers ──────────────────────────────────────────────────────────────

_CHART_BASE = dict(
    paper_bgcolor=_CARD,
    plot_bgcolor=_BG,
    font=dict(family="Inter, system-ui, sans-serif", color=_T1, size=12),
    margin=dict(l=60, r=24, t=44, b=44),
    xaxis=dict(gridcolor=_EDGE, tickfont=dict(color=_T2),
               showline=True, linecolor=_EDGE, zerolinecolor=_EDGE),
    yaxis=dict(gridcolor=_EDGE, tickfont=dict(color=_T2),
               showline=True, linecolor=_EDGE, zerolinecolor=_EDGE),
    hoverlabel=dict(bgcolor=_CARD, font_color=_T1, bordercolor=_EDGE),
    legend=dict(
        font=dict(color=_T1, size=11),
        bgcolor="rgba(0,0,0,0)",
        orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1,
    ),
)


def _add_recessions(fig: go.Figure) -> None:
    for start, end in _RECESSIONS:
        fig.add_vrect(
            x0=start, x1=end,
            fillcolor="#334155", opacity=0.35,
            layer="below", line_width=0,
        )


# ── App initialise ─────────────────────────────────────────────────────────────

app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    title="Credit Spreads — Dash | Bond Analytics",
    suppress_callback_exceptions=True,
)

# ── Sidebar ────────────────────────────────────────────────────────────────────

_sidebar_style = {
    "position":   "fixed",
    "top":        0,
    "left":       0,
    "bottom":     0,
    "width":      "240px",
    "padding":    "24px 16px",
    "background": _CARD,
    "borderRight": f"1px solid {_EDGE}",
    "overflowY":  "auto",
    "zIndex":     1000,
}

_content_style = {
    "marginLeft": "240px",
    "padding":    "28px 32px",
    "background": _BG,
    "minHeight":  "100vh",
}

sidebar = html.Div([

    # App brand
    html.Div([
        html.Div("Bond Analytics", style={
            "fontSize": "13px", "fontWeight": "700", "color": _BLUE,
            "letterSpacing": ".06em", "textTransform": "uppercase",
        }),
        html.Div("Credit Spreads", style={
            "fontSize": "18px", "fontWeight": "700", "color": _T1,
            "marginTop": "2px",
        }),
        html.Div("ICE BofA OAS via FRED", style={
            "fontSize": "10px", "color": _T3, "marginTop": "2px",
        }),
    ], style={"marginBottom": "28px"}),

    html.Hr(style={"borderColor": _EDGE, "margin": "0 0 20px"}),

    # Ratings multiselect
    html.Div("RATINGS", style={
        "fontSize": "10px", "fontWeight": "700", "color": _T3,
        "textTransform": "uppercase", "letterSpacing": ".1em",
        "marginBottom": "8px",
    }),
    dcc.Checklist(
        id="ratings-check",
        options=[{"label": html.Span(r, style={"color": SPREAD_COLORS.get(r, _T1),
                                                "fontWeight": "600", "fontSize": "13px",
                                                "marginLeft": "6px"}),
                  "value": r}
                 for r in RATING_ORDER],
        value=["IG", "BBB", "HY", "BB"],
        style={"display": "flex", "flexDirection": "column", "gap": "6px"},
        inputStyle={"accentColor": _BLUE},
    ),

    html.Hr(style={"borderColor": _EDGE, "margin": "20px 0"}),

    # Year slider
    html.Div("FROM YEAR", style={
        "fontSize": "10px", "fontWeight": "700", "color": _T3,
        "textTransform": "uppercase", "letterSpacing": ".1em",
        "marginBottom": "12px",
    }),
    dcc.Slider(
        id="yr-slider",
        min=2000, max=2025, step=1, value=2008,
        marks={y: {"label": str(y), "style": {"color": _T2, "fontSize": "10px"}}
               for y in [2000, 2005, 2010, 2015, 2020, 2025]},
        tooltip={"placement": "bottom", "always_visible": True},
    ),

    html.Hr(style={"borderColor": _EDGE, "margin": "20px 0"}),

    # Data info
    html.Div("DATA", style={
        "fontSize": "10px", "fontWeight": "700", "color": _T3,
        "textTransform": "uppercase", "letterSpacing": ".1em",
        "marginBottom": "8px",
    }),
    html.Div(id="cache-info", style={"fontSize": "11px", "color": _T2}),

    html.Hr(style={"borderColor": _EDGE, "margin": "20px 0"}),

    # Nav note
    html.Div([
        html.Div("Other pages", style={"fontSize": "10px", "color": _T3,
                                        "textTransform": "uppercase",
                                        "letterSpacing": ".1em", "marginBottom": "10px"}),
        html.Div("← This is a Dash prototype.", style={"fontSize": "11px", "color": _T2}),
        html.Div("The full app runs in Streamlit.", style={"fontSize": "11px", "color": _T2,
                                                            "marginTop": "4px"}),
    ]),

], style=_sidebar_style)


# ── Main content ───────────────────────────────────────────────────────────────

content = html.Div([

    # Page header
    html.Div([
        html.H2("Credit Spreads", style={
            "color": _T1, "fontWeight": "700", "marginBottom": "2px", "fontSize": "22px",
        }),
        html.Div(
            "Option-adjusted spread (OAS) across the credit spectrum · "
            "Source: ICE BofA Bond Indices via FRED",
            style={"fontSize": "12px", "color": _T2, "marginBottom": "20px"},
        ),
    ]),

    # KPI snapshot row
    html.Div(id="kpi-cards", style={"marginBottom": "24px"}),

    # Tabs
    dcc.Tabs(
        id="main-tabs",
        value="history",
        children=[
            dcc.Tab(label="📈  Spread History",   value="history"),
            dcc.Tab(label="📊  Credit Spectrum",  value="spectrum"),
            dcc.Tab(label="🔍  IG vs HY",         value="ighy"),
        ],
        colors={"border": _EDGE, "primary": _BLUE, "background": _CARD},
        style={"borderBottom": f"1px solid {_EDGE}"},
        content_style={"background": _BG, "paddingTop": "24px"},
        parent_style={"marginBottom": "0"},
    ),

    # Tab content
    html.Div(id="tab-content"),

    # Footer
    html.Div([
        html.Hr(style={"borderColor": _EDGE}),
        html.Div(
            "Data: ICE BofA US Corporate and High Yield OAS indices via FRED. "
            "IG = BAMLC0A0CM · HY = BAMLH0A0HYM2. "
            "Grey bands = NBER US recession periods.",
            style={"fontSize": "11px", "color": _T3},
        ),
    ], style={"marginTop": "40px"}),

], style=_content_style)


app.layout = html.Div([
    sidebar,
    content,
], style={"fontFamily": "Inter, system-ui, sans-serif", "background": _BG})


# ── Callbacks ──────────────────────────────────────────────────────────────────

@callback(
    Output("cache-info", "children"),
    Input("yr-slider", "value"),   # any trigger to initialise
)
def update_cache_info(_):
    if CACHE.exists():
        import os, datetime
        mtime = datetime.datetime.fromtimestamp(os.path.getmtime(CACHE))
        df = load_df()
        end = df["Date"].max().strftime("%d %b %Y") if not df.empty else "—"
        return [
            html.Div(f"Cached: {mtime.strftime('%d %b %Y')}"),
            html.Div(f"Data to: {end}"),
            html.Div(f"Rows: {len(df):,}"),
        ]
    return html.Div("Not cached", style={"color": _RED})


@callback(
    Output("kpi-cards", "children"),
    Input("ratings-check", "value"),
)
def update_kpi_cards(selected_ratings):
    df = load_df()
    if df.empty:
        return html.Div("No data", style={"color": _T2})

    snap = get_snapshot(df)
    cards = []
    for rating in ["IG", "BBB", "HY", "BB", "B", "CCC"]:
        row = snap[snap["Series"] == rating]
        if row.empty:
            continue
        oas = row.iloc[0]["OAS_Pct"]
        chg = row.iloc[0]["Change"]
        clr = SPREAD_COLORS.get(rating, "#888")
        chg_color = _GRN if chg <= 0 else _RED
        chg_str = f"{chg:+.0f} bp" if pd.notna(chg) else "—"
        is_selected = rating in (selected_ratings or [])

        cards.append(html.Div([
            html.Div(f"{rating} OAS", style={
                "fontSize": "10px", "color": _T2, "textTransform": "uppercase",
                "letterSpacing": ".08em", "marginBottom": "4px",
            }),
            html.Div(f"{oas:.0f}", style={
                "fontSize": "26px", "fontWeight": "700", "color": clr, "lineHeight": "1",
            }),
            html.Div("bp", style={"fontSize": "11px", "color": _T2}),
            html.Div(f"{chg_str} vs 1Y", style={
                "fontSize": "11px", "color": chg_color, "marginTop": "4px",
            }),
        ], style={
            "background": _CARD if is_selected else _BG,
            "border": f"1px solid {clr if is_selected else _EDGE}",
            "borderRadius": "8px",
            "padding": "12px 16px",
            "textAlign": "center",
            "minWidth": "100px",
            "flex": "1",
            "transition": "all 0.15s ease",
        }))

    return html.Div(cards, style={
        "display": "flex", "gap": "10px", "flexWrap": "wrap",
    })


@callback(
    Output("tab-content", "children"),
    Input("main-tabs", "value"),
    Input("ratings-check", "value"),
    Input("yr-slider", "value"),
)
def render_tab(tab, selected_ratings, yr_from):
    df = load_df()
    if df.empty:
        return html.Div("No data available.", style={"color": _T2, "padding": "40px 0"})

    selected_ratings = selected_ratings or []

    if tab == "history":
        return _tab_history(df, selected_ratings, yr_from)
    elif tab == "spectrum":
        return _tab_spectrum(df)
    elif tab == "ighy":
        return _tab_ighy(df, yr_from)
    return html.Div()


# ── Tab renderers ──────────────────────────────────────────────────────────────

def _section_header(title: str, subtitle: str = "") -> html.Div:
    return html.Div([
        html.Div(title, style={
            "fontSize": "13px", "fontWeight": "700", "color": _T1,
            "textTransform": "uppercase", "letterSpacing": ".08em",
        }),
        html.Div(subtitle, style={"fontSize": "12px", "color": _T2, "marginTop": "3px"}),
    ], style={
        "background": _CARD, "borderLeft": f"4px solid {_BLUE}",
        "padding": "10px 16px", "marginBottom": "16px",
        "borderRadius": "0 8px 8px 0",
    })


def _tab_history(df: pd.DataFrame, selected: list[str], yr_from: int) -> html.Div:
    fdf = df[
        df["Series"].isin(selected) & (df["Date"].dt.year >= yr_from)
    ].copy()

    fig = go.Figure()
    _add_recessions(fig)

    for s in [r for r in RATING_ORDER if r in selected]:
        sdf = fdf[fdf["Series"] == s].sort_values("Date")
        if sdf.empty:
            continue
        fig.add_trace(go.Scatter(
            x=sdf["Date"], y=sdf["OAS_Pct"], name=s,
            mode="lines",
            line=dict(color=SPREAD_COLORS.get(s, "#888"), width=2),
            hovertemplate=f"<b>{s}</b><br>%{{x|%d %b %Y}}: %{{y:.0f}} bp<extra></extra>",
        ))

    fig.update_layout(
        height=460,
        title=dict(text="Credit Spreads — OAS (basis points)",
                   font=dict(size=13, color=_T1), x=0),
        yaxis_title="OAS (bp)",
        **_CHART_BASE,
    )

    return html.Div([
        _section_header(
            "Spread History",
            "OAS (option-adjusted spread) over US Treasuries — grey bands = NBER recessions",
        ),
        dcc.Graph(figure=fig, config={"displayModeBar": False}),
        html.Div(
            "Option-adjusted spread (OAS) = yield of the bond index minus the equivalent-maturity "
            "Treasury yield, in basis points. A widening spread signals rising credit risk or risk-off sentiment.",
            style={"fontSize": "12px", "color": _T2, "marginTop": "12px",
                   "background": _CARD, "padding": "10px 14px", "borderRadius": "6px"},
        ),
    ])


def _tab_spectrum(df: pd.DataFrame) -> html.Div:
    latest = (
        df[df["Series"].isin(RATING_ORDER)]
        .sort_values("Date")
        .groupby("Series")
        .last()
        .reset_index()
    )
    ordered = [r for r in RATING_ORDER if r in latest["Series"].values]
    y_vals  = [latest.loc[latest["Series"] == r, "OAS_Pct"].iloc[0] for r in ordered]
    colors  = [SPREAD_COLORS.get(r, "#888") for r in ordered]

    fig_bar = go.Figure(go.Bar(
        x=ordered, y=y_vals,
        marker_color=colors,
        text=[f"{v:.0f} bp" for v in y_vals],
        textposition="outside",
        textfont=dict(color=_T1, size=11),
        hovertemplate="<b>%{x}</b>: %{y:.0f} bp<extra></extra>",
    ))
    fig_bar.add_shape(
        type="line", x0=-0.5, x1=3.5, y0=0, y1=0,
        line=dict(color=_AMB, dash="dot", width=1.5),
    )
    fig_bar.add_annotation(
        x=3.5, y=0, text="IG / HY boundary",
        font=dict(color=_AMB, size=10), showarrow=False, yshift=10,
    )
    fig_bar.update_layout(
        height=400,
        title=dict(text="Current Spread by Rating Bucket (bp)",
                   font=dict(size=13, color=_T1), x=0),
        yaxis_title="OAS (bp)",
        showlegend=False,
        **_CHART_BASE,
    )

    # Table data
    table_rows = []
    for r, v in zip(ordered, y_vals):
        clr = SPREAD_COLORS.get(r, "#888")
        table_rows.append({"Rating": r, "OAS (bp)": f"{v:.0f}"})

    ig_row  = latest[latest["Series"] == "IG"]
    hy_row  = latest[latest["Series"] == "HY"]
    ratio_card = html.Div()
    if not ig_row.empty and not hy_row.empty:
        ig_oas = ig_row.iloc[0]["OAS_Pct"]
        hy_oas = hy_row.iloc[0]["OAS_Pct"]
        ratio  = hy_oas / ig_oas if ig_oas > 0 else 0
        ratio_card = html.Div([
            html.Div("HY / IG Ratio", style={
                "fontSize": "10px", "color": _T2, "textTransform": "uppercase",
                "letterSpacing": ".08em",
            }),
            html.Div(f"{ratio:.1f}×", style={
                "fontSize": "28px", "fontWeight": "700", "color": _AMB,
            }),
            html.Div(f"IG = {ig_oas:.0f} bp · HY = {hy_oas:.0f} bp",
                     style={"fontSize": "11px", "color": _T2}),
        ], style={
            "background": _CARD, "border": f"1px solid {_EDGE}", "borderRadius": "8px",
            "padding": "14px 18px", "marginTop": "16px",
        })

    return html.Div([
        _section_header(
            "Credit Risk Spectrum",
            "Current spread by rating — from investment grade (left) to high yield (right)",
        ),
        dbc.Row([
            dbc.Col(dcc.Graph(figure=fig_bar, config={"displayModeBar": False}), width=8),
            dbc.Col([
                dash_table.DataTable(
                    data=table_rows,
                    columns=[{"name": c, "id": c} for c in ["Rating", "OAS (bp)"]],
                    style_table={"overflowX": "auto"},
                    style_header={
                        "background": _CARD, "color": _T2,
                        "fontWeight": "600", "fontSize": "11px",
                        "border": f"1px solid {_EDGE}",
                    },
                    style_cell={
                        "background": _BG, "color": _T1,
                        "fontSize": "12px", "border": f"1px solid {_EDGE}",
                        "padding": "6px 12px",
                    },
                ),
                ratio_card,
            ], width=4),
        ]),
        html.Div(
            "Investment grade (IG): rated BBB/Baa and above. "
            "High yield (HY): rated BB/Ba and below. "
            "The HY/IG ratio above 4× indicates stressed credit conditions.",
            style={"fontSize": "12px", "color": _T2, "marginTop": "16px",
                   "background": _CARD, "padding": "10px 14px", "borderRadius": "6px"},
        ),
    ])


def _tab_ighy(df: pd.DataFrame, yr_from: int) -> html.Div:
    ig_df = df[(df["Series"] == "IG") & (df["Date"].dt.year >= yr_from)].sort_values("Date")
    hy_df = df[(df["Series"] == "HY") & (df["Date"].dt.year >= yr_from)].sort_values("Date")

    if ig_df.empty or hy_df.empty:
        return html.Div("Insufficient data.", style={"color": _T2})

    # Absolute levels
    fig_lvl = go.Figure()
    _add_recessions(fig_lvl)
    for sdf, name in [(ig_df, "IG"), (hy_df, "HY")]:
        clr = SPREAD_COLORS[name]
        fig_lvl.add_trace(go.Scatter(
            x=sdf["Date"], y=sdf["OAS_Pct"], name=name,
            mode="lines", line=dict(color=clr, width=2),
            hovertemplate=f"<b>{name}</b><br>%{{x|%b %Y}}: %{{y:.0f}} bp<extra></extra>",
        ))
    fig_lvl.update_layout(
        height=360,
        title=dict(text="IG vs HY Spread Levels (bp)",
                   font=dict(size=13, color=_T1), x=0),
        yaxis_title="OAS (bp)",
        **_CHART_BASE,
    )

    # Ratio
    merged = ig_df[["Date", "OAS_Pct"]].merge(
        hy_df[["Date", "OAS_Pct"]], on="Date", suffixes=("_IG", "_HY")
    )
    merged["Ratio"] = merged["OAS_Pct_HY"] / merged["OAS_Pct_IG"]

    fig_ratio = go.Figure()
    _add_recessions(fig_ratio)
    fig_ratio.add_trace(go.Scatter(
        x=merged["Date"], y=merged["Ratio"],
        name="HY/IG Ratio", mode="lines",
        line=dict(color=_AMB, width=2),
        fill="tozeroy", fillcolor="rgba(245,158,11,0.05)",
        hovertemplate="HY/IG: <b>%{y:.2f}×</b><br>%{x|%b %Y}<extra></extra>",
    ))
    fig_ratio.add_hline(
        y=4, line=dict(color=_RED, dash="dot", width=1.5),
        annotation_text="Stress threshold (4×)",
        annotation_font=dict(color=_RED, size=10),
    )
    fig_ratio.update_layout(
        height=360,
        title=dict(text="HY / IG Spread Ratio (×)",
                   font=dict(size=13, color=_T1), x=0),
        yaxis_title="Ratio (×)",
        **_CHART_BASE,
    )

    return html.Div([
        _section_header(
            "IG vs HY Comparison",
            "Investment-grade vs high-yield spread relationship over time",
        ),
        dbc.Row([
            dbc.Col(dcc.Graph(figure=fig_lvl,   config={"displayModeBar": False}), width=6),
            dbc.Col(dcc.Graph(figure=fig_ratio, config={"displayModeBar": False}), width=6),
        ]),
        html.Div(
            "When HY and IG spreads widen simultaneously: broad risk-off. "
            "When HY widens but IG is stable: credit-specific stress in lower-quality issuers. "
            "The HY/IG ratio compresses during risk-on and blows out in crises (2008–09, Mar 2020).",
            style={"fontSize": "12px", "color": _T2, "marginTop": "16px",
                   "background": _CARD, "padding": "10px 14px", "borderRadius": "6px"},
        ),
    ])


# ── Run ────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("\n  Bond Analytics — Credit Spreads (Dash prototype)")
    print("  ──────────────────────────────────────────────────")
    print("  http://localhost:8050\n")
    app.run(debug=False, port=8050)
