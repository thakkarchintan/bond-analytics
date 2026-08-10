"""
Product Roadmap & Discussion Log — Bond Analytics
Tracks all architectural decisions, data source additions, and feature work discussed.
"""
from __future__ import annotations
import streamlit as st

# ── Palette (matches app) ──────────────────────────────────────────────────────
_BG   = "#0f172a"
_CARD = "#1e293b"
_EDGE = "#334155"
_T1   = "#f1f5f9"
_T2   = "#94a3b8"
_T3   = "#475569"
_BLUE = "#3b82f6"
_GRN  = "#10b981"
_AMB  = "#f59e0b"
_RED  = "#ef4444"
_PRP  = "#8b5cf6"
_CYN  = "#22d3ee"

_CSS = """
<style>
.rm-page-title  { font-size:24px;font-weight:700;color:#f1f5f9;margin-bottom:2px; }
.rm-page-sub    { font-size:13px;color:#94a3b8;margin-bottom:24px; }
.rm-section     { font-size:11px;font-weight:700;text-transform:uppercase;
                  letter-spacing:.12em;color:#94a3b8;margin:28px 0 10px;
                  border-bottom:1px solid #334155;padding-bottom:6px; }
.rm-card        { background:#1e293b;border:1px solid #334155;border-radius:10px;
                  padding:14px 18px;margin-bottom:10px; }
.rm-card-title  { font-size:14px;font-weight:600;color:#f1f5f9;margin-bottom:5px; }
.rm-card-body   { font-size:12px;color:#94a3b8;line-height:1.65; }
.rm-badge       { display:inline-block;padding:2px 9px;border-radius:4px;
                  font-size:10px;font-weight:700;margin-right:6px;letter-spacing:.04em; }
.rm-tag         { display:inline-block;padding:1px 7px;border-radius:3px;
                  font-size:10px;background:#0f172a;color:#64748b;
                  border:1px solid #334155;margin-right:4px; }
.rm-sub-item    { margin:5px 0 5px 14px;font-size:12px;color:#94a3b8; }
.rm-sub-item b  { color:#cbd5e1; }
.rm-note        { font-size:11px;color:#475569;margin-top:6px;font-style:italic; }
</style>
"""

# ── Status helpers ─────────────────────────────────────────────────────────────

def _badge(label: str, color: str) -> str:
    return f'<span class="rm-badge" style="background:{color}22;color:{color};">{label}</span>'

def _tag(label: str) -> str:
    return f'<span class="rm-tag">{label}</span>'

PROPOSED   = _badge("Proposed",    _BLUE)
IN_PROG    = _badge("In Progress", _AMB)
DONE       = _badge("Done",        _GRN)
IDEA       = _badge("Idea",        _PRP)
HIGH       = _badge("High",        _RED)
MEDIUM     = _badge("Medium",      _AMB)
LOW        = _badge("Low",         _T2)

# ── Item renderer ──────────────────────────────────────────────────────────────

def _card(title: str, status: str, priority: str, tags: list[str],
          body: str, note: str = "") -> str:
    tags_html = "".join(_tag(t) for t in tags)
    note_html = f'<div class="rm-note">💬 {note}</div>' if note else ""
    return (
        f'<div class="rm-card">'
        f'<div class="rm-card-title">{title}</div>'
        f'<div style="margin-bottom:8px;">{status}&nbsp;{priority}&nbsp;&nbsp;{tags_html}</div>'
        f'<div class="rm-card-body">{body}</div>'
        f'{note_html}'
        f'</div>'
    )


# ── Data ──────────────────────────────────────────────────────────────────────

