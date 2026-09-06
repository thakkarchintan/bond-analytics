import { useEffect, useState, useCallback } from 'react'
import { RefreshCw } from 'lucide-react'

interface SeriesPoint { date: string; value: number | null }

const REBAL_FREQS = ['Monthly', 'Quarterly', 'Half-Yearly', 'Yearly'] as const
type RebalFreq = typeof REBAL_FREQS[number]

const FREQ_MONTHS: Record<RebalFreq, number> = { Monthly: 1, Quarterly: 3, 'Half-Yearly': 6, Yearly: 12 }

// ── Math helpers ──────────────────────────────────────────────────────────────

function calcCAGR(values: number[], dates: string[]): number {
  if (values.length < 2) return NaN
  const start = values[0], end = values[values.length - 1]
  const years = (new Date(dates[dates.length - 1]).getTime() - new Date(dates[0]).getTime()) / (365.25 * 86400000)
  if (start <= 0 || years <= 0) return NaN
  return (end / start) ** (1 / years) - 1
}

function maxDrawdown(values: number[]): number {
  let peak = values[0], mdd = 0
  for (const v of values) {
    if (v > peak) peak = v
    const dd = v / peak - 1
    if (dd < mdd) mdd = dd
  }
  return mdd
}

function sharpe(values: number[], rfAnnual: number): number {
  if (values.length < 2) return NaN
  const returns: number[] = []
  for (let i = 1; i < values.length; i++) returns.push(values[i] / values[i - 1] - 1)
  const rfDaily = rfAnnual / 252
  const excess = returns.map(r => r - rfDaily)
  const mean = excess.reduce((a, b) => a + b, 0) / excess.length
  const std = Math.sqrt(excess.reduce((a, b) => a + (b - mean) ** 2, 0) / excess.length)
  return std === 0 ? NaN : (mean / std) * Math.sqrt(252)
}

function rebalanceDates(dates: string[], freq: RebalFreq): Set<string> {
  const months = FREQ_MONTHS[freq]
  const result = new Set<string>()
  result.add(dates[0])
  let lastDate = new Date(dates[0])
  for (const d of dates.slice(1)) {
    const cur = new Date(d)
    const diff = (cur.getFullYear() - lastDate.getFullYear()) * 12 + (cur.getMonth() - lastDate.getMonth())
    if (diff >= months) {
      result.add(d)
      lastDate = cur
    }
  }
  return result
}

function buildPortfolio(
  priceMap: Record<string, number[]>,
  dates: string[],
  weights: Record<string, number>,
  freq: RebalFreq,
  capital: number,
): { portValues: number[]; indivValues: Record<string, number[]> } {
  const assets = Object.keys(weights)
  const rebDates = rebalanceDates(dates, freq)

  // units per asset
  const units: Record<string, number> = {}
  for (const a of assets) {
    const p0 = priceMap[a][0]
    units[a] = p0 > 0 ? (weights[a] * capital) / p0 : 0
  }

  const indivValues: Record<string, number[]> = Object.fromEntries(assets.map(a => [a, []]))
  const portValues: number[] = []

  for (let i = 0; i < dates.length; i++) {
    let total = 0
    for (const a of assets) {
      const v = units[a] * priceMap[a][i]
      indivValues[a].push(v)
      total += v
    }
    portValues.push(total)

    if (i > 0 && rebDates.has(dates[i])) {
      for (const a of assets) {
        const p = priceMap[a][i]
        units[a] = p > 0 ? (weights[a] * total) / p : 0
      }
    }
  }
  return { portValues, indivValues }
}

// ── Component ─────────────────────────────────────────────────────────────────

