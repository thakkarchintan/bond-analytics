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

interface LeadRow  { Date: string; Value: number; Series: string }
interface OecdRow  { Date: string; Country: string; ISO: string; Indicator: string; Value: number }

const LEADING_COLORS: Record<string,string> = {
  '2Y10Y Spread':         '#f39200',
  'Consumer Sentiment':   '#60a5fa',
  'Housing Starts':       '#34d399',
  'Industrial Production':'#a78bfa',
  'Initial Claims':       '#f87171',
  'Recession':            '#ff4d4d',
  'Unemployment':         '#fbbf24',
}

const OECD_COUNTRIES_DEFAULT = ['United States','Germany','China','Japan','United Kingdom','France','India','Canada']
const OECD_PALETTE = ['#60a5fa','#f39200','#f87171','#34d399','#22d3ee','#a78bfa','#fbbf24','#fb923c']

export default function LeadingIndicators() {
  const [leading, setLeading] = useState<LeadRow[]>([])
  const [oecd, setOecd] = useState<OecdRow[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [tab, setTab] = useState<'us'|'oecd'>('us')
  const [startYear, setStartYear] = useState(2000)
  const [indicator, setIndicator] = useState<'CLI'|'BCI'|'CCI'>('CLI')
  const [oecdCountries, setOecdCountries] = useState<string[]>(OECD_COUNTRIES_DEFAULT)

  useEffect(() => {
    Promise.all([
      apiFetch<LeadRow[]>('/api/macro/leading'),
      apiFetch<OecdRow[]>('/api/macro/oecd-bc'),
    ]).then(([l, o]) => { setLeading(l); setOecd(o); setLoading(false) })
      .catch(err => { setError(err.message); setLoading(false) })
  }, [])

  if (loading) return <div className="content-wrap"><div style={{ color:'#aaa', textAlign:'center', padding: 80 }}><div style={{ width:32, height:32, border:'3px solid #f39200', borderTopColor:'transparent', borderRadius:'50%', animation:'spin 0.8s linear infinite', margin:'0 auto 16px' }}/> Loading indicator data…</div></div>
  if (error)   return <div className="content-wrap"><div style={{ color:'#ff4d4d', padding: 40 }}>Error: {error}<br/><small style={{color:'#888'}}>Is the FastAPI backend running?</small></div></div>

  const startDate = `${startYear}-01-01`
  const allOecdCountries = Array.from(new Set(oecd.map(r => r.Country))).sort()

  // US leading series traces (excluding Recession — used as shading)
  const leadSeries = ['2Y10Y Spread','Consumer Sentiment','Housing Starts','Industrial Production','Initial Claims','Unemployment']
  const leadTraces: PlotTrace[] = leadSeries.map(s => {
    const rows = leading.filter(r => r.Series === s && r.Date >= startDate).sort((a,b) => a.Date.localeCompare(b.Date))
    return { type:'scatter', mode:'lines', name:s, x:rows.map(r=>r.Date), y:rows.map(r=>r.Value), line:{color:LEADING_COLORS[s]??'#888',width:1.5} }
  })

  // Recession shading as shape
  const recRows = leading.filter(r => r.Series === 'Recession' && r.Date >= startDate).sort((a,b) => a.Date.localeCompare(b.Date))
  const recTrace: PlotTrace = {
    type:'scatter', mode:'none', name:'Recession', fill:'tozeroy', fillcolor:'rgba(255,77,77,0.08)',
    x: recRows.map(r=>r.Date), y: recRows.map(r=>r.Value),
    hoverinfo:'skip', showlegend:true,
  }

  // 2Y10Y by itself for clarity
  const spreadTrace: PlotTrace = {
    ...leadTraces.find(t => t.name === '2Y10Y Spread')!,
    name: '2Y10Y Spread (bps)',
  }

  // OECD traces
  const oecdTraces: PlotTrace[] = oecdCountries.map((c, i) => {
    const rows = oecd.filter(r => r.Country === c && r.Indicator === indicator && r.Date >= startDate).sort((a,b) => a.Date.localeCompare(b.Date))
    return { type:'scatter', mode:'lines', name:c, x:rows.map(r=>r.Date), y:rows.map(r=>r.Value), line:{color:OECD_PALETTE[i%OECD_PALETTE.length],width:1.5} }
  })

  return (
    <div className="bond-layout">
      <aside className="bond-sidebar">
        <div className="ctrl-section">
          <div className="ctrl-label">VIEW</div>
          <div className="pill-group">
            {(['us','oecd'] as const).map(t => (
              <button key={t} className={`pill ${tab===t?'active':''}`} onClick={() => setTab(t)}>
                {t === 'us' ? 'US Indicators' : 'OECD'}
              </button>
            ))}
          </div>
        </div>
        <div className="ctrl-section">
          <div className="ctrl-label">START YEAR</div>
          <input type="number" className="ctrl-input" value={startYear} min={1990} max={2024} onChange={e => setStartYear(+e.target.value)} />
        </div>

        {tab === 'oecd' && (
          <>
            <div className="ctrl-section">
              <div className="ctrl-label">INDICATOR</div>
              {(['CLI','BCI','CCI'] as const).map(ind => (
                <button key={ind} className={`pill ${indicator===ind?'active':''}`} style={{ marginRight:4, marginBottom:4 }} onClick={() => setIndicator(ind)}>{ind}</button>
              ))}
            </div>
            <div className="ctrl-section" style={{ maxHeight:300, overflowY:'auto' }}>
              <div className="ctrl-label">COUNTRIES</div>
              {allOecdCountries.map((c, i) => (
                <label key={c} style={{ display:'flex', alignItems:'center', gap:8, padding:'3px 0', cursor:'pointer', fontSize:12, color: oecdCountries.includes(c) ? OECD_PALETTE[oecdCountries.indexOf(c)%OECD_PALETTE.length]??'#e8e8e8' : '#555' }}>
                  <input type="checkbox" checked={oecdCountries.includes(c)} onChange={e => setOecdCountries(s => e.target.checked ? [...s,c] : s.filter(x=>x!==c))} />
                  {c}
                </label>
              ))}
            </div>
          </>
        )}
      </aside>

      <div className="bond-main">
        {tab === 'us' ? (
          <>
            <div style={{ borderLeft:'3px solid #f39200', padding:'10px 14px', background:'rgba(243,146,0,0.04)', borderRadius:'0 6px 6px 0', marginBottom:12 }}>
              <div style={{ color:'#e8e8e8', fontWeight:600, fontSize:13, textTransform:'uppercase', letterSpacing:'0.04em' }}>2Y–10Y Treasury Spread</div>
              <div style={{ color:'#888', fontSize:11, marginTop:4 }}>FRED · inverted spread = recession signal</div>
            </div>
            <Chart traces={[recTrace, spreadTrace]} layout={{ yaxis: { title:{ text:'Spread (%)', font:{color:'#666',size:11} } } }} />

            <div style={{ borderLeft:'3px solid #f39200', padding:'10px 14px', background:'rgba(243,146,0,0.04)', borderRadius:'0 6px 6px 0', margin:'28px 0 12px' }}>
              <div style={{ color:'#e8e8e8', fontWeight:600, fontSize:13, textTransform:'uppercase', letterSpacing:'0.04em' }}>US Leading Indicators</div>
              <div style={{ color:'#888', fontSize:11, marginTop:4 }}>FRED · Consumer Sentiment, Housing Starts, Industrial Production, Initial Claims, Unemployment</div>
            </div>
            <Chart traces={[recTrace, ...leadTraces.filter(t => !['2Y10Y Spread'].includes(t.name as string))]} layout={{}} height={400} />
          </>
        ) : (
          <>
            <div style={{ borderLeft:'3px solid #f39200', padding:'10px 14px', background:'rgba(243,146,0,0.04)', borderRadius:'0 6px 6px 0', marginBottom:12 }}>
              <div style={{ color:'#e8e8e8', fontWeight:600, fontSize:13, textTransform:'uppercase', letterSpacing:'0.04em' }}>OECD {indicator} — {indicator === 'CLI' ? 'Composite Leading Indicator' : indicator === 'BCI' ? 'Business Confidence' : 'Consumer Confidence'}</div>
              <div style={{ color:'#888', fontSize:11, marginTop:4 }}>OECD via DBnomics · {oecdCountries.length} countries · index ~100 = long-run average</div>
            </div>
            <Chart traces={oecdTraces} layout={{ yaxis: { title:{ text:`${indicator} Index`, font:{color:'#666',size:11} } } }} height={440} />
          </>
        )}
      </div>
    </div>
  )
}
