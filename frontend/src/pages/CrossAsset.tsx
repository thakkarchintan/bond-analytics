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

interface AssetRow { Date: string; Value: number; Series: string }

const SERIES_COLOR: Record<string, string> = {
  'S&P 500':  '#60a5fa',
  'VIX':      '#ff4d4d',
  'WTI Crude':'#f39200',
}

export default function CrossAsset() {
  const [data, setData] = useState<AssetRow[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [startYear, setStartYear] = useState(2010)

  useEffect(() => {
    apiFetch<AssetRow[]>('/api/macro/cross-asset')
      .then(d => { setData(d); setLoading(false) })
      .catch(err => { setError(err.message); setLoading(false) })
  }, [])

  if (loading) return <div className="content-wrap"><div style={{ color:'#aaa', textAlign:'center', padding: 80 }}><div style={{ width:32, height:32, border:'3px solid #f39200', borderTopColor:'transparent', borderRadius:'50%', animation:'spin 0.8s linear infinite', margin:'0 auto 16px' }}/> Loading cross-asset data…</div></div>
  if (error)   return <div className="content-wrap"><div style={{ color:'#ff4d4d', padding: 40 }}>Error: {error}<br/><small style={{color:'#888'}}>Is the FastAPI backend running?</small></div></div>

  const startDate = `${startYear}-01-01`
  const series = ['S&P 500', 'VIX', 'WTI Crude']

  // Latest values
  const latest = Object.fromEntries(series.map(s => {
    const rows = data.filter(r => r.Series === s).sort((a,b) => b.Date.localeCompare(a.Date))
    return [s, { val: rows[0]?.Value, date: rows[0]?.Date }]
  }))

  // Separate chart per series (different scales)
  const makeTrace = (s: string): PlotTrace => {
    const rows = data.filter(r => r.Series === s && r.Date >= startDate).sort((a,b) => a.Date.localeCompare(b.Date))
    return { type:'scatter', mode:'lines', name:s, x:rows.map(r=>r.Date), y:rows.map(r=>r.Value), line:{color:SERIES_COLOR[s]??'#888',width:1.5} }
  }

  // Combined normalised (z-score) view
  const normalised = series.map(s => {
    const rows = data.filter(r => r.Series === s && r.Date >= startDate).sort((a,b) => a.Date.localeCompare(b.Date))
    const vals = rows.map(r => r.Value)
    const mean = vals.reduce((a,b)=>a+b,0)/vals.length
    const std  = Math.sqrt(vals.reduce((a,b)=>a+(b-mean)**2,0)/vals.length) || 1
    return { type:'scatter', mode:'lines', name:s + ' (z)', x:rows.map(r=>r.Date), y:vals.map(v=>(v-mean)/std), line:{color:SERIES_COLOR[s]??'#888',width:1.5} }
  })

  return (
    <div className="bond-layout">
      <aside className="bond-sidebar">
        <div className="ctrl-section">
          <div className="ctrl-label">START YEAR</div>
          <input type="number" className="ctrl-input" value={startYear} min={2000} max={2024} onChange={e => setStartYear(+e.target.value)} />
        </div>

        <div className="ctrl-section">
          <div className="ctrl-label">LATEST VALUES</div>
          {series.map(s => (
            <div key={s} style={{ padding:'8px 0', borderBottom:'1px solid #1a1a1a' }}>
              <div style={{ color:'#888', fontSize:10, textTransform:'uppercase', letterSpacing:'0.06em' }}>{s}</div>
              <div style={{ color: SERIES_COLOR[s], fontSize:18, fontWeight:700, fontVariantNumeric:'tabular-nums', marginTop:2 }}>
                {latest[s]?.val != null ? latest[s].val!.toLocaleString('en-US', { maximumFractionDigits: s === 'VIX' ? 2 : 0 }) : '—'}
              </div>
              <div style={{ color:'#555', fontSize:10, marginTop:2 }}>{latest[s]?.date ?? ''}</div>
            </div>
          ))}
        </div>
      </aside>

      <div className="bond-main">
        {/* S&P 500 */}
        <div style={{ borderLeft:'3px solid #f39200', padding:'10px 14px', background:'rgba(243,146,0,0.04)', borderRadius:'0 6px 6px 0', marginBottom:12 }}>
          <div style={{ color:'#e8e8e8', fontWeight:600, fontSize:13, textTransform:'uppercase', letterSpacing:'0.04em' }}>S&P 500</div>
          <div style={{ color:'#888', fontSize:11, marginTop:4 }}>FRED · daily</div>
        </div>
        <Chart traces={[makeTrace('S&P 500')]} layout={{ yaxis: { title:{ text:'Index', font:{color:'#666',size:11} } } }} />

        {/* VIX */}
        <div style={{ borderLeft:'3px solid #ff4d4d', padding:'10px 14px', background:'rgba(255,77,77,0.04)', borderRadius:'0 6px 6px 0', margin:'28px 0 12px' }}>
          <div style={{ color:'#e8e8e8', fontWeight:600, fontSize:13, textTransform:'uppercase', letterSpacing:'0.04em' }}>VIX — Volatility Index</div>
          <div style={{ color:'#888', fontSize:11, marginTop:4 }}>FRED · daily · fear gauge</div>
        </div>
        <Chart traces={[makeTrace('VIX')]} layout={{ yaxis: { title:{ text:'VIX', font:{color:'#666',size:11} } } }} />

        {/* WTI */}
        <div style={{ borderLeft:'3px solid #f39200', padding:'10px 14px', background:'rgba(243,146,0,0.04)', borderRadius:'0 6px 6px 0', margin:'28px 0 12px' }}>
          <div style={{ color:'#e8e8e8', fontWeight:600, fontSize:13, textTransform:'uppercase', letterSpacing:'0.04em' }}>WTI Crude Oil</div>
          <div style={{ color:'#888', fontSize:11, marginTop:4 }}>FRED · daily · USD/barrel</div>
        </div>
        <Chart traces={[makeTrace('WTI Crude')]} layout={{ yaxis: { title:{ text:'USD / bbl', font:{color:'#666',size:11} } } }} />

        {/* Normalised overlay */}
        <div style={{ borderLeft:'3px solid #a78bfa', padding:'10px 14px', background:'rgba(167,139,250,0.04)', borderRadius:'0 6px 6px 0', margin:'28px 0 12px' }}>
          <div style={{ color:'#e8e8e8', fontWeight:600, fontSize:13, textTransform:'uppercase', letterSpacing:'0.04em' }}>Normalised (Z-Score) Overlay</div>
          <div style={{ color:'#888', fontSize:11, marginTop:4 }}>All three series on the same z-score axis for cross-asset comparison</div>
        </div>
        <Chart traces={normalised as PlotTrace[]} layout={{ yaxis: { title:{ text:'Z-score', font:{color:'#666',size:11} }, zerolinecolor:'#444' } }} />
      </div>
    </div>
  )
}
