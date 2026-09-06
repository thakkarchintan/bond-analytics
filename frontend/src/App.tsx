import { useState } from 'react'
import {
  BarChart3, TrendingUp, Globe, Activity, Settings2,
  History, PanelLeftClose, PanelLeftOpen, ChevronDown, RefreshCw,
  LayoutDashboard, DollarSign, Landmark, LineChart, Zap,
} from 'lucide-react'
import BondAnalyticsPage from './pages/BondAnalytics'
import CapitalMarketsPage from './pages/CapitalMarkets'
import MacroDashboardPage from './pages/MacroDashboard'
import YieldCurvesPage from './pages/YieldCurves'
import CentralBankRatesPage from './pages/CentralBankRates'
import CreditSpreadsPage from './pages/CreditSpreads'
import FXCurrenciesPage from './pages/FXCurrencies'
import CrossAssetPage from './pages/CrossAsset'
import LeadingIndicatorsPage from './pages/LeadingIndicators'
import InflationGrowthPage from './pages/InflationGrowth'
import FiscalScorecardPage from './pages/FiscalScorecard'
import BondCalculatorPage from './pages/BondCalculator'
import HeatmapPage from './pages/Heatmap'
import HistoricalShocksPage from './pages/HistoricalShocks'
import CurveTradeBuilderPage from './pages/CurveTradeBuilder'
import NewsSummaryPage from './pages/NewsSummary'
import BondPortfolioPage from './pages/BondPortfolio'
import BondSimulatorPage from './pages/BondSimulator'
import DataSourcesPage from './pages/DataSources'
import ChangelogPage from './pages/Changelog'
import RoadmapPage from './pages/Roadmap'

type Page =
  | 'Bond Analytics'
  | 'Macro Dashboard'
  | 'Yield Curves'
  | 'Central Bank Rates'
  | 'Credit Spreads'
  | 'FX Currencies'
  | 'Cross Asset'
  | 'Leading Indicators'
  | 'Inflation & Growth'
  | 'Fiscal Scorecard'
  | 'Global Capital Markets'
  | 'Bond Calculator'
  | 'Historical Shocks'
  | 'Curve Trade Builder'
  | 'Heatmap'
  | 'Bond Portfolio'
  | 'Bond Simulator'
  | 'News Summary'
  | 'Data Sources'
  | 'Changelog'
  | 'Roadmap'
  | 'Settings'

const navGroups: Array<{
  label: string
  items: Array<{ label: Page; icon: typeof BarChart3; soon?: boolean }>
}> = [
  {
    label: 'FIXED INCOME',
    items: [
      { label: 'Bond Analytics',    icon: BarChart3 },
      { label: 'Yield Curves',      icon: TrendingUp },
      { label: 'Credit Spreads',    icon: Activity },
      { label: 'Bond Calculator',   icon: BarChart3 },
      { label: 'Historical Shocks', icon: History },
      { label: 'Curve Trade Builder', icon: LineChart },
      { label: 'Heatmap',           icon: Activity },
      { label: 'Bond Portfolio',    icon: BarChart3 },
      { label: 'Bond Simulator',    icon: LineChart },
    ],
  },
  {
    label: 'MACRO',
    items: [
      { label: 'Macro Dashboard',     icon: LayoutDashboard },
      { label: 'Central Bank Rates',  icon: Landmark },
      { label: 'FX Currencies',       icon: DollarSign },
      { label: 'Cross Asset',         icon: LineChart },
      { label: 'Leading Indicators',  icon: Zap },
      { label: 'Inflation & Growth',  icon: History },
      { label: 'Fiscal Scorecard',    icon: History },
      { label: 'Global Capital Markets', icon: Globe },
      { label: 'News Summary',      icon: Globe },
    ],
  },
  {
    label: 'ADMIN',
    items: [
      { label: 'Data Sources', icon: Activity },
      { label: 'Changelog',    icon: History },
      { label: 'Roadmap',      icon: BarChart3 },
    ],
  },
  {
    label: 'SYSTEM',
    items: [
      { label: 'Settings', icon: Settings2, soon: true },
    ],
  },
]

