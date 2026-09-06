import { useState, useEffect, useRef, useCallback } from 'react'
import { BarChart3, TrendingUp, Play, SlidersHorizontal, RefreshCw } from 'lucide-react'
import { fetchSpreadGrid, fetchColumns, fetchSeries, evalFormula, type SpreadCard, type SeriesPoint } from '../api/bond'

/* ── Sparkline SVG (real data) ──────────────────────────────────────────────── */
function Sparkline({ points, color = '#f39200', height = 54 }: { points: { value: number }[]; color?: string; height?: number }) {
  if (!points.length) return <div style={{ height }} />
  const w = 400; const h = height
  const vals = points.map(p => p.value)
  const min = Math.min(...vals); const max = Math.max(...vals)
  const range = max - min || 1
  const pts = vals.map((v, i) => {
    const x = (i / (vals.length - 1)) * w
    const y = h - ((v - min) / range) * (h - 4) - 2
    return `${x},${y}`
  }).join(' ')
  const lastPt = pts.split(' ').at(-1)!.split(',')
  const gradId = `g${color.replace('#', '')}${h}`
  return (
    <svg viewBox={`0 0 ${w} ${h}`} preserveAspectRatio="none" style={{ height }}>
      <defs>
        <linearGradient id={gradId} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor={color} stopOpacity="0.25" />
          <stop offset="100%" stopColor={color} stopOpacity="0.02" />
        </linearGradient>
      </defs>
      <polygon points={`0,${h} ${pts} ${w},${h}`} fill={`url(#${gradId})`} />
      <polyline points={pts} fill="none" stroke={color} strokeWidth="1.5" strokeLinejoin="round" />
      <circle cx={parseFloat(lastPt[0])} cy={parseFloat(lastPt[1])} r="2.5" fill={color} />
    </svg>
  )
}

/* ── Spread card ────────────────────────────────────────────────────────────── */
function SpreadCardItem({ card, ncols }: { card: SpreadCard; ncols: number }) {
  const isPos = card.change >= 0
  return (
    <div className="spread-card">
      <div className="spread-card-head">
        <div>
          <div className="spread-card-title">{card.name}</div>
          <div className="spread-card-formula">{card.formula}</div>
        </div>
      </div>
      <div className="spread-card-meta">
        <span className="spread-val">{card.last.toFixed(3)}</span>
        <span className={`spread-chg ${isPos ? 'pos' : 'neg'}`}>
          {isPos ? '▲' : '▼'} {Math.abs(card.change).toFixed(3)}
        </span>
      </div>
      <div className="sparkline-wrap">
        <Sparkline points={card.sparkline} height={ncols <= 2 ? 64 : 50} />
      </div>
    </div>
  )
}

/* ── Plotly chart (lazy-loaded) ─────────────────────────────────────────────── */
interface PlotlyTrace {
  x: string[]
  y: number[]
  name: string
  type: string
  mode: string
  line: { color: string; width: number }
  fill?: string
  fillcolor?: string
}

function PlotlyChart({ traces, title }: { traces: PlotlyTrace[]; title: string }) {
  const ref = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!ref.current || !traces.length) return
    let cancelled = false
    import('plotly.js-dist-min').then((Plotly) => {
      if (cancelled || !ref.current) return
      Plotly.react(ref.current!, traces as never, {
        title: { text: title, font: { color: '#e8e8e8', size: 13 } },
        paper_bgcolor: '#1a1a1a',
        plot_bgcolor:  '#111111',
        font:          { color: '#aaaaaa', family: 'system-ui, sans-serif', size: 11 },
        margin:        { t: 36, r: 16, b: 40, l: 56 },
        xaxis: {
          gridcolor: '#2a2a2a', zerolinecolor: '#2a2a2a',
          tickfont: { color: '#888', size: 10 },
        },
        yaxis: {
          gridcolor: '#2a2a2a', zerolinecolor: '#444',
          tickfont: { color: '#888', size: 10 },
        },
        legend: {
          bgcolor: 'rgba(26,26,26,0.9)', bordercolor: '#2a2a2a',
          font: { color: '#aaa', size: 10 },
        },
        hovermode: 'x unified',
        hoverlabel: { bgcolor: '#1a1a1a', bordercolor: '#f39200', font: { color: '#e8e8e8' } },
      } as never, { responsive: true, displayModeBar: false })
    })
    return () => { cancelled = true }
  }, [traces, title])

  return <div ref={ref} style={{ width: '100%', height: 320 }} />
}

