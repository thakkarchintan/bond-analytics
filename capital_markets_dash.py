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
from dash import dcc, html, Input, Output, State, callback, dash_table, ctx
import dash_bootstrap_components as dbc
from datetime import date

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

# ── Bond Analytics data ────────────────────────────────────────────────────────

_BOND_DATA: pd.DataFrame | None = None

def _load_bond_data() -> pd.DataFrame:
    global _BOND_DATA
    if _BOND_DATA is None:
        xlsx = HERE / "Final.xlsx"
        if not xlsx.exists():
            _BOND_DATA = pd.DataFrame()
            return _BOND_DATA
        try:
            df = pd.read_excel(xlsx, sheet_name=0)
            df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
            df.dropna(subset=["Date"], inplace=True)
            _BOND_DATA = df
        except Exception as exc:
            print(f"[bond-data] load error: {exc}")
            _BOND_DATA = pd.DataFrame()
    return _BOND_DATA


_FORMULAS: dict[str, str] = {
    "Eurex 5-10 Spread":          "FGBLY - FGBMY",
    "Eurex 2-5 Spread":           "FGBMY - FGBSY",
    "Eurex 2-10 Spread":          "FGBLY - FGBSY",
    "Eurex 10-30 Spread":         "FGBXY - FGBLY",
    "Eurex 2-5-10 Fly":           "FGBLY - 2 * FGBMY + FGBSY",
    "Eurex 5-10-30 Fly":          "FGBXY - 2 * FGBLY + FGBMY",
    "US 5-10 Spread":             "US10Y - US5Y",
    "US 2-5 Spread":              "US5Y - US2Y",
    "US 2-10 Spread":             "US10Y - US2Y",
    "US 10-30 Spread":            "US30Y - US10Y",
    "US 2-5-10 Fly":              "US10Y - 2 * US5Y + US2Y",
    "US 5-10-30 Fly":             "US30Y - 2 * US10Y + US5Y",
    "Italian vs German 2Y":       "FBTSY - FGBSY",
    "Italian vs German 10Y":      "FBTPY - FGBLY",
    "Australian vs Canadian 10Y": "AUS10Y - CAD10Y",
    "French vs German 10Y":       "FOATY - FGBLY",
    "UK vs German 10Y":           "UK10Y - FGBLY",
    "UK vs Australian 10Y":       "UK10Y - AUS10Y",
    "US vs Australian 10Y":       "US10Y - AUS10Y",
    "Canadian vs US 2-5-10 Fly":  "CAD10Y - 2 * CAD5Y + CAD2Y - US10Y + 2 * US5Y - US2Y",
}

_INSTRUMENTS = [
    "FGBSY", "FGBMY", "FGBLY", "FGBXY",
    "US2Y", "US5Y", "US10Y", "US30Y",
    "EUR3M", "EUR1M", "EUR1W", "ESTR",
    "FBTSY", "FBTPY", "FOATY",
    "UK10Y", "AUS10Y", "AUS3Y",
    "CAD10Y", "CAD2Y", "CAD3Y", "CAD5Y", "CAD7Y",
    "AEX", "CAC40", "DIJA", "FDAX", "FSMI", "FTSE", "NQ", "SPX",
    "Gold (USD)", "BTC (USD)", "DJIA",
]

_BA_MIN = "1994-01-03"
_BA_MAX = "2025-11-06"

_CTRL_LBL = {
    "fontSize": "10px", "fontWeight": "700", "color": _T3,
    "textTransform": "uppercase", "letterSpacing": ".1em",
    "marginBottom": "6px", "marginTop": "14px",
}

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
        "position": "relative",   # anchor for the fullscreen button
    }
    if style:
        s.update(style)

    fs_btn = html.Button(
        "⛶",
        className="fs-btn",
        title="Fullscreen",
        style={
            "position":   "absolute",
            "top":        "14px",
            "right":      "14px",
            "background": "rgba(248,250,252,0.95)",
            "border":     f"1px solid {_BORDER}",
            "borderRadius": "5px",
            "padding":    "2px 8px",
            "cursor":     "pointer",
            "fontSize":   "15px",
            "color":      _T2,
            "lineHeight": "1.3",
            "zIndex":     "50",
        },
    )

    children_list = children if isinstance(children, list) else [children]
    return html.Div([fs_btn] + children_list, style=s, className="fs-card")


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


