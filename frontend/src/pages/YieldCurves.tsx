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
interface UsCurveRow { Date: string; Maturity: string; Yield_Pct: number }

const COUNTRIES = ['Australia','Canada','Euro Area','Japan','New Zealand','Norway','South Korea','Sweden','Switzerland','United Kingdom','United States']
const COLORS: Record<string,string> = {
  'Australia': '#fb923c', 'Canada': '#818cf8', 'Euro Area': '#a78bfa',
  'Japan': '#34d399', 'New Zealand': '#86efac', 'Norway': '#67e8f9',
  'South Korea': '#fbbf24', 'Sweden': '#2dd4bf', 'Switzerland': '#e879f9',
  'United Kingdom': '#22d3ee', 'United States': '#60a5fa',
}
const ECB_MATURITIES = ['3M','6M','1Y','2Y','5Y','10Y','20Y','30Y']
const US_MATURITIES = ['1M','3M','6M','1Y','2Y','3Y','5Y','7Y','10Y','20Y','30Y']
const DATE_PALETTE = ['#f39200','#60a5fa','#34d399','#a78bfa','#f87171']

export default function YieldCurves() {
  const [yields, setYields] = useState<YieldRow[]>([])
  const [ecb, setEcb] = useState<EcbRow[]>([])
  const [usCurve, setUsCurve] = useState<UsCurveRow[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [tab, setTab] = useState<'history'|'curve'|'us'>('history')
  const [selected, setSelected] = useState<string[]>(['United States','Euro Area','United Kingdom','Japan','Australia','Canada'])
  const [startYear, setStartYear] = useState(2010)
  const [ecbDate, setEcbDate] = useState('')
  const [usDates, setUsDates] = useState<string[]>([])

  useEffect(() => {
    Promise.all([
      apiFetch<YieldRow[]>('/api/macro/yields'),
      apiFetch<EcbRow[]>('/api/macro/ecb-curve'),
      apiFetch<UsCurveRow[]>('/api/macro/us-curve'),
    ]).then(([y, e, u]) => {
      setYields(y)
      setEcb(e)
      setUsCurve(u)
      const ecbDates = Array.from(new Set(e.map(r => r.Date))).sort()
      if (ecbDates.length) setEcbDate(ecbDates[ecbDates.length - 1])
      const usDatesAll = Array.from(new Set(u.map(r => r.Date))).sort()
      // Default: last 5 available dates with ~3-month spacing
      const picks: string[] = []
      if (usDatesAll.length) {
        picks.push(usDatesAll[usDatesAll.length - 1])
        const targets = [90, 180, 365, 730]
        const latest = new Date(picks[0]).getTime()
        for (const days of targets) {
          const target = latest - days * 86400000
          const closest = usDatesAll.reduce((a, b) =>
            Math.abs(new Date(b).getTime() - target) < Math.abs(new Date(a).getTime() - target) ? b : a
          )
          if (!picks.includes(closest)) picks.push(closest)
        }
      }
      setUsDates(picks.slice(0, 5).sort())
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

  // ── US Curve ──
  const allUsDates = Array.from(new Set(usCurve.map(r => r.Date))).sort()
  const matOrder = ['1M','3M','6M','1Y','2Y','3Y','5Y','7Y','10Y','20Y','30Y']

  const usCurveTraces: PlotTrace[] = usDates.map((d, i) => {
    const rows = usCurve.filter(r => r.Date === d)
    const sorted = matOrder.filter(m => rows.some(r => r.Maturity === m)).map(m => ({ m, y: rows.find(r => r.Maturity === m)!.Yield_Pct }))
    return {
      type: 'scatter', mode: 'lines+markers', name: d,
      x: sorted.map(r => r.m), y: sorted.map(r => r.y),
      line: { color: DATE_PALETTE[i % DATE_PALETTE.length], width: 2 },
      marker: { color: DATE_PALETTE[i % DATE_PALETTE.length], size: 6 },
    }
  })

  // Spread badges from latest US date
  const latestUsDate = allUsDates[allUsDates.length - 1] ?? ''
  const latestUsRows = usCurve.filter(r => r.Date === latestUsDate)
  const getYield = (mat: string) => latestUsRows.find(r => r.Maturity === mat)?.Yield_Pct
  const y2 = getYield('2Y'), y10 = getYield('10Y'), y3m = getYield('3M')
  const spread2y10y = y2 != null && y10 != null ? (y10 - y2) : null
  const spread3m10y = y3m != null && y10 != null ? (y10 - y3m) : null

  // US 10Y history
  const us10yHist: PlotTrace = {
    type:'scatter', mode:'lines', name:'US 10Y Yield',
    x: usCurve.filter(r => r.Maturity === '10Y' && r.Date >= startDate).sort((a,b)=>a.Date.localeCompare(b.Date)).map(r=>r.Date),
    y: usCurve.filter(r => r.Maturity === '10Y' && r.Date >= startDate).sort((a,b)=>a.Date.localeCompare(b.Date)).map(r=>r.Yield_Pct),
    line: { color: '#f39200', width: 1.5 },
  }

  return (
    <div className="bond-layout">
      {/* ── Sidebar ── */}
      <aside className="bond-sidebar">
        <div className="ctrl-section">
          <div className="ctrl-label">VIEW</div>
          <div className="pill-group" style={{ flexWrap:'wrap', gap:4 }}>
            {(['history','us','curve'] as const).map(t => (
              <button key={t} className={`pill ${tab===t?'active':''}`} onClick={() => setTab(t)}>
                {t === 'history' ? 'Historical' : t === 'us' ? 'US Curve' : 'ECB Curve'}
              </button>
            ))}
          </div>
        </div>

        {tab === 'history' && (
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
        )}

        {tab === 'us' && (
          <>
            <div className="ctrl-section">
              <div className="ctrl-label">START YEAR (history)</div>
              <input type="number" className="ctrl-input" value={startYear} min={2000} max={2024}
                onChange={e => setStartYear(+e.target.value)} />
            </div>
            <div className="ctrl-section">
              <div className="ctrl-label">COMPARE DATES (up to 5)</div>
              <div style={{ fontSize:10, color:'#555', marginBottom:6 }}>Select dates for term structure overlay</div>
              {allUsDates.slice().reverse().slice(0, 120).filter((_, i) => i % 3 === 0 || allUsDates.slice().reverse().indexOf(allUsDates[allUsDates.length-1]) === i).map(d => (
                <label key={d} style={{ display:'flex', alignItems:'center', gap:8, padding:'2px 0', cursor:'pointer', fontSize:11,
                  color: usDates.includes(d) ? DATE_PALETTE[usDates.indexOf(d) % DATE_PALETTE.length] : '#555' }}>
                  <input type="checkbox" checked={usDates.includes(d)}
                    onChange={e => setUsDates(s => e.target.checked ? (s.length < 5 ? [...s,d].sort() : s) : s.filter(x=>x!==d))} />
                  {d}
                </label>
              ))}
            </div>
          </>
        )}

        {tab === 'curve' && (
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
        {tab === 'history' && (
          <>
            <div style={{ borderLeft:'3px solid #f39200', paddingLeft:12, margin:'0 0 16px', padding:'10px 14px', background:'rgba(243,146,0,0.04)', borderRadius:'0 6px 6px 0' }}>
              <div style={{ color:'#e8e8e8', fontWeight:600, fontSize:13, textTransform:'uppercase', letterSpacing:'0.04em' }}>10Y Government Bond Yields</div>
              <div style={{ color:'#888', fontSize:11, marginTop:4 }}>Monthly data from FRED · {selected.length} countries selected</div>
            </div>
            <Chart traces={histTraces} layout={{ yaxis: { title: { text: 'Yield (%)', font: { color: '#666', size: 11 } } } }} />
          </>
        )}

        {tab === 'us' && (
          <>
            {/* Spread badges */}
            <div style={{ display:'flex', gap:12, marginBottom:16, flexWrap:'wrap' }}>
              {[
                { label:'2Y–10Y Spread', val: spread2y10y, warn: spread2y10y != null && spread2y10y < 0 },
                { label:'3M–10Y Spread', val: spread3m10y, warn: spread3m10y != null && spread3m10y < 0 },
              ].map(({ label, val, warn }) => (
                <div key={label} style={{ background:'#1a1a1a', border:`1px solid ${warn ? '#ff4d4d44' : '#2a2a2a'}`, borderRadius:8, padding:'10px 16px', minWidth:160 }}>
                  <div style={{ color:'#666', fontSize:10, textTransform:'uppercase', letterSpacing:'0.05em', marginBottom:4 }}>{label}</div>
                  <div style={{ color: val == null ? '#555' : warn ? '#ff4d4d' : '#00c087', fontSize:20, fontWeight:700, fontVariantNumeric:'tabular-nums' }}>
                    {val != null ? (val >= 0 ? '+' : '') + val.toFixed(2) + '%' : '—'}
                  </div>
                  <div style={{ color: warn ? '#ff4d4d88' : '#555', fontSize:10, marginTop:2 }}>{warn ? 'INVERTED' : val != null && val < 0.5 ? 'Flat' : 'Normal'}</div>
                </div>
              ))}
              <div style={{ background:'#1a1a1a', border:'1px solid #2a2a2a', borderRadius:8, padding:'10px 16px', minWidth:160 }}>
                <div style={{ color:'#666', fontSize:10, textTransform:'uppercase', letterSpacing:'0.05em', marginBottom:4 }}>Latest Date</div>
                <div style={{ color:'#f39200', fontSize:14, fontWeight:600, marginTop:4 }}>{latestUsDate}</div>
                <div style={{ color:'#555', fontSize:10, marginTop:2 }}>US Treasury</div>
              </div>
            </div>

            <div style={{ borderLeft:'3px solid #f39200', padding:'10px 14px', background:'rgba(243,146,0,0.04)', borderRadius:'0 6px 6px 0', marginBottom:12 }}>
              <div style={{ color:'#e8e8e8', fontWeight:600, fontSize:13, textTransform:'uppercase', letterSpacing:'0.04em' }}>US Treasury Term Structure</div>
              <div style={{ color:'#888', fontSize:11, marginTop:4 }}>FRED · {usDates.length} dates compared · 1M–30Y maturities</div>
            </div>
            <Chart traces={usCurveTraces}
              layout={{ xaxis: { title:{ text:'Maturity', font:{color:'#666',size:11} }, categoryorder:'array', categoryarray: matOrder }, yaxis: { title:{ text:'Yield (%)', font:{color:'#666',size:11} } } }}
              height={380} />

            <div style={{ borderLeft:'3px solid #60a5fa', padding:'10px 14px', background:'rgba(96,165,250,0.04)', borderRadius:'0 6px 6px 0', margin:'28px 0 12px' }}>
              <div style={{ color:'#e8e8e8', fontWeight:600, fontSize:13, textTransform:'uppercase', letterSpacing:'0.04em' }}>US 10Y Yield — Historical</div>
              <div style={{ color:'#888', fontSize:11, marginTop:4 }}>FRED · daily · from {startYear}</div>
            </div>
            <Chart traces={us10yHist.x ? [us10yHist] : []} layout={{ yaxis: { title:{ text:'Yield (%)', font:{color:'#666',size:11} } } }} />
          </>
        )}

        {tab === 'curve' && (
          <>
            <div style={{ borderLeft:'3px solid #f39200', paddingLeft:12, margin:'0 0 16px', padding:'10px 14px', background:'rgba(243,146,0,0.04)', borderRadius:'0 6px 6px 0' }}>
              <div style={{ color:'#e8e8e8', fontWeight:600, fontSize:13, textTransform:'uppercase', letterSpacing:'0.04em' }}>ECB Svensson Yield Curve</div>
              <div style={{ color:'#888', fontSize:11, marginTop:4 }}>DBnomics · Date: {ecbDate}</div>
            </div>
            <Chart traces={ecbRows.length ? [ecbTrace] : []} layout={{ xaxis: { title: { text: 'Maturity', font: { color:'#666', size:11 } } }, yaxis: { title: { text: 'Rate (%)', font: { color:'#666', size:11 } } } }} height={400} />

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

