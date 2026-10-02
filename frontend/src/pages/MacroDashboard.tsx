import { useState, useEffect, useRef } from 'react'
import { RefreshCw } from 'lucide-react'
import apiFetch from '../api/client'

/* ── Types ──────────────────────────────────────────────────────────────────── */
interface MacroRow {
  Country: string
  Year: number
  GDP_USD_Bn: number | null
  RealGDP_Pct: number | null
  CPI_Pct: number | null
  FiscalBal_Pct: number | null
  PrimaryBal_Pct: number | null
  DebtGDP_Pct: number | null
  CurrentAcct_Pct: number | null
  Unemployment_Pct: number | null
  TenY_Yield: number | null
  Policy_Rate: number | null
  Govt_Debt_USD_Bn: number | null
}

/* ── Country palette (Bloomberg-adjacent) ───────────────────────────────────── */
const COLORS: Record<string, string> = {
  'United States':  '#60a5fa',
  'Euro Area':      '#a78bfa',
  'United Kingdom': '#22d3ee',
  'Japan':          '#34d399',
  'China':          '#f87171',
  'India':          '#f472b6',
  'Canada':         '#818cf8',
  'Australia':      '#fb923c',
  'Brazil':         '#a3e635',
  'South Korea':    '#fbbf24',
  'Switzerland':    '#e879f9',
  'Sweden':         '#2dd4bf',
  'Mexico':         '#c084fc',
  'South Africa':   '#f9a8d4',
  'Norway':         '#67e8f9',
  'New Zealand':    '#86efac',
}

const DEFAULT_COUNTRIES = ['United States', 'Euro Area', 'United Kingdom', 'Japan', 'China', 'India', 'Canada', 'Brazil']

/* ── Plotly chart wrapper ───────────────────────────────────────────────────── */
type PlotTrace = Record<string, unknown>
type PlotLayout = Record<string, unknown>

function Chart({ traces, layout }: { traces: PlotTrace[]; layout: PlotLayout }) {
  const ref = useRef<HTMLDivElement>(null)
  useEffect(() => {
    if (!ref.current || !traces.length) return
    let cancelled = false
    import('plotly.js-dist-min').then(Plotly => {
      if (cancelled || !ref.current) return
      const base: PlotLayout = {
        paper_bgcolor: '#1a1a1a',
        plot_bgcolor:  '#111111',
        font:   { color: '#aaa', family: 'system-ui,sans-serif', size: 11 },
        margin: { t: 36, r: 16, b: 44, l: 62 },
        xaxis:  { gridcolor: '#2a2a2a', tickfont: { color: '#777', size: 10 }, zerolinecolor: '#2a2a2a' },
        yaxis:  { gridcolor: '#2a2a2a', tickfont: { color: '#777', size: 10 }, zerolinecolor: '#444' },
        legend: { orientation: 'h', y: 1.12, x: 0, font: { color: '#aaa', size: 10 }, bgcolor: 'rgba(0,0,0,0)' },
        hovermode: 'x unified',
        hoverlabel: { bgcolor: '#1a1a1a', bordercolor: '#f39200', font: { color: '#e8e8e8' } },
        ...layout,
      }
      Plotly.react(ref.current!, traces as never, base as never, { responsive: true, displayModeBar: false })
    })
    return () => { cancelled = true }
  }, [traces, layout])
  return <div ref={ref} style={{ width: '100%', height: 340 }} />
}

/* ── Section header ─────────────────────────────────────────────────────────── */
function SectionHeader({ title, subtitle }: { title: string; subtitle: string }) {
  return (
    <div style={{
      borderLeft: '3px solid #f39200', paddingLeft: 12,
      margin: '28px 0 12px', background: 'rgba(243,146,0,0.04)',
      padding: '10px 14px', borderRadius: '0 6px 6px 0',
    }}>
      <div style={{ fontSize: 11, fontWeight: 700, color: '#f39200', textTransform: 'uppercase', letterSpacing: '0.08em' }}>{title}</div>
      <div style={{ fontSize: 11, color: '#666', marginTop: 3 }}>{subtitle}</div>
    </div>
  )
}