# ── Shared footer ─────────────────────────────────────────────────────────────

def _footer(note: str = "") -> html.Div:
    return html.Div([
        html.Hr(style={"borderColor": _BORDER}),
        html.Div(note or (
            html.Span([
                html.Strong("Data sources: "),
                "Capital Markets — World Bank / IMF. "
                "Bond Analytics — Final.xlsx (Eurex, US Treasuries, cross-country rates).",
            ])
        ), style={"fontSize": "11px", "color": _T3}),
    ], style={"marginTop": "40px"})


# ── Bond Analytics renderers ──────────────────────────────────────────────────

def _ba_render_spreads(start: str, end: str, ncols: int) -> html.Div:
    df = _load_bond_data()
    if df.empty:
        return html.Div("⚠ Final.xlsx not found. Place it in the same folder as this script.",
                        style={"color": _AMB, "padding": "40px 0"})

    filt = df[
        (df["Date"] >= pd.to_datetime(start)) &
        (df["Date"] <= pd.to_datetime(end))
    ].copy()

    if filt.empty:
        return html.Div("No data in selected date range.", style={"color": _AMB, "padding": "20px 0"})

    nc       = ncols or 2
    col_w    = 12 // nc
    chart_h  = {1: 500, 2: 420, 3: 360, 4: 300}.get(nc, 380)
    items    = list(_FORMULAS.items())
    rows_out = []

    for i in range(0, len(items), nc):
        cols_out = []
        for name, formula in items[i : i + nc]:
            try:
                filt["_v"] = filt.eval(formula)
            except Exception as exc:
                cols_out.append(dbc.Col(
                    html.Div(f"Error — {name}: {exc}",
                             style={"color": _RED, "fontSize": "12px", "padding": "12px"}),
                    width=col_w,
                ))
                continue

            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=filt["Date"], y=filt["_v"],
                mode="lines", name=name,
                line=dict(color=_BLUE, width=1.5),
                hovertemplate=f"<b>{name}</b><br>%{{x|%d %b %Y}}: %{{y:.4f}}<extra></extra>",
            ))
            fig.update_layout(
                height=chart_h,
                title=dict(text=name, font=dict(size=12, color=_BLUE, weight="bold"), x=0),
                showlegend=False,
                **_chart_layout(margin=dict(l=60, r=16, t=44, b=44)),
            )
            cols_out.append(dbc.Col(
                _card_wrap([dcc.Graph(figure=fig, config=_CHART_CONFIG)]),
                width=col_w,
            ))
        if cols_out:
            rows_out.append(dbc.Row(cols_out, className="g-3 mb-0"))

    return html.Div([
        _section_label("Bond Spreads & Flies",
                       "20 preset formulas — Eurex, US Treasuries, cross-country"),
        html.Div(rows_out),
    ])


