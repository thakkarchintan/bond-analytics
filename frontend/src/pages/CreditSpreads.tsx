import { useState, useEffect, useRef } from 'react'
import apiFetch from '../api/client'

type PlotTrace = Record<string, unknown>
type PlotLayout = Record<string, unknown>

function Chart({ traces, layout, height = 340 }: { traces: PlotTrace[]; layout: PlotLayout; height?: number }) {
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
        xaxis: { gridcolor: '#2a2a2a', tickfont: { color: '#777', size: 10 }, zerolinecolor: '#2a2a2a' },
        yaxis: { gridcolor: '#2a2a2a', tickfont: { color: '#777', size: 10 }, zerolinecolor: '#444', ticksuffix: '%' },
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

interface SpreadRow { Date: string; Series: string; OAS_Pct: number }

const SERIES_COLORS: Record<string, string> = {
  'IG': '#60a5fa', 'HY': '#f87171',
  'AAA': '#34d399', 'AA': '#22d3ee', 'A': '#818cf8',
  'BBB': '#f39200', 'BB': '#fbbf24', 'B': '#fb923c', 'CCC': '#ff4d4d',
}

const IG_HY = ['IG', 'HY']
const RATING_LADDER = ['AAA','AA','A','BBB','BB','B','CCC']

export default function CreditSpreads() {
  const [data, setData] = useState<SpreadRow[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [startYear, setStartYear] = useState(2010)
  const [view, setView] = useState<'main'|'ladder'>('main')

  useEffect(() => {
    apiFetch<SpreadRow[]>('/api/macro/credit-spreads')
      .then(d => { setData(d); setLoading(false) })
      .catch(err => { setError(err.message); setLoading(false) })
  }, [])

  if (loading) return <div className="content-wrap"><div style={{ color:'#aaa', textAlign:'center', padding: 80 }}><div style={{ width:32, height:32, border:'3px solid #f39200', borderTopColor:'transparent', borderRadius:'50%', animation:'spin 0.8s linear infinite', margin:'0 auto 16px' }}/> Loading credit spread data…</div></div>
  if (error)   return <div className="content-wrap"><div style={{ color:'#ff4d4d', padding: 40 }}>Error: {error}<br/><small style={{color:'#888'}}>Is the FastAPI backend running?</small></div></div>

  const startDate = `${startYear}-01-01`

  const makeTraces = (series: string[]): PlotTrace[] =>
    series.map(s => {
      const rows = data.filter(r => r.Series === s && r.Date >= startDate).sort((a,b) => a.Date.localeCompare(b.Date))
      return { type:'scatter', mode:'lines', name:s, x:rows.map(r=>r.Date), y:rows.map(r=>r.OAS_Pct), line:{color:SERIES_COLORS[s]??'#888',width:1.5} }
    })

  // Latest values
  const latestByS = Object.fromEntries(
    [...IG_HY, ...RATING_LADDER].map(s => {
      const rows = data.filter(r => r.Series === s).sort((a,b) => b.Date.localeCompare(a.Date))
      return [s, rows[0]?.OAS_Pct]
    })
  )

  return (
    <div className="bond-layout">
      <aside className="bond-sidebar">
        <div className="ctrl-section">
          <div className="ctrl-label">VIEW</div>
          <div className="pill-group">
            {(['main','ladder'] as const).map(v => (
              <button key={v} className={`pill ${view===v?'active':''}`} onClick={() => setView(v)}>
                {v === 'main' ? 'IG / HY' : 'Rating Ladder'}
              </button>
            ))}
          </div>
        </div>
        <div className="ctrl-section">
          <div className="ctrl-label">START YEAR</div>
          <input type="number" className="ctrl-input" value={startYear} min={2000} max={2024} onChange={e => setStartYear(+e.target.value)} />
        </div>

        {/* Latest spread snapshot */}
        <div className="ctrl-section">
          <div className="ctrl-label">LATEST OAS (%)</div>
          {[...IG_HY, ...RATING_LADDER].map(s => (
            <div key={s} style={{ display:'flex', justifyContent:'space-between', padding:'4px 0', fontSize:12, borderBottom:'1px solid #1a1a1a' }}>
              <span style={{ color: SERIES_COLORS[s]??'#aaa' }}>{s}</span>
              <span style={{ color:'#e8e8e8', fontVariantNumeric:'tabular-nums' }}>
                {latestByS[s] != null ? latestByS[s]!.toFixed(2) + '%' : '—'}
              </span>
            </div>
          ))}
        </div>
      </aside>

      <div className="bond-main">
        {view === 'main' ? (
          <>
            <div style={{ borderLeft:'3px solid #f39200', padding:'10px 14px', background:'rgba(243,146,0,0.04)', borderRadius:'0 6px 6px 0', marginBottom:12 }}>
              <div style={{ color:'#e8e8e8', fontWeight:600, fontSize:13, textTransform:'uppercase', letterSpacing:'0.04em' }}>IG vs HY OAS Credit Spreads</div>
              <div style={{ color:'#888', fontSize:11, marginTop:4 }}>ICE BofA OAS — Investment Grade vs High Yield</div>
            </div>
            <Chart traces={makeTraces(IG_HY)} layout={{ yaxis: { title:{ text:'OAS (%)', font:{color:'#666',size:11} } } }} />

            {/* KPI strip */}
            <div className="kpi-strip" style={{ margin:'20px 0' }}>
              {IG_HY.map(s => (
                <div key={s} className="kpi-card">
                  <div style={{ color:'#888', fontSize:10, textTransform:'uppercase', letterSpacing:'0.06em', marginBottom:4 }}>{s === 'IG' ? 'Investment Grade' : 'High Yield'}</div>
                  <div style={{ color: SERIES_COLORS[s], fontSize:22, fontWeight:700, fontVariantNumeric:'tabular-nums' }}>
                    {latestByS[s] != null ? latestByS[s]!.toFixed(2) + '%' : '—'}
                  </div>
                </div>
              ))}
            </div>
          </>
        ) : (
          <>
            <div style={{ borderLeft:'3px solid #f39200', padding:'10px 14px', background:'rgba(243,146,0,0.04)', borderRadius:'0 6px 6px 0', marginBottom:12 }}>
              <div style={{ color:'#e8e8e8', fontWeight:600, fontSize:13, textTransform:'uppercase', letterSpacing:'0.04em' }}>Credit Rating Ladder — OAS</div>
              <div style={{ color:'#888', fontSize:11, marginTop:4 }}>ICE BofA OAS by rating bucket: AAA → CCC</div>
            </div>
            <Chart traces={makeTraces(RATING_LADDER)} layout={{ yaxis: { title:{ text:'OAS (%)', font:{color:'#666',size:11} } } }} height={380} />
          </>
        )}
      </div>
    </div>
  )
}
