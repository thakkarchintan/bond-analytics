"""
Data Sources catalog — admin view.
All datasets used in Bond Analytics: coverage, freshness, source, and alternatives.
"""
from __future__ import annotations

import datetime as dt
import pathlib

import pandas as pd
import streamlit as st

_HERE = pathlib.Path(__file__).parent

# ── Catalog definition ─────────────────────────────────────────────────────────
# Each entry: static metadata. Date ranges are loaded live from the parquet.

_CATALOG = [
    # ── FRED (current) ─────────────────────────────────────────────────────────
    {
        "group":       "FRED — Federal Reserve Economic Data",
        "name":        "US Treasury Yield Curve",
        "cache":       "gmacro_us_curve_cache.parquet",
        "date_col":    "Date",
        "pages":       ["Global Yield Curves"],
        "frequency":   "Daily",
        "coverage":    "United States · 11 maturities (1M–30Y)",
        "source_url":  "https://fred.stlouisfed.org",
        "notes":       "FRED DGS series (constant-maturity Treasury yields). Highly current.",
        "lag_type":    "structural",
        "alternatives":"US Treasury direct (same data); Bloomberg (paid)",
    },
    {
        "group":       "FRED — Federal Reserve Economic Data",
        "name":        "Breakeven Inflation & TIPS Real Yields",
        "cache":       "gmacro_breakeven_cache.parquet",
        "date_col":    "Date",
        "pages":       ["Inflation & Growth"],
        "frequency":   "Daily",
        "coverage":    "United States · 5Y/10Y breakeven, 5-10Y forward, 5Y/10Y real yield",
        "source_url":  "https://fred.stlouisfed.org",
        "notes":       "FRED T5YIE, T10YIE, T5YIFR, DFII5, DFII10. Fed's preferred inflation expectations.",
        "lag_type":    "structural",
        "alternatives":"Cleveland Fed inflation expectations model (daily, model-based)",
    },
    {
        "group":       "FRED — Federal Reserve Economic Data",
        "name":        "Cross-Asset (VIX · WTI Crude · S&P 500)",
        "cache":       "gmacro_cross_asset_cache.parquet",
        "date_col":    "Date",
        "pages":       ["Cross-Asset Dashboard"],
        "frequency":   "Daily",
        "coverage":    "United States · 3 series",
        "source_url":  "https://fred.stlouisfed.org",
        "notes":       "VIXCLS, DCOILWTICO, SP500. Gold (GOLDAMGBD228NLBM) and ISM PMI (NAPM) both 404 on FRED CSV.",
        "lag_type":    "structural",
        "alternatives":"Yahoo Finance (same data, no auth); Alpha Vantage (paid for intraday)",
    },
    {
        "group":       "FRED — Federal Reserve Economic Data",
        "name":        "FX Spot Rates vs USD",
        "cache":       "gmacro_fx_cache.parquet",
        "date_col":    "Date",
        "pages":       ["FX & Currencies"],
        "frequency":   "Daily",
        "coverage":    "14 currencies vs USD (EUR, GBP, JPY, CNY, INR, BRL, KRW, MXN, AUD, CAD, CHF, NOK, SEK, ZAR)",
        "source_url":  "https://fred.stlouisfed.org",
        "notes":       "FRED H.10 bilateral exchange rates. ~1 week lag for some EM pairs.",
        "lag_type":    "structural",
        "alternatives":"ECB reference rates (EUR pairs, daily); BIS (cross-rates); Open Exchange Rates API",
    },
    {
        "group":       "FRED — Federal Reserve Economic Data",
        "name":        "US Leading Indicators",
        "cache":       "gmacro_leading_cache.parquet",
        "date_col":    "Date",
        "pages":       ["Leading Indicators"],
        "frequency":   "Weekly / Monthly",
        "coverage":    "United States · 7 series (Claims, Sentiment, Housing, INDPRO, Unemployment, 2Y10Y, NBER Recession)",
        "source_url":  "https://fred.stlouisfed.org",
        "notes":       "Initial claims weekly; others monthly. USREC is NBER recession indicator (lagged by definition).",
        "lag_type":    "structural",
        "alternatives":"Conference Board LEI (monthly, broader composite); BLS direct feeds",
    },
    {
        "group":       "FRED — Federal Reserve Economic Data",
        "name":        "Money Market Rates (SOFR · Fed Funds)",
        "cache":       "gmacro_mmkt_cache.parquet",
        "date_col":    "Date",
        "pages":       ["Central Bank Rates"],
        "frequency":   "Daily",
        "coverage":    "United States · 2 series",
        "source_url":  "https://fred.stlouisfed.org",
        "notes":       "SOFR (SOFR series), Effective Fed Funds Rate (DFF). SOFR since 2018.",
        "lag_type":    "structural",
        "alternatives":"NY Fed direct (SOFR official source); CME (SOFR futures-implied)",
    },
    {
        "group":       "FRED — Federal Reserve Economic Data",
        "name":        "ICE BofA OAS Credit Spreads",
        "cache":       "gmacro_spreads_cache.parquet",
        "date_col":    "Date",
        "pages":       ["Credit Spreads", "Cross-Asset Dashboard"],
        "frequency":   "Daily",
        "coverage":    "US market · 9 series (AAA/AA/A/BBB/BB/B/CCC/IG/HY)",
        "source_url":  "https://fred.stlouisfed.org",
        "notes":       "FRED redistributes ICE BofA indices. Start date 2023-08-07 (FRED series launch date in cache).",
        "lag_type":    "structural",
        "alternatives":"ICE BofA Index Tool (paid); Bloomberg BAML indices (paid); S&P LCD (loans)",
    },
    {
        "group":       "FRED — Federal Reserve Economic Data",
        "name":        "10Y Government Bond Yields (Multi-Country)",
        "cache":       "gmacro_yields_cache.parquet",
        "date_col":    "Date",
        "pages":       ["Central Bank Rates"],
        "frequency":   "Monthly",
        "coverage":    "11 countries (US, UK, Euro Area, Japan, Canada, Australia, Norway, Sweden, S.Korea, NZ, CH)",
        "source_url":  "https://fred.stlouisfed.org",
        "notes":       "FRED IRLT (OECD long-term rates) for DMs. Monthly average. US uses DGS10 daily → monthly.",
        "lag_type":    "structural",
        "alternatives":"OECD.Stat (same IRLT data, possibly fresher); ECB SDW (Euro Area daily); national CBs",
    },
    {
        "group":       "FRED — Federal Reserve Economic Data",
        "name":        "CB Policy Rates Direct (US · Euro Area)",
        "cache":       "gmacro_cb_rates_cache.parquet",
        "date_col":    "Date",
        "pages":       ["Central Bank Rates"],
        "frequency":   "Monthly",
        "coverage":    "United States · Euro Area",
        "source_url":  "https://fred.stlouisfed.org",
        "notes":       "Fallback when BIS CBPOL is unavailable. FRED FEDFUNDS + ECB SDW MRO rate.",
        "lag_type":    "structural",
        "alternatives":"BIS WS_CBPOL (primary; 25 CBs); BoE directly for GBP",
    },
    # ── ECB ────────────────────────────────────────────────────────────────────
    {
        "group":       "ECB — European Central Bank",
        "name":        "Euro Area AAA Govt Bond Yield Curve",
        "cache":       "dbn_ecb_yc_cache.parquet",
        "date_col":    "Date",
        "pages":       ["Global Yield Curves"],
        "frequency":   "Daily",
        "coverage":    "Euro Area · 8 maturities (3M · 6M · 1Y · 2Y · 5Y · 10Y · 20Y · 30Y)",
        "source_url":  "https://www.ecb.europa.eu/stats/financial_markets_and_interest_rates/euro_area_yield_curves",
        "notes":       "ECB Svensson model spot rates. Restricted to AAA-rated euro area sovereign bonds. Via DBnomics ECB/YC.",
        "lag_type":    "structural",
        "alternatives":"ECB SDW direct API (same data, same day); Refinitiv/Bloomberg (paid, intraday)",
    },
    # ── BIS (via DBnomics) ─────────────────────────────────────────────────────
    {
        "group":       "BIS — Bank for International Settlements",
        "name":        "Central Bank Policy Rates",
        "cache":       "dbn_cbpol_cache.parquet",
        "date_col":    "Date",
        "pages":       ["Central Bank Rates"],
        "frequency":   "Daily",
        "coverage":    "25 central banks (Fed, ECB, BoE, BoJ, PBoC, RBI, BCB, SARB + 17 others)",
        "source_url":  "https://www.bis.org/statistics/cbpol.htm",
        "notes":       "BIS WS_CBPOL dataset. History back to 1946 for some CBs. ~1 month lag. Via DBnomics.",
        "lag_type":    "structural",
        "alternatives":"FRED (US only, daily); ECB SDW (Euro Area, daily); BoE (UK, daily); individual CB websites",
    },
    {
        "group":       "BIS — Bank for International Settlements",
        "name":        "Central Bank Total Assets (Balance Sheets)",
        "cache":       "dbn_cbta_cache.parquet",
        "date_col":    "Date",
        "pages":       ["Central Bank Rates"],
        "frequency":   "Monthly",
        "coverage":    "8 central banks (Fed, ECB, BoJ, BoE, PBoC, SNB, BoC, RBA) · USD bn",
        "source_url":  "https://www.bis.org/statistics/",
        "notes":       "BIS WS_CBTA. ~3–4 month lag (BIS release schedule). Longest history back to 1914 (Fed).",
        "lag_type":    "structural",
        "alternatives":"Individual CB balance sheet releases (same lag); Fed H.4.1 (weekly, US only); ECB weekly",
    },
    {
        "group":       "BIS — Bank for International Settlements",
        "name":        "Real Effective Exchange Rates (REER)",
        "cache":       "dbn_eer_cache.parquet",
        "date_col":    "Date",
        "pages":       ["FX & Currencies"],
        "frequency":   "Monthly",
        "coverage":    "14 currencies (USD/EUR/GBP/JPY/CNY/AUD/CAD/CHF/KRW/INR/BRL/NOK/SEK/MXN) · 2020=100",
        "source_url":  "https://www.bis.org/statistics/eer.htm",
        "notes":       "BIS WS_EER real broad basket (up to 64 economies, trade-weighted). ~2 month lag. Via DBnomics.",
        "lag_type":    "structural",
        "alternatives":"IMF REER (IFS dataset, similar methodology); Darvas broad REER (academic, broader)",
    },
    # ── OECD (via DBnomics) ────────────────────────────────────────────────────
    {
        "group":       "OECD — Organisation for Economic Co-operation and Development",
        "name":        "Business / Consumer / Composite Leading Indicators (BCI · CCI · CLI)",
        "cache":       "dbn_oecd_bc_cache.parquet",
        "date_col":    "Date",
        "pages":       ["Leading Indicators", "Global Business Cycle"],
        "frequency":   "Monthly",
        "coverage":    "29 countries + OECD aggregates · BCI (29) · CCI (27) · CLI (16)",
        "source_url":  "https://stats.oecd.org/",
        "notes":       "OECD DP_LIVE via DBnomics. DBnomics mirror is ~3 years stale (Nov 2023). Direct OECD.Stat API returns 403. LTRENDIDX: 100 = long-run trend.",
        "lag_type":    "fixable",
        "alternatives":"OECD.Stat direct (same data, current — but API access issues); FRED has some OECD CLI series (USALOLITONOSW etc.) — US/G7 only, but current",
    },
    # ── IMF ────────────────────────────────────────────────────────────────────
    {
        "group":       "IMF — International Monetary Fund",
        "name":        "World Economic Outlook (WEO) — Annual Macro",
        "cache":       "gmacro_annual_cache.parquet",
        "date_col":    None,
        "pages":       ["Global Macro Dashboard", "Central Bank Rates", "Fiscal Scorecard", "Inflation & Growth"],
        "frequency":   "Annual",
        "coverage":    "16 countries · GDP · CPI · Fiscal balance · Debt/GDP · Current account · Unemployment",
        "source_url":  "https://www.imf.org/en/Publications/WEO",
        "notes":       "IMF WEO API. Annual data; projections 2–3 years ahead. Updated twice yearly (Apr/Oct).",
        "lag_type":    "structural",
        "alternatives":"World Bank WDI (similar annual macro, broader country coverage); OECD Economic Outlook (OECD members only)",
    },
    # ── Internal ───────────────────────────────────────────────────────────────
    {
        "group":       "Internal / Manual",
        "name":        "Global Capital Markets",
        "cache":       "capital_markets_cache.parquet",
        "date_col":    None,
        "pages":       ["Global Capital Markets"],
        "frequency":   "Annual",
        "coverage":    "10 countries · Equity mkt cap · Govt bond stock · Debt/GDP · Listed companies",
        "source_url":  None,
        "notes":       "Manually curated from World Bank, SIFMA, WFE, and IMF datasets. Static snapshot.",
        "lag_type":    "fixable",
        "alternatives":"World Bank GFDD (Global Financial Development Database); BIS debt securities statistics; SIFMA Research",
    },
]