def _ba_render_custom(
    analysis_type: str,
    instrument: str,
    formula: str | None,
    overlay_instr: str | None,
    overlay_formula: str | None,
    start: str,
    end: str,
) -> html.Div:
    df = _load_bond_data()
    if df.empty:
        return html.Div("⚠ Final.xlsx not found.", style={"color": _AMB})

    filt = df[
        (df["Date"] >= pd.to_datetime(start)) &
        (df["Date"] <= pd.to_datetime(end))
    ].copy()
    if filt.empty:
        return html.Div("No data in selected date range.", style={"color": _AMB})

    # ── Primary ───────────────────────────────────────────────────────────────
    if instrument == "custom":
        if not (formula or "").strip():
            return html.Div("Enter a custom formula and press Submit.", style={"color": _AMB})
        try:
            filt["Primary"] = filt.eval(formula.strip())
            primary_title = formula.strip()
        except Exception as exc:
            return html.Div(f"Formula error: {exc}", style={"color": _RED})
    else:
        if instrument not in filt.columns:
            return html.Div(f"Instrument '{instrument}' not in data.", style={"color": _RED})
        filt["Primary"] = filt[instrument]
        primary_title = instrument

    charts: list = []

    if analysis_type == "single":
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=filt["Date"], y=filt["Primary"],
            mode="lines", name=primary_title,
            line=dict(color=_BLUE, width=1.5),
        ))
        fig.update_layout(
            height=450,
            title=dict(text=primary_title, font=dict(size=13, color=_BLUE, weight="bold"), x=0),
            showlegend=False,
            **_chart_layout(margin=dict(l=60, r=16, t=48, b=44)),
        )
        charts.append(_card_wrap([
            _section_label("Level Chart", primary_title),
            dcc.Graph(figure=fig, config=_CHART_CONFIG),
        ]))

        filt["DailyChg"] = filt["Primary"].diff()
        fig_chg = go.Figure()
        fig_chg.add_trace(go.Bar(
            x=filt["Date"], y=filt["DailyChg"],
            name="Daily Change", marker_color=_BLUE,
        ))
        fig_chg.update_layout(
            height=340,
            title=dict(text=f"Daily Change — {primary_title}",
                       font=dict(size=12, color=_T1, weight="bold"), x=0),
            showlegend=False,
            **_chart_layout(margin=dict(l=60, r=16, t=44, b=44)),
        )
        charts.append(_card_wrap([
            _section_label("Daily Change"),
            dcc.Graph(figure=fig_chg, config=_CHART_CONFIG),
        ]))

    elif analysis_type == "overlay":
        if overlay_instr == "custom":
            if not (overlay_formula or "").strip():
                return html.Div("Enter an overlay formula and press Submit.", style={"color": _AMB})
            try:
                filt["Overlay"] = filt.eval(overlay_formula.strip())
                overlay_title = overlay_formula.strip()
            except Exception as exc:
                return html.Div(f"Overlay formula error: {exc}", style={"color": _RED})
        else:
            if overlay_instr not in filt.columns:
                return html.Div(f"Instrument '{overlay_instr}' not in data.", style={"color": _RED})
            filt["Overlay"] = filt[overlay_instr]
            overlay_title = overlay_instr or ""

        # dual-axis overlay
        base = _chart_layout(margin=dict(l=70, r=70, t=48, b=90))
        yax_base = base.pop("yaxis", {})
        base.pop("legend", None)

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=filt["Date"], y=filt["Primary"], mode="lines",
            name=primary_title, line=dict(color=_BLUE, width=1.5), yaxis="y1",
        ))
        fig.add_trace(go.Scatter(
            x=filt["Date"], y=filt["Overlay"], mode="lines",
            name=overlay_title, line=dict(color=_RED, width=1.5), yaxis="y2",
        ))
        fig.update_layout(
            height=480,
            title=dict(text=f"{primary_title}  vs  {overlay_title}",
                       font=dict(size=13, color=_T1, weight="bold"), x=0),
            **base,
        )
        fig.update_layout(
            yaxis={**yax_base,
                   "title": dict(text=primary_title, font=dict(color=_BLUE)),
                   "tickfont": dict(color=_BLUE)},
            yaxis2=dict(
                title=dict(text=overlay_title, font=dict(color=_RED)),
                tickfont=dict(color=_RED),
                overlaying="y", side="right", showgrid=False,
            ),
            legend=dict(
                orientation="h", yanchor="top", y=-0.14, xanchor="center", x=0.5,
                font=dict(color=_T2, size=11),
                bgcolor="rgba(255,255,255,0.8)", bordercolor=_BORDER, borderwidth=1,
            ),
        )
        charts.append(_card_wrap([
            _section_label("Overlay Chart", f"{primary_title} vs {overlay_title}"),
            dcc.Graph(figure=fig, config=_CHART_CONFIG),
        ]))

        for title_, col_, clr_ in [
            (f"Daily Change — {primary_title}", "Primary", _BLUE),
            (f"Daily Change — {overlay_title}",  "Overlay",  _RED),
        ]:
            filt[col_ + "Chg"] = filt[col_].diff()
            fig_c = go.Figure()
            fig_c.add_trace(go.Bar(
                x=filt["Date"], y=filt[col_ + "Chg"],
                name=title_, marker_color=clr_,
            ))
            fig_c.update_layout(
                height=320,
                title=dict(text=title_, font=dict(size=12, color=clr_, weight="bold"), x=0),
                showlegend=False,
                **_chart_layout(margin=dict(l=60, r=16, t=44, b=44)),
            )
            charts.append(_card_wrap([
                _section_label(title_),
                dcc.Graph(figure=fig_c, config=_CHART_CONFIG),
            ]))

    return html.Div(charts)


