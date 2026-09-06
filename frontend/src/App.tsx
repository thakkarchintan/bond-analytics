import { useState } from 'react'
import {
  BarChart3, TrendingUp, Globe, Activity, Settings2,
  History, PanelLeftClose, PanelLeftOpen, ChevronDown, RefreshCw,
  LayoutDashboard,
} from 'lucide-react'
import BondAnalyticsPage from './pages/BondAnalytics'
import CapitalMarketsPage from './pages/CapitalMarkets'
import MacroDashboardPage from './pages/MacroDashboard'

type Page = 'Bond Analytics' | 'Macro Dashboard' | 'Global Capital Markets' | 'Yield Curves' | 'Credit Spreads' | 'Cross Asset' | 'Settings'

const navItems: Array<{ label: Page; icon: typeof BarChart3; soon?: boolean }> = [
  { label: 'Bond Analytics',         icon: BarChart3 },
  { label: 'Macro Dashboard',        icon: LayoutDashboard },
  { label: 'Global Capital Markets', icon: Globe },
  { label: 'Yield Curves',           icon: TrendingUp, soon: true },
  { label: 'Credit Spreads',         icon: Activity,   soon: true },
  { label: 'Cross Asset',            icon: History,    soon: true },
  { label: 'Settings',               icon: Settings2,  soon: true },
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
  'Global Capital Markets': {
    eyebrow: 'MACRO · 10 COUNTRIES',
    title: 'Global Capital Markets',
    subtitle: 'Equity vs government bond markets · market size vs GDP · historical evolution 2005–2023.',
  },
  'Yield Curves': {
    eyebrow: 'RATES · TERM STRUCTURE',
    title: 'Yield Curves',
    subtitle: 'Government yield curves across maturities and countries.',
  },
  'Credit Spreads': {
    eyebrow: 'CREDIT · FIXED INCOME',
    title: 'Credit Spreads',
    subtitle: 'Investment grade and high yield credit spread analysis.',
  },
  'Cross Asset': {
    eyebrow: 'MACRO · MULTI-ASSET',
    title: 'Cross Asset',
    subtitle: 'Equity, rates, FX, and commodities in one view.',
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
              <div className="brand-sub">Bloomberg Terminal</div>
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
          {!collapsed && <div className="sidebar-group-label">ANALYTICS</div>}
          {navItems.map(({ label, icon: Icon, soon }) => (
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
          {page === 'Bond Analytics'         && <BondAnalyticsPage />}
          {page === 'Macro Dashboard'        && <MacroDashboardPage />}
          {page === 'Global Capital Markets' && <CapitalMarketsPage />}
          {!['Bond Analytics', 'Macro Dashboard', 'Global Capital Markets'].includes(page) && (
            <div className="content-wrap">
              <div className="placeholder-state">
                <Settings2 size={40} />
                <div className="section-title" style={{ marginBottom: 8 }}>{page}</div>
                <p>This section is coming soon. The Bond Analytics and Global Capital Markets pages are available now.</p>
              </div>
            </div>
          )}
        </div>
      </main>
    </div>
  )
}
