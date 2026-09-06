import { useState, useEffect, useRef } from 'react'
import { evalFormula } from '../api/bond'

type PlotTrace = Record<string, unknown>
type PlotLayout = Record<string, unknown>

function Chart({ traces, layout, height = 360 }: { traces: PlotTrace[]; layout: PlotLayout; height?: number }) {
  const ref = useRef<HTMLDivElement>(null)
  useEffect(() => {
    if (!ref.current || !traces.length) return
    let cancelled = false
    import('plotly.js-dist-min').then(Plotly => {
      if (cancelled || !ref.current) return
      const base: PlotLayout = {
        paper_bgcolor: '#1a1a1a', plot_bgcolor: '#111111',
        font: { color: '#aaa', family: 'system-ui,sans-serif', size: 11 },
        margin: { t: 36, r: 16, b: 44, l: 62 },
        xaxis: { gridcolor: '#2a2a2a', tickfont: { color: '#777', size: 10 } },
        yaxis: { gridcolor: '#2a2a2a', tickfont: { color: '#777', size: 10 }, zerolinecolor: '#444' },
        legend: { orientation: 'h', y: 1.12, x: 0, font: { color: '#aaa', size: 10 }, bgcolor: 'rgba(0,0,0,0)' },
        hovermode: 'x unified',
        hoverlabel: { bgcolor: '#1a1a1a', bordercolor: '#f39200', font: { color: '#e8e8e8' } },
        ...layout,
      }
      Plotly.react(ref.current!, traces as never, base as never, { responsive: true, displayModeBar: false })
    })
    return () => { cancelled = true }
  }, [traces, layout])
  return <div ref={ref} style={{ width: '100%', height }} />
}

interface ShockEpisode {
  name: string
  start: string
  end: string
  color: string
  description: string
}

const SHOCK_EPISODES: ShockEpisode[] = [
  { name: 'GFC 2008',       start: '2007-06-01', end: '2009-06-30', color: '#ff4d4d',   description: 'Global Financial Crisis · Lehman collapse Sep 2008' },
  { name: 'Euro Crisis',    start: '2010-01-01', end: '2012-12-31', color: '#f39200',   description: 'European sovereign debt crisis · Greece / PIIGS' },
  { name: 'Taper Tantrum',  start: '2013-05-01', end: '2013-12-31', color: '#fbbf24',   description: 'Fed taper signal May 2013 → yield spike' },
  { name: 'COVID-19',       start: '2020-01-01', end: '2021-06-30', color: '#a78bfa',   description: 'Pandemic shock + emergency rate cuts Mar 2020' },
  { name: 'Rate Hike Cycle',start: '2022-01-01', end: '2023-12-31', color: '#f87171',   description: 'Fed + ECB fastest hiking cycle in 40 years' },
  { name: 'Custom',         start: '', end: '',                      color: '#60a5fa',   description: 'Set your own date range' },
]

const PRESET_FORMULAS: Record<string, string> = {
  'US 2-10 Spread':     'US10Y - US2Y',
  'Eurex 5-10 Spread':  'FGBLY - FGBMY',
  'US 10Y Yield':       'US10Y',
  'US 2Y Yield':        'US2Y',
  'DE 10Y Yield':       'FGBLY',
  'UK 10Y Yield':       'UK10Y',
  'US-DE 10Y Spread':   'US10Y - FGBLY',
  'S&P 500':            'SPX',
  'Gold':               'Gold (USD)',
}

interface SeriesPoint { date: string; value: number }