# ── App ────────────────────────────────────────────────────────────────────────

app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    title="Capital Markets — Dash | Bond Analytics",
    suppress_callback_exceptions=True,
)

# ── Sidebar ────────────────────────────────────────────────────────────────────

_SIDEBAR_W  = "260px"
_COLLAPSED_W = "44px"

_sidebar_style = {
    "position":   "fixed",
    "top":        0,
    "left":       0,
    "bottom":     0,
    "width":      _SIDEBAR_W,
    "padding":    "12px 18px 24px",
    "background": _SIDE,
    "borderRight": f"1px solid {_BORDER}",
    "overflowY":  "auto",
    "overflowX":  "hidden",
    "zIndex":     1000,
    "boxShadow":  "2px 0 8px rgba(0,0,0,0.06)",
    "transition": "width 0.22s ease, padding 0.22s ease",
}

_sidebar_collapsed = {
    **_sidebar_style,
    "width":   _COLLAPSED_W,
    "padding": "12px 6px 24px",
}

_content_style = {
    "marginLeft": _SIDEBAR_W,
    "padding":    "28px 32px",
    "background": _PAGE,
    "minHeight":  "100vh",
    "transition": "margin-left 0.22s ease",
}

_content_expanded = {
    **_content_style,
    "marginLeft": _COLLAPSED_W,
}

_TOGGLE_BTN_STYLE = {
    "width": "100%", "background": "none", "border": f"1px solid {_BORDER}",
    "borderRadius": "6px", "padding": "5px", "cursor": "pointer",
    "color": _T2, "fontSize": "15px", "lineHeight": "1",
    "marginBottom": "14px", "textAlign": "center",
    "transition": "background 0.15s",
}

_INPUT_STYLE = {
    "width": "100%", "fontSize": "12px", "padding": "5px 8px",
    "border": f"1px solid {_BORDER}", "borderRadius": "5px",
    "background": "#f8fafc", "color": _T1, "marginBottom": "8px",
    "boxSizing": "border-box",
}

_DD_STYLE = {"fontSize": "13px", "marginBottom": "8px"}

