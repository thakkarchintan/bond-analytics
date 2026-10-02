const CATEGORY_COLORS: Record<string, { bg: string; text: string }> = {
  Feature:     { bg: 'rgba(96,165,250,0.12)',  text: '#60a5fa' },
  Enhancement: { bg: 'rgba(243,146,0,0.12)',   text: '#f39200' },
  Fix:         { bg: 'rgba(255,77,77,0.12)',   text: '#ff4d4d' },
  Refactor:    { bg: 'rgba(52,211,153,0.12)',  text: '#34d399' },
  Security:    { bg: 'rgba(167,139,250,0.12)', text: '#a78bfa' },
  Performance: { bg: 'rgba(251,191,36,0.12)',  text: '#fbbf24' },
  Config:      { bg: 'rgba(34,211,238,0.12)',  text: '#22d3ee' },
  UI:          { bg: 'rgba(244,114,182,0.12)', text: '#f472b6' },
  Polish:      { bg: 'rgba(148,163,184,0.12)', text: '#94a3b8' },
  Migration:   { bg: 'rgba(52,211,153,0.12)',  text: '#34d399' },
}

interface Entry {
  id: number
  version: string
  timestamp: string
  category: string
  title: string
  description: string[]
}

const CHANGELOG: Entry[] = [
  {
    id: 54,
    version: '2.6',
    timestamp: '07 Sep 2026, 21:35 IST',
    category: 'Enhancement',
    title: 'Low-priority gap close — 5 pages enriched with new views and analytics',
    description: [
      'InflationGrowth — new Breakeven tab: TIPS-implied breakeven rates (5Y, 10Y, 5-10Y forward) and real yields (5Y, 10Y) charts with KPI strip; data from /api/macro/breakeven',
      'FXCurrencies — new Indexed tab rebasing all currencies to 100 at period start (rise = local weakened vs USD); added YoY change column with colour-coded ▲/▼ and weakened/strengthened labels to Spot table',
      'CreditSpreads — new Spectrum view: bar chart of current OAS across full AAA→CCC rating ladder with vs-IG-premium table; added historical percentile badges for IG and HY with tight/moderate/wide labels',
      'MacroDashboard — added Unemployment Rate (% labour force) time-series chart in global macro section',
      'FiscalScorecard — added Debt Sustainability bubble scatter (DebtGDP vs FiscalBal, bubble size ∝ GDP); added Primary Balance and Current Account history charts',
    ],
  },
  {
    id: 53,
    version: '2.5',
    timestamp: '07 Sep 2026, 21:25 IST',
    category: 'Enhancement',
    title: 'Medium-priority gap close — 2 new API endpoints + 5 pages enriched',
    description: [
      'api/routers/macro.py — added GET /api/macro/us-curve (US Treasury 11-maturity daily data) and GET /api/macro/mmkt (SOFR + Effective Fed Funds daily)',
      'YieldCurves — new US Curve tab: compare the full 1M–30Y term structure across up to 5 user-selected dates; 2Y10Y and 3M10Y spread badges below chart',
      'CrossAsset — added US 10Y yield series, IG and HY OAS spreads, and NBER recession shading to the cross-asset time-series view',
      'InflationGrowth — added Scatter view: Stagflation Quadrant (CPI vs Real GDP) and Phillips Curve (Unemployment vs CPI) for any selected year',
      'CentralBankRates — added 1yr rate change badges to policy rate KPI cards; added Money Market Rates section showing Fed Funds and SOFR',
      'LeadingIndicators — added 6 traffic-light signal cards for US leading indicators with configurable thresholds and colour coding',
    ],
  },
  {
    id: 52,
    version: '2.4',
    timestamp: 'Sep 2026',
    category: 'Migration',
    title: 'Admin pages — Data Sources, Changelog, Roadmap ported to React',
    description: [
      'DataSources.tsx — full catalog of all 16 parquet-backed datasets with source, coverage, frequency, notes, and alternatives; filterable by source group',
      'Changelog.tsx — all 51 historical entries embedded; Bloomberg dark theme with category colour badges',
      'Roadmap.tsx — all 5 roadmap sections (Architecture, New Pages, FRED backlog, Stooq, DBnomics) with status and priority badges',
      'All 3 pages wired into App.tsx under a new ADMIN nav group; visible to all users in React build',
    ],
  },
  {
    id: 51,
    version: '2.3',
    timestamp: 'Sep 2026',
    category: 'Migration',
    title: 'Bond Portfolio, Bond Simulator, News Summary — backend + frontend ported to React',
    description: [
      'api/routers/bond.py — POST /api/bond/portfolio: per-position and portfolio-level MV, Macaulay/modified duration, DV01, convexity, weights; POST /api/bond/simulate: Monte Carlo GBM yield paths, price distribution, P5–P95 percentiles, VaR95, CVaR95',
      'api/routers/news.py — GET /api/news: NewsAPI fetch + optional Cohere/OpenRouter LLM summary; graceful degradation when API keys missing',
      'BondPortfolio.tsx — editable position table (add/remove rows), POST to /api/bond/portfolio, KPI strip, per-position breakdown, ±100bps P&L sensitivity table',
      'BondSimulator.tsx — GBM params sidebar, Plotly yield-path fan chart (50 paths), price distribution histogram with P5/median/P95 lines, VaR/CVaR KPI strip',
      'NewsSummary.tsx — preset query chips + custom search, AI summary block, article cards with image/source/timeago, API key status indicators',
    ],
  },
  {
    id: 50,
    version: '2.2',
    timestamp: 'Sep 2026',
    category: 'Migration',
    title: 'Fixed income tools — Bond Calculator, Heatmap, Historical Shocks, Curve Trade Builder ported to React',
    description: [
      'BondCalculator.tsx — pure client-side bond math: price, YTM, Macaulay/modified duration, DV01, convexity; real-time updates on every input change; P&L sensitivity table −200bp to +200bp',
      'Heatmap.tsx — Pearson correlation matrix computed client-side; Plotly annotated heatmap + numeric table; multi-column selector with date range filter; GET /api/bond/columns + /api/bond/series',
      'HistoricalShocks.tsx — 5 preset events (GFC, Euro Crisis, Taper Tantrum, COVID, Rate Hike Cycle) + custom date range; per-episode Plotly line charts from Final.xlsx',
      'CurveTradeBuilder.tsx — 2-leg spreads and 3-leg butterflies; historical time series with 1Y z-score; Plotly distribution histogram; DV01 attribution table; GET /api/bond/formula',
      'All pages use lazy import("plotly.js-dist-min") inside useEffect with Bloomberg dark base layout (paper_bgcolor #1a1a1a, plot_bgcolor #111111)',
      'frontend/src/plotly.d.ts — module declaration added to silence TS7016 across all Plotly pages',
    ],
  },
  {
    id: 49,
    version: '2.1',
    timestamp: 'Sep 2026',
    category: 'Migration',
    title: 'Macro pages (9 pages) ported from Streamlit to React',
    description: [
      'YieldCurves.tsx — 10Y government bond yields across 11 countries + ECB Svensson term structure; multi-series Plotly chart; date range filter',
      'CentralBankRates.tsx — BIS CB policy rates for 8 banks + CB balance sheets (total assets USD bn); source: dbn_cbpol_cache.parquet + dbn_cbta_cache.parquet',
      'CreditSpreads.tsx — ICE BofA OAS spreads (AAA → CCC, IG, HY) with recession-context annotations; source: gmacro_spreads_cache.parquet',
      'FXCurrencies.tsx — FX spot rates vs USD (14 currencies) + BIS REER (2020=100); source: gmacro_fx_cache.parquet + dbn_eer_cache.parquet',
      'CrossAsset.tsx — VIX, WTI Crude, S&P 500 from FRED alongside US 10Y yield; source: gmacro_cross_asset_cache.parquet',
      'LeadingIndicators.tsx — US leading indicators (jobless claims, Michigan sentiment, housing starts, INDPRO, unemployment, 2Y10Y) + OECD CLI for 16 countries; NBER recession shading',
      'InflationGrowth.tsx — US CPI, GDP, breakeven inflation, TIPS real yields; FRED data via gmacro_breakeven_cache.parquet',
      'FiscalScorecard.tsx — debt/GDP, fiscal balance, current account for 16 countries; IMF WEO annual data',
      'CapitalMarkets.tsx — equity market cap vs bond stock across 10 countries; World Bank/SIFMA data from capital_markets_cache.parquet',
    ],
  },
  {
    id: 48,
    version: '2.0',
    timestamp: 'Sep 2026',
    category: 'Migration',
    title: 'React/Vite + FastAPI stack — initial scaffold and core pages',
    description: [
      'Stack migration: Streamlit → React 18 + Vite + TypeScript frontend, FastAPI backend replacing Streamlit server',
      'Bloomberg dark theme: sidebar #0d0d0d, page #111111, cards #1a1a1a, borders #2a2a2a, accent orange #f39200, green #00c087, red #ff4d4d',
      'Collapsible sidebar with grouped navigation (FIXED INCOME / MACRO / ADMIN); Lucide icons; Bloomberg-style topbar with eyebrow/title/subtitle',
      'api/main.py — FastAPI app with CORS for Vite dev server; StaticFiles mount for production React build',
      'api/routers/bond.py — GET /api/bond/columns, GET /api/bond/series, POST /api/bond/formula, GET /api/bond/spread-grid; all backed by Final.xlsx via load_final()',
      'api/routers/macro.py — all macro endpoints serving parquet caches (FRED, BIS, ECB, OECD, IMF datasets)',
      'api/routers/capital.py — GET /api/capital/data from capital_markets_cache.parquet',
      'Vite proxy: /api → localhost:8000; plotly.js-dist-min installed and lazy-loaded per page',
      'BondAnalytics.tsx (Bond Spreads page) — 20 preset spread formulas via GET /api/bond/spread-grid; custom formula builder; Plotly fan chart',
    ],
  },
  {
    id: 47,
    version: '1.47',
    timestamp: '09 Aug 2026',
    category: 'Feature',
    title: 'React migration started — Dash prototype abandoned in favour of React/Vite',
    description: [
      'Decision: Streamlit → React/Vite (not Dash) chosen for full migration; Bloomberg dark theme chosen as design system',
      'React chosen over Dash for: better TypeScript support, richer ecosystem, proper URL routing with React Router, and more flexible layout system',
      'Roadmap.py updated to reflect migration decision; credit_spreads_dash.py retained as reference but no longer actively developed',
    ],
  },
  {
    id: 46,
    version: '1.46',
    timestamp: '09 Aug 2026',
    category: 'Enhancement',
    title: 'Curve Trade Builder — larger fonts across page',
    description: [
      'CurveTradeBuilder.py — base chart font increased 12→15, axis tick font 11→14, legend font 11→14',
      'Section headers increased 13→15px, subtitles 12→14px',
      'Metric cards: label 10→13px, value 18→22px, sub text 10→13px',
      'Inline HTML text blocks (banner, shape description, tenor labels, DV01 info, warnings) all scaled up ~2px',
      'Bottom chart margin increased 44→64px to accommodate larger legend text',
    ],
  },
  {
    id: 45,
    version: '1.45',
    timestamp: '09 Aug 2026',
    category: 'Feature',
    title: 'Historical Shocks — Yield Curve Before & After section on every event page',
    description: [
      'HistoricalShocks.py — new section at the bottom of each event: 3 full-width yield curve charts showing shape before and after the shock',
      'Row 1: US Treasury curve (FRED data — 11 maturities) at event start vs event end dates',
      'Row 2: Euro Area curve (ECB Svensson model via DBnomics) at same dates',
      'Row 3: Sovereign curve for any country in the Excel dataset — selectable via dropdown',
      'Before/after dates derived from each event shade period; point-in-time events use ±3 months around the key date',
    ],
  },
  {
    id: 44,
    version: '1.44',
    timestamp: '09 Aug 2026',
    category: 'Enhancement',
    title: 'Curve Trade Builder — curve shape descriptions below Step 1 chart',
    description: [
      'CurveTradeBuilder.py — added _SHAPE_DESCRIPTIONS with 2–3 line commentary for each preset',
      'Descriptions explain what the curve shape signals and when it historically forms',
      'Rendered below the Step 1 yield curve chart with a left accent bar',
    ],
  },
  {
    id: 43,
    version: '1.43',
    timestamp: '09 Aug 2026',
    category: 'Enhancement',
    title: 'Curve Trade Builder + Historical Shocks — compact inputs and font improvements',
    description: [
      'CurveTradeBuilder.py — Step 1 tenor inputs now inline (label + number box on same row)',
      'HistoricalShocks.py — chart fonts increased ~50%: body 11→17, titles 14→21, axis ticks 16, legend 16',
      'HistoricalShocks.py — legend text colour changed to near-black (#111111) for readability',
    ],
  },
  {
    id: 42,
    version: '1.42',
    timestamp: '09 Aug 2026',
    category: 'Enhancement',
    title: 'Curve Trade Builder + Historical Shocks — layout and UX improvements',
    description: [
      'CurveTradeBuilder.py — Step 1: shape selector and tenor yields in left column; live yield curve chart in right column',
      'CurveTradeBuilder.py — DV01 overrides now persist in session state',
      'HistoricalShocks.py — charts displayed one per row at full page width',
      'HistoricalShocks.py — Bloomberg terminal colour scheme applied',
    ],
  },
  {
    id: 41,
    version: '1.41',
    timestamp: '08 Aug 2026',
    category: 'Enhancement',
    title: 'Curve Trade Builder — Simulation Mode toggle for DV01-neutral P&L demo',
    description: [
      'CurveTradeBuilder.py — Simulation Mode toggle at top of page',
      'When ON: P&L computed as DV01 × bp shift (linear approximation); net DV01 = $0 → Total P&L = $0 exactly',
      'Ideal for classroom demos; blue info banner appears when sim mode is active',
    ],
  },
  {
    id: 40,
    version: '1.40',
    timestamp: '08 Aug 2026',
    category: 'Feature',
    title: 'Curve Trade Builder — 2/3-leg yield curve trades with scenario P&L and DV01-neutral ratios',
    description: [
      'CurveTradeBuilder.py — new page: 4-step builder for yield curve trades',
      'Step 1: yield curve shape preset (Normal / Flat / Inverted / Humped) with per-tenor manual override',
      'Step 2: scenario — Bear/Bull Steepening, Bear/Bull Flattening, Parallel Up/Down, Custom',
      'Step 3: 2- or 3-leg trades with tenor, direction (Long/Short) and notional ($M) per leg',
      'Step 4: yield curve before/after chart, P&L per leg, DV01 attribution, DV01-neutral hedge ratio',
    ],
  },
  {
    id: 39,
    version: '1.39',
    timestamp: '08 Aug 2026',
    category: 'Enhancement',
    title: 'Bond Calculator — hold-to-maturity rate evolution: Price, Duration and DV01 over time',
    description: [
      'BondCalculator.py — new section "Rate Scenario — Risk Evolution Over Time"',
      'Three charts: Price pull-to-par, Modified Duration decline, DV01 dollar risk over holding period',
      'Preset rate shock scenarios −200bp to +200bp; per-scenario snapshot table',
    ],
  },
  {
    id: 38,
    version: '1.38',
    timestamp: '07 Aug 2026',
    category: 'Enhancement',
    title: 'Historical Shocks — economist write-ups + chart captions; fix CentralBankRates colorbar error',
    description: [
      'HistoricalShocks.py — each of the 12 events now has a detailed economist-level write-up (2–3 paragraphs)',
      'Every chart now has a 1–2 sentence caption explaining what the data shows',
      'CentralBankRates.py — fixed ValueError: titlefont is not a valid colorbar property',
    ],
  },
  {
    id: 37,
    version: '1.37',
    timestamp: '07 Aug 2026',
    category: 'Feature',
    title: 'Historical Global Shocks — 12 market events with event-specific yield, spread and cross-asset charts',
    description: [
      'HistoricalShocks.py — 12 key market events (Dot-com, GFC, Euro Crisis, ECB Whatever It Takes, Taper Tantrum, Oil/Deflation, Brexit, COVID, Inflation Shock, UK LDI Crisis + 2 bonus)',
      'Each event shows 3–4 contextually relevant charts chosen per event to illustrate the specific mechanism',
      'Shaded event period + orange dotted vertical markers for key dates',
      'global_macro_data.py — added historical OAS fetch: HY (BAMLH0A0HYM2OAS) + BBB (BAMLC0A4CBBBOAS) back to 1996–97',
    ],
  },
  {
    id: 36,
    version: '1.36',
    timestamp: '07 Aug 2026',
    category: 'Feature',
    title: 'Data Sources catalog — admin microapp with live freshness for all 16 datasets',
    description: [
      'DataSources.py — new admin-only page: catalog of all 16 parquet-backed datasets with live freshness, date range, row count, frequency, source API, and alternatives',
      'Freshness: 🟢 Current (<30d), 🟡 Lagged (1–6mo), 🔴 Stale (>6mo); OECD BCI/CCI/CLI flagged stale with "fixable lag"',
      'Filterable by source group and freshness tier; summary reference table at the bottom',
    ],
  },
  {
    id: 35,
    version: '1.35',
    timestamp: '06 Aug 2026',
    category: 'Feature',
    title: 'DBnomics integration: BIS CB balance sheets · ECB yield curve · OECD CLI · BIS EER · Global Business Cycle',
    description: [
      'dbnomics_data.py — new data layer: BIS WS_CBPOL (25 CBs), BIS WS_CBTA (8 CB balance sheets), BIS WS_EER (14-currency REER), ECB YC (8-maturity AAA govt bond curve), OECD DP_LIVE (BCI/CCI/CLI 29 countries)',
      'GlobalBusinessCycle.py — new page: OECD BCI/CCI/CLI snapshot cards, country comparison line chart, 36-month deviation heatmap, country deep-dive',
      'YieldCurves.py — new Euro Area Curve tab: ECB Svensson model, 8 maturities (3M–30Y)',
      'CentralBankRates.py — new CB Balance Sheets section: Fed/ECB/BoJ/BoE/PBoC/SNB/BoC/RBA total assets',
      'FXCurrencies.py — new BIS EER section: real broad effective exchange rates, 2020=100',
    ],
  },
  {
    id: 34,
    version: '1.34',
    timestamp: '06 Aug 2026',
    category: 'Feature',
    title: '3 new pages: Cross-Asset Dashboard · Leading Indicators · Bond Simulator',
    description: [
      'CrossAsset.py — VIX, WTI Crude, S&P 500 from FRED alongside US 10Y yield and IG/HY spreads; normalized performance + monthly return correlation matrix',
      'LeadingIndicators.py — Initial Jobless Claims, Consumer Sentiment, Housing Starts, INDPRO, Unemployment, 2Y10Y Spread with NBER recession shading',
      'BondSimulator.py — interactive price-yield curve with duration tangent and convexity-adjusted overlay, cash flow timeline with PV breakdown, rate shock table −300bp to +300bp',
      'global_macro_data.py — 2 new FRED datasets with parquet caching',
    ],
  },
  {
    id: 33,
    version: '1.33',
    timestamp: '06 Aug 2026',
    category: 'Feature',
    title: '5 new data streams: US yield curve · breakeven/real yields · credit spreads · money market rates',
    description: [
      'global_macro_data.py — 5 new FRED/ECB/BoE datasets: US curve (11 maturities), TIPS breakeven+real yields, ICE BofA OAS spreads (IG/HY/AAA–CCC), SOFR+Fed Funds, CB rates',
      'YieldCurves.py — new US Treasury Curve tab: compare full 1M–30Y curve across up to 5 dates',
      'InflationGrowth.py — new Breakeven Inflation & Real Yields section',
      'CreditSpreads.py — new standalone page: snapshot cards, Spread History, Credit Spectrum bar chart, IG vs HY comparison',
    ],
  },
  {
    id: 32,
    version: '1.32',
    timestamp: '06 Aug 2026',
    category: 'Feature',
    title: 'Bond Investment Strategies — full yield shock scenario per strategy tab',
    description: [
      'Each strategy tab (Ladder, Bullet, Barbell) includes the full per-economy, per-maturity yield shock scenario builder',
      'Preset buttons: +25/+50/+100, -25/-50/-100bp parallel shifts, Bear Steepen, Bull Flatten, Reset',
      'Impact analysis: P&L by country chart, P&L by maturity bucket chart, waterfall attribution per bond',
    ],
  },
  {
    id: 31,
    version: '1.31',
    timestamp: '06 Aug 2026',
    category: 'Feature',
    title: 'Bond Investment Strategies — Ladder · Bullet · Barbell',
    description: [
      'BondInvestmentStrategies.py — new page with 4 tabs: Ladder, Bullet, Barbell, Compare',
      'Each tab: strategy explainer, auto-build button, portfolio metrics, maturity distribution chart, cash flow waterfall, parallel rate shock table',
      'Compare tab: side-by-side metrics table, rate sensitivity line chart, cash flow waterfall for all three strategies simultaneously',
    ],
  },
  {
    id: 30,
    version: '1.30',
    timestamp: '06 Aug 2026',
    category: 'Feature',
    title: 'Home screen with clickable app cards',
    description: [
      'HomePage.py — landing page with 3-column card grid; emoji, name, and 1–2 line description per card',
      'Clicking any card navigates directly to that app',
      'Greeting personalised with the logged-in user\'s first name',
    ],
  },
  {
    id: 29,
    version: '1.29',
    timestamp: '06 Aug 2026',
    category: 'Fix',
    title: 'Fix set_page_config crash on local run',
    description: [
      'app.py — moved st.set_page_config() to line 3, before all other imports',
      'Fixes StreamlitAPIException crash caused by Authenticator.__init__() touching session_state before set_page_config',
    ],
  },
  {
    id: 28,
    version: '1.28',
    timestamp: '06 Aug 2026',
    category: 'Fix',
    title: 'FRED User-Agent fix + commit IMF annual parquet cache',
    description: [
      'global_macro_data.py — FRED requests now use browser User-Agent/Accept headers; fixes connection drops on bulk FRED fetches',
      'gmacro_annual_cache.parquet committed — IMF annual data loads instantly on cold deploy',
    ],
  },
  {
    id: 26,
    version: '1.26',
    timestamp: '06 Aug 2026',
    category: 'Feature',
    title: 'Central Bank Rates — 10Y yield overlay + yield curve slope; FX — BIS REER + real rate differential',
    description: [
      'global_macro_data.py — added YIELD_SERIES (11 FRED/OECD 10Y series) and BIS WS_EER_M (broad REER)',
      'Central Bank Rates — policy rate charts now overlay 10Y govt bond yield as dashed lines; new yield curve slope section (10Y − policy rate)',
      'FX & Currencies — new BIS broad REER section (2020=100) for all 16 countries',
    ],
  },
  {
    id: 25,
    version: '1.25',
    timestamp: '06 Aug 2026',
    category: 'Feature',
    title: '4 new Global Macro pages — Central Bank Rates, Fiscal Scorecard, Inflation & Growth, FX & Currencies',
    description: [
      'global_macro_data.py — shared data layer: IMF Datamapper (8 indicators × 16 countries), BIS WS_CBPOL_M policy rates (40+ CBs), FRED spot FX (15 pairs)',
      'Central Bank Rates — policy rate snapshot, rate history chart, rate cycle heatmap, real policy rate overlay',
      'Fiscal Scorecard — debt/GDP time series, fiscal balance, debt sustainability scatter quadrant',
      'Inflation & Growth — stagflation quadrant, CPI + GDP time series with rankings, Phillips curve scatter',
      'FX & Currencies — latest rates snapshot, indexed performance, annual returns heatmap, carry trade indicator',
    ],
  },
  {
    id: 24,
    version: '1.24',
    timestamp: '05 Aug 2026',
    category: 'Polish',
    title: 'Capital Markets — financing model blurb truly full-width',
    description: [
      'Moved Market-based / Bank-based / Government debt-heavy blurb out of _section9_dna into main body as native st.markdown call for full content width',
    ],
  },
  {
    id: 22,
    version: '1.22',
    timestamp: '05 Aug 2026',
    category: 'Feature',
    title: 'Bond Portfolio — short positions + DV01 hedging scenario',
    description: [
      'Qty input now allows negative values — negative qty = short position (like a futures short)',
      'Summary cards: Gross Exposure, Net Position, signed Portfolio DV01; DV01 card turns green when near-zero',
      'Automatic hedge callout: green banner when |DV01| < 1bp per $1M gross',
    ],
  },
  {
    id: 18,
    version: '1.18',
    timestamp: '05 Aug 2026',
    category: 'Feature',
    title: 'Bond Portfolio — Yield Shock Scenario Builder + Risk & Impact Analysis',
    description: [
      'New Yield Shock Scenario Builder: compact grid of inputs (basis points) by economy × maturity bucket',
      '9 preset buttons: parallel shifts (+25/+50/+100/−25/−50/−100bp), Bear Steepen, Bull Flatten, Reset',
      'Impact analysis: 4 summary cards, P&L by country, P&L by maturity bucket, waterfall attribution, detailed table',
      'Exact bond pricing used for impact (full bond_price() recalculation), not duration approximation',
    ],
  },
  {
    id: 16,
    version: '1.16',
    timestamp: '05 Aug 2026',
    category: 'Feature',
    title: 'Global Capital Markets Dashboard — equity vs bond markets across 10 countries',
    description: [
      'CapitalMarkets.py — new page: 9 analytical sections covering market size, composition, depth, and evolution',
      'Data: World Bank GFDD + SIFMA + IMF WEO; manually curated and cached as capital_markets_cache.parquet',
      'Sections: Market size comparison, equity vs bond split, issuance volumes, depth indicators',
    ],
  },
  {
    id: 14,
    version: '1.14',
    timestamp: '04 Aug 2026',
    category: 'Feature',
    title: 'Bond Portfolio — full analytics suite',
    description: [
      'BondPortfolio.py — 60+ sovereign bonds across 11 countries with checkboxes, quantity stepper, and market value',
      'Portfolio analytics: country allocation donut, maturity profile bars, yield positioning scatter',
      'Holdings table: price, YTM, duration, DV01, convexity, market value, weight per bond',
      'Rate shock summary table: ±10/25/50/100/200bp parallel shifts with approx ΔMV',
    ],
  },
  {
    id: 12,
    version: '1.12',
    timestamp: '03 Aug 2026',
    category: 'Feature',
    title: 'Heatmap — Pearson correlation matrix for yields, equities, and commodities',
    description: [
      'HeatmapTab.py — column multi-select from Final.xlsx; configurable date range; full Pearson correlation matrix',
      'Plotly annotated heatmap with RdBu_r colour scale; numeric table below for export',
    ],
  },
  {
    id: 10,
    version: '1.10',
    timestamp: '02 Aug 2026',
    category: 'Feature',
    title: 'News Summary — NewsAPI + LLM-powered market brief',
    description: [
      'NewsSummary/ — NewsAPI fetch (last 7 days), optional Cohere/OpenRouter summary, article cards',
      'Preset query chips for bonds, rates, ECB, credit spreads, EM debt, IMF',
      'Graceful degradation when API keys not set; has_news_key / has_llm_key flags in response',
    ],
  },
  {
    id: 8,
    version: '1.08',
    timestamp: '01 Aug 2026',
    category: 'Feature',
    title: 'Bond Calculator — full pricing suite with P&L evolution',
    description: [
      'BondCalculator.py — price, YTM, Macaulay/modified duration, DV01, convexity; all update live',
      'Cash flow timeline bar chart; P&L sensitivity table; hold-to-maturity price pull-to-par chart',
    ],
  },
  {
    id: 5,
    version: '1.05',
    timestamp: '30 Jul 2026',
    category: 'Feature',
    title: 'Bond Analytics (Spreads page) — 20 preset spread formulas + custom formula builder',
    description: [
      'GridTab.py / BondAnalytics page — 20 preset curves (Eurex, US Treasuries, cross-country spreads)',
      'Custom formula builder: type any algebraic expression using column names from Final.xlsx',
      'Plotly chart with date-range filter and Bloomberg dark styling',
    ],
  },
  {
    id: 3,
    version: '1.03',
    timestamp: '28 Jul 2026',
    category: 'Feature',
    title: 'Google OAuth authentication + Firebase user management',
    description: [
      'auth/authenticator.py — Google OAuth2 PKCE flow; JWT tokens stored in browser localStorage',
      'firebase_utils.py — Firestore user records; admin allow-list via ADMINS env variable',
      'Restricted pages (Changelog, Data Sources, Roadmap) visible only to admins',
    ],
  },
  {
    id: 1,
    version: '1.00',
    timestamp: 'Jul 2026',
    category: 'Feature',
    title: 'Initial Streamlit app launch — Bond Analytics v1',
    description: [
      'Streamlit app with Final.xlsx as the core data store (34 time-series columns: Eurex/US/cross-country yields, equity indices, commodities)',
      'Bond Analytics page: spread grid with 20 preset formulas (Eurex 2Y/5Y/10Y/30Y flies and spreads, US Treasuries, cross-country comparisons)',
      'Global Macro Dashboard: IMF WEO data for 16 countries — GDP, CPI, debt, fiscal balance, unemployment',
      'Global Yield Curves: 10Y govt bond yields for 11 countries from FRED + ECB Svensson curve',
    ],
  },
]

