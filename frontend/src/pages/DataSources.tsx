import { useState } from 'react'

interface DataEntry {
  group: string
  name: string
  cache: string
  pages: string[]
  frequency: string
  coverage: string
  source_url?: string
  via?: string
  via_url?: string
  notes: string
  lag_type: 'structural' | 'fixable'
  alternatives?: string
}

const CATALOG: DataEntry[] = [
  // FRED
  {
    group: 'FRED — Federal Reserve Economic Data',
    name: 'US Treasury Yield Curve',
    cache: 'gmacro_us_curve_cache.parquet',
    pages: ['Yield Curves'],
    frequency: 'Daily',
    coverage: 'United States · 11 maturities (1M–30Y)',
    source_url: 'https://fred.stlouisfed.org',
    notes: 'FRED DGS series (constant-maturity Treasury yields). Highly current.',
    lag_type: 'structural',
    alternatives: 'US Treasury direct (same data); Bloomberg (paid)',
  },
  {
    group: 'FRED — Federal Reserve Economic Data',
    name: 'Breakeven Inflation & TIPS Real Yields',
    cache: 'gmacro_breakeven_cache.parquet',
    pages: ['Inflation & Growth'],
    frequency: 'Daily',
    coverage: 'United States · 5Y/10Y breakeven, 5-10Y forward, 5Y/10Y real yield',
    source_url: 'https://fred.stlouisfed.org',
    notes: 'FRED T5YIE, T10YIE, T5YIFR, DFII5, DFII10. Fed\'s preferred inflation expectations.',
    lag_type: 'structural',
    alternatives: 'Cleveland Fed inflation expectations model (daily, model-based)',
  },
  {
    group: 'FRED — Federal Reserve Economic Data',
    name: 'Cross-Asset (VIX · WTI Crude · S&P 500)',
    cache: 'gmacro_cross_asset_cache.parquet',
    pages: ['Cross Asset'],
    frequency: 'Daily',
    coverage: 'United States · 3 series',
    source_url: 'https://fred.stlouisfed.org',
    notes: 'VIXCLS, DCOILWTICO, SP500. Gold (GOLDAMGBD228NLBM) and ISM PMI (NAPM) both 404 on FRED CSV.',
    lag_type: 'structural',
    alternatives: 'Yahoo Finance (same data, no auth); Alpha Vantage (paid for intraday)',
  },
  {
    group: 'FRED — Federal Reserve Economic Data',
    name: 'FX Spot Rates vs USD',
    cache: 'gmacro_fx_cache.parquet',
    pages: ['FX Currencies'],
    frequency: 'Daily',
    coverage: '14 currencies vs USD (EUR, GBP, JPY, CNY, INR, BRL, KRW, MXN, AUD, CAD, CHF, NOK, SEK, ZAR)',
    source_url: 'https://fred.stlouisfed.org',
    notes: 'FRED H.10 bilateral exchange rates. ~1 week lag for some EM pairs.',
    lag_type: 'structural',
    alternatives: 'ECB reference rates (EUR pairs, daily); BIS (cross-rates)',
  },
  {
    group: 'FRED — Federal Reserve Economic Data',
    name: 'US Leading Indicators',
    cache: 'gmacro_leading_cache.parquet',
    pages: ['Leading Indicators'],
    frequency: 'Weekly / Monthly',
    coverage: 'United States · 7 series (Claims, Sentiment, Housing, INDPRO, Unemployment, 2Y10Y, NBER Recession)',
    source_url: 'https://fred.stlouisfed.org',
    notes: 'Initial claims weekly; others monthly. USREC is NBER recession indicator (lagged by definition).',
    lag_type: 'structural',
    alternatives: 'Conference Board LEI (monthly, broader composite)',
  },
  {
    group: 'FRED — Federal Reserve Economic Data',
    name: 'Money Market Rates (SOFR · Fed Funds)',
    cache: 'gmacro_mmkt_cache.parquet',
    pages: ['Central Bank Rates'],
    frequency: 'Daily',
    coverage: 'United States · 2 series',
    source_url: 'https://fred.stlouisfed.org',
    notes: 'SOFR (SOFR series), Effective Fed Funds Rate (DFF). SOFR since 2018.',
    lag_type: 'structural',
    alternatives: 'NY Fed direct (SOFR official source); CME (SOFR futures-implied)',
  },
  {
    group: 'FRED — Federal Reserve Economic Data',
    name: 'ICE BofA OAS Credit Spreads',
    cache: 'gmacro_spreads_cache.parquet',
    pages: ['Credit Spreads', 'Cross Asset'],
    frequency: 'Daily',
    coverage: 'US market · 9 series (AAA/AA/A/BBB/BB/B/CCC/IG/HY)',
    source_url: 'https://fred.stlouisfed.org',
    notes: 'FRED redistributes ICE BofA indices. IG + HY historical cache (gmacro_spreads_long_cache.parquet) back to 1996.',
    lag_type: 'structural',
    alternatives: 'ICE BofA Index Tool (paid); Bloomberg BAML indices (paid)',
  },
  {
    group: 'FRED — Federal Reserve Economic Data',
    name: '10Y Government Bond Yields (Multi-Country)',
    cache: 'gmacro_yields_cache.parquet',
    pages: ['Central Bank Rates'],
    frequency: 'Monthly',
    coverage: '11 countries (US, UK, Euro Area, Japan, Canada, Australia, Norway, Sweden, S.Korea, NZ, CH)',
    source_url: 'https://fred.stlouisfed.org',
    notes: 'FRED IRLT (OECD long-term rates) for DMs. Monthly average.',
    lag_type: 'structural',
    alternatives: 'OECD.Stat (same IRLT data, possibly fresher); ECB SDW (Euro Area daily)',
  },
  {
    group: 'FRED — Federal Reserve Economic Data',
    name: 'CB Policy Rates Direct (US · Euro Area)',
    cache: 'gmacro_cb_rates_cache.parquet',
    pages: ['Central Bank Rates'],
    frequency: 'Monthly',
    coverage: 'United States · Euro Area',
    source_url: 'https://fred.stlouisfed.org',
    notes: 'Fallback when BIS CBPOL is unavailable. FRED FEDFUNDS + ECB SDW MRO rate.',
    lag_type: 'structural',
    alternatives: 'BIS WS_CBPOL (primary; 25 CBs); BoE directly for GBP',
  },
  // ECB
  {
    group: 'ECB — European Central Bank',
    name: 'Euro Area AAA Govt Bond Yield Curve',
    cache: 'dbn_ecb_yc_cache.parquet',
    pages: ['Yield Curves'],
    frequency: 'Daily',
    coverage: 'Euro Area · 8 maturities (3M · 6M · 1Y · 2Y · 5Y · 10Y · 20Y · 30Y)',
    source_url: 'https://www.ecb.europa.eu/stats/financial_markets_and_interest_rates/euro_area_yield_curves',
    via: 'DBnomics',
    via_url: 'https://db.nomics.world/ECB/YC',
    notes: 'ECB Svensson model spot rates. Restricted to AAA-rated euro area sovereign bonds. Dataset: ECB/YC.',
    lag_type: 'structural',
    alternatives: 'ECB SDW direct API (same data, same day); Refinitiv/Bloomberg (paid)',
  },
  // BIS
  {
    group: 'BIS — Bank for International Settlements',
    name: 'Central Bank Policy Rates',
    cache: 'dbn_cbpol_cache.parquet',
    pages: ['Central Bank Rates'],
    frequency: 'Daily',
    coverage: '25 central banks (Fed, ECB, BoE, BoJ, PBoC, RBI, BCB, SARB + 17 others)',
    source_url: 'https://www.bis.org/statistics/cbpol.htm',
    via: 'DBnomics',
    via_url: 'https://db.nomics.world/BIS/WS_CBPOL',
    notes: 'Dataset: BIS/WS_CBPOL. History back to 1946 for some CBs. ~1 month structural lag.',
    lag_type: 'structural',
    alternatives: 'FRED (US only, daily); ECB SDW (Euro Area, daily); individual CB websites',
  },
  {
    group: 'BIS — Bank for International Settlements',
    name: 'Central Bank Total Assets (Balance Sheets)',
    cache: 'dbn_cbta_cache.parquet',
    pages: ['Central Bank Rates'],
    frequency: 'Monthly',
    coverage: '8 central banks (Fed, ECB, BoJ, BoE, PBoC, SNB, BoC, RBA) · USD bn',
    source_url: 'https://www.bis.org/statistics/',
    via: 'DBnomics',
    via_url: 'https://db.nomics.world/BIS/WS_CBTA',
    notes: 'Dataset: BIS/WS_CBTA. ~3–4 month structural lag (BIS release schedule). History back to 1914 (Fed).',
    lag_type: 'structural',
    alternatives: 'Individual CB balance sheet releases; Fed H.4.1 (weekly, US only)',
  },
  {
    group: 'BIS — Bank for International Settlements',
    name: 'Real Effective Exchange Rates (REER)',
    cache: 'dbn_eer_cache.parquet',
    pages: ['FX Currencies'],
    frequency: 'Monthly',
    coverage: '14 currencies (USD/EUR/GBP/JPY/CNY/AUD/CAD/CHF/KRW/INR/BRL/NOK/SEK/MXN) · 2020=100',
    source_url: 'https://www.bis.org/statistics/eer.htm',
    via: 'DBnomics',
    via_url: 'https://db.nomics.world/BIS/WS_EER',
    notes: 'Dataset: BIS/WS_EER real broad basket (up to 64 economies, trade-weighted). ~2 month structural lag.',
    lag_type: 'structural',
    alternatives: 'IMF REER (IFS dataset, similar methodology)',
  },
  // OECD
  {
    group: 'OECD — Organisation for Economic Co-operation and Development',
    name: 'Business / Consumer / Composite Leading Indicators (BCI · CCI · CLI)',
    cache: 'dbn_oecd_bc_cache.parquet',
    pages: ['Leading Indicators', 'Global Business Cycle'],
    frequency: 'Monthly',
    coverage: '29 countries + OECD aggregates · BCI (29) · CCI (27) · CLI (16)',
    source_url: 'https://stats.oecd.org/',
    via: 'DBnomics',
    via_url: 'https://db.nomics.world/OECD/DP_LIVE',
    notes: 'Dataset: OECD/DP_LIVE. DBnomics mirror is ~3 years stale (Nov 2023); direct OECD.Stat API returns 403. LTRENDIDX: 100 = long-run trend.',
    lag_type: 'fixable',
    alternatives: 'OECD.Stat direct (same data, current — API access issues); FRED has some OECD CLI series (US/G7 only, but current)',
  },
  // IMF
  {
    group: 'IMF — International Monetary Fund',
    name: 'World Economic Outlook (WEO) — Annual Macro',
    cache: 'gmacro_annual_cache.parquet',
    pages: ['Macro Dashboard', 'Central Bank Rates', 'Fiscal Scorecard', 'Inflation & Growth'],
    frequency: 'Annual',
    coverage: '16 countries · GDP · CPI · Fiscal balance · Debt/GDP · Current account · Unemployment',
    source_url: 'https://www.imf.org/en/Publications/WEO',
    notes: 'IMF WEO API. Annual data; projections 2–3 years ahead. Updated twice yearly (Apr/Oct).',
    lag_type: 'structural',
    alternatives: 'World Bank WDI (similar annual macro, broader country coverage)',
  },
  // Internal
  {
    group: 'Internal / Manual',
    name: 'Global Capital Markets',
    cache: 'capital_markets_cache.parquet',
    pages: ['Global Capital Markets'],
    frequency: 'Annual',
    coverage: '10 countries · Equity mkt cap · Govt bond stock · Debt/GDP · Listed companies',
    notes: 'Manually curated from World Bank, SIFMA, WFE, and IMF datasets. Static snapshot.',
    lag_type: 'fixable',
    alternatives: 'World Bank GFDD (Global Financial Development Database); BIS debt securities statistics; SIFMA Research',
  },
]