sidebar = html.Div([

    # Toggle button (always visible)
    html.Button("◀", id="cm-toggle", title="Collapse sidebar", style=_TOGGLE_BTN_STYLE),

    # Everything below is hidden when sidebar is collapsed
    html.Div(id="cm-sidebar-content", children=[

    # Brand
    html.Div([
        html.Div("Bond Analytics", style={
            "fontSize": "11px", "fontWeight": "700", "color": _BLUE,
            "letterSpacing": ".1em", "textTransform": "uppercase",
        }),
        html.Div("Dashboard", style={
            "fontSize": "20px", "fontWeight": "700", "color": _T1, "marginTop": "2px",
        }),
    ], style={"marginBottom": "14px"}),

    html.Hr(style={"borderColor": _BORDER, "margin": "0 0 10px"}),

    # ── Page selector ──────────────────────────────────────────────────────────
    html.Div("PAGE", style=_CTRL_LBL),
    dcc.Dropdown(
        id="cm-page",
        options=[
            {"label": "Bond Analytics",        "value": "bond"},
            {"label": "Global Capital Markets", "value": "capital"},
        ],
        value="bond",
        clearable=False,
        style={"fontSize": "13px", "marginBottom": "8px"},
        className="cm-dropdown",
    ),

    html.Hr(style={"borderColor": _BORDER, "margin": "12px 0"}),

    # ── Capital Markets controls (hidden by default) ────────────────────────────
    html.Div(id="cm-cap-controls", style={"display": "none"}, children=[

        html.Div("YEAR", style=_CTRL_LBL),
        dcc.Slider(
            id="cm-year",
            min=2005, max=2023, step=1, value=2023,
            marks={y: {"label": str(y), "style": {"color": _T3, "fontSize": "10px"}}
                   for y in [2005, 2010, 2015, 2020, 2023]},
            tooltip={"placement": "bottom", "always_visible": True},
        ),

        html.Hr(style={"borderColor": _BORDER, "margin": "16px 0 10px"}),

        html.Div("COUNTRIES", style=_CTRL_LBL),
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

        html.Hr(style={"borderColor": _BORDER, "margin": "16px 0 10px"}),

        html.Div("SECTIONS", style=_CTRL_LBL),
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

        html.Hr(style={"borderColor": _BORDER, "margin": "16px 0 10px"}),
        html.Div("💡 Tip: ⛶ button on each chart goes fullscreen.",
                 style={"fontSize": "11px", "color": _T3, "lineHeight": "1.5"}),

    ]),  # end cm-cap-controls

    # ── Bond Analytics controls (shown by default) ─────────────────────────────
    html.Div(id="cm-bond-controls", children=[

        html.Div("SECTION", style=_CTRL_LBL),
        dcc.Dropdown(
            id="ba-section",
            options=[
                {"label": "Bond Spreads & Flies",   "value": "spreads"},
                {"label": "Custom Formula Graphs",  "value": "custom"},
            ],
            value="spreads",
            clearable=False,
            style={"fontSize": "13px", "marginBottom": "8px"},
            className="cm-dropdown",
        ),

        html.Hr(style={"borderColor": _BORDER, "margin": "12px 0 8px"}),

        # Spreads controls
        html.Div(id="ba-spreads-controls", children=[
            html.Div("FROM DATE", style=_CTRL_LBL),
            dcc.Input(id="ba-start", type="date", value=_BA_MIN, style=_INPUT_STYLE),
            html.Div("TO DATE", style=_CTRL_LBL),
            dcc.Input(id="ba-end",   type="date", value=_BA_MAX, style=_INPUT_STYLE),
            html.Div("COLUMNS", style=_CTRL_LBL),
            dcc.Slider(id="ba-ncols", min=1, max=4, step=1, value=2,
                       marks={i: {"label": str(i), "style": {"color": _T3, "fontSize": "10px"}}
                              for i in range(1, 5)},
                       tooltip={"placement": "bottom", "always_visible": True}),
        ]),

        # Custom formula controls (hidden by default)
        html.Div(id="ba-custom-controls", style={"display": "none"}, children=[

            html.Div("ANALYSIS TYPE", style=_CTRL_LBL),
            dcc.Dropdown(
                id="ba-analysis-type",
                options=[
                    {"label": "Single",  "value": "single"},
                    {"label": "Overlay", "value": "overlay"},
                ],
                value="single",
                clearable=False,
                style={"fontSize": "13px", "marginBottom": "8px"},
                className="cm-dropdown",
            ),

            html.Div("PRIMARY INSTRUMENT", style=_CTRL_LBL),
            dcc.Dropdown(
                id="ba-instrument",
                options=(
                    [{"label": "Custom Formula", "value": "custom"}] +
                    [{"label": c, "value": c} for c in _INSTRUMENTS]
                ),
                value="US10Y", clearable=False, style=_DD_STYLE,
            ),
            html.Div(id="ba-formula-wrap", style={"display": "none"}, children=[
                html.Div("FORMULA  (e.g. US10Y - US2Y)", style=_CTRL_LBL),
                dcc.Textarea(id="ba-formula", value="",
                             style={**_INPUT_STYLE, "height": "56px", "resize": "vertical",
                                    "marginBottom": "8px"}),
            ]),

            # Overlay block
            html.Div(id="ba-overlay-wrap", style={"display": "none"}, children=[
                html.Div("OVERLAY INSTRUMENT", style=_CTRL_LBL),
                dcc.Dropdown(
                    id="ba-overlay-instr",
                    options=(
                        [{"label": "Custom Formula", "value": "custom"}] +
                        [{"label": c, "value": c} for c in _INSTRUMENTS]
                    ),
                    value="US2Y", clearable=False, style=_DD_STYLE,
                ),
                html.Div(id="ba-overlay-formula-wrap", style={"display": "none"}, children=[
                    html.Div("OVERLAY FORMULA", style=_CTRL_LBL),
                    dcc.Textarea(id="ba-overlay-formula", value="",
                                 style={**_INPUT_STYLE, "height": "56px", "resize": "vertical",
                                        "marginBottom": "8px"}),
                ]),
            ]),

            html.Div("FROM DATE", style=_CTRL_LBL),
            dcc.Input(id="ba-cust-start", type="date", value=_BA_MIN, style=_INPUT_STYLE),
            html.Div("TO DATE", style=_CTRL_LBL),
            dcc.Input(id="ba-cust-end",   type="date", value=_BA_MAX, style=_INPUT_STYLE),

            html.Button("Submit", id="ba-submit", n_clicks=0, style={
                "width": "100%", "background": _BLUE, "color": "white",
                "border": "none", "borderRadius": "6px", "padding": "9px",
                "cursor": "pointer", "fontWeight": "600", "fontSize": "13px",
                "marginTop": "10px",
            }),
        ]),  # end ba-custom-controls

    ]),  # end cm-bond-controls

    ]),  # end cm-sidebar-content

], id="cm-sidebar", style=_sidebar_style)