/* ── Build line traces from filtered data ───────────────────────────────────── */
function lineTraces(
  rows: MacroRow[],
  col: keyof MacroRow,
  countries: string[],
): PlotTrace[] {
  return countries.flatMap(c => {
    const pts = rows.filter(r => r.Country === c && r[col] != null).sort((a, b) => a.Year - b.Year)
    if (!pts.length) return []
    return [{
      x: pts.map(r => r.Year),
      y: pts.map(r => r[col] as number),
      name: c,
      type: 'scatter', mode: 'lines+markers',
      line: { color: COLORS[c] ?? '#888', width: 2 },
      marker: { size: 4 },
      hovertemplate: `<b>${c}</b><br>%{x}: %{y:.2f}<extra></extra>`,
    }]
  })
}

/* ── Bar trace for latest year ───────────────────────────────────────────────── */
function barTrace(rows: MacroRow[], col: keyof MacroRow, year: number, countries: string[]): PlotTrace[] {
  const pts = countries
    .map(c => rows.find(r => r.Country === c && r.Year === year && r[col] != null))
    .filter(Boolean) as MacroRow[]
  pts.sort((a, b) => ((b[col] as number) ?? 0) - ((a[col] as number) ?? 0))
  if (!pts.length) return []
  return [{
    x: pts.map(r => r.Country),
    y: pts.map(r => r[col] as number),
    type: 'bar',
    marker: { color: pts.map(r => COLORS[r.Country] ?? '#888') },
    hovertemplate: '%{x}: %{y:.1f}<extra></extra>',
  }]
}

/* ── KPI metric card ─────────────────────────────────────────────────────────── */
function KpiCard({ label, value }: { label: string; value: string }) {
  return (
    <div style={{
      background: '#1a1a1a', border: '1px solid #2a2a2a', borderRadius: 8,
      padding: '14px 12px', textAlign: 'center',
    }}>
      <div style={{ fontSize: 9, color: '#666', textTransform: 'uppercase', letterSpacing: '0.1em', marginBottom: 6 }}>{label}</div>
      <div style={{ fontSize: 20, fontWeight: 700, color: '#e8e8e8' }}>{value}</div>
    </div>
  )
}