export default function PortfolioRebalancePage() {
  const [allColumns, setAllColumns] = useState<string[]>([])
  const [selected, setSelected] = useState<string[]>([])
  const [rawWeights, setRawWeights] = useState<Record<string, number>>({})
  const [freq, setFreq] = useState<RebalFreq>('Quarterly')
  const [capital, setCapital] = useState(1_000_000)
  const [rfRate, setRfRate] = useState(5)
  const [series, setSeries] = useState<Record<string, SeriesPoint[]>>({})
  const [loading, setLoading] = useState(false)
  const [running, setRunning] = useState(false)
  const [error, setError] = useState('')

  // Load column list on mount
  useEffect(() => {
    fetch('/api/bond/columns')
      .then(r => r.json())
      .then((cols: string[]) => {
        setAllColumns(cols)
        const def = cols.slice(0, 2)
        setSelected(def)
        const w: Record<string, number> = {}
        def.forEach(c => { w[c] = +(100 / def.length).toFixed(2) })
        setRawWeights(w)
      })
      .catch(() => setError('Failed to load columns.'))
  }, [])

  const totalWeight = Object.values(rawWeights).reduce((a, b) => a + b, 0)
  const normalizedWeights = Object.fromEntries(
    Object.entries(rawWeights).map(([k, v]) => [k, v / totalWeight])
  )

  const toggleAsset = (col: string) => {
    setSelected(prev => {
      const next = prev.includes(col) ? prev.filter(c => c !== col) : [...prev, col]
      const w: Record<string, number> = {}
      next.forEach(c => { w[c] = rawWeights[c] ?? +(100 / next.length).toFixed(2) })
      setRawWeights(w)
      return next
    })
  }

  const normalize = () => {
    const total = Object.values(rawWeights).reduce((a, b) => a + b, 0)
    if (total === 0) return
    setRawWeights(Object.fromEntries(Object.entries(rawWeights).map(([k, v]) => [k, +(v / total * 100).toFixed(2)])))
  }

  const run = useCallback(async () => {
    if (selected.length === 0) return
    setLoading(true)
    setError('')
    try {
      const resp = await fetch(`/api/bond/series?cols=${selected.join(',')}`)
      const data: Record<string, SeriesPoint[]> = await resp.json()
      setSeries(data)
    } catch {
      setError('Failed to load series data.')
    } finally {
      setLoading(false)
      setRunning(true)
    }
  }, [selected])

  // Build aligned date/price arrays
  const { dates, priceMap } = (() => {
    if (!running || selected.length === 0 || !series[selected[0]]) return { dates: [], priceMap: {} }
    // Find common dates with valid data
    const sets = selected.map(c => new Set(series[c]?.filter(p => p.value != null).map(p => p.date) ?? []))
    const common = sets.reduce((a, b) => new Set([...a].filter(x => b.has(x))))
    const sortedDates = [...common].sort()
    const pMap: Record<string, number[]> = {}
    for (const col of selected) {
      const byDate = Object.fromEntries((series[col] ?? []).map(p => [p.date, p.value as number]))
      pMap[col] = sortedDates.map(d => byDate[d])
    }
    return { dates: sortedDates, priceMap: pMap }
  })()

  const { portValues, indivValues } = running && dates.length > 1
    ? buildPortfolio(priceMap, dates, normalizedWeights, freq, capital)
    : { portValues: [] as number[], indivValues: {} as Record<string, number[]> }

  // Render Plotly chart
  useEffect(() => {
    if (!running || portValues.length === 0) return
    const palette = ['#f39200','#3b82f6','#00c087','#ff4d4d','#a78bfa','#22d3ee','#fbbf24','#f472b6']
    const traces = selected.map((col, i) => ({
      type: 'scatter', mode: 'lines', name: col,
      x: dates, y: indivValues[col] ?? [],
      line: { color: palette[i % palette.length], width: 1.5 },
    }))
    traces.push({
      type: 'scatter', mode: 'lines', name: 'Portfolio',
      x: dates, y: portValues,
      line: { color: '#ffffff', width: 2.5 },
    } as typeof traces[0])
    const layout = {
      paper_bgcolor: '#1a1a1a', plot_bgcolor: '#111111',
      font: { color: '#e0e0e0', size: 12 },
      margin: { l: 70, r: 20, t: 40, b: 44 },
      height: 380,
      title: { text: 'Equity Curves', font: { size: 13, color: '#e0e0e0' }, x: 0 },
      xaxis: { gridcolor: '#2a2a2a', tickfont: { color: '#888' } },
      yaxis: { gridcolor: '#2a2a2a', tickfont: { color: '#888' }, title: 'Value ($)' },
      legend: { font: { color: '#ccc' }, bgcolor: 'rgba(0,0,0,0)' },
    }
    import('plotly.js-dist-min').then(Plotly => {
      Plotly.react('pr-chart', traces, layout, { responsive: true, displayModeBar: false })
    })
  }, [running, portValues, dates, selected, indivValues])

  // Metrics
  const metrics = running && dates.length > 1
    ? selected.map(col => ({
        asset: col,
        cagr: calcCAGR(indivValues[col] ?? [], dates),
        mdd: maxDrawdown(indivValues[col] ?? []),
        sharpe: sharpe(indivValues[col] ?? [], rfRate / 100),
      })).concat([{
        asset: 'Portfolio',
        cagr: calcCAGR(portValues, dates),
        mdd: maxDrawdown(portValues),
        sharpe: sharpe(portValues, rfRate / 100),
      }])
    : []

  const fmt = (v: number, pct = true) => isNaN(v) ? 'N/A' : pct ? `${(v * 100).toFixed(2)}%` : v.toFixed(2)

  return (
    <div className="content-wrap">
      {/* Controls */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 16, marginBottom: 20 }}>
        <div>
          <label style={{ color: '#888', fontSize: 11, display: 'block', marginBottom: 6 }}>REBALANCE FREQUENCY</label>
          <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
            {REBAL_FREQS.map(f => (
              <button key={f} onClick={() => setFreq(f)} style={{
                padding: '5px 12px', borderRadius: 6, fontSize: 12, cursor: 'pointer',
                border: `1px solid ${freq === f ? '#f39200' : '#2a2a2a'}`,
                background: freq === f ? 'rgba(243,146,0,0.15)' : 'transparent',
                color: freq === f ? '#f39200' : '#666',
              }}>{f}</button>
            ))}
          </div>
        </div>
        <div>
          <label style={{ color: '#888', fontSize: 11, display: 'block', marginBottom: 6 }}>INITIAL CAPITAL ($)</label>
          <input
            type="number" value={capital} onChange={e => setCapital(+e.target.value)}
            style={{ background: '#1a1a1a', border: '1px solid #2a2a2a', color: '#e0e0e0', padding: '6px 10px', borderRadius: 6, fontSize: 13, width: '100%' }}
          />
        </div>
        <div>
          <label style={{ color: '#888', fontSize: 11, display: 'block', marginBottom: 6 }}>RISK-FREE RATE (% annual)</label>
          <input
            type="number" value={rfRate} step={0.25} onChange={e => setRfRate(+e.target.value)}
            style={{ background: '#1a1a1a', border: '1px solid #2a2a2a', color: '#e0e0e0', padding: '6px 10px', borderRadius: 6, fontSize: 13, width: '100%' }}
          />
        </div>
      </div>

      {/* Asset selector */}
      <div style={{ background: '#1a1a1a', border: '1px solid #2a2a2a', borderRadius: 8, padding: 16, marginBottom: 16 }}>
        <div style={{ fontSize: 12, color: '#888', marginBottom: 10 }}>SELECT ASSETS</div>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
          {allColumns.map(col => {
            const sel = selected.includes(col)
            return (
              <button key={col} onClick={() => toggleAsset(col)} style={{
                padding: '4px 10px', borderRadius: 12, fontSize: 11, cursor: 'pointer',
                border: `1px solid ${sel ? '#f39200' : '#2a2a2a'}`,
                background: sel ? 'rgba(243,146,0,0.15)' : 'transparent',
                color: sel ? '#f39200' : '#555',
              }}>{col}</button>
            )
          })}
        </div>
      </div>

      {/* Weight inputs */}
      {selected.length > 0 && (
        <div style={{ background: '#1a1a1a', border: '1px solid #2a2a2a', borderRadius: 8, padding: 16, marginBottom: 16 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 10 }}>
            <span style={{ fontSize: 12, color: '#888' }}>TARGET WEIGHTS</span>
            <span style={{ fontSize: 12, color: Math.abs(totalWeight - 100) < 0.1 ? '#00c087' : '#ff4d4d' }}>
              Total: {totalWeight.toFixed(2)}%
            </span>
            {Math.abs(totalWeight - 100) >= 0.1 && (
              <button onClick={normalize} style={{
                padding: '3px 10px', fontSize: 11, borderRadius: 4, cursor: 'pointer',
                background: 'rgba(243,146,0,0.15)', border: '1px solid #f39200', color: '#f39200',
              }}>Normalize to 100%</button>
            )}
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(160px, 1fr))', gap: 10 }}>
            {selected.map(col => (
              <div key={col}>
                <label style={{ fontSize: 11, color: '#888', display: 'block', marginBottom: 4 }}>{col}</label>
                <input
                  type="number" min={0} max={100} step={0.5}
                  value={rawWeights[col] ?? 0}
                  onChange={e => setRawWeights(w => ({ ...w, [col]: +e.target.value }))}
                  style={{ background: '#111', border: '1px solid #2a2a2a', color: '#e0e0e0', padding: '5px 8px', borderRadius: 6, fontSize: 13, width: '100%' }}
                />
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Run button */}
      <button
        onClick={run}
        disabled={loading || selected.length === 0}
        style={{
          padding: '9px 24px', borderRadius: 6, fontSize: 13, fontWeight: 600, cursor: 'pointer',
          background: '#f39200', border: 'none', color: '#000', marginBottom: 24,
          opacity: loading || selected.length === 0 ? 0.5 : 1,
          display: 'flex', alignItems: 'center', gap: 8,
        }}
      >
        <RefreshCw size={14} />
        {loading ? 'Loading…' : 'Run Backtest'}
      </button>

      {error && <p style={{ color: '#ff4d4d', marginBottom: 16 }}>{error}</p>}

      {running && portValues.length > 0 && (
        <>
          <div id="pr-chart" style={{ width: '100%', minHeight: 380, marginBottom: 24 }} />

          {/* Metrics table */}
          <div className="section-title" style={{ marginBottom: 12 }}>Performance Metrics</div>
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
              <thead>
                <tr style={{ borderBottom: '1px solid #2a2a2a' }}>
                  {['Asset','CAGR','Max Drawdown','Sharpe'].map(h => (
                    <th key={h} style={{ textAlign: 'left', padding: '8px 12px', color: '#888', fontWeight: 600, fontSize: 11 }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {metrics.map(m => (
                  <tr key={m.asset} style={{
                    borderBottom: '1px solid #1a1a1a',
                    background: m.asset === 'Portfolio' ? 'rgba(243,146,0,0.06)' : 'transparent',
                  }}>
                    <td style={{ padding: '7px 12px', color: m.asset === 'Portfolio' ? '#f39200' : '#e0e0e0', fontWeight: m.asset === 'Portfolio' ? 700 : 400 }}>{m.asset}</td>
                    <td style={{ padding: '7px 12px', color: isNaN(m.cagr) ? '#555' : m.cagr >= 0 ? '#00c087' : '#ff4d4d' }}>{fmt(m.cagr)}</td>
                    <td style={{ padding: '7px 12px', color: '#ff4d4d' }}>{fmt(m.mdd)}</td>
                    <td style={{ padding: '7px 12px', color: isNaN(m.sharpe) ? '#555' : m.sharpe >= 1 ? '#00c087' : m.sharpe >= 0 ? '#f39200' : '#ff4d4d' }}>{fmt(m.sharpe, false)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Rebalance schedule */}
          <div className="section-title" style={{ marginTop: 24, marginBottom: 8 }}>Rebalance Schedule ({freq})</div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
            {[...rebalanceDates(dates, freq)].slice(0, 60).map(d => (
              <span key={d} style={{ fontSize: 11, padding: '2px 8px', borderRadius: 4, background: '#1a1a1a', border: '1px solid #2a2a2a', color: '#888' }}>
                {new Date(d).toLocaleDateString('en', { day: '2-digit', month: 'short', year: 'numeric' })}
              </span>
            ))}
          </div>
        </>
      )}
    </div>
  )
}