content = html.Div([

    # ── Capital Markets page (hidden by default) ───────────────────────────────
    html.Div([
        html.H2("Global Capital Markets Dashboard", style={
            "color": _T1, "fontWeight": "700", "fontSize": "22px", "marginBottom": "2px",
        }),
        html.Div(
            "10 countries · equity vs government bond markets · market size vs GDP · "
            "historical evolution 2005–2023",
            style={"fontSize": "12px", "color": _T2, "marginBottom": "24px"},
        ),
        html.Div(id="cm-cap-page-content"),
        _footer(
            "Data: Equity market capitalisation — World Bank. "
            "Govt bond size — IMF Gross Govt Debt × GDP. "
            "GDP — IMF World Economic Outlook."
        ),
    ], id="cm-cap-page", style={"display": "none"}),

    # ── Bond Analytics page (shown by default) ─────────────────────────────────
    html.Div([
        html.H2("Bond Analytics", style={
            "color": _T1, "fontWeight": "700", "fontSize": "22px", "marginBottom": "2px",
        }),
        html.Div(
            "Bond spreads & flies · custom formula charts · Eurex, US Treasuries, cross-country rates",
            style={"fontSize": "12px", "color": _T2, "marginBottom": "24px"},
        ),
        html.Div(id="ba-page-content"),
        _footer("Data: Final.xlsx — Eurex (FGBSY/MY/LY/XY), US Treasuries, EUR rates, cross-country govt bonds."),
    ], id="cm-bond-page"),

], id="cm-content", style=_content_style)


app.layout = html.Div(
    [sidebar, content],
    style={"fontFamily": "Inter, system-ui, sans-serif", "background": _PAGE},
)


# ── Sidebar toggle callback ────────────────────────────────────────────────────

@callback(
    Output("cm-sidebar",         "style"),
    Output("cm-content",         "style"),
    Output("cm-sidebar-content", "style"),
    Output("cm-toggle",          "children"),
    Output("cm-toggle",          "title"),
    Input("cm-toggle",           "n_clicks"),
    prevent_initial_call=True,
)
def toggle_sidebar(n):
    collapsed = bool(n and n % 2 == 1)
    if collapsed:
        return (
            _sidebar_collapsed,
            _content_expanded,
            {"display": "none"},
            "▶",
            "Expand sidebar",
        )
    return (
        _sidebar_style,
        _content_style,
        {},
        "◀",
        "Collapse sidebar",
    )


# ── Page switch callback ───────────────────────────────────────────────────────

@callback(
    Output("cm-cap-controls", "style"),
    Output("cm-bond-controls", "style"),
    Output("cm-cap-page",     "style"),
    Output("cm-bond-page",    "style"),
    Input("cm-page", "value"),
)
def switch_page(page: str):
    if page == "capital":
        return {}, {"display": "none"}, {}, {"display": "none"}
    return {"display": "none"}, {}, {"display": "none"}, {}


# ── Bond Analytics section switch ─────────────────────────────────────────────

@callback(
    Output("ba-spreads-controls", "style"),
    Output("ba-custom-controls",  "style"),
    Input("ba-section", "value"),
)
def switch_ba_section(section: str):
    if section == "custom":
        return {"display": "none"}, {}
    return {}, {"display": "none"}


# ── Bond Analytics conditional UI ─────────────────────────────────────────────

@callback(
    Output("ba-formula-wrap", "style"),
    Input("ba-instrument", "value"),
)
def toggle_primary_formula(instrument: str):
    return {} if instrument == "custom" else {"display": "none"}


@callback(
    Output("ba-overlay-wrap", "style"),
    Input("ba-analysis-type", "value"),
)
def toggle_overlay(analysis_type: str):
    return {} if analysis_type == "overlay" else {"display": "none"}


