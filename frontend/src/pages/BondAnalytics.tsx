import { useState, useMemo } from 'react'
import { BarChart3, TrendingUp, Play, SlidersHorizontal } from 'lucide-react'

/* ── Mock data ─────────────────────────────────────────────────────────────── */
function mockSeries(seed: number, len = 80): number[] {
  let v = seed
  return Array.from({ length: len }, (_, i) => {
    v += (Math.sin(i * 0.31 + seed) * 0.4 + (Math.random() - 0.5) * 0.3)
    return parseFloat(v.toFixed(4))
  })
}

const FORMULAS: Array<{ name: string; formula: string; seed: number }> = [
  { name: 'Eurex 5-10 Spread',          formula: 'FGBLY − FGBMY',          seed: 1.2  },
  { name: 'Eurex 2-5 Spread',           formula: 'FGBMY − FGBSY',          seed: 0.5  },
  { name: 'Eurex 2-10 Spread',          formula: 'FGBLY − FGBSY',          seed: 1.8  },
  { name: 'Eurex 10-30 Spread',         formula: 'FGBXY − FGBLY',          seed: -0.3 },
  { name: 'Eurex 2-5-10 Fly',           formula: 'FGBLY − 2×FGBMY + FGBSY', seed: 0.02 },
  { name: 'Eurex 5-10-30 Fly',          formula: 'FGBXY − 2×FGBLY + FGBMY', seed: -0.05 },
  { name: 'US 5-10 Spread',             formula: 'US10Y − US5Y',           seed: 0.8  },
  { name: 'US 2-5 Spread',              formula: 'US5Y − US2Y',            seed: -0.2 },
  { name: 'US 2-10 Spread',             formula: 'US10Y − US2Y',           seed: 0.6  },
  { name: 'US 10-30 Spread',            formula: 'US30Y − US10Y',          seed: 1.1  },
  { name: 'US 2-5-10 Fly',              formula: 'US10Y − 2×US5Y + US2Y',  seed: -0.01 },
  { name: 'US 5-10-30 Fly',             formula: 'US30Y − 2×US10Y + US5Y', seed: 0.03 },
  { name: 'Italian vs German 2Y',        formula: 'FBTSY − FGBSY',          seed: 1.4  },
  { name: 'Italian vs German 10Y',       formula: 'FBTPY − FGBLY',          seed: 1.7  },
  { name: 'Aus vs Canadian 10Y',         formula: 'AUS10Y − CAD10Y',        seed: 0.3  },
  { name: 'French vs German 10Y',        formula: 'FOATY − FGBLY',          seed: 0.55 },
  { name: 'UK vs German 10Y',            formula: 'UK10Y − FGBLY',          seed: 1.0  },
  { name: 'UK vs Australian 10Y',        formula: 'UK10Y − AUS10Y',         seed: 0.7  },
  { name: 'US vs Australian 10Y',        formula: 'US10Y − AUS10Y',         seed: -0.4 },
  { name: 'CA vs US 2-5-10 Fly',         formula: 'CAD10Y − 2×CAD5Y + CAD2Y − (US10Y − 2×US5Y + US2Y)', seed: 0.001 },
]

const INSTRUMENTS = [
  'FGBSY','FGBMY','FGBLY','FGBXY',
  'US2Y','US5Y','US10Y','US30Y',
  'FBTSY','FBTPY','FOATY','UK10Y',
  'AUS10Y','AUS3Y','CAD10Y','CAD2Y','CAD5Y',
]

/* ── Sparkline SVG ─────────────────────────────────────────────────────────── */
function Sparkline({ data, color = '#f39200', height = 54 }: { data: number[]; color?: string; height?: number }) {
  const w = 400; const h = height
  const min = Math.min(...data); const max = Math.max(...data)
  const range = max - min || 1
  const pts = data.map((v, i) => {
    const x = (i / (data.length - 1)) * w
    const y = h - ((v - min) / range) * (h - 4) - 2
    return `${x},${y}`
  }).join(' ')
  const last = parseFloat(pts.split(' ').at(-1)!.split(',')[1])
  const gradId = `g${Math.random().toString(36).slice(2)}`
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
      <circle cx={parseFloat(pts.split(' ').at(-1)!.split(',')[0])} cy={last} r="2.5" fill={color} />
    </svg>
  )
}

/* ── Spread card ────────────────────────────────────────────────────────────── */
function SpreadCard({ name, formula, seed, ncols }: { name: string; formula: string; seed: number; ncols: number }) {
  const series = useMemo(() => mockSeries(seed), [seed])
  const last = series.at(-1)!
  const prev = series.at(-2)!
  const chg = last - prev
  const isPos = chg >= 0
  return (
    <div className="spread-card">
      <div className="spread-card-head">
        <div>
          <div className="spread-card-title">{name}</div>
          <div className="spread-card-formula">{formula}</div>
        </div>
      </div>
      <div className="spread-card-meta">
        <span className="spread-val">{last.toFixed(3)}</span>
        <span className={`spread-chg ${isPos ? 'pos' : 'neg'}`}>
          {isPos ? '▲' : '▼'} {Math.abs(chg).toFixed(3)}
        </span>
      </div>
      <div className="sparkline-wrap">
        <Sparkline data={series} height={ncols <= 2 ? 64 : 50} />
      </div>
    </div>
  )
}