export default function Changelog() {
  return (
    <div className="content-wrap" style={{ maxWidth: 900 }}>
      <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginBottom: 24 }}>
        {Object.entries(CATEGORY_COLORS).map(([cat, { bg, text }]) => (
          <span key={cat} style={{ padding: '2px 10px', borderRadius: 4, background: bg, color: text, fontSize: 11, fontWeight: 600 }}>{cat}</span>
        ))}
      </div>

      <div style={{ display: 'grid', gap: 10 }}>
        {CHANGELOG.map(entry => {
          const { bg, text } = CATEGORY_COLORS[entry.category] ?? { bg: 'rgba(148,163,184,0.12)', text: '#94a3b8' }
          return (
            <div key={entry.id} style={{ background: '#1a1a1a', border: '1px solid #2a2a2a', borderRadius: 8, padding: '14px 18px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap', marginBottom: 8 }}>
                <span style={{ fontFamily: 'monospace', fontSize: 11, fontWeight: 700, background: '#0d0d0d', color: '#f39200', padding: '2px 8px', borderRadius: 4 }}>v{entry.version}</span>
                <span style={{ padding: '2px 9px', borderRadius: 4, background: bg, color: text, fontSize: 11, fontWeight: 600 }}>{entry.category}</span>
                <span style={{ color: '#444', fontSize: 11 }}>{entry.timestamp}</span>
              </div>
              <div style={{ color: '#e8e8e8', fontWeight: 600, fontSize: 13, marginBottom: 8 }}>{entry.title}</div>
              <ul style={{ margin: 0, paddingLeft: 18 }}>
                {entry.description.map((line, i) => (
                  <li key={i} style={{ color: '#888', fontSize: 12, lineHeight: 1.6 }}>{line}</li>
                ))}
              </ul>
            </div>
          )
        })}
      </div>
    </div>
  )
}