/* ── Snapshot table ──────────────────────────────────────────────────────────── */
function SnapshotTable({ rows, year, countries }: { rows: MacroRow[]; year: number; countries: string[] }) {
  const cols: Array<{ key: keyof MacroRow; label: string; fmt: (v: number) => string }> = [
    { key: 'GDP_USD_Bn',      label: 'GDP USD bn',   fmt: v => v >= 1000 ? `$${(v/1000).toFixed(1)}tn` : `$${v.toFixed(0)}bn` },
    { key: 'RealGDP_Pct',    label: 'Growth %',      fmt: v => `${v.toFixed(1)}%` },
    { key: 'CPI_Pct',        label: 'Inflation %',   fmt: v => `${v.toFixed(1)}%` },
    { key: 'DebtGDP_Pct',    label: 'Debt/GDP %',    fmt: v => `${v.toFixed(0)}%` },
    { key: 'FiscalBal_Pct',  label: 'Fiscal Bal %',  fmt: v => `${v.toFixed(1)}%` },
    { key: 'TenY_Yield',     label: '10Y Yield %',   fmt: v => `${v.toFixed(2)}%` },
  ]
  const snap = countries.map(c => rows.find(r => r.Country === c && r.Year === year)).filter(Boolean) as MacroRow[]
  if (!snap.length) return null
  return (
    <div style={{ overflowX: 'auto', marginBottom: 20 }}>
      <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 12 }}>
        <thead>
          <tr style={{ borderBottom: '2px solid #2a2a2a' }}>
            <th style={{ padding: '9px 12px', textAlign: 'left', color: '#666', fontSize: 10, textTransform: 'uppercase', letterSpacing: '0.06em' }}>Country</th>
            {cols.map(c => (
              <th key={c.key} style={{ padding: '9px 12px', textAlign: 'center', color: '#666', fontSize: 10, textTransform: 'uppercase', letterSpacing: '0.06em' }}>{c.label}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {snap.map(row => (
            <tr key={row.Country} style={{ borderBottom: '1px solid #1e1e1e' }}>
              <td style={{ padding: '9px 12px', fontWeight: 600, color: COLORS[row.Country] ?? '#aaa' }}>{row.Country}</td>
              {cols.map(c => {
                const v = row[c.key] as number | null
                return (
                  <td key={c.key} style={{ padding: '9px 12px', textAlign: 'center', color: '#e8e8e8' }}>
                    {v != null ? c.fmt(v) : '—'}
                  </td>
                )
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

/* ── Scatter trace (correlation) ─────────────────────────────────────────────── */
function scatterTraces(rows: MacroRow[], xCol: keyof MacroRow, yCol: keyof MacroRow, countries: string[]): PlotTrace[] {
  return countries.flatMap(c => {
    const pts = rows.filter(r => r.Country === c && r[xCol] != null && r[yCol] != null)
    if (!pts.length) return []
    return [{
      x: pts.map(r => r[xCol] as number),
      y: pts.map(r => r[yCol] as number),
      name: c, type: 'scatter', mode: 'markers',
      marker: { color: COLORS[c] ?? '#888', size: 7, opacity: 0.8, line: { width: 1, color: '#111' } },
      text: pts.map(r => String(r.Year)),
      hovertemplate: `<b>${c}</b><br>%{text}<br>X: %{x:.1f}<br>Y: %{y:.2f}<extra></extra>`,
    }]
  })
}

/* ── Main component ──────────────────────────────────────────────────────────── */
export default function MacroDashboardPage() {
  const [data, setData]           = useState<MacroRow[]>([])
  const [loading, setLoading]     = useState(true)
  const [error, setError]         = useState('')
  const [selected, setSelected]   = useState<string[]>(DEFAULT_COUNTRIES)
  const [yearFrom, setYearFrom]   = useState(2000)
  const [yearTo, setYearTo]       = useState(2025)
  const [viewMode, setViewMode]   = useState<'compare' | 'bars'>('compare')

  useEffect(() => {
    apiFetch<MacroRow[]>('/api/macro/dashboard')
      .then(setData)
      .catch(e => setError(String(e)))
      .finally(() => setLoading(false))
  }, [])

  const allCountries = [...new Set(data.map(r => r.Country))].sort()
  const maxYear = data.length ? Math.max(...data.map(r => r.Year)) : 2025
  const filtered = data.filter(r => selected.includes(r.Country) && r.Year >= yearFrom && r.Year <= yearTo)

  // KPI averages for snapshot year
  const snap = filtered.filter(r => r.Year === yearTo)
  const avg = (col: keyof MacroRow) => {
    const vals = snap.map(r => r[col] as number | null).filter(v => v != null) as number[]
    if (!vals.length) return null
    return vals.reduce((a, b) => a + b, 0) / vals.length
  }
  const fmtPct = (v: number | null) => v != null ? `${v.toFixed(1)}%` : '—'
  const fmtBn  = (v: number | null) => v != null ? (v >= 1000 ? `$${(v/1000).toFixed(1)}tn` : `$${v.toFixed(0)}bn`) : '—'

  const toggleCountry = (c: string) =>
    setSelected(s => s.includes(c) ? s.filter(x => x !== c) : [...s, c])

  if (loading) return (
    <div className="content-wrap">
      <div className="placeholder-state">
        <RefreshCw size={32} style={{ animation: 'spin 1s linear infinite' }} />
        <p>Loading macro dashboard data…</p>
      </div>
    </div>
  )

  if (error) return (
    <div className="content-wrap">
      <div className="placeholder-state">
        <p style={{ color: '#ff4d4d' }}>{error}</p>
        <p style={{ color: '#666', fontSize: 12 }}>Is the FastAPI backend running?</p>
      </div>
    </div>
  )

  return (
    <div className="bond-layout">

      {/* ── Sidebar ── */}
      <div className="bond-sidebar" style={{ overflowY: 'auto' }}>

        <div className="ctrl-section">
          <div className="ctrl-label">View Mode</div>
          <div className="pill-group">
            <button className={`pill ${viewMode === 'compare' ? 'active' : ''}`} onClick={() => setViewMode('compare')}>Lines</button>
            <button className={`pill ${viewMode === 'bars' ? 'active' : ''}`} onClick={() => setViewMode('bars')}>Bars</button>
          </div>
        </div>

        <div className="ctrl-section">
          <div className="ctrl-label">Year From</div>
          <input className="ctrl-input" type="number" min={2000} max={yearTo} value={yearFrom}
            onChange={e => setYearFrom(Number(e.target.value))} />
        </div>
        <div className="ctrl-section">
          <div className="ctrl-label">Year To</div>
          <input className="ctrl-input" type="number" min={yearFrom} max={maxYear} value={yearTo}
            onChange={e => setYearTo(Number(e.target.value))} />
        </div>

        <hr className="ctrl-divider" />
        <div className="ctrl-label" style={{ marginBottom: 8 }}>Countries</div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
          {allCountries.map(c => (
            <label key={c} style={{
              display: 'flex', alignItems: 'center', gap: 8, cursor: 'pointer',
              fontSize: 11, color: selected.includes(c) ? (COLORS[c] ?? '#e8e8e8') : '#555',
              padding: '3px 0',
            }}>
              <input type="checkbox" checked={selected.includes(c)} onChange={() => toggleCountry(c)}
                style={{ accentColor: COLORS[c] ?? '#f39200' }} />
              {c}
            </label>
          ))}
        </div>
      </div>

      {/* ── Main ── */}
      <div className="bond-main">

        {/* Sub-header */}
        <div style={{ marginBottom: 16 }}>
          <div style={{ fontSize: 9, color: '#f39200', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.1em' }}>
            MACRO · {selected.length} Countries · {yearFrom}–{yearTo}
          </div>
          <div style={{ fontSize: 18, fontWeight: 700, color: '#e8e8e8', marginTop: 2 }}>Global Macro Dashboard</div>
          <div style={{ fontSize: 12, color: '#666', marginTop: 2 }}>Source: IMF WEO · FRED · BIS</div>
        </div>

        {/* KPI strip */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gap: 10, marginBottom: 20 }}>
          <KpiCard label={`Avg GDP (${yearTo})`}          value={fmtBn(avg('GDP_USD_Bn'))} />
          <KpiCard label={`Avg Growth (${yearTo})`}       value={fmtPct(avg('RealGDP_Pct'))} />
          <KpiCard label={`Avg Inflation (${yearTo})`}    value={fmtPct(avg('CPI_Pct'))} />
          <KpiCard label={`Avg Debt/GDP (${yearTo})`}     value={fmtPct(avg('DebtGDP_Pct'))} />
          <KpiCard label={`Avg Fiscal Bal (${yearTo})`}   value={fmtPct(avg('FiscalBal_Pct'))} />
        </div>

        {/* Snapshot table */}
        <SectionHeader title="Global Snapshot" subtitle={`Country scorecard · ${yearTo}`} />
        <SnapshotTable rows={data} year={yearTo} countries={selected} />

        {/* GDP */}
        <SectionHeader title="GDP" subtitle="Gross Domestic Product, current prices (USD billions) · IMF WEO" />
        {viewMode === 'compare'
          ? <Chart traces={lineTraces(filtered, 'GDP_USD_Bn', selected)} layout={{ title: { text: 'GDP — USD Billions', font: { color: '#e8e8e8', size: 12 } }, yaxis: { title: { text: 'USD bn' } } }} />
          : <Chart traces={barTrace(filtered, 'GDP_USD_Bn', yearTo, selected)} layout={{ title: { text: `GDP — USD Billions (${yearTo})`, font: { color: '#e8e8e8', size: 12 } }, yaxis: { title: { text: 'USD bn' } }, showlegend: false }} />
        }

        {/* Real GDP Growth */}
        <SectionHeader title="Real GDP Growth" subtitle="% change, constant prices · IMF WEO" />
        <Chart traces={lineTraces(filtered, 'RealGDP_Pct', selected)} layout={{ title: { text: 'Real GDP Growth %', font: { color: '#e8e8e8', size: 12 } }, yaxis: { title: { text: '%' } } }} />

        {/* Government Debt / GDP */}
        <SectionHeader title="Government Debt / GDP" subtitle="General Government Gross Debt as % of GDP · IMF WEO" />
        {viewMode === 'compare'
          ? <Chart traces={lineTraces(filtered, 'DebtGDP_Pct', selected)} layout={{ title: { text: 'Debt/GDP %', font: { color: '#e8e8e8', size: 12 } }, yaxis: { title: { text: '%' } } }} />
          : <Chart traces={barTrace(filtered, 'DebtGDP_Pct', yearTo, selected)} layout={{ title: { text: `Debt/GDP % (${yearTo})`, font: { color: '#e8e8e8', size: 12 } }, yaxis: { title: { text: '%' } }, showlegend: false }} />
        }

        {/* Fiscal Balance */}
        <SectionHeader title="Fiscal Balance" subtitle="General Govt Net Lending (+) / Borrowing (−) as % of GDP · IMF WEO" />
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
          <Chart traces={lineTraces(filtered, 'FiscalBal_Pct', selected)} layout={{ title: { text: 'Fiscal Balance % GDP', font: { color: '#e8e8e8', size: 12 } }, yaxis: { title: { text: '%' } } }} />
          <Chart traces={lineTraces(filtered, 'PrimaryBal_Pct', selected)} layout={{ title: { text: 'Primary Balance % GDP', font: { color: '#e8e8e8', size: 12 } }, yaxis: { title: { text: '%' } } }} />
        </div>

        {/* CPI Inflation */}
        <SectionHeader title="CPI Inflation" subtitle="Consumer Price Index, period average % change · IMF WEO" />
        {viewMode === 'compare'
          ? <Chart traces={lineTraces(filtered, 'CPI_Pct', selected)} layout={{ title: { text: 'CPI Inflation %', font: { color: '#e8e8e8', size: 12 } }, yaxis: { title: { text: '%' } } }} />
          : <Chart traces={barTrace(filtered, 'CPI_Pct', yearTo, selected)} layout={{ title: { text: `CPI Inflation % (${yearTo})`, font: { color: '#e8e8e8', size: 12 } }, yaxis: { title: { text: '%' } }, showlegend: false }} />
        }

        {/* 10Y Yield */}
        <SectionHeader title="10Y Government Yield" subtitle="Annual average · FRED OECD series" />
        <Chart traces={lineTraces(filtered, 'TenY_Yield', selected)} layout={{ title: { text: '10Y Govt Bond Yield %', font: { color: '#e8e8e8', size: 12 } }, yaxis: { title: { text: '%' } } }} />

        {/* Policy Rate */}
        <SectionHeader title="Policy Rate" subtitle="Central bank policy rate · BIS" />
        <Chart traces={lineTraces(filtered, 'Policy_Rate', selected)} layout={{ title: { text: 'CB Policy Rate %', font: { color: '#e8e8e8', size: 12 } }, yaxis: { title: { text: '%' } } }} />

        {/* Unemployment */}
        <SectionHeader title="Unemployment Rate" subtitle="% of labour force · IMF WEO" />
        <Chart traces={lineTraces(filtered, 'Unemployment_Pct', selected)} layout={{ title: { text: 'Unemployment %', font: { color: '#e8e8e8', size: 12 } }, yaxis: { title: { text: '%' } } }} />

        {/* Current Account */}
        <SectionHeader title="Current Account Balance" subtitle="% of GDP · IMF WEO" />
        <Chart traces={lineTraces(filtered, 'CurrentAcct_Pct', selected)} layout={{ title: { text: 'Current Account % GDP', font: { color: '#e8e8e8', size: 12 } }, yaxis: { title: { text: '%' } } }} />

        {/* Correlation: Debt vs Yield */}
        <SectionHeader title="Correlation: Debt/GDP vs 10Y Yield" subtitle="Each dot = one country × one year · higher debt tends to precede higher yields" />
        <Chart
          traces={scatterTraces(filtered, 'DebtGDP_Pct', 'TenY_Yield', selected)}
          layout={{ title: { text: 'Debt/GDP vs 10Y Yield', font: { color: '#e8e8e8', size: 12 } }, xaxis: { title: { text: 'Debt/GDP %' } }, yaxis: { title: { text: '10Y Yield %' } } }}
        />

        <div style={{ height: 40 }} />
      </div>
    </div>
  )
}