/* ── KPI values from spread grid ─────────────────────────────────────────────── */
const KPI_NAMES = ['US 2-10 Spread', 'Eurex 5-10 Spread', 'Italian vs German 10Y', 'UK vs. German 10Y']

/* ── Bond Analytics page ────────────────────────────────────────────────────── */
export default function BondAnalyticsPage() {
  const [section, setSection] = useState<'spreads' | 'custom'>('spreads')
  const [ncols, setNcols] = useState(2)
  const [startDate, setStartDate] = useState('1994-01-03')
  const [endDate, setEndDate]     = useState('')

  // Spread grid state
  const [spreadData, setSpreadData]   = useState<SpreadCard[]>([])
  const [gridLoading, setGridLoading] = useState(false)
  const [gridError, setGridError]     = useState('')

  // Custom section state
  const [analysisType, setAnalysisType] = useState<'single' | 'overlay'>('single')
  const [columns, setColumns]           = useState<string[]>([])
  const [instrument, setInstrument]     = useState('US10Y')
  const [formula, setFormula]           = useState('')
  const [overlayInstr, setOverlayInstr] = useState('US2Y')
  const [overlayFormula, setOverlayFormula] = useState('')
  const [custStart, setCustStart] = useState('1994-01-03')
  const [custEnd, setCustEnd]     = useState('')
  const [chartTraces, setChartTraces]   = useState<PlotlyTrace[]>([])
  const [chartTitle, setChartTitle]     = useState('')
  const [chartLoading, setChartLoading] = useState(false)
  const [chartError, setChartError]     = useState('')
  const [submitted, setSubmitted]       = useState(false)

  // Load spread grid
  const loadGrid = useCallback(() => {
    setGridLoading(true)
    setGridError('')
    fetchSpreadGrid(startDate || undefined, endDate || undefined)
      .then(setSpreadData)
      .catch(e => setGridError(String(e)))
      .finally(() => setGridLoading(false))
  }, [startDate, endDate])

  useEffect(() => { loadGrid() }, [loadGrid])

  // Load column list
  useEffect(() => {
    fetchColumns().then(setColumns).catch(() => {})
  }, [])

  // Build KPI data from spread grid
  const kpiCards = KPI_NAMES.map(name => spreadData.find(c => c.name === name)).filter(Boolean) as SpreadCard[]

  // Submit custom chart
  const handleSubmit = useCallback(async () => {
    setChartLoading(true)
    setChartError('')
    setSubmitted(true)
    try {
      const traces: PlotlyTrace[] = []
      const primaryLabel = instrument === 'custom' ? (formula || 'Formula') : instrument
      const primaryFormula = instrument === 'custom' ? formula : instrument

      let primaryPoints: SeriesPoint[]
      if (instrument === 'custom' && formula.includes(' ')) {
        primaryPoints = await evalFormula(formula, custStart || undefined, custEnd || undefined)
      } else {
        const res = await fetchSeries([primaryFormula], custStart || undefined, custEnd || undefined)
        primaryPoints = res[primaryFormula] || []
      }

      traces.push({
        x: primaryPoints.map(p => p.date),
        y: primaryPoints.map(p => p.value),
        name: primaryLabel,
        type: 'scatter',
        mode: 'lines',
        line: { color: '#f39200', width: 1.5 },
        fill: analysisType === 'single' ? 'tozeroy' : undefined,
        fillcolor: analysisType === 'single' ? 'rgba(243,146,0,0.07)' : undefined,
      })

      if (analysisType === 'overlay') {
        const overlayLabel = overlayInstr === 'custom' ? (overlayFormula || 'Overlay') : overlayInstr
        const overlayFmla  = overlayInstr === 'custom' ? overlayFormula : overlayInstr

        let overlayPoints: SeriesPoint[]
        if (overlayInstr === 'custom' && overlayFormula.includes(' ')) {
          overlayPoints = await evalFormula(overlayFormula, custStart || undefined, custEnd || undefined)
        } else {
          const res = await fetchSeries([overlayFmla], custStart || undefined, custEnd || undefined)
          overlayPoints = res[overlayFmla] || []
        }
        traces.push({
          x: overlayPoints.map(p => p.date),
          y: overlayPoints.map(p => p.value),
          name: overlayLabel,
          type: 'scatter',
          mode: 'lines',
          line: { color: '#00c087', width: 1.5 },
        })
      }

      setChartTraces(traces)
      setChartTitle(primaryLabel + (analysisType === 'overlay' ? ` vs ${overlayInstr === 'custom' ? 'Overlay' : overlayInstr}` : ''))
    } catch (e) {
      setChartError(String(e))
    } finally {
      setChartLoading(false)
    }
  }, [instrument, formula, analysisType, overlayInstr, overlayFormula, custStart, custEnd])

  return (
    <div className="bond-layout">

      {/* ── Left sidebar controls ── */}
      <div className="bond-sidebar">

        <div className="ctrl-section">
          <div className="ctrl-label">Section</div>
          <div className="ctrl-select-wrap">
            <select className="ctrl-select" value={section} onChange={e => setSection(e.target.value as 'spreads' | 'custom')}>
              <option value="spreads">Bond Spreads &amp; Flies</option>
              <option value="custom">Custom Formula Graphs</option>
            </select>
          </div>
        </div>

        <hr className="ctrl-divider" />

        {section === 'spreads' && (
          <>
            <div className="ctrl-section">
              <div className="ctrl-label">From Date</div>
              <input className="ctrl-input" type="date" value={startDate} onChange={e => setStartDate(e.target.value)} />
            </div>
            <div className="ctrl-section">
              <div className="ctrl-label">To Date</div>
              <input className="ctrl-input" type="date" value={endDate} onChange={e => setEndDate(e.target.value)} />
            </div>
            <div className="ctrl-section">
              <div className="ctrl-label">Columns</div>
              <div className="pill-group">
                {[1, 2, 3, 4].map(n => (
                  <button key={n} className={`pill ${ncols === n ? 'active' : ''}`} onClick={() => setNcols(n)}>{n}</button>
                ))}
              </div>
            </div>
            <button className="primary-button" onClick={loadGrid}>
              <RefreshCw size={13} /> Refresh
            </button>
          </>
        )}

        {section === 'custom' && (
          <>
            <div className="ctrl-section">
              <div className="ctrl-label">Analysis Type</div>
              <div className="ctrl-select-wrap">
                <select className="ctrl-select" value={analysisType} onChange={e => setAnalysisType(e.target.value as 'single' | 'overlay')}>
                  <option value="single">Single</option>
                  <option value="overlay">Overlay</option>
                </select>
              </div>
            </div>

            <div className="ctrl-section">
              <div className="ctrl-label">Primary Instrument</div>
              <div className="ctrl-select-wrap">
                <select className="ctrl-select" value={instrument} onChange={e => setInstrument(e.target.value)}>
                  <option value="custom">Custom Formula</option>
                  {columns.map(c => <option key={c} value={c}>{c}</option>)}
                </select>
              </div>
            </div>

            {instrument === 'custom' && (
              <div className="ctrl-section">
                <div className="ctrl-label">Formula</div>
                <textarea
                  className="formula-textarea"
                  placeholder="e.g. US10Y - US2Y"
                  value={formula}
                  onChange={e => setFormula(e.target.value)}
                />
                <div className="formula-hint">Use column names from Final.xlsx</div>
              </div>
            )}

            {analysisType === 'overlay' && (
              <>
                <div className="ctrl-section">
                  <div className="ctrl-label">Overlay Instrument</div>
                  <div className="ctrl-select-wrap">
                    <select className="ctrl-select" value={overlayInstr} onChange={e => setOverlayInstr(e.target.value)}>
                      <option value="custom">Custom Formula</option>
                      {columns.map(c => <option key={c} value={c}>{c}</option>)}
                    </select>
                  </div>
                </div>
                {overlayInstr === 'custom' && (
                  <div className="ctrl-section">
                    <div className="ctrl-label">Overlay Formula</div>
                    <textarea
                      className="formula-textarea"
                      placeholder="e.g. FGBLY - FGBMY"
                      value={overlayFormula}
                      onChange={e => setOverlayFormula(e.target.value)}
                    />
                  </div>
                )}
              </>
            )}

            <div className="ctrl-section">
              <div className="ctrl-label">From Date</div>
              <input className="ctrl-input" type="date" value={custStart} onChange={e => setCustStart(e.target.value)} />
            </div>
            <div className="ctrl-section">
              <div className="ctrl-label">To Date</div>
              <input className="ctrl-input" type="date" value={custEnd} onChange={e => setCustEnd(e.target.value)} />
            </div>

            <button className="primary-button" onClick={handleSubmit} disabled={chartLoading}>
              <Play size={13} /> {chartLoading ? 'Loading…' : 'Submit'}
            </button>
          </>
        )}
      </div>

      {/* ── Main content ── */}
      <div className="bond-main">

        {/* KPI strip */}
        <div className="kpi-strip">
          {kpiCards.length > 0 ? kpiCards.map(card => (
            <div key={card.name} className="kpi-card">
              <span>{card.name}</span>
              <b>{card.last.toFixed(3)}</b>
              <small style={{ color: card.change >= 0 ? '#00c087' : '#ff4d4d' }}>
                {card.change >= 0 ? '▲' : '▼'} {Math.abs(card.change).toFixed(3)} today
              </small>
            </div>
          )) : (
            // Skeleton KPI cards while loading
            ['US 2-10 Spread', 'Eurex 5-10 Spread', 'IT vs DE 10Y', 'UK vs DE 10Y'].map(name => (
              <div key={name} className="kpi-card">
                <span>{name}</span>
                <b style={{ color: '#444' }}>—</b>
                <small style={{ color: '#555' }}>loading…</small>
              </div>
            ))
          )}
        </div>

        {/* Section toggle */}
        <div className="surface-tabs">
          <button className={`surface-tab ${section === 'spreads' ? 'active' : ''}`} onClick={() => setSection('spreads')}>
            <BarChart3 size={13} /> Bond Spreads &amp; Flies
          </button>
          <button className={`surface-tab ${section === 'custom' ? 'active' : ''}`} onClick={() => setSection('custom')}>
            <SlidersHorizontal size={13} /> Custom Formula Graphs
          </button>
        </div>

        {/* Spreads section */}
        {section === 'spreads' && (
          <>
            <div className="section-header" style={{ marginBottom: 14 }}>
              <div className="section-title-block">
                <div className="section-eyebrow">Preset Formulas · {spreadData.length} Spreads &amp; Flies</div>
                <div className="section-title">Bond Spreads &amp; Flies</div>
                <div className="section-sub">
                  {startDate || 'All dates'} → {endDate || 'latest'}
                </div>
              </div>
            </div>

            {gridLoading && (
              <div className="placeholder-state">
                <RefreshCw size={32} style={{ animation: 'spin 1s linear infinite' }} />
                <p>Loading spread data from Final.xlsx…</p>
              </div>
            )}

            {gridError && (
              <div className="placeholder-state">
                <p style={{ color: '#ff4d4d' }}>Error: {gridError}</p>
                <p style={{ color: '#888', fontSize: 12 }}>Is the FastAPI backend running? Start it with: uvicorn api.main:app --reload</p>
              </div>
            )}

            {!gridLoading && !gridError && (
              <div className="spread-grid" style={{ gridTemplateColumns: `repeat(${ncols}, 1fr)` }}>
                {spreadData.map(card => (
                  <SpreadCardItem key={card.name} card={card} ncols={ncols} />
                ))}
              </div>
            )}
          </>
        )}

        {/* Custom section */}
        {section === 'custom' && (
          <>
            <div className="section-header" style={{ marginBottom: 14 }}>
              <div className="section-title-block">
                <div className="section-eyebrow">Custom Formula · {analysisType === 'overlay' ? 'Overlay' : 'Single'}</div>
                <div className="section-title">Custom Formula Graphs</div>
                <div className="section-sub">Configure options in the left panel and press Submit</div>
              </div>
            </div>

            {!submitted && !chartLoading && (
              <div className="placeholder-state">
                <TrendingUp size={40} />
                <div className="section-title" style={{ marginBottom: 8 }}>No chart yet</div>
                <p>Select an instrument or enter a custom formula, then press Submit.</p>
              </div>
            )}

            {chartLoading && (
              <div className="placeholder-state">
                <RefreshCw size={32} style={{ animation: 'spin 1s linear infinite' }} />
                <p>Fetching data…</p>
              </div>
            )}

            {chartError && (
              <div className="placeholder-state">
                <p style={{ color: '#ff4d4d' }}>{chartError}</p>
              </div>
            )}

            {submitted && !chartLoading && !chartError && chartTraces.length > 0 && (
              <div className="card">
                <div className="card-head">
                  <span>{chartTitle}</span>
                  <span style={{ color: '#f39200' }}>Level Chart</span>
                </div>
                <div style={{ padding: '8px 0' }}>
                  <PlotlyChart traces={chartTraces} title={chartTitle} />
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  )
}