@callback(
    Output("ba-overlay-formula-wrap", "style"),
    Input("ba-overlay-instr", "value"),
)
def toggle_overlay_formula(instrument: str):
    return {} if instrument == "custom" else {"display": "none"}


# ── Bond Analytics main render ─────────────────────────────────────────────────

@callback(
    Output("ba-page-content", "children"),
    Input("ba-section",  "value"),
    Input("ba-start",    "value"),
    Input("ba-end",      "value"),
    Input("ba-ncols",    "value"),
    Input("ba-submit",   "n_clicks"),
    State("ba-analysis-type",     "value"),
    State("ba-instrument",        "value"),
    State("ba-formula",           "value"),
    State("ba-overlay-instr",     "value"),
    State("ba-overlay-formula",   "value"),
    State("ba-cust-start",        "value"),
    State("ba-cust-end",          "value"),
)
def render_bond_page(
    section, start, end, ncols, n_clicks,
    analysis_type, instrument, formula,
    overlay_instr, overlay_formula, cust_start, cust_end,
):
    tid = ctx.triggered_id

    if section == "spreads":
        if tid == "ba-submit":
            return dash.no_update
        return _ba_render_spreads(start or _BA_MIN, end or _BA_MAX, ncols or 2)

    if section == "custom":
        if tid == "ba-submit" and n_clicks:
            return _ba_render_custom(
                analysis_type or "single",
                instrument or "US10Y",
                formula,
                overlay_instr,
                overlay_formula,
                cust_start or _BA_MIN,
                cust_end   or _BA_MAX,
            )
        if tid in ("ba-section", None):
            return html.Div(
                "Configure options in the sidebar and press Submit to render charts.",
                style={"color": _T2, "textAlign": "center", "padding": "80px 0",
                       "fontSize": "14px"},
            )
        return dash.no_update

    return html.Div()


# ── Capital Markets callback ───────────────────────────────────────────────────

@callback(
    Output("cm-cap-page-content", "children"),
    Input("cm-year",      "value"),
    Input("cm-countries", "value"),
    Input("cm-sections",  "value"),
    Input("cm-page",      "value"),
)
def render_page(year: int, selected_countries: list[str], sections: list[str], page: str):
    if page != "capital":
        return dash.no_update
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

    if "eq_gdp" in sections:
        blocks.append(_equity_gdp(yr_df, year))
    if "gb_gdp" in sections:
        blocks.append(_govtbond_gdp(yr_df, year))

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
        height=380, showlegend=False,
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
        height=380, showlegend=False,
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
    cards = []

    for i, (title, col, ylab) in enumerate([
        ("Equity Market Cap — 2005 to 2023",  "Equity_USD",   "USD Trillions"),
        ("Govt Bond Market — 2005 to 2023",   "GovtBond_USD", "USD Trillions"),
    ]):
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
            height=380,
            title=dict(text=title, font=dict(size=13, color=_T1, weight="bold"), x=0),
            yaxis_title=ylab,
            **_chart_layout(margin=dict(l=60, r=24, t=48, b=130)),
        )
        label = _section_label(
            "Historical Evolution",
            "Use the Year slider to explore a specific snapshot, or track trends below",
        ) if i == 0 else None
        cards.append(_card_wrap(
            ([label] if label else []) + [dcc.Graph(figure=fig, config=_CHART_CONFIG)]
        ))

    # Total capital markets
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
        height=400,
        title=dict(
            text="Total Capital Markets (Equity + Govt Bonds) — 2005 to 2023",
            font=dict(size=14, color=_T1, weight="bold"), x=0,
        ),
        yaxis_title="USD Trillions",
        **_chart_layout(margin=dict(l=60, r=24, t=48, b=130)),
    )
    cards.append(_card_wrap([dcc.Graph(figure=fig_total, config=_CHART_CONFIG)]))

    return html.Div(cards)


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

    return html.Div([
        _card_wrap([
            _section_label("Ratios & Bubbles",
                           "The Bond/Equity ratio reveals a country's financing model at a glance"),
            dcc.Graph(figure=fig_ratio, config=_CHART_CONFIG),
        ]),
        _card_wrap([
            dcc.Graph(figure=fig_bubble, config=_CHART_CONFIG),
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