/* ── Custom chart placeholder ───────────────────────────────────────────────── */
function CustomChartPlaceholder({ instrument, formula }: { instrument: string; formula?: string }) {
  const label = formula?.trim() || instrument
  const series = useMemo(() => mockSeries(label.length * 0.13 + 1.1, 120), [label])
  return (
    <div className="card" style={{ marginBottom: 16 }}>
      <div className="card-head">
        <span>{label}</span>
        <span style={{ color: '#f39200', letterSpacing: 0 }}>Level Chart</span>
      </div>
      <div style={{ padding: '12px 16px 8px' }}>
        <Sparkline data={series} height={160} />
      </div>
    </div>
  )
}

/* ── Bond Analytics page ────────────────────────────────────────────────────── */
export default function BondAnalyticsPage() {
  const [section, setSection] = useState<'spreads' | 'custom'>('spreads')
  const [ncols, setNcols] = useState(2)
  const [startDate, setStartDate] = useState('1994-01-03')
  const [endDate, setEndDate]     = useState('2025-11-06')

  // Custom section state
  const [analysisType, setAnalysisType] = useState<'single' | 'overlay'>('single')
  const [instrument, setInstrument] = useState('US10Y')
  const [formula, setFormula] = useState('')
  const [overlayInstr, setOverlayInstr] = useState('US2Y')
  const [overlayFormula, setOverlayFormula] = useState('')
  const [submitted, setSubmitted] = useState(false)
  const [custStart, setCustStart] = useState('1994-01-03')
  const [custEnd, setCustEnd]     = useState('2025-11-06')

  const colOptions = [1, 2, 3, 4]

  return (
    <div className="bond-layout">

      {/* ── Left sidebar controls ── */}
      <div className="bond-sidebar">

        <div className="ctrl-section">
          <div className="ctrl-label">Section</div>
          <div className="ctrl-select-wrap">
            <select className="ctrl-select" value={section} onChange={e => { setSection(e.target.value as 'spreads' | 'custom'); setSubmitted(false) }}>
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
                {colOptions.map(n => (
                  <button key={n} className={`pill ${ncols === n ? 'active' : ''}`} onClick={() => setNcols(n)}>{n}</button>
                ))}
              </div>
            </div>
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
                  {INSTRUMENTS.map(i => <option key={i} value={i}>{i}</option>)}
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
                      {INSTRUMENTS.map(i => <option key={i} value={i}>{i}</option>)}
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

            <button className="primary-button" onClick={() => setSubmitted(true)}>
              <Play size={13} /> Submit
            </button>
          </>
        )}
      </div>

      {/* ── Main content ── */}
      <div className="bond-main">

        {/* KPI strip */}
        <div className="kpi-strip">
          <div className="kpi-card">
            <span>US 2-10 Spread</span>
            <b>0.621</b>
            <small style={{ color: '#00c087' }}>▲ 0.012 today</small>
          </div>
          <div className="kpi-card">
            <span>Eurex 5-10 Spread</span>
            <b>1.204</b>
            <small style={{ color: '#ff4d4d' }}>▼ 0.008 today</small>
          </div>
          <div className="kpi-card">
            <span>IT vs DE 10Y</span>
            <b>1.712</b>
            <small style={{ color: '#00c087' }}>▲ 0.021 today</small>
          </div>
          <div className="kpi-card">
            <span>UK vs DE 10Y</span>
            <b>1.038</b>
            <small style={{ color: '#f39200' }}>— 0.000 today</small>
          </div>
        </div>

        {/* Section toggle */}
        <div className="surface-tabs">
          <button
            className={`surface-tab ${section === 'spreads' ? 'active' : ''}`}
            onClick={() => setSection('spreads')}
          >
            <BarChart3 size={13} /> Bond Spreads &amp; Flies
          </button>
          <button
            className={`surface-tab ${section === 'custom' ? 'active' : ''}`}
            onClick={() => setSection('custom')}
          >
            <SlidersHorizontal size={13} /> Custom Formula Graphs
          </button>
        </div>

        {/* Spreads section */}
        {section === 'spreads' && (
          <>
            <div className="section-header" style={{ marginBottom: 14 }}>
              <div className="section-title-block">
                <div className="section-eyebrow">Preset Formulas · 20 Spreads &amp; Flies</div>
                <div className="section-title">Bond Spreads &amp; Flies</div>
                <div className="section-sub">{startDate} → {endDate}</div>
              </div>
            </div>
            <div
              className="spread-grid"
              style={{ gridTemplateColumns: `repeat(${ncols}, 1fr)` }}
            >
              {FORMULAS.map(f => (
                <SpreadCard key={f.name} {...f} ncols={ncols} />
              ))}
            </div>
          </>
        )}

        {/* Custom section */}
        {section === 'custom' && (
          <>
            <div className="section-header" style={{ marginBottom: 14 }}>
              <div className="section-title-block">
                <div className="section-eyebrow">Custom Formula · {analysisType === 'overlay' ? 'Overlay' : 'Single'}</div>
                <div className="section-title">Custom Formula Graphs</div>
                <div className="section-sub">
                  Configure options in the left panel and press Submit
                </div>
              </div>
            </div>

            {!submitted && (
              <div className="placeholder-state">
                <TrendingUp size={40} />
                <div className="section-title" style={{ marginBottom: 8 }}>No chart yet</div>
                <p>Select an instrument or enter a custom formula in the left panel, then press Submit to render the charts.</p>
              </div>
            )}

            {submitted && (
              <>
                <CustomChartPlaceholder
                  instrument={instrument}
                  formula={instrument === 'custom' ? formula : undefined}
                />
                {analysisType === 'overlay' && (
                  <CustomChartPlaceholder
                    instrument={overlayInstr}
                    formula={overlayInstr === 'custom' ? overlayFormula : undefined}
                  />
                )}
              </>
            )}
          </>
        )}
      </div>
    </div>
  )
}