# ── Freshness classification ───────────────────────────────────────────────────

def _freshness(cache_file: str, date_col: str | None) -> tuple[str | None, str, str, str]:
    """Returns (end_date_str, lag_str, badge_label, badge_color)."""
    path = _HERE / cache_file
    if not path.exists() or date_col is None:
        return None, "—", "No date", "#94a3b8"
    try:
        df = pd.read_parquet(path, columns=[date_col])
        end = pd.to_datetime(df[date_col]).max()
        lag_days = (dt.date.today() - end.date()).days
        end_str = end.strftime("%d %b %Y")
        if lag_days < 30:
            lag_str = f"{lag_days}d"
            return end_str, lag_str, "Current", "#10b981"
        elif lag_days < 180:
            months = round(lag_days / 30)
            return end_str, f"~{months}mo", "Lagged", "#f59e0b"
        elif lag_days < 365:
            months = round(lag_days / 30)
            return end_str, f"~{months}mo", "Stale", "#ef4444"
        else:
            months = round(lag_days / 30)
            years = lag_days / 365
            lag_str = f"~{years:.1f}yr" if years >= 2 else f"~{months}mo"
            return end_str, lag_str, "Stale", "#ef4444"
    except Exception:
        return None, "—", "Unknown", "#94a3b8"