SECTIONS = [

    # ── 1. ARCHITECTURE ───────────────────────────────────────────────────────
    {
        "title": "App Architecture",
        "items": [
            {
                "title": "Grouped navigation — replace flat 22-item selectbox",
                "status": PROPOSED, "priority": HIGH,
                "tags": ["UX", "Navigation"],
                "body": (
                    "Current: 22 pages in a flat sidebar selectbox — no hierarchy.<br>"
                    "Proposed: 6 labelled groups using <code>st.navigation()</code> or sidebar headers:<br>"
                    "<div class='rm-sub-item'>• <b>Country Intel</b> — Country Deep Dive, Country Compare</div>"
                    "<div class='rm-sub-item'>• <b>Global Markets</b> — Yield Curves, Credit Spreads, Cross-Asset, FX</div>"
                    "<div class='rm-sub-item'>• <b>Central Banks</b> — Policy Rates & Balance Sheets, Historical Shocks</div>"
                    "<div class='rm-sub-item'>• <b>Cycle & Growth</b> — Inflation & Leading Indicators, Business Cycle, Fiscal</div>"
                    "<div class='rm-sub-item'>• <b>Tools</b> — Spreads & RV, Curve Trade Builder, Bond Tools, Strategies</div>"
                    "<div class='rm-sub-item'>• <b>Portfolio</b> — Portfolio & Rebalance (merged)</div>"
                ),
                "note": "22 flat → 6 groups, 17 pages. Naming collision fixed: 'Bond Analytics' page renamed 'Spreads & Relative Value'.",
            },
            {
                "title": "Page consolidations — merge closely related pages",
                "status": PROPOSED, "priority": MEDIUM,
                "tags": ["UX", "Navigation"],
                "body": (
                    "Pairs that should become tabs within a single page:<br>"
                    "<div class='rm-sub-item'>• <b>Bond Calculator + Bond Simulator</b> → Bond Tools</div>"
                    "<div class='rm-sub-item'>• <b>Bond Portfolio + Bond Investment Strategies + Portfolio Rebalance + Correlation Matrix</b> → Portfolio</div>"
                    "<div class='rm-sub-item'>• <b>Global Macro Dashboard + Global Business Cycle</b> → Global Macro (both high-level global views)</div>"
                    "<div class='rm-sub-item'>• <b>Inflation & Growth + Leading Indicators</b> → Inflation & Cycle (logically sequential)</div>"
                    "<div class='rm-sub-item'>• <b>Central Bank Rates + Balance Sheets</b> → Central Banks (already share data)</div>"
                ),
                "note": "Lower urgency than navigation grouping. Reduces page count before merges add new ones.",
            },
            {
                "title": "Within-page content quality — standardise page layout",
                "status": PROPOSED, "priority": MEDIUM,
                "tags": ["UX", "Design"],
                "body": (
                    "Each page should follow the same content hierarchy:<br>"
                    "<div class='rm-sub-item'>1. <b>Key metrics row</b> — 3–5 KPI tiles, current state at a glance</div>"
                    "<div class='rm-sub-item'>2. <b>Primary chart</b> — the main story</div>"
                    "<div class='rm-sub-item'>3. <b>Supporting charts</b> — 2–3 contextual views</div>"
                    "<div class='rm-sub-item'>4. <b>Controls near the chart they affect</b> — not all dumped in sidebar</div>"
                    "<div class='rm-sub-item'>5. <b>Data table</b> — optional, collapsed by default</div>"
                    "Charts should tell a narrative, not just present data. Sidebar should only hold global filters."
                ),
            },
            {
                "title": "Evaluate Dash as replacement UI framework",
                "status": IN_PROG, "priority": HIGH,
                "tags": ["Framework", "Dash"],
                "body": (
                    "Streamlit limitations at current scale:<br>"
                    "<div class='rm-sub-item'>• No proper URL routing — can't bookmark a specific view</div>"
                    "<div class='rm-sub-item'>• Full page reruns on every interaction — performance degrades with many charts</div>"
                    "<div class='rm-sub-item'>• No synchronized/linked charts (click date on one → all update)</div>"
                    "<div class='rm-sub-item'>• Sidebar navigation becomes bottleneck as pages grow</div>"
                    "<div class='rm-sub-item'>• Poor mobile experience</div>"
                    "Dash advantages: proper routing, callbacks (only affected component rerenders), "
                    "CSS grid layout, linked charts, ~80% Plotly code reuse.<br><br>"
                    "<b>Action:</b> Credit Spreads page prototyped in Dash (<code>credit_spreads_dash.py</code>) — "
                    "run alongside Streamlit app to compare. Decision pending user review."
                ),
                "note": "Dash is already installed. Run: python credit_spreads_dash.py (port 8050)",
            },
        ],
    },

    # ── 2. NEW PAGES ──────────────────────────────────────────────────────────
    {
        "title": "New Pages to Build",
        "items": [
            {
                "title": "Country Deep Dive — single-country aggregated view",
                "status": PROPOSED, "priority": HIGH,
                "tags": ["New Page", "Country Intel"],
                "body": (
                    "Pick one country → see all available data in one view:<br>"
                    "<div class='rm-sub-item'>• Yield curve (current shape + history)</div>"
                    "<div class='rm-sub-item'>• CB policy rate history</div>"
                    "<div class='rm-sub-item'>• Realized CPI inflation vs breakeven expectations</div>"
                    "<div class='rm-sub-item'>• GDP growth (annual IMF → quarterly OECD when added)</div>"
                    "<div class='rm-sub-item'>• Fiscal position (debt/GDP, fiscal balance)</div>"
                    "<div class='rm-sub-item'>• FX spot + REER</div>"
                    "<div class='rm-sub-item'>• Commodity context overlay (oil for Norway/Canada, copper for Australia)</div>"
                    "Data already exists across 6+ caches — no new fetching needed for first version."
                ),
                "note": "Data coverage varies: US + Euro Area richest; EM countries only have annual IMF + FX.",
            },
            {
                "title": "Country Compare — multi-country, multi-metric overlay",
                "status": PROPOSED, "priority": HIGH,
                "tags": ["New Page", "Country Intel"],
                "body": (
                    "Metric-first navigation: <b>[Pick metric] × [Pick countries] × [Pick date range]</b><br><br>"
                    "Available metrics for comparison across countries:<br>"
                    "<div class='rm-sub-item'>• <b>CB Policy Rate</b> — 25 CBs (BIS), daily ✅</div>"
                    "<div class='rm-sub-item'>• <b>10Y Govt Bond Yield</b> — 11 countries (FRED/OECD), monthly ✅</div>"
                    "<div class='rm-sub-item'>• <b>10Y Yield (daily)</b> — 9 countries via Stooq (to add) 📋</div>"
                    "<div class='rm-sub-item'>• <b>GDP Growth</b> — 16 countries (IMF), annual ✅ → quarterly via OECD 📋</div>"
                    "<div class='rm-sub-item'>• <b>CPI Inflation</b> — 16 countries annual ✅ → monthly via Eurostat/FRED 📋</div>"
                    "<div class='rm-sub-item'>• <b>Debt/GDP + Fiscal Balance</b> — 16 countries (IMF) ✅</div>"
                    "<div class='rm-sub-item'>• <b>FX Spot vs USD</b> — 14 currencies (FRED), daily ✅</div>"
                    "<div class='rm-sub-item'>• <b>REER</b> — 14 currencies (BIS), monthly ✅</div>"
                    "<div class='rm-sub-item'>• <b>CB Balance Sheet</b> — 8 CBs (BIS), monthly ✅</div>"
                    "<div class='rm-sub-item'>• <b>Leading Indicators CLI</b> — 16 countries (OECD) ⚠️ stale</div>"
                ),
                "note": "This page is the primary reason to add Stooq daily yields and Eurostat/OECD monthly data.",
            },
        ],
    },

    # ── 3. DATA SOURCES — FRED ─────────────────────────────────────────────────
    {
        "title": "New Data — FRED (free, no API key, same fetch pattern)",
        "items": [
            {
                "title": "ACM Term Premium — NY Fed model",
                "status": PROPOSED, "priority": HIGH,
                "tags": ["FRED", "Rates", "Country Compare"],
                "body": (
                    "Adrian-Crump-Moench decomposition of the 10Y yield into expectations + term premium.<br>"
                    "Most-cited tool in fixed income macro for separating 'where rates are going' from "
                    "'extra compensation for duration risk'.<br>"
                    "<div class='rm-sub-item'>• <b>ACMTERM10</b> — 10Y term premium, daily, back to 1961</div>"
                    "<div class='rm-sub-item'>• <b>ACMTERM5</b> — 5Y term premium</div>"
                    "<div class='rm-sub-item'>• <b>ACMTERM2</b> — 2Y term premium</div>"
                    "<div class='rm-sub-item'>• <b>ACMTERM1</b> — 1Y term premium</div>"
                    "Fits: Yield Curves page (decomposition panel) + Country Deep Dive (US)."
                ),
            },
            {
                "title": "Realized Inflation — CPI & PCE components",
                "status": PROPOSED, "priority": HIGH,
                "tags": ["FRED", "Inflation", "Country Compare"],
                "body": (
                    "App has breakeven inflation expectations but not the realized print the Fed reacts to.<br>"
                    "<div class='rm-sub-item'>• <b>CPIAUCSL</b> — CPI All Items, monthly</div>"
                    "<div class='rm-sub-item'>• <b>CPILFESL</b> — Core CPI (ex food & energy), monthly</div>"
                    "<div class='rm-sub-item'>• <b>PCEPI</b> — PCE Deflator, monthly</div>"
                    "<div class='rm-sub-item'>• <b>PCEPILFE</b> — Core PCE — Fed's preferred measure ⭐</div>"
                    "<div class='rm-sub-item'>• <b>PPIACO</b> — PPI All Commodities (upstream inflation)</div>"
                    "Enables: expectations vs outcomes comparison, real-time Country Compare for US inflation."
                ),
            },
            {
                "title": "Chicago Fed Financial Conditions Index (NFCI)",
                "status": PROPOSED, "priority": HIGH,
                "tags": ["FRED", "Financial Conditions"],
                "body": (
                    "Single number summarising tightening/easing across rates, spreads, equity and FX. "
                    "Widely referenced in Fed communications and research.<br>"
                    "<div class='rm-sub-item'>• <b>NFCI</b> — weekly, back to 1971</div>"
                    "Fits: Cross-Asset Dashboard or Leading Indicators page."
                ),
            },
            {
                "title": "Fed Balance Sheet detail — weekly H.4.1",
                "status": PROPOSED, "priority": HIGH,
                "tags": ["FRED", "Central Banks", "QT/QE"],
                "body": (
                    "Currently have BIS monthly CB total assets. Fed's weekly H.4.1 is far more granular for tracking QT/QE pace.<br>"
                    "<div class='rm-sub-item'>• <b>WALCL</b> — Total assets, weekly</div>"
                    "<div class='rm-sub-item'>• <b>WSODL</b> — Treasury holdings (direct QT signal)</div>"
                    "<div class='rm-sub-item'>• <b>WSHOMCB</b> — MBS holdings (mortgage channel)</div>"
                    "<div class='rm-sub-item'>• <b>WRESBAL</b> — Bank reserves at Fed (liquidity signal)</div>"
                    "Fits: Central Banks page (new QT/QE panel)."
                ),
            },
            {
                "title": "Money Supply — M2",
                "status": PROPOSED, "priority": MEDIUM,
                "tags": ["FRED", "Monetary"],
                "body": (
                    "Missing entirely. Money supply growth vs nominal GDP is a foundational macro lens "
                    "and a leading indicator for inflation with a long lag.<br>"
                    "<div class='rm-sub-item'>• <b>M2SL</b> — M2, monthly, back to 1959</div>"
                    "<div class='rm-sub-item'>• <b>WM2NS</b> — Weekly M2 (less reliable but more timely)</div>"
                ),
            },
            {
                "title": "Money market curve — short-end rates",
                "status": PROPOSED, "priority": MEDIUM,
                "tags": ["FRED", "Rates"],
                "body": (
                    "SOFR and Fed Funds are in the app. Missing the rest of the USD front-end:<br>"
                    "<div class='rm-sub-item'>• <b>DTB3</b> — 3M T-bill, daily</div>"
                    "<div class='rm-sub-item'>• <b>DTB6</b> — 6M T-bill, daily</div>"
                    "<div class='rm-sub-item'>• <b>DTB1YR</b> — 1Y T-bill, daily</div>"
                    "Combined with existing DGS1–DGS30, gives a complete USD curve from overnight to 30Y."
                ),
            },
            {
                "title": "Labor market detail — wages, JOLTS, U-6",
                "status": PROPOSED, "priority": MEDIUM,
                "tags": ["FRED", "Labor", "Inflation"],
                "body": (
                    "Beyond headline claims + unemployment, the Fed watches:<br>"
                    "<div class='rm-sub-item'>• <b>CES0500000003</b> — Average Hourly Earnings YoY (wage inflation)</div>"
                    "<div class='rm-sub-item'>• <b>U6RATE</b> — Broad unemployment (true labor slack)</div>"
                    "<div class='rm-sub-item'>• <b>JTSJOL</b> — JOLTS Job Openings (leads wage growth)</div>"
                    "<div class='rm-sub-item'>• <b>JTSQUR</b> — Quits Rate (workers' confidence → wage bargaining)</div>"
                    "Fits: Leading Indicators / Inflation & Cycle page."
                ),
            },
            {
                "title": "Mortgage rates & bank lending standards",
                "status": PROPOSED, "priority": MEDIUM,
                "tags": ["FRED", "Housing", "Credit"],
                "body": (
                    "Rate transmission to real economy runs largely through housing — missing entirely:<br>"
                    "<div class='rm-sub-item'>• <b>MORTGAGE30US</b> — 30Y fixed mortgage rate, weekly since 1971</div>"
                    "<div class='rm-sub-item'>• <b>MORTGAGE15US</b> — 15Y fixed</div>"
                    "<div class='rm-sub-item'>• <b>DRSFRMACBS</b> — Senior Loan Officer Survey (SLOOS), quarterly</div>"
                    "Fits: Cross-Asset or a new Housing / Credit Transmission panel."
                ),
            },
            {
                "title": "Fiscal flows — monthly deficit & federal debt",
                "status": PROPOSED, "priority": MEDIUM,
                "tags": ["FRED", "Fiscal"],
                "body": (
                    "IMF WEO gives annual fiscal data. Monthly Treasury Statement adds real-time fiscal impulse:<br>"
                    "<div class='rm-sub-item'>• <b>MTSDS133FMS</b> — Monthly Treasury Statement: federal surplus/deficit</div>"
                    "<div class='rm-sub-item'>• <b>GFDEBTN</b> — Total federal debt outstanding, quarterly</div>"
                    "Fits: Fiscal Scorecard page."
                ),
            },
            {
                "title": "Consumer inflation expectations — Michigan survey",
                "status": PROPOSED, "priority": LOW,
                "tags": ["FRED", "Inflation Expectations"],
                "body": (
                    "<div class='rm-sub-item'>• <b>UMCSENT</b> — Michigan Consumer Sentiment, monthly</div>"
                    "<div class='rm-sub-item'>• <b>MICH</b> — Michigan 1Y inflation expectation</div>"
                    "<div class='rm-sub-item'>• <b>MICH5</b> — 5Y forward inflation expectation ⭐ (de-anchoring risk)</div>"
                    "Fits: Inflation & Growth / Leading Indicators page."
                ),
            },
        ],
    },

    # ── 4. DATA SOURCES — STOOQ ───────────────────────────────────────────────
    {
        "title": "New Data — Stooq (free, no API key, CSV download)",
        "items": [
            {
                "title": "Sovereign 10Y yields — daily for 8 countries",
                "status": PROPOSED, "priority": HIGH,
                "tags": ["Stooq", "Rates", "Country Compare"],
                "body": (
                    "Biggest single upgrade for Country Compare. Currently only US (FRED daily) and "
                    "Euro Area (ECB Svensson daily) have daily yield curves. All others are monthly OECD.<br>"
                    "<div class='rm-sub-item'>• <b>de10y.b</b> — Germany 10Y Bund (daily)</div>"
                    "<div class='rm-sub-item'>• <b>gb10y.b</b> — UK 10Y Gilt (daily)</div>"
                    "<div class='rm-sub-item'>• <b>jp10y.b</b> — Japan 10Y JGB (daily)</div>"
                    "<div class='rm-sub-item'>• <b>it10y.b</b> — Italy 10Y BTP (daily) — not in app at all</div>"
                    "<div class='rm-sub-item'>• <b>fr10y.b</b> — France 10Y OAT (daily) — not in app at all</div>"
                    "<div class='rm-sub-item'>• <b>es10y.b</b> — Spain 10Y (daily) — not in app at all</div>"
                    "<div class='rm-sub-item'>• <b>au10y.b</b> — Australia 10Y (daily)</div>"
                    "<div class='rm-sub-item'>• <b>ca10y.b</b> — Canada 10Y (daily)</div>"
                    "Same CSV fetch pattern as FRED. History back to mid-1990s."
                ),
                "note": "Stooq is blocked in the remote dev sandbox (proxy policy) but works from any normal server.",
            },
            {
                "title": "Commodities — Gold, Brent, Copper, Natural Gas",
                "status": PROPOSED, "priority": HIGH,
                "tags": ["Stooq", "Commodities", "Cross-Asset"],
                "body": (
                    "FRED returns 404 for Gold. Stooq fills the gap across all commodity sectors:<br>"
                    "<b>Energies:</b>"
                    "<div class='rm-sub-item'>• <b>cb.f</b> — Brent Crude (more relevant than WTI for EU/EM inflation)</div>"
                    "<div class='rm-sub-item'>• <b>ng.f</b> — Natural Gas (critical for 2021-23 EU energy crisis analysis)</div>"
                    "<b>Metals:</b>"
                    "<div class='rm-sub-item'>• <b>gc.f</b> — Gold (inverse proxy for real yields — app has TIPS real yield but not Gold)</div>"
                    "<div class='rm-sub-item'>• <b>hg.f</b> — Copper (Dr. Copper — leading indicator for global growth/credit cycle)</div>"
                    "<div class='rm-sub-item'>• <b>si.f</b> — Silver</div>"
                    "<b>Grains/Softs:</b>"
                    "<div class='rm-sub-item'>• <b>w.f</b> — Wheat · <b>c.f</b> — Corn · <b>s.f</b> — Soybeans</div>"
                    "<div class='rm-sub-item'>• <b>kc.f</b> — Coffee · <b>sb.f</b> — Sugar · <b>ct.f</b> — Cotton</div>"
                    "<b>Livestock:</b> lc.f (Cattle) · lh.f (Hogs)"
                ),
                "note": "Gold + Copper are highest priority (key macro relationships). Grains/Softs add value for EM inflation analysis.",
            },
        ],
    },

    # ── 5. DATA SOURCES — DBNOMICS / OTHER ────────────────────────────────────
    {
        "title": "New Data — DBnomics / Other Free APIs",
        "items": [
            {
                "title": "Eurostat HICP — monthly CPI by EU country",
                "status": PROPOSED, "priority": HIGH,
                "tags": ["DBnomics", "Eurostat", "Inflation", "Country Compare"],
                "body": (
                    "App has ECB yield curves but no realized inflation for Euro Area members. "
                    "HICP by country (Germany, France, Italy, Spain) is the key gap for EU inflation analysis.<br>"
                    "<div class='rm-sub-item'>• <b>Eurostat/PRC_HICP_MANR</b> via DBnomics — monthly, all EU countries</div>"
                    "Combined with US FRED CPI: enables real-time US vs EU inflation comparison on Country Compare."
                ),
            },
            {
                "title": "OECD Quarterly National Accounts — quarterly GDP",
                "status": PROPOSED, "priority": HIGH,
                "tags": ["DBnomics", "OECD", "Growth", "Country Compare"],
                "body": (
                    "Currently IMF WEO is annual only. OECD QNA gives quarterly real GDP growth — "
                    "far more timely for cycle analysis and Country Compare.<br>"
                    "<div class='rm-sub-item'>• <b>OECD/QNA</b> via DBnomics — quarterly, all major economies</div>"
                    "Replaces annual IMF data as the primary cycle comparison tool."
                ),
            },
            {
                "title": "BIS Total Credit to Private Non-Financial Sector",
                "status": PROPOSED, "priority": MEDIUM,
                "tags": ["DBnomics", "BIS", "Credit Cycle"],
                "body": (
                    "Critical for assessing credit cycle and financial stability — "
                    "how much debt the private sector carries relative to GDP.<br>"
                    "<div class='rm-sub-item'>• <b>BIS/WS_TC</b> via DBnomics — 44 countries, quarterly</div>"
                    "Fits: Global Business Cycle or a new Credit Cycle panel."
                ),
            },
        ],
    },
]


