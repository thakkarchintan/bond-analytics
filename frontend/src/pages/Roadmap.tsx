const STATUS_COLORS: Record<string, { bg: string; text: string; label: string }> = {
  proposed:    { bg: 'rgba(96,165,250,0.12)',  text: '#60a5fa',  label: 'Proposed'     },
  in_progress: { bg: 'rgba(243,146,0,0.12)',   text: '#f39200',  label: 'In Progress'  },
  done:        { bg: 'rgba(52,211,153,0.12)',  text: '#34d399',  label: 'Done'         },
  idea:        { bg: 'rgba(167,139,250,0.12)', text: '#a78bfa',  label: 'Idea'         },
}

const PRIORITY_COLORS: Record<string, { bg: string; text: string; label: string }> = {
  high:   { bg: 'rgba(255,77,77,0.12)',   text: '#ff4d4d', label: 'High'   },
  medium: { bg: 'rgba(251,191,36,0.12)',  text: '#fbbf24', label: 'Medium' },
  low:    { bg: 'rgba(148,163,184,0.12)', text: '#94a3b8', label: 'Low'    },
}

interface RoadmapItem {
  title: string
  status: keyof typeof STATUS_COLORS
  priority: keyof typeof PRIORITY_COLORS
  tags: string[]
  body: string
  note?: string
}

interface Section { title: string; items: RoadmapItem[] }