def _rows(cache_file: str) -> str:
    path = _HERE / cache_file
    if not path.exists():
        return "—"
    try:
        df = pd.read_parquet(path)
        n = len(df)
        return f"{n:,}"
    except Exception:
        return "—"


# ── Styles ────────────────────────────────────────────────────────────────────

_CSS = """
<style>
.ds-header  { font-size: 22px; font-weight: 700; color: #0f172a; margin-bottom: 4px; }
.ds-sub     { font-size: 13px; color: #64748b; margin-bottom: 20px; }
.ds-group   { font-size: 11px; font-weight: 700; text-transform: uppercase;
              letter-spacing: .1em; color: #94a3b8; margin: 24px 0 8px; }
.ds-card    { border: 1px solid #e2e8f0; border-radius: 10px; padding: 14px 18px;
              margin-bottom: 10px; background: #ffffff; }
.ds-name    { font-size: 14px; font-weight: 600; color: #0f172a; margin-bottom: 4px; }
.ds-meta    { font-size: 12px; color: #475569; line-height: 1.6; }
.ds-badge   { display: inline-block; padding: 2px 9px; border-radius: 4px;
              font-size: 11px; font-weight: 600; margin-right: 6px; }
.ds-alt     { font-size: 11px; color: #64748b; margin-top: 6px;
              border-top: 1px solid #f1f5f9; padding-top: 6px; }
.ds-fixable { font-size: 10px; font-weight: 600; color: #d97706;
              background: #fffbeb; border: 1px solid #fde68a;
              border-radius: 3px; padding: 1px 6px; margin-left: 4px; }
</style>
"""