export default function HistoricalShocks() {
  const [episode, setEpisode] = useState<ShockEpisode>(SHOCK_EPISODES[0])
  const [customStart, setCustomStart] = useState('2020-01-01')
  const [customEnd,   setCustomEnd]   = useState('2021-12-31')
  const [selectedFormulas, setSelectedFormulas] = useState<string[]>(['US 2-10 Spread', 'US 10Y Yield', 'S&P 500'])
  const [customFormula, setCustomFormula] = useState('')
  const [seriesData, setSeriesData] = useState<Record<string, SeriesPoint[]>>({})
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const start = episode.name === 'Custom' ? customStart : episode.start
  const end   = episode.name === 'Custom' ? customEnd   : episode.end

  async function load() {
    setLoading(true); setError('')
    const formulas = [
      ...selectedFormulas.map(f => ({ name: f, expr: PRESET_FORMULAS[f] })),
      ...(customFormula.trim() ? [{ name: customFormula, expr: customFormula }] : []),
    ]
    try {
      const results: Record<string, SeriesPoint[]> = {}
      await Promise.all(formulas.map(async ({ name, expr }) => {
        results[name] = await evalFormula(expr, start, end)
      }))
      setSeriesData(results)
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Error loading data')
    }
    setLoading(false)
  }

  // Normalise: index all series to 100 at first point
  function normalise(pts: SeriesPoint[]): SeriesPoint[] {
    if (!pts.length) return []
    const base = pts[0].value
    if (base === 0) return pts
    return pts.map(p => ({ ...p, value: p.value / base * 100 }))
  }

  const PALETTE = ['#f39200','#60a5fa','#34d399','#f87171','#a78bfa','#fbbf24','#22d3ee','#e879f9']

  const names = Object.keys(seriesData)
  const rawTraces: PlotTrace[] = names.map((n, i) => ({
    type:'scatter', mode:'lines', name:n,
    x: seriesData[n].map(p=>p.date),
    y: seriesData[n].map(p=>p.value),
    line:{color:PALETTE[i%PALETTE.length],width:1.5},
  }))

  const normTraces: PlotTrace[] = names.map((n, i) => ({
    type:'scatter', mode:'lines', name:n + ' (idx)',
    x: normalise(seriesData[n]).map(p=>p.date),
    y: normalise(seriesData[n]).map(p=>p.value),
    line:{color:PALETTE[i%PALETTE.length],width:1.5},
  }))

  // Stats for each series
  const stats = names.map(n => {
    const vals = seriesData[n].map(p=>p.value).filter(v=>isFinite(v))
    if (!vals.length) return null
    const chg   = vals[vals.length-1] - vals[0]
    const chgPct = vals[0] !== 0 ? chg / Math.abs(vals[0]) * 100 : NaN
    const peak  = Math.max(...vals)
    const trough = Math.min(...vals)
    return { n, start: vals[0], end: vals[vals.length-1], chg, chgPct, peak, trough }
  }).filter(Boolean)

  return (
    <div className="bond-layout">
      <aside className="bond-sidebar">
        <div className="ctrl-section">
          <div className="ctrl-label">SHOCK EPISODE</div>
          {SHOCK_EPISODES.map(ep => (
            <button key={ep.name}
              className={`pill ${episode.name===ep.name?'active':''}`}
              style={{ marginBottom:4, width:'100%', textAlign:'left', justifyContent:'flex-start' }}
              onClick={() => setEpisode(ep)}>
              <span style={{ display:'inline-block', width:8, height:8, borderRadius:'50%', background:ep.color, marginRight:6 }} />
              {ep.name}
            </button>
          ))}
        </div>

        {episode.name === 'Custom' && (
          <div className="ctrl-section">
            <div className="ctrl-label">CUSTOM RANGE</div>
            <input type="date" className="ctrl-input" value={customStart} onChange={e=>setCustomStart(e.target.value)} style={{ marginBottom:6 }} />
            <input type="date" className="ctrl-input" value={customEnd}   onChange={e=>setCustomEnd(e.target.value)} />
          </div>
        )}

        <div className="ctrl-section">
          <div className="ctrl-label">SERIES</div>
          {Object.keys(PRESET_FORMULAS).map(f => (
            <label key={f} style={{ display:'flex', alignItems:'center', gap:8, padding:'3px 0', cursor:'pointer', fontSize:12, color: selectedFormulas.includes(f) ? '#f39200' : '#666' }}>
              <input type="checkbox" checked={selectedFormulas.includes(f)} onChange={e => setSelectedFormulas(s => e.target.checked ? [...s,f] : s.filter(x=>x!==f))} style={{ accentColor:'#f39200' }} />
              {f}
            </label>
          ))}
        </div>

        <div className="ctrl-section">
          <div className="ctrl-label">CUSTOM FORMULA</div>
          <input className="ctrl-input" placeholder="e.g. US10Y - UK10Y" value={customFormula} onChange={e=>setCustomFormula(e.target.value)} />
        </div>

        <button className="primary-button" style={{ width:'100%', marginTop:8 }} onClick={load} disabled={loading}>
          {loading ? 'Loading…' : 'Load Episode'}
        </button>
      </aside>

      <div className="bond-main">
        <div style={{ borderLeft:`3px solid ${episode.color}`, padding:'10px 14px', background:`rgba(0,0,0,0.2)`, borderRadius:'0 6px 6px 0', marginBottom:16 }}>
          <div style={{ color:'#e8e8e8', fontWeight:600, fontSize:13, textTransform:'uppercase', letterSpacing:'0.04em' }}>{episode.name}</div>
          <div style={{ color:'#888', fontSize:11, marginTop:4 }}>{episode.description || `${start} → ${end}`}{episode.name !== 'Custom' ? ` · ${start} → ${end}` : ''}</div>
        </div>

        {error && <div style={{ color:'#ff4d4d', fontSize:12, marginBottom:12 }}>Error: {error}<br/><small style={{color:'#888'}}>Is the FastAPI backend running?</small></div>}

        {!names.length && !loading && (
          <div style={{ color:'#555', textAlign:'center', padding:'60px 20px', fontSize:13 }}>
            Select an episode and series, then press <strong style={{ color:'#f39200' }}>Load Episode</strong>
          </div>
        )}

        {loading && <div style={{ color:'#aaa', textAlign:'center', padding:60 }}><div style={{ width:32, height:32, border:'3px solid #f39200', borderTopColor:'transparent', borderRadius:'50%', animation:'spin 0.8s linear infinite', margin:'0 auto 16px' }}/>Loading series…</div>}

        {names.length > 0 && !loading && (
          <>
            {/* Stats strip */}
            <div className="kpi-strip" style={{ marginBottom:20 }}>
              {stats.map(s => s && (
                <div key={s.n} className="kpi-card">
                  <div style={{ color:'#888', fontSize:10, textTransform:'uppercase', letterSpacing:'0.06em', marginBottom:4 }}>{s.n}</div>
                  <div style={{ color: s.chg >= 0 ? '#00c087' : '#ff4d4d', fontSize:18, fontWeight:700, fontVariantNumeric:'tabular-nums' }}>
                    {s.chg >= 0 ? '+' : ''}{s.chg.toFixed(2)}
                  </div>
                  <div style={{ color:'#555', fontSize:10 }}>{isNaN(s.chgPct) ? '' : `${s.chgPct >= 0 ? '+' : ''}${s.chgPct.toFixed(1)}%`}</div>
                </div>
              ))}
            </div>

            {/* Raw chart */}
            <div style={{ borderLeft:'3px solid #f39200', padding:'10px 14px', background:'rgba(243,146,0,0.04)', borderRadius:'0 6px 6px 0', marginBottom:12 }}>
              <div style={{ color:'#e8e8e8', fontWeight:600, fontSize:13, textTransform:'uppercase', letterSpacing:'0.04em' }}>Raw Values</div>
            </div>
            <Chart traces={rawTraces} layout={{ yaxis:{ title:{text:'Value',font:{color:'#666',size:11}} } }} />

            {/* Normalised chart */}
            <div style={{ borderLeft:'3px solid #60a5fa', padding:'10px 14px', background:'rgba(96,165,250,0.04)', borderRadius:'0 6px 6px 0', margin:'28px 0 12px' }}>
              <div style={{ color:'#e8e8e8', fontWeight:600, fontSize:13, textTransform:'uppercase', letterSpacing:'0.04em' }}>Indexed to 100 (start of episode)</div>
              <div style={{ color:'#888', fontSize:11, marginTop:4 }}>All series rebased to 100 at {start} for cross-series comparison</div>
            </div>
            <Chart traces={normTraces} layout={{ yaxis:{ title:{text:'Index (base=100)',font:{color:'#666',size:11}} } }} />

            {/* Detailed stats table */}
            <div style={{ marginTop:24, overflowX:'auto' }}>
              <table style={{ width:'100%', borderCollapse:'collapse', fontSize:12 }}>
                <thead>
                  <tr style={{ borderBottom:'1px solid #2a2a2a' }}>
                    {['Series','Start','End','Change','% Change','Peak','Trough'].map(h => <th key={h} style={{ padding:'8px 12px', textAlign:'left', color:'#666', fontWeight:500, textTransform:'uppercase', fontSize:10, letterSpacing:'0.05em', whiteSpace:'nowrap' }}>{h}</th>)}
                  </tr>
                </thead>
                <tbody>
                  {stats.map(s => s && (
                    <tr key={s.n} style={{ borderBottom:'1px solid #1f1f1f' }}>
                      <td style={{ padding:'8px 12px', color:'#f39200', fontWeight:500 }}>{s.n}</td>
                      <td style={{ padding:'8px 12px', color:'#aaa', fontVariantNumeric:'tabular-nums' }}>{s.start.toFixed(2)}</td>
                      <td style={{ padding:'8px 12px', color:'#aaa', fontVariantNumeric:'tabular-nums' }}>{s.end.toFixed(2)}</td>
                      <td style={{ padding:'8px 12px', color: s.chg>=0?'#00c087':'#ff4d4d', fontVariantNumeric:'tabular-nums', fontWeight:600 }}>{s.chg>=0?'+':''}{s.chg.toFixed(2)}</td>
                      <td style={{ padding:'8px 12px', color: s.chg>=0?'#00c087':'#ff4d4d', fontVariantNumeric:'tabular-nums' }}>{isNaN(s.chgPct)?'—':(s.chgPct>=0?'+':'')+s.chgPct.toFixed(1)+'%'}</td>
                      <td style={{ padding:'8px 12px', color:'#60a5fa', fontVariantNumeric:'tabular-nums' }}>{s.peak.toFixed(2)}</td>
                      <td style={{ padding:'8px 12px', color:'#f87171', fontVariantNumeric:'tabular-nums' }}>{s.trough.toFixed(2)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </>
        )}
      </div>
    </div>
  )
}