const SECTIONS: Section[] = [
  {
    title: 'App Architecture',
    items: [
      {
        title: 'Grouped navigation — React sidebar with FIXED INCOME / MACRO / ADMIN groups',
        status: 'done', priority: 'high',
        tags: ['UX', 'Navigation', 'React'],
        body: 'Implemented in the React migration: collapsible sidebar with 3 labelled nav groups, Lucide icons, Bloomberg-style topbar. Replaces the flat 22-item Streamlit selectbox.',
        note: 'Done as part of the React/Vite migration (v2.0).',
      },
      {
        title: 'Page consolidations — merge closely related pages',
        status: 'proposed', priority: 'medium',
        tags: ['UX', 'Navigation'],
        body: 'Pairs that should become tabs within a single page:\n• Bond Calculator + Bond Simulator → Bond Tools\n• Bond Portfolio + Correlation Heatmap → Portfolio suite\n• Inflation & Growth + Leading Indicators → Inflation & Cycle',
        note: 'Lower urgency. Reduces page count before adding new ones.',
      },
      {
        title: 'Within-page content quality — standardise page layout',
        status: 'proposed', priority: 'medium',
        tags: ['UX', 'Design'],
        body: 'Each page should follow: (1) Key metrics row, (2) Primary chart, (3) Supporting charts, (4) Controls near the chart they affect, (5) Optional data table collapsed by default. Charts should tell a narrative, not just present data.',
      },
      {
        title: 'React/Vite + FastAPI migration from Streamlit',
        status: 'in_progress', priority: 'high',
        tags: ['Framework', 'React', 'FastAPI'],
        body: 'Migration in progress: 19 of 24 Streamlit pages ported to React/Vite with Bloomberg dark theme. FastAPI backend replaces Streamlit server. Parquet caches serve all data without re-fetching on every request.\n\nCompleted: Bond Analytics, Yield Curves, Central Bank Rates, Credit Spreads, FX Currencies, Cross Asset, Leading Indicators, Inflation & Growth, Fiscal Scorecard, Capital Markets, Bond Calculator, Heatmap, Historical Shocks, Curve Trade Builder, Bond Portfolio, Bond Simulator, News Summary, Data Sources, Changelog, Roadmap.\n\nRemaining: Portfolio Rebalance, Bond Investment Strategies, Global Business Cycle.',
        note: 'Active development. All pages committed to branch claude/bond-analytics-fred-api-gm3g6s.',
      },
    ],
  },
  {
    title: 'New Pages to Build',
    items: [
      {
        title: 'Country Deep Dive — single-country aggregated view',
        status: 'proposed', priority: 'high',
        tags: ['New Page', 'Country Intel'],
        body: 'Pick one country → see all available data in one view:\n• Yield curve (current shape + history)\n• CB policy rate history\n• Realized CPI inflation vs breakeven expectations\n• GDP growth (annual IMF → quarterly OECD when added)\n• Fiscal position (debt/GDP, fiscal balance)\n• FX spot + REER\n\nData already exists across 6+ caches — no new fetching needed for first version.',
        note: 'US + Euro Area richest; EM countries only have annual IMF + FX.',
      },
      {
        title: 'Country Compare — multi-country, multi-metric overlay',
        status: 'proposed', priority: 'high',
        tags: ['New Page', 'Country Intel'],
        body: 'Metric-first: [Pick metric] × [Pick countries] × [Pick date range]\n\nAvailable metrics:\n• CB Policy Rate — 25 CBs (BIS), daily ✅\n• 10Y Govt Bond Yield — 11 countries (FRED/OECD), monthly ✅\n• GDP Growth — 16 countries (IMF), annual ✅ → quarterly via OECD 📋\n• CPI Inflation — 16 countries annual ✅ → monthly via Eurostat/FRED 📋\n• Debt/GDP + Fiscal Balance — 16 countries (IMF) ✅\n• FX Spot vs USD — 14 currencies (FRED), daily ✅\n• REER — 14 currencies (BIS), monthly ✅',
        note: 'Primary reason to add Stooq daily yields and Eurostat monthly data.',
      },
      {
        title: 'Portfolio Rebalance — multi-asset weight optimisation',
        status: 'proposed', priority: 'high',
        tags: ['New Page', 'Portfolio'],
        body: 'Port from portfolio_rebalance.py: pick columns from Final.xlsx as assets, set target weights, choose rebalance frequency (Monthly/Quarterly/Half-Yearly/Yearly). Shows CAGR, Sharpe ratio, max drawdown comparison between rebalanced vs buy-and-hold. Risk-free rate input.',
        note: 'All data comes from Final.xlsx — no new API calls needed.',
      },
      {
        title: 'Bond Investment Strategies — Ladder, Bullet, Barbell builder',
        status: 'proposed', priority: 'medium',
        tags: ['New Page', 'Fixed Income'],
        body: 'Port from BondInvestmentStrategies.py: 4 tabs (Ladder, Bullet, Barbell, Compare). Each tab: strategy explainer, bond universe selector, portfolio metrics (YTM, duration, DV01, convexity), maturity distribution chart, cash flow waterfall, yield shock scenario builder with preset shifts. Compare tab: side-by-side metrics for all 3 strategies.',
        note: 'Most complex remaining port. Reuses bond math already in FastAPI backend.',
      },
      {
        title: 'Global Business Cycle — OECD BCI/CCI/CLI across 30 countries',
        status: 'proposed', priority: 'medium',
        tags: ['New Page', 'Macro'],
        body: 'Port from GlobalBusinessCycle.py: latest snapshot KPI cards, country comparison line chart, 36-month deviation heatmap, country deep-dive with all 3 indicators. Source: dbn_oecd_bc_cache.parquet (already in repo). Note: data is ~3 years stale via DBnomics mirror.',
        note: 'Easy port — all data already cached. Freshness is a data-layer issue, not a UI one.',
      },
    ],
  },
  {
    title: 'New Data — FRED (free, no API key, same fetch pattern)',
    items: [
      {
        title: 'ACM Term Premium — NY Fed model',
        status: 'proposed', priority: 'high',
        tags: ['FRED', 'Rates'],
        body: 'Adrian-Crump-Moench decomposition of the 10Y yield into expectations + term premium. Most-cited tool in fixed income macro.\n• ACMTERM10 — 10Y term premium, daily, back to 1961\n• ACMTERM5, ACMTERM2, ACMTERM1\n\nFits: Yield Curves page (decomposition panel) + Country Deep Dive (US).',
      },
      {
        title: 'Realized Inflation — CPI & PCE components',
        status: 'proposed', priority: 'high',
        tags: ['FRED', 'Inflation'],
        body: 'App has breakeven inflation expectations but not the realized print the Fed reacts to.\n• CPIAUCSL — CPI All Items, monthly\n• CPILFESL — Core CPI (ex food & energy)\n• PCEPI — PCE Deflator\n• PCEPILFE — Core PCE (Fed\'s preferred) ⭐\n• PPIACO — PPI All Commodities (upstream inflation)',
      },
      {
        title: 'Chicago Fed Financial Conditions Index (NFCI)',
        status: 'proposed', priority: 'high',
        tags: ['FRED', 'Financial Conditions'],
        body: 'Single number summarising tightening/easing across rates, spreads, equity and FX. Widely referenced in Fed communications.\n• NFCI — weekly, back to 1971\n\nFits: Cross-Asset Dashboard or Leading Indicators.',
      },
      {
        title: 'Fed Balance Sheet detail — weekly H.4.1',
        status: 'proposed', priority: 'high',
        tags: ['FRED', 'Central Banks', 'QT/QE'],
        body: 'Currently have BIS monthly CB total assets. Fed weekly H.4.1 is far more granular for tracking QT/QE pace.\n• WALCL — Total assets, weekly\n• WSODL — Treasury holdings (direct QT signal)\n• WSHOMCB — MBS holdings\n• WRESBAL — Bank reserves at Fed (liquidity signal)',
      },
      {
        title: 'Money Supply — M2',
        status: 'proposed', priority: 'medium',
        tags: ['FRED', 'Monetary'],
        body: 'Missing entirely. Money supply growth vs nominal GDP is a foundational macro lens and a leading indicator for inflation with a long lag.\n• M2SL — M2, monthly, back to 1959',
      },
      {
        title: 'Money market curve — short-end rates',
        status: 'proposed', priority: 'medium',
        tags: ['FRED', 'Rates'],
        body: 'SOFR and Fed Funds are in the app. Missing the rest of the USD front-end:\n• DTB3 — 3M T-bill, daily\n• DTB6 — 6M T-bill\n• DTB1YR — 1Y T-bill\n\nCombined with existing DGS1–DGS30: complete USD curve from overnight to 30Y.',
      },
      {
        title: 'Labor market detail — wages, JOLTS, U-6',
        status: 'proposed', priority: 'medium',
        tags: ['FRED', 'Labor', 'Inflation'],
        body: 'Beyond headline claims + unemployment, the Fed watches:\n• CES0500000003 — Average Hourly Earnings YoY (wage inflation)\n• U6RATE — Broad unemployment (true labor slack)\n• JTSJOL — JOLTS Job Openings (leads wage growth)\n• JTSQUR — Quits Rate (workers\' confidence → wage bargaining)',
      },
      {
        title: 'Consumer inflation expectations — Michigan survey',
        status: 'proposed', priority: 'low',
        tags: ['FRED', 'Inflation Expectations'],
        body: '• UMCSENT — Michigan Consumer Sentiment, monthly\n• MICH — Michigan 1Y inflation expectation\n• MICH5 — 5Y forward inflation expectation ⭐ (de-anchoring risk)',
      },
    ],
  },
  {
    title: 'New Data — Stooq (free, no API key, CSV download)',
    items: [
      {
        title: 'Sovereign 10Y yields — daily for 8 countries',
        status: 'proposed', priority: 'high',
        tags: ['Stooq', 'Rates', 'Country Compare'],
        body: 'Biggest single upgrade for Country Compare. Currently only US (FRED daily) and Euro Area (ECB daily) have daily yield data. All others are monthly OECD.\n• de10y.b — Germany 10Y Bund\n• gb10y.b — UK 10Y Gilt\n• jp10y.b — Japan 10Y JGB\n• it10y.b — Italy 10Y BTP (not in app at all)\n• fr10y.b — France 10Y OAT (not in app)\n• au10y.b — Australia\n• ca10y.b — Canada\n\nHistory back to mid-1990s.',
        note: 'Stooq is blocked in the remote dev sandbox (proxy policy) but works from any normal server.',
      },
      {
        title: 'Commodities — Gold, Brent, Copper, Natural Gas',
        status: 'proposed', priority: 'high',
        tags: ['Stooq', 'Commodities', 'Cross-Asset'],
        body: 'FRED returns 404 for Gold. Stooq fills the gap across all commodity sectors:\n• gc.f — Gold (inverse proxy for real yields)\n• cb.f — Brent Crude (more relevant than WTI for EU/EM)\n• ng.f — Natural Gas (critical for 2021-23 EU energy crisis)\n• hg.f — Copper (Dr. Copper — leading indicator for global growth)\n\nGold + Copper are highest priority.',
      },
    ],
  },
  {
    title: 'New Data — DBnomics / Other Free APIs',
    items: [
      {
        title: 'Eurostat HICP — monthly CPI by EU country',
        status: 'proposed', priority: 'high',
        tags: ['DBnomics', 'Eurostat', 'Inflation'],
        body: 'App has ECB yield curves but no realized inflation for Euro Area members. HICP by country (Germany, France, Italy, Spain) is the key gap for EU inflation analysis.\n• Eurostat/PRC_HICP_MANR via DBnomics — monthly, all EU countries\n\nEnables real-time US vs EU inflation comparison on Country Compare.',
      },
      {
        title: 'OECD Quarterly National Accounts — quarterly GDP',
        status: 'proposed', priority: 'high',
        tags: ['DBnomics', 'OECD', 'Growth'],
        body: 'Currently IMF WEO is annual only. OECD QNA gives quarterly real GDP growth — far more timely for cycle analysis.\n• OECD/QNA via DBnomics — quarterly, all major economies\n\nReplaces annual IMF data as the primary cycle comparison tool.',
      },
      {
        title: 'BIS Total Credit to Private Non-Financial Sector',
        status: 'proposed', priority: 'medium',
        tags: ['DBnomics', 'BIS', 'Credit Cycle'],
        body: 'Critical for assessing credit cycle and financial stability — how much debt the private sector carries relative to GDP.\n• BIS/WS_TC via DBnomics — 44 countries, quarterly\n\nFits: Global Business Cycle or a new Credit Cycle panel.',
      },
    ],
  },
]

