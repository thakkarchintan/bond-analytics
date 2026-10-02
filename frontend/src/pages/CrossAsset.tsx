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

interface AssetRow  { Date: string; Value: number; Series: string }
interface UsCurveRow { Date: string; Maturity: string; Yield_Pct: number }
interface SpreadRow { Date: string; Series: string; OAS_Pct: number }
interface LeadRow   { Date: string; Value: number; Series: string }

const SERIES_COLOR: Record<string, string> = {
  'S&P 500':  '#60a5fa',
  'VIX':      '#ff4d4d',
  'WTI Crude':'#f39200',
  'US 10Y':   '#34d399',
  'IG Spread':'#a78bfa',
  'HY Spread':'#f87171',
}

export default function CrossAsset() {
  const [data, setData] = useState<AssetRow[]>([])
  const [usCurve, setUsCurve] = useState<UsCurveRow[]>([])
  const [spreads, setSpreads] = useState<SpreadRow[]>([])
  const [recession, setRecession] = useState<LeadRow[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [startYear, setStartYear] = useState(2010)

  useEffect(() => {
    Promise.all([
      apiFetch<AssetRow[]>('/api/macro/cross-asset'),
      apiFetch<UsCurveRow[]>('/api/macro/us-curve'),
      apiFetch<SpreadRow[]>('/api/macro/credit-spreads'),
      apiFetch<LeadRow[]>('/api/macro/leading'),
    ]).then(([d, u, s, l]) => {
      setData(d)
      setUsCurve(u)
      setSpreads(s)
      setRecession(l.filter(r => r.Series === 'Recession'))
      setLoading(false)
    }).catch(err => { setError(err.message); setLoading(false) })
  }, [])

  if (loading) return <div className="content-wrap"><div style={{ color:'#aaa', textAlign:'center', padding: 80 }}><div style={{ width:32, height:32, border:'3px solid #f39200', borderTopColor:'transparent', borderRadius:'50%', animation:'spin 0.8s linear infinite', margin:'0 auto 16px' }}/> Loading cross-asset data…</div></div>
  if (error)   return <div className="content-wrap"><div style={{ color:'#ff4d4d', padding: 40 }}>Error: {error}<br/><small style={{color:'#888'}}>Is the FastAPI backend running?</small></div></div>

  const startDate = `${startYear}-01-01`
  const series = ['S&P 500', 'VIX', 'WTI Crude']

  // Recession shading trace (shared)
  const recRows = recession.filter(r => r.Date >= startDate).sort((a,b) => a.Date.localeCompare(b.Date))
  const recTrace: PlotTrace = {
    type:'scatter', mode:'none', name:'Recession', fill:'tozeroy', fillcolor:'rgba(255,77,77,0.07)',
    x: recRows.map(r=>r.Date), y: recRows.map(r=>r.Value),
    hoverinfo:'skip', showlegend:false,
  }

  // Latest values
  const latest = Object.fromEntries(series.map(s => {
    const rows = data.filter(r => r.Series === s).sort((a,b) => b.Date.localeCompare(a.Date))
    return [s, { val: rows[0]?.Value, date: rows[0]?.Date }]
  }))

  // US 10Y latest
  const us10yRows = usCurve.filter(r => r.Maturity === '10Y').sort((a,b) => b.Date.localeCompare(a.Date))
  const latestUs10y = us10yRows[0]

  // IG / HY latest
  const igRows = spreads.filter(r => r.Series === 'IG OAS').sort((a,b) => b.Date.localeCompare(a.Date))
  const hyRows = spreads.filter(r => r.Series === 'HY OAS').sort((a,b) => b.Date.localeCompare(a.Date))

  const makeTrace = (s: string): PlotTrace => {
    const rows = data.filter(r => r.Series === s && r.Date >= startDate).sort((a,b) => a.Date.localeCompare(b.Date))
    return { type:'scatter', mode:'lines', name:s, x:rows.map(r=>r.Date), y:rows.map(r=>r.Value), line:{color:SERIES_COLOR[s]??'#888',width:1.5} }
  }

  const us10yTrace: PlotTrace = {
    type:'scatter', mode:'lines', name:'US 10Y Yield',
    x: usCurve.filter(r => r.Maturity === '10Y' && r.Date >= startDate).sort((a,b)=>a.Date.localeCompare(b.Date)).map(r=>r.Date),
    y: usCurve.filter(r => r.Maturity === '10Y' && r.Date >= startDate).sort((a,b)=>a.Date.localeCompare(b.Date)).map(r=>r.Yield_Pct),
    line:{color:SERIES_COLOR['US 10Y'],width:1.5},
  }

  const igTrace: PlotTrace = {
    type:'scatter', mode:'lines', name:'IG OAS',
    x: spreads.filter(r => r.Series === 'IG OAS' && r.Date >= startDate).sort((a,b)=>a.Date.localeCompare(b.Date)).map(r=>r.Date),
    y: spreads.filter(r => r.Series === 'IG OAS' && r.Date >= startDate).sort((a,b)=>a.Date.localeCompare(b.Date)).map(r=>r.OAS_Pct),
    line:{color:SERIES_COLOR['IG Spread'],width:1.5},
  }

  const hyTrace: PlotTrace = {
    type:'scatter', mode:'lines', name:'HY OAS',
    x: spreads.filter(r => r.Series === 'HY OAS' && r.Date >= startDate).sort((a,b)=>a.Date.localeCompare(b.Date)).map(r=>r.Date),
    y: spreads.filter(r => r.Series === 'HY OAS' && r.Date >= startDate).sort((a,b)=>a.Date.localeCompare(b.Date)).map(r=>r.OAS_Pct),
    line:{color:SERIES_COLOR['HY Spread'],width:1.5},
  }

  // Combined normalised (z-score) view
  const normSeries = [
    { name:'S&P 500', vals: data.filter(r=>r.Series==='S&P 500'&&r.Date>=startDate).sort((a,b)=>a.Date.localeCompare(b.Date)), key:'val' as const },
    { name:'VIX', vals: data.filter(r=>r.Series==='VIX'&&r.Date>=startDate).sort((a,b)=>a.Date.localeCompare(b.Date)), key:'val' as const },
    { name:'WTI Crude', vals: data.filter(r=>r.Series==='WTI Crude'&&r.Date>=startDate).sort((a,b)=>a.Date.localeCompare(b.Date)), key:'val' as const },
  ]
  const normalised = normSeries.map(({ name, vals }) => {
    const ys = vals.map(r => r.Value)
    const mean = ys.reduce((a,b)=>a+b,0)/ys.length
    const std  = Math.sqrt(ys.reduce((a,b)=>a+(b-mean)**2,0)/ys.length) || 1
    return { type:'scatter', mode:'lines', name: name + ' (z)', x:vals.map(r=>r.Date), y:ys.map(v=>(v-mean)/std), line:{color:SERIES_COLOR[name]??'#888',width:1.5} } as PlotTrace
  })

  const kpiItems = [
    ...series.map(s => ({ label: s, val: latest[s]?.val, date: latest[s]?.date, color: SERIES_COLOR[s], fmt: (v: number) => s === 'VIX' ? v.toFixed(2) : v.toLocaleString('en-US',{maximumFractionDigits:0}) })),
    { label:'US 10Y', val: latestUs10y?.Yield_Pct, date: latestUs10y?.Date, color: SERIES_COLOR['US 10Y'], fmt: (v: number) => v.toFixed(2) + '%' },
    { label:'IG OAS', val: igRows[0]?.OAS_Pct, date: igRows[0]?.Date, color: SERIES_COLOR['IG Spread'], fmt: (v: number) => v.toFixed(0) + 'bps' },
    { label:'HY OAS', val: hyRows[0]?.OAS_Pct, date: hyRows[0]?.Date, color: SERIES_COLOR['HY Spread'], fmt: (v: number) => v.toFixed(0) + 'bps' },
  ]

  return (
    <div className="bond-layout">
      <aside className="bond-sidebar">
        <div className="ctrl-section">
          <div className="ctrl-label">START YEAR</div>
          <input type="number" className="ctrl-input" value={startYear} min={2000} max={2024} onChange={e => setStartYear(+e.target.value)} />
        </div>

        <div className="ctrl-section">
          <div className="ctrl-label">LATEST VALUES</div>
          {kpiItems.map(({ label, val, date, color, fmt }) => (
            <div key={label} style={{ padding:'8px 0', borderBottom:'1px solid #1a1a1a' }}>
              <div style={{ color:'#888', fontSize:10, textTransform:'uppercase', letterSpacing:'0.06em' }}>{label}</div>
              <div style={{ color, fontSize:16, fontWeight:700, fontVariantNumeric:'tabular-nums', marginTop:2 }}>
                {val != null ? fmt(val) : '—'}
              </div>
              <div style={{ color:'#555', fontSize:10, marginTop:1 }}>{date ?? ''}</div>
            </div>
          ))}
        </div>
      </aside>

      <div className="bond-main">
        {/* S&P 500 */}
        <div style={{ borderLeft:'3px solid #60a5fa', padding:'10px 14px', background:'rgba(96,165,250,0.04)', borderRadius:'0 6px 6px 0', marginBottom:12 }}>
          <div style={{ color:'#e8e8e8', fontWeight:600, fontSize:13, textTransform:'uppercase', letterSpacing:'0.04em' }}>S&P 500</div>
          <div style={{ color:'#888', fontSize:11, marginTop:4 }}>FRED · daily</div>
        </div>
        <Chart traces={recRows.length ? [recTrace, makeTrace('S&P 500')] : [makeTrace('S&P 500')]} layout={{ yaxis: { title:{ text:'Index', font:{color:'#666',size:11} } } }} />

        {/* VIX */}
        <div style={{ borderLeft:'3px solid #ff4d4d', padding:'10px 14px', background:'rgba(255,77,77,0.04)', borderRadius:'0 6px 6px 0', margin:'28px 0 12px' }}>
          <div style={{ color:'#e8e8e8', fontWeight:600, fontSize:13, textTransform:'uppercase', letterSpacing:'0.04em' }}>VIX — Volatility Index</div>
          <div style={{ color:'#888', fontSize:11, marginTop:4 }}>FRED · daily · fear gauge</div>
        </div>
        <Chart traces={recRows.length ? [recTrace, makeTrace('VIX')] : [makeTrace('VIX')]} layout={{ yaxis: { title:{ text:'VIX', font:{color:'#666',size:11} } } }} />

        {/* WTI */}
        <div style={{ borderLeft:'3px solid #f39200', padding:'10px 14px', background:'rgba(243,146,0,0.04)', borderRadius:'0 6px 6px 0', margin:'28px 0 12px' }}>
          <div style={{ color:'#e8e8e8', fontWeight:600, fontSize:13, textTransform:'uppercase', letterSpacing:'0.04em' }}>WTI Crude Oil</div>
          <div style={{ color:'#888', fontSize:11, marginTop:4 }}>FRED · daily · USD/barrel</div>
        </div>
        <Chart traces={recRows.length ? [recTrace, makeTrace('WTI Crude')] : [makeTrace('WTI Crude')]} layout={{ yaxis: { title:{ text:'USD / bbl', font:{color:'#666',size:11} } } }} />

        {/* US 10Y */}
        <div style={{ borderLeft:'3px solid #34d399', padding:'10px 14px', background:'rgba(52,211,153,0.04)', borderRadius:'0 6px 6px 0', margin:'28px 0 12px' }}>
          <div style={{ color:'#e8e8e8', fontWeight:600, fontSize:13, textTransform:'uppercase', letterSpacing:'0.04em' }}>US 10Y Treasury Yield</div>
          <div style={{ color:'#888', fontSize:11, marginTop:4 }}>FRED · daily · %</div>
        </div>
        <Chart traces={recRows.length ? [recTrace, us10yTrace] : [us10yTrace]} layout={{ yaxis: { ticksuffix:'%', title:{ text:'Yield (%)', font:{color:'#666',size:11} } } }} />

        {/* Credit Spreads */}
        <div style={{ borderLeft:'3px solid #a78bfa', padding:'10px 14px', background:'rgba(167,139,250,0.04)', borderRadius:'0 6px 6px 0', margin:'28px 0 12px' }}>
          <div style={{ color:'#e8e8e8', fontWeight:600, fontSize:13, textTransform:'uppercase', letterSpacing:'0.04em' }}>Credit Spreads — IG & HY OAS</div>
          <div style={{ color:'#888', fontSize:11, marginTop:4 }}>ICE BofA · daily · basis points</div>
        </div>
        <Chart traces={recRows.length ? [recTrace, igTrace, hyTrace] : [igTrace, hyTrace]} layout={{ yaxis: { title:{ text:'OAS (bps)', font:{color:'#666',size:11} } } }} />

        {/* Normalised overlay */}
        <div style={{ borderLeft:'3px solid #a78bfa', padding:'10px 14px', background:'rgba(167,139,250,0.04)', borderRadius:'0 6px 6px 0', margin:'28px 0 12px' }}>
          <div style={{ color:'#e8e8e8', fontWeight:600, fontSize:13, textTransform:'uppercase', letterSpacing:'0.04em' }}>Normalised (Z-Score) Overlay</div>
          <div style={{ color:'#888', fontSize:11, marginTop:4 }}>S&P 500, VIX, WTI on same z-score axis</div>
        </div>
        <Chart traces={normalised} layout={{ yaxis: { title:{ text:'Z-score', font:{color:'#666',size:11} }, zerolinecolor:'#444' } }} />
      </div>
    </div>
  )
}