# ── Page renderer ──────────────────────────────────────────────────────────────

def roadmap() -> None:
    st.markdown(_CSS, unsafe_allow_html=True)
    st.markdown('<div class="rm-page-title">📋 Product Roadmap</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="rm-page-sub">'
        'Bond Analytics · Discussion log, architectural decisions, and data source backlog · '
        'Updated through Aug 2026'
        '</div>',
        unsafe_allow_html=True,
    )

    # ── Summary stats ──────────────────────────────────────────────────────────
    total   = sum(len(s["items"]) for s in SECTIONS)
    high_ct = sum(
        1 for s in SECTIONS for i in s["items"]
        if i["priority"] == HIGH
    )
    proposed_ct = sum(
        1 for s in SECTIONS for i in s["items"]
        if i["status"] == PROPOSED
    )

    c1, c2, c3, c4 = st.columns(4)
    for col, label, val, clr in [
        (c1, "Total items",    total,       _BLUE),
        (c2, "High priority",  high_ct,     _RED),
        (c3, "Proposed",       proposed_ct, _AMB),
        (c4, "In Progress",    1,           _GRN),
    ]:
        col.markdown(
            f'<div style="background:{_CARD};border:1px solid {_EDGE};border-radius:8px;'
            f'padding:12px 16px;text-align:center;">'
            f'<div style="font-size:26px;font-weight:700;color:{clr};">{val}</div>'
            f'<div style="font-size:11px;color:{_T2};margin-top:2px;">{label}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Legend ──────────────────────────────────────────────────────────────────
    st.markdown(
        f'<div style="font-size:11px;color:{_T2};margin-bottom:20px;">'
        f'{PROPOSED} Not started &nbsp;&nbsp;'
        f'{IN_PROG} Active &nbsp;&nbsp;'
        f'{DONE} Complete &nbsp;&nbsp;'
        f'{IDEA} Future idea &nbsp;&nbsp;&nbsp;|&nbsp;&nbsp;&nbsp;'
        f'{HIGH} High priority &nbsp;&nbsp;{MEDIUM} Medium &nbsp;&nbsp;{LOW} Low'
        f'</div>',
        unsafe_allow_html=True,
    )

    # ── Sections ───────────────────────────────────────────────────────────────
    for section in SECTIONS:
        st.markdown(
            f'<div class="rm-section">{section["title"]}</div>',
            unsafe_allow_html=True,
        )
        for item in section["items"]:
            st.markdown(
                _card(
                    title    = item["title"],
                    status   = item["status"],
                    priority = item["priority"],
                    tags     = item["tags"],
                    body     = item["body"],
                    note     = item.get("note", ""),
                ),
                unsafe_allow_html=True,
            )