const pageHeadings: Record<Page, { eyebrow: string; title: string; subtitle: string }> = {
  'Bond Analytics': {
    eyebrow: 'FIXED INCOME · RATES',
    title: 'Bond Analytics',
    subtitle: 'Eurex, US Treasuries, cross-country spreads, flies, and custom formula charts.',
  },
  'Macro Dashboard': {
    eyebrow: 'MACRO · IMF · FRED · BIS',
    title: 'Global Macro Dashboard',
    subtitle: 'GDP, inflation, debt, fiscal balance, 10Y yields and policy rates across 16 countries.',
  },
  'Yield Curves': {
    eyebrow: 'RATES · TERM STRUCTURE',
    title: 'Yield Curves',
    subtitle: '10Y government bond yields across 11 countries + ECB Svensson term structure.',
  },
  'Central Bank Rates': {
    eyebrow: 'MONETARY POLICY · BIS',
    title: 'Central Bank Rates',
    subtitle: 'Policy rates and balance sheets for major central banks.',
  },
  'Credit Spreads': {
    eyebrow: 'CREDIT · FIXED INCOME · ICE BofA',
    title: 'Credit Spreads',
    subtitle: 'Investment grade and high yield OAS credit spreads, rating ladder AAA–CCC.',
  },
  'FX Currencies': {
    eyebrow: 'FX · CURRENCIES · BIS',
    title: 'FX Currencies',
    subtitle: 'FX spot rates vs USD and real effective exchange rates (REER) for 14 currencies.',
  },
  'Cross Asset': {
    eyebrow: 'MACRO · MULTI-ASSET · FRED',
    title: 'Cross Asset',
    subtitle: 'S&P 500, VIX, and WTI crude oil — equity, volatility, and energy in one view.',
  },
  'Leading Indicators': {
    eyebrow: 'MACRO · OECD · FRED',
    title: 'Leading Indicators',
    subtitle: 'US leading indicators and OECD CLI/BCI/CCI for 29 countries.',
  },
  'Inflation & Growth': {
    eyebrow: 'MACRO · IMF WEO',
    title: 'Inflation & Growth',
    subtitle: 'CPI inflation, real GDP growth, and unemployment across 16 countries.',
  },
  'Fiscal Scorecard': {
    eyebrow: 'FISCAL · IMF WEO',
    title: 'Fiscal Scorecard',
    subtitle: 'Debt/GDP, fiscal balance, primary balance, and current account across 16 countries.',
  },
  'Global Capital Markets': {
    eyebrow: 'MACRO · 10 COUNTRIES · WORLD BANK',
    title: 'Global Capital Markets',
    subtitle: 'Equity vs government bond markets · market size vs GDP · historical evolution 2005–2023.',
  },
  'Bond Calculator': {
    eyebrow: 'FIXED INCOME · ANALYTICS',
    title: 'Bond Calculator',
    subtitle: 'Price, yield, Macaulay/Modified duration, DV01, convexity, and P&L sensitivity — client-side math.',
  },
  'Historical Shocks': {
    eyebrow: 'FIXED INCOME · HISTORY',
    title: 'Historical Shocks',
    subtitle: 'Compare market behaviour across GFC, Euro Crisis, Taper Tantrum, COVID, and rate hike cycles.',
  },
  'Curve Trade Builder': {
    eyebrow: 'FIXED INCOME · RATES',
    title: 'Curve Trade Builder',
    subtitle: '2-leg spreads and 3-leg butterflies — historical levels, z-scores, and estimated P&L.',
  },
  'Heatmap': {
    eyebrow: 'FIXED INCOME · CORRELATION',
    title: 'Correlation Heatmap',
    subtitle: 'Pearson correlation matrix for yields, equities, and commodities over any date range.',
  },
  'Bond Portfolio': {
    eyebrow: 'FIXED INCOME · RISK',
    title: 'Bond Portfolio Analytics',
    subtitle: 'Market value, duration, DV01, convexity, and P&L sensitivity for a multi-bond portfolio.',
  },
  'Bond Simulator': {
    eyebrow: 'FIXED INCOME · MONTE CARLO',
    title: 'Monte Carlo Bond Simulator',
    subtitle: 'GBM yield simulation — price distribution, VaR, CVaR, and yield fan at horizon.',
  },
  'Data Sources': {
    eyebrow: 'ADMIN · DATA CATALOG',
    title: 'Data Sources',
    subtitle: 'All 16 parquet-backed datasets — source, coverage, frequency, lag type, and alternatives.',
  },
  'Changelog': {
    eyebrow: 'ADMIN · RELEASE NOTES',
    title: 'Changelog',
    subtitle: 'Full deployment history from Streamlit v1.0 through the React/Vite migration.',
  },
  'Roadmap': {
    eyebrow: 'ADMIN · PRODUCT',
    title: 'Roadmap',
    subtitle: 'Architecture decisions, new page backlog, and data source expansion pipeline.',
  },
  'News Summary': {
    eyebrow: 'MARKETS · NEWSAPI',
    title: 'News Summary',
    subtitle: 'Live bond and macro news with AI-generated summary.',
  },
  'Settings': {
    eyebrow: 'PREFERENCES',
    title: 'Settings',
    subtitle: 'Configure data sources and display preferences.',
  },
}