_FRESHNESS_ICON = {"Current": "🟢", "Lagged": "🟡", "Stale": "🔴", "No date": "⚪", "Unknown": "⚪"}
_LAG_NOTE = {"structural": "Source releases on this schedule — no faster alternative.",
             "fixable":    "Fresher data may be available — see alternatives."}


def data_sources() -> None:
    st.markdown(_CSS, unsafe_allow_html=True)
    st.markdown('<div class="ds-header">Data Sources — Bond Analytics</div>', unsafe_allow_html=True)
    st.markdown(
        f'<div class="ds-sub">Admin view · {len(_CATALOG)} datasets · '
        f'Freshness computed live from cached parquets · '
        f'🟢 Current (&lt;30d) &nbsp; 🟡 Lagged (1–6mo) &nbsp; 🔴 Stale (&gt;6mo)</div>',
        unsafe_allow_html=True,
    )

    # ── Filters ───────────────────────────────────────────────────────────────
    col_f1, col_f2 = st.columns([2, 2])
    with col_f1:
        groups = ["All"] + sorted(set(d["group"] for d in _CATALOG))
        sel_group = st.selectbox("Filter by source", groups, key="ds_group")
    with col_f2:
        freshness_opts = ["All", "🟢 Current", "🟡 Lagged", "🔴 Stale"]
        sel_fresh = st.selectbox("Filter by freshness", freshness_opts, key="ds_fresh")

    filtered = _CATALOG if sel_group == "All" else [d for d in _CATALOG if d["group"] == sel_group]

    # ── Group and render ──────────────────────────────────────────────────────
    current_group = None
    shown = 0
    for entry in filtered:
        end_str, lag_str, badge, color = _freshness(entry["cache"], entry["date_col"])

        # Apply freshness filter
        if sel_fresh != "All":
            want = sel_fresh.split(" ", 1)[1]  # "Current", "Lagged", "Stale"
            if badge != want:
                continue

        shown += 1
        if entry["group"] != current_group:
            current_group = entry["group"]
            st.markdown(f'<div class="ds-group">{current_group}</div>', unsafe_allow_html=True)

        icon = _FRESHNESS_ICON.get(badge, "⚪")
        pages_str = " · ".join(entry["pages"])
        fixable_html = (
            '<span class="ds-fixable">fixable lag</span>'
            if entry["lag_type"] == "fixable" else ""
        )
        alt_html = (
            f'<div class="ds-alt">💡 <b>Alternatives:</b> {entry["alternatives"]}</div>'
            if entry.get("alternatives") else ""
        )
        src_link = (
            f'<a href="{entry["source_url"]}" target="_blank" '
            f'style="color:#3b82f6;text-decoration:none;">{entry["source_url"].split("//")[1].split("/")[0]}</a>'
            if entry.get("source_url") else "Internal"
        )
        row_count = _rows(entry["cache"])
        end_display = end_str or "N/A (no date col)"

        st.markdown(
            f"""
            <div class="ds-card">
              <div class="ds-name">
                {icon} &nbsp;{entry["name"]}
                {fixable_html}
              </div>
              <div class="ds-meta">
                <span class="ds-badge" style="background:{color}22;color:{color};">{badge} · {lag_str}</span>
                <span class="ds-badge" style="background:#f1f5f9;color:#475569;">{entry["frequency"]}</span>
                &nbsp; <b>End:</b> {end_display} &nbsp;·&nbsp; <b>Rows:</b> {row_count}
              </div>
              <div class="ds-meta" style="margin-top:5px;">
                <b>Pages:</b> {pages_str} &nbsp;·&nbsp; <b>Source:</b> {src_link}
              </div>
              <div class="ds-meta" style="margin-top:4px;color:#64748b;">
                <b>Coverage:</b> {entry["coverage"]}
              </div>
              <div class="ds-meta" style="margin-top:4px;color:#64748b;font-style:italic;">
                {entry["notes"]}
              </div>
              {alt_html}
            </div>
            """,
            unsafe_allow_html=True,
        )

    if shown == 0:
        st.info("No datasets match the current filters.")

    # ── Summary table ─────────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("**Quick reference table**")
    rows = []
    for entry in _CATALOG:
        end_str, lag_str, badge, _ = _freshness(entry["cache"], entry["date_col"])
        rows.append({
            "Dataset":     entry["name"],
            "Source":      entry["group"].split("—")[0].strip(),
            "Frequency":   entry["frequency"],
            "Data end":    end_str or "Annual",
            "Lag":         lag_str,
            "Freshness":   badge,
            "Lag type":    entry["lag_type"].title(),
            "Pages":       ", ".join(entry["pages"]),
        })
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