export default function Roadmap() {
  const totalItems = SECTIONS.reduce((s, sec) => s + sec.items.length, 0)
  const highCount = SECTIONS.flatMap(s => s.items).filter(i => i.priority === 'high').length
  const proposedCount = SECTIONS.flatMap(s => s.items).filter(i => i.status === 'proposed').length
  const doneCount = SECTIONS.flatMap(s => s.items).filter(i => i.status === 'done').length

  return (
    <div className="content-wrap" style={{ maxWidth: 900 }}>
      {/* Summary KPIs */}
      <div className="kpi-strip" style={{ marginBottom: 24 }}>
        {[
          { label: 'Total Items',    val: totalItems,    color: '#60a5fa' },
          { label: 'High Priority',  val: highCount,     color: '#ff4d4d' },
          { label: 'Proposed',       val: proposedCount, color: '#f39200' },
          { label: 'Done',           val: doneCount,     color: '#34d399' },
        ].map(({ label, val, color }) => (
          <div key={label} className="kpi-card">
            <div style={{ color: '#888', fontSize: 10, textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 4 }}>{label}</div>
            <div style={{ color, fontSize: 22, fontWeight: 700, fontVariantNumeric: 'tabular-nums' }}>{val}</div>
          </div>
        ))}
      </div>

      {/* Legend */}
      <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginBottom: 24 }}>
        {Object.values(STATUS_COLORS).map(({ bg, text, label }) => (
          <span key={label} style={{ padding: '2px 10px', borderRadius: 4, background: bg, color: text, fontSize: 11, fontWeight: 600 }}>{label}</span>
        ))}
        <span style={{ color: '#333', padding: '2px 4px' }}>|</span>
        {Object.values(PRIORITY_COLORS).map(({ bg, text, label }) => (
          <span key={label} style={{ padding: '2px 10px', borderRadius: 4, background: bg, color: text, fontSize: 11, fontWeight: 600 }}>{label}</span>
        ))}
      </div>

      {/* Sections */}
      {SECTIONS.map(section => (
        <div key={section.title}>
          <div style={{ fontSize: 11, fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.1em', color: '#555', margin: '28px 0 12px', borderBottom: '1px solid #1f1f1f', paddingBottom: 6 }}>
            {section.title}
          </div>
          {section.items.map(item => {
            const st = STATUS_COLORS[item.status]
            const pr = PRIORITY_COLORS[item.priority]
            return (
              <div key={item.title} style={{ background: '#1a1a1a', border: '1px solid #2a2a2a', borderRadius: 8, padding: '14px 18px', marginBottom: 10 }}>
                <div style={{ display: 'flex', alignItems: 'flex-start', gap: 8, flexWrap: 'wrap', marginBottom: 8 }}>
                  <span style={{ padding: '2px 9px', borderRadius: 4, background: st.bg, color: st.text, fontSize: 10, fontWeight: 700, whiteSpace: 'nowrap' }}>{st.label}</span>
                  <span style={{ padding: '2px 9px', borderRadius: 4, background: pr.bg, color: pr.text, fontSize: 10, fontWeight: 700, whiteSpace: 'nowrap' }}>{pr.label}</span>
                  {item.tags.map(t => (
                    <span key={t} style={{ padding: '2px 7px', borderRadius: 3, background: '#111', border: '1px solid #2a2a2a', color: '#555', fontSize: 10 }}>{t}</span>
                  ))}
                </div>
                <div style={{ color: '#e8e8e8', fontWeight: 600, fontSize: 13, marginBottom: 8 }}>{item.title}</div>
                <div style={{ color: '#888', fontSize: 12, lineHeight: 1.7, whiteSpace: 'pre-line' }}>{item.body}</div>
                {item.note && (
                  <div style={{ fontSize: 11, color: '#555', fontStyle: 'italic', marginTop: 8, borderTop: '1px solid #222', paddingTop: 8 }}>
                    📌 {item.note}
                  </div>
                )}
              </div>
            )
          })}
        </div>
      ))}
    </div>
  )
}