export default function App() {
  const [page, setPage] = useState<Page>('Bond Analytics')
  const [collapsed, setCollapsed] = useState(false)

  const h = pageHeadings[page]

  return (
    <div className="app-shell">
      {/* ── Sidebar ── */}
      <aside className={`sidebar ${collapsed ? 'sidebar-collapsed' : ''}`}>
        <div className="brand">
          {!collapsed && (
            <div>
              <div className="brand-name">Bond Analytics</div>
              <div className="brand-sub">Global Fixed Income</div>
            </div>
          )}
          <button
            className="sidebar-toggle"
            title={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
            onClick={() => setCollapsed(c => !c)}
          >
            {collapsed ? <PanelLeftOpen size={14} /> : <PanelLeftClose size={14} />}
          </button>
        </div>

        <nav>
          {navGroups.map(group => (
            <div key={group.label}>
              {!collapsed && <div className="sidebar-group-label">{group.label}</div>}
              {group.items.map(({ label, icon: Icon, soon }) => (
                <button
                  key={label}
                  title={label}
                  className={`nav-item ${page === label ? 'active' : ''}`}
                  onClick={() => !soon && setPage(label)}
                >
                  <Icon size={15} />
                  <span>{label}</span>
                  {soon && <span className="nav-soon">SOON</span>}
                </button>
              ))}
            </div>
          ))}
        </nav>

        <div className="sidebar-bottom">
          <div className="profile">
            <div className="avatar">CT</div>
            {!collapsed && (
              <>
                <div>
                  <b>Chintan T.</b>
                  <small>Analyst</small>
                </div>
                <ChevronDown size={13} />
              </>
            )}
          </div>
        </div>
      </aside>

      {/* ── Main ── */}
      <main className="main-area">
        <header className="topbar">
          <div className="topbar-heading">
            <div className="eyebrow">{h.eyebrow}</div>
            <div className="page-title">{h.title}</div>
            <div className="topbar-subtitle">{h.subtitle}</div>
          </div>
          <div className="top-actions">
            <span className="live-badge"><span className="live-dot" />LIVE</span>
            <button className="icon-button" title="Refresh" onClick={() => window.location.reload()}>
              <RefreshCw size={16} />
            </button>
            <button className="user-chip">CT</button>
          </div>
        </header>

        <div className="main-scroll">
          {page === 'Bond Analytics'        && <BondAnalyticsPage />}
          {page === 'Macro Dashboard'       && <MacroDashboardPage />}
          {page === 'Yield Curves'          && <YieldCurvesPage />}
          {page === 'Central Bank Rates'    && <CentralBankRatesPage />}
          {page === 'Credit Spreads'        && <CreditSpreadsPage />}
          {page === 'FX Currencies'         && <FXCurrenciesPage />}
          {page === 'Cross Asset'           && <CrossAssetPage />}
          {page === 'Leading Indicators'    && <LeadingIndicatorsPage />}
          {page === 'Inflation & Growth'    && <InflationGrowthPage />}
          {page === 'Fiscal Scorecard'      && <FiscalScorecardPage />}
          {page === 'Global Capital Markets'&& <CapitalMarketsPage />}
          {page === 'Bond Calculator'       && <BondCalculatorPage />}
          {page === 'Historical Shocks'     && <HistoricalShocksPage />}
          {page === 'Curve Trade Builder'   && <CurveTradeBuilderPage />}
          {page === 'Heatmap'              && <HeatmapPage />}
          {page === 'Bond Portfolio'       && <BondPortfolioPage />}
          {page === 'Bond Simulator'       && <BondSimulatorPage />}
          {page === 'News Summary'         && <NewsSummaryPage />}
          {page === 'Data Sources'         && <DataSourcesPage />}
          {page === 'Changelog'            && <ChangelogPage />}
          {page === 'Roadmap'              && <RoadmapPage />}
          {page === 'Settings' && (
            <div className="content-wrap">
              <div className="placeholder-state">
                <Settings2 size={40} />
                <div className="section-title" style={{ marginBottom: 8 }}>Settings</div>
                <p>Configuration options coming soon.</p>
              </div>
            </div>
          )}
        </div>
      </main>
    </div>
  )
}
