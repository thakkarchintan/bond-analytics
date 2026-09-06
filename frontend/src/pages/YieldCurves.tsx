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

interface YieldRow { Date: string; Country: string; Yield_Pct: number }
interface EcbRow { Date: string; Maturity: string; MatYrs: number; Rate: number }

const COUNTRIES = ['Australia','Canada','Euro Area','Japan','New Zealand','Norway','South Korea','Sweden','Switzerland','United Kingdom','United States']
const COLORS: Record<string,string> = {
  'Australia': '#fb923c', 'Canada': '#818cf8', 'Euro Area': '#a78bfa',
  'Japan': '#34d399', 'New Zealand': '#86efac', 'Norway': '#67e8f9',
  'South Korea': '#fbbf24', 'Sweden': '#2dd4bf', 'Switzerland': '#e879f9',
  'United Kingdom': '#22d3ee', 'United States': '#60a5fa',
}
const ECB_MATURITIES = ['3M','6M','1Y','2Y','5Y','10Y','20Y','30Y']

export default function YieldCurves() {
  const [yields, setYields] = useState<YieldRow[]>([])
  const [ecb, setEcb] = useState<EcbRow[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [tab, setTab] = useState<'history'|'curve'>('history')
  const [selected, setSelected] = useState<string[]>(['United States','Euro Area','United Kingdom','Japan','Australia','Canada'])
  const [startYear, setStartYear] = useState(2010)
  const [ecbDate, setEcbDate] = useState('')

  useEffect(() => {
    Promise.all([
      apiFetch<YieldRow[]>('/api/macro/yields'),
      apiFetch<EcbRow[]>('/api/macro/ecb-curve'),
    ]).then(([y, e]) => {
      setYields(y)
      setEcb(e)
      // default ECB date = latest available
      const dates = Array.from(new Set(e.map(r => r.Date))).sort()
      if (dates.length) setEcbDate(dates[dates.length - 1])
      setLoading(false)
    }).catch(err => { setError(err.message); setLoading(false) })
  }, [])

  if (loading) return <div className="content-wrap"><div style={{ color:'#aaa', textAlign:'center', padding: 80 }}><div style={{ width:32, height:32, border:'3px solid #f39200', borderTopColor:'transparent', borderRadius:'50%', animation:'spin 0.8s linear infinite', margin:'0 auto 16px' }}/> Loading yield curve data…</div></div>
  if (error)   return <div className="content-wrap"><div style={{ color:'#ff4d4d', padding: 40 }}>Error: {error}<br/><small style={{color:'#888'}}>Is the FastAPI backend running?</small></div></div>

  // ── Historical yield lines ──
  const startDate = `${startYear}-01-01`
  const histTraces: PlotTrace[] = selected.map(c => {
    const rows = yields.filter(r => r.Country === c && r.Date >= startDate).sort((a,b) => a.Date.localeCompare(b.Date))
    return { type: 'scatter', mode: 'lines', name: c, x: rows.map(r => r.Date), y: rows.map(r => r.Yield_Pct), line: { color: COLORS[c] ?? '#888', width: 1.5 } }
  })

  // ── ECB term structure at selected date ──
  const ecbRows = ecb.filter(r => r.Date === ecbDate).sort((a,b) => a.MatYrs - b.MatYrs)
  const ecbTrace: PlotTrace = {
    type: 'scatter', mode: 'lines+markers', name: `ECB curve ${ecbDate}`,
    x: ecbRows.map(r => r.Maturity), y: ecbRows.map(r => r.Rate),
    line: { color: '#f39200', width: 2 }, marker: { color: '#f39200', size: 7 },
  }

  const ecbDates = Array.from(new Set(ecb.map(r => r.Date))).sort()

  return (
    <div className="bond-layout">
      {/* ── Sidebar ── */}
      <aside className="bond-sidebar">
        {/* Tab selector */}
        <div className="ctrl-section">
          <div className="ctrl-label">VIEW</div>
          <div className="pill-group">
            {(['history','curve'] as const).map(t => (
              <button key={t} className={`pill ${tab===t?'active':''}`} onClick={() => setTab(t)}>
                {t === 'history' ? 'Historical' : 'ECB Curve'}
              </button>
            ))}
          </div>
        </div>

        {tab === 'history' ? (
          <>
            <div className="ctrl-section">
              <div className="ctrl-label">START YEAR</div>
              <input type="number" className="ctrl-input" value={startYear} min={2000} max={2024}
                onChange={e => setStartYear(+e.target.value)} />
            </div>
            <div className="ctrl-section">
              <div className="ctrl-label">COUNTRIES</div>
              {COUNTRIES.map(c => (
                <label key={c} style={{ display:'flex', alignItems:'center', gap:8, padding:'3px 0', cursor:'pointer', fontSize:12, color: selected.includes(c) ? COLORS[c]??'#e8e8e8' : '#666' }}>
                  <input type="checkbox" checked={selected.includes(c)} onChange={e => setSelected(s => e.target.checked ? [...s,c] : s.filter(x=>x!==c))} style={{ accentColor: COLORS[c] }} />
                  {c}
                </label>
              ))}
            </div>
          </>
        ) : (
          <div className="ctrl-section">
            <div className="ctrl-label">DATE</div>
            <select className="ctrl-select" value={ecbDate} onChange={e => setEcbDate(e.target.value)}>
              {ecbDates.slice(-60).reverse().map(d => <option key={d} value={d}>{d}</option>)}
            </select>
          </div>
        )}
      </aside>

      {/* ── Main ── */}
      <div className="bond-main">
        {tab === 'history' ? (
          <>
            <div style={{ borderLeft:'3px solid #f39200', paddingLeft:12, margin:'0 0 16px', padding:'10px 14px', background:'rgba(243,146,0,0.04)', borderRadius:'0 6px 6px 0' }}>
              <div style={{ color:'#e8e8e8', fontWeight:600, fontSize:13, textTransform:'uppercase', letterSpacing:'0.04em' }}>10Y Government Bond Yields</div>
              <div style={{ color:'#888', fontSize:11, marginTop:4 }}>Monthly data from FRED · {selected.length} countries selected</div>
            </div>
            <Chart traces={histTraces} layout={{ title: { text: '', }, yaxis: { title: { text: 'Yield (%)', font: { color: '#666', size: 11 } } } }} />
          </>
        ) : (
          <>
            <div style={{ borderLeft:'3px solid #f39200', paddingLeft:12, margin:'0 0 16px', padding:'10px 14px', background:'rgba(243,146,0,0.04)', borderRadius:'0 6px 6px 0' }}>
              <div style={{ color:'#e8e8e8', fontWeight:600, fontSize:13, textTransform:'uppercase', letterSpacing:'0.04em' }}>ECB Svensson Yield Curve</div>
              <div style={{ color:'#888', fontSize:11, marginTop:4 }}>DBnomics · Date: {ecbDate}</div>
            </div>
            <Chart traces={ecbRows.length ? [ecbTrace] : []} layout={{ xaxis: { title: { text: 'Maturity', font: { color:'#666', size:11 } } }, yaxis: { title: { text: 'Rate (%)', font: { color:'#666', size:11 } } } }} height={400} />

            {/* Mini sparklines: all ECB maturities over time */}
            <div style={{ borderLeft:'3px solid #f39200', paddingLeft:12, margin:'24px 0 12px', padding:'10px 14px', background:'rgba(243,146,0,0.04)', borderRadius:'0 6px 6px 0' }}>
              <div style={{ color:'#e8e8e8', fontWeight:600, fontSize:13, textTransform:'uppercase', letterSpacing:'0.04em' }}>Yield History by Maturity</div>
              <div style={{ color:'#888', fontSize:11, marginTop:4 }}>ECB Svensson — all tenors</div>
            </div>
            <Chart traces={ECB_MATURITIES.map((m, i) => {
              const rows = ecb.filter(r => r.Maturity === m).sort((a,b) => a.Date.localeCompare(b.Date))
              const hue = ['#f39200','#60a5fa','#34d399','#a78bfa','#f87171','#fbbf24','#22d3ee','#e879f9'][i] ?? '#888'
              return { type:'scatter', mode:'lines', name:m, x:rows.map(r=>r.Date), y:rows.map(r=>r.Rate), line:{color:hue,width:1.5} }
            })} layout={{ yaxis: { ticksuffix:'%' } }} height={320} />
          </>
        )}
      </div>
    </div>
  )
}