const GROUPS = ['All', ...Array.from(new Set(CATALOG.map(d => d.group)))]

const LAG_ICON: Record<string, string> = { structural: '🔒', fixable: '⚠️' }
const LAG_NOTE: Record<string, string> = {
  structural: 'Source releases on this schedule — no faster alternative.',
  fixable: 'Fresher data may be available — see alternatives.',
}

export default function DataSources() {
  const [selGroup, setSelGroup] = useState('All')

  const filtered = selGroup === 'All' ? CATALOG : CATALOG.filter(d => d.group === selGroup)

  const grouped: Record<string, DataEntry[]> = {}
  for (const d of filtered) {
    if (!grouped[d.group]) grouped[d.group] = []
    grouped[d.group].push(d)
  }

  return (
    <div className="content-wrap" style={{ maxWidth: 1000 }}>
      {/* Summary strip */}
      <div className="kpi-strip" style={{ marginBottom: 24 }}>
        {[
          { label: 'Total Datasets', val: CATALOG.length, color: '#f39200' },
          { label: 'Daily Feeds', val: CATALOG.filter(d => d.frequency === 'Daily').length, color: '#00c087' },
          { label: 'Via DBnomics', val: CATALOG.filter(d => d.via === 'DBnomics').length, color: '#a78bfa' },
          { label: 'Fixable Lag', val: CATALOG.filter(d => d.lag_type === 'fixable').length, color: '#fbbf24' },
        ].map(({ label, val, color }) => (
          <div key={label} className="kpi-card">
            <div style={{ color: '#888', fontSize: 10, textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 4 }}>{label}</div>
            <div style={{ color, fontSize: 22, fontWeight: 700, fontVariantNumeric: 'tabular-nums' }}>{val}</div>
          </div>
        ))}
      </div>

      {/* Filter */}
      <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginBottom: 24 }}>
        {GROUPS.map(g => (
          <button
            key={g}
            onClick={() => setSelGroup(g)}
            style={{
              padding: '5px 12px', borderRadius: 5, fontSize: 11, cursor: 'pointer',
              background: selGroup === g ? 'rgba(243,146,0,0.15)' : 'transparent',
              border: `1px solid ${selGroup === g ? '#f39200' : '#2a2a2a'}`,
              color: selGroup === g ? '#f39200' : '#888',
            }}
          >
            {g.split('—')[0].trim()}
          </button>
        ))}
      </div>

      {/* Cards */}
      {Object.entries(grouped).map(([group, entries]) => (
        <div key={group}>
          <div style={{ fontSize: 11, fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.1em', color: '#555', margin: '24px 0 10px', borderBottom: '1px solid #1f1f1f', paddingBottom: 6 }}>
            {group}
          </div>
          {entries.map(entry => (
            <div key={entry.name} style={{ background: '#1a1a1a', border: '1px solid #2a2a2a', borderRadius: 8, padding: '14px 18px', marginBottom: 10 }}>
              <div style={{ display: 'flex', alignItems: 'flex-start', gap: 8, flexWrap: 'wrap', marginBottom: 6 }}>
                <div style={{ color: '#e8e8e8', fontWeight: 600, fontSize: 13, flex: 1, minWidth: 0 }}>{entry.name}</div>
                {entry.lag_type === 'fixable' && (
                  <span style={{ fontSize: 10, fontWeight: 700, color: '#fbbf24', background: 'rgba(251,191,36,0.1)', border: '1px solid rgba(251,191,36,0.3)', borderRadius: 3, padding: '1px 7px', whiteSpace: 'nowrap' }}>
                    ⚠️ fixable lag
                  </span>
                )}
              </div>

              <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', marginBottom: 8 }}>
                <span style={{ fontSize: 11, background: '#111', border: '1px solid #2a2a2a', borderRadius: 4, color: '#888', padding: '2px 8px' }}>{entry.frequency}</span>
                <span style={{ fontSize: 11, background: '#111', border: '1px solid #2a2a2a', borderRadius: 4, color: '#aaa', padding: '2px 8px', fontFamily: 'monospace' }}>{entry.cache}</span>
              </div>

              <div style={{ fontSize: 12, color: '#888', lineHeight: 1.6, marginBottom: 4 }}>
                <b style={{ color: '#666' }}>Pages:</b> {entry.pages.join(' · ')}
                {' '}·{' '}
                <b style={{ color: '#666' }}>Coverage:</b> {entry.coverage}
              </div>

              <div style={{ fontSize: 12, color: '#888', lineHeight: 1.6, marginBottom: 4 }}>
                <b style={{ color: '#666' }}>Source:</b>{' '}
                {entry.source_url
                  ? <a href={entry.source_url} target="_blank" rel="noopener noreferrer" style={{ color: '#60a5fa', textDecoration: 'none' }}>{new URL(entry.source_url).hostname}</a>
                  : 'Internal'
                }
                {entry.via && (
                  <> &nbsp;·&nbsp; <b style={{ color: '#666' }}>via</b>{' '}
                    <a href={entry.via_url} target="_blank" rel="noopener noreferrer" style={{ color: '#a78bfa', textDecoration: 'none', fontWeight: 600 }}>{entry.via}</a>
                  </>
                )}
              </div>

              <div style={{ fontSize: 12, color: '#666', fontStyle: 'italic', lineHeight: 1.6 }}>{entry.notes}</div>

              {entry.alternatives && (
                <div style={{ fontSize: 11, color: '#555', marginTop: 8, borderTop: '1px solid #222', paddingTop: 8 }}>
                  <span style={{ color: '#444' }}>💡 </span>
                  <b style={{ color: '#555' }}>Alternatives:</b> {entry.alternatives}
                </div>
              )}

              <div style={{ fontSize: 10, color: '#3a3a3a', marginTop: 6 }}>
                {LAG_ICON[entry.lag_type]} {LAG_NOTE[entry.lag_type]}
              </div>
            </div>
          ))}
        </div>
      ))}

      {/* Quick reference table */}
      <div style={{ borderLeft: '3px solid #f39200', padding: '10px 14px', background: 'rgba(243,146,0,0.04)', borderRadius: '0 6px 6px 0', margin: '32px 0 12px' }}>
        <div style={{ color: '#e8e8e8', fontWeight: 600, fontSize: 13, textTransform: 'uppercase', letterSpacing: '0.04em' }}>Quick Reference</div>
      </div>
      <div style={{ overflowX: 'auto' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 11 }}>
          <thead>
            <tr style={{ borderBottom: '1px solid #2a2a2a' }}>
              {['Dataset', 'Source', 'Via', 'Frequency', 'Lag Type', 'Pages'].map(h => (
                <th key={h} style={{ padding: '8px 10px', textAlign: 'left', color: '#555', fontWeight: 600, textTransform: 'uppercase', fontSize: 10, letterSpacing: '0.05em', whiteSpace: 'nowrap' }}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {CATALOG.map((d, i) => (
              <tr key={i} style={{ borderBottom: '1px solid #1a1a1a' }}>
                <td style={{ padding: '6px 10px', color: '#e8e8e8' }}>{d.name}</td>
                <td style={{ padding: '6px 10px', color: '#888' }}>{d.group.split('—')[0].trim()}</td>
                <td style={{ padding: '6px 10px', color: '#a78bfa' }}>{d.via ?? '—'}</td>
                <td style={{ padding: '6px 10px', color: '#aaa' }}>{d.frequency}</td>
                <td style={{ padding: '6px 10px' }}>
                  <span style={{ color: d.lag_type === 'fixable' ? '#fbbf24' : '#555', fontSize: 10, fontWeight: 600 }}>
                    {d.lag_type === 'fixable' ? '⚠️ fixable' : '🔒 structural'}
                  </span>
                </td>
                <td style={{ padding: '6px 10px', color: '#666', fontSize: 10 }}>{d.pages.join(', ')}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
