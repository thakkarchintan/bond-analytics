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

interface AnnualRow {
  Country: string; Year: number
  GDP_USD_Bn: number | null; RealGDP_Pct: number | null
  CPI_Pct: number | null; Unemployment_Pct: number | null
  CurrentAcct_Pct: number | null
}

const COUNTRIES = ['United States','Euro Area','United Kingdom','Japan','China','India','Canada','Brazil','Australia','South Korea','Switzerland','Sweden','Mexico','South Africa','Norway','New Zealand']
const PALETTE   = ['#60a5fa','#a78bfa','#22d3ee','#34d399','#f87171','#f472b6','#818cf8','#a3e635','#fb923c','#fbbf24','#e879f9','#2dd4bf','#c084fc','#f9a8d4','#67e8f9','#86efac']

export default function InflationGrowth() {
  const [data, setData] = useState<AnnualRow[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [selected, setSelected] = useState<string[]>(['United States','Euro Area','United Kingdom','Japan','China','India','Canada','Brazil'])
  const [startYear, setStartYear] = useState(2010)
  const [mode, setMode] = useState<'lines'|'bars'>('lines')
  const [view, setView] = useState<'timeseries'|'scatter'>('timeseries')
  const [scatterYear, setScatterYear] = useState(2023)

  useEffect(() => {
    apiFetch<AnnualRow[]>('/api/macro/inflation')
      .then(d => {
        setData(d)
        const years = Array.from(new Set(d.map(r => r.Year))).sort()
        if (years.length) setScatterYear(years[years.length - 1])
        setLoading(false)
      })
      .catch(err => { setError(err.message); setLoading(false) })
  }, [])

  if (loading) return <div className="content-wrap"><div style={{ color:'#aaa', textAlign:'center', padding: 80 }}><div style={{ width:32, height:32, border:'3px solid #f39200', borderTopColor:'transparent', borderRadius:'50%', animation:'spin 0.8s linear infinite', margin:'0 auto 16px' }}/> Loading inflation & growth data…</div></div>
  if (error)   return <div className="content-wrap"><div style={{ color:'#ff4d4d', padding: 40 }}>Error: {error}<br/><small style={{color:'#888'}}>Is the FastAPI backend running?</small></div></div>

  const years = Array.from(new Set(data.map(r => r.Year))).sort()
  const filtYears = years.filter(y => y >= startYear)
  const latestYear = Math.max(...years)

  function makeTraces(field: keyof AnnualRow): PlotTrace[] {
    return selected.map((c, i) => {
      const color = PALETTE[COUNTRIES.indexOf(c) % PALETTE.length]
      if (mode === 'bars') {
        const vals = filtYears.map(y => { const row = data.find(r => r.Country === c && r.Year === y); return (row?.[field] as number | null) ?? null })
        return { type:'bar', name:c, x:filtYears, y:vals, marker:{color}, opacity:0.85 }
      } else {
        const rows = data.filter(r => r.Country === c && r.Year >= startYear).sort((a,b) => a.Year - b.Year)
        return { type:'scatter', mode:'lines+markers', name:c, x:rows.map(r=>r.Year), y:rows.map(r=>r[field] as number|null), line:{color,width:1.5}, marker:{color,size:4} }
      }
    })
  }

  // Scatter views
  const scatterData = COUNTRIES.filter(c => selected.includes(c)).map((c, i) => {
    const row = data.find(r => r.Country === c && r.Year === scatterYear)
    return { c, color: PALETTE[i % PALETTE.length], cpi: row?.CPI_Pct ?? null, gdp: row?.RealGDP_Pct ?? null, unemp: row?.Unemployment_Pct ?? null }
  }).filter(r => r.cpi != null && r.gdp != null)

  const stagflationTrace: PlotTrace = {
    type: 'scatter', mode: 'markers+text',
    x: scatterData.map(r => r.gdp),
    y: scatterData.map(r => r.cpi),
    text: scatterData.map(r => r.c.replace('United States','US').replace('United Kingdom','UK').replace('Euro Area','EA')),
    textposition: 'top center',
    textfont: { size: 10, color: '#aaa' },
    marker: { color: scatterData.map(r => r.color), size: 12, line: { color: '#111', width: 1 } },
    hovertemplate: '<b>%{text}</b><br>Real GDP: %{x:.1f}%<br>CPI: %{y:.1f}%<extra></extra>',
  }

  const phillipsData = COUNTRIES.filter(c => selected.includes(c)).map((c, i) => {
    const row = data.find(r => r.Country === c && r.Year === scatterYear)
    return { c, color: PALETTE[i % PALETTE.length], cpi: row?.CPI_Pct ?? null, unemp: row?.Unemployment_Pct ?? null }
  }).filter(r => r.cpi != null && r.unemp != null)

  const phillipsTrace: PlotTrace = {
    type: 'scatter', mode: 'markers+text',
    x: phillipsData.map(r => r.unemp),
    y: phillipsData.map(r => r.cpi),
    text: phillipsData.map(r => r.c.replace('United States','US').replace('United Kingdom','UK').replace('Euro Area','EA')),
    textposition: 'top center',
    textfont: { size: 10, color: '#aaa' },
    marker: { color: phillipsData.map(r => r.color), size: 12, line: { color: '#111', width: 1 } },
    hovertemplate: '<b>%{text}</b><br>Unemployment: %{x:.1f}%<br>CPI: %{y:.1f}%<extra></extra>',
  }

  // Quadrant reference lines
  const quadrantShapes = [
    { type:'line', x0:-10, x1:20, y0:2, y1:2, line:{color:'#444',width:1,dash:'dot'} },
    { type:'line', x0:2, x1:2, y0:-5, y1:20, line:{color:'#444',width:1,dash:'dot'} },
  ]

  // Latest snapshot
  const snapshot = selected.map(c => {
    const row = data.find(r => r.Country === c && r.Year === latestYear)
    return { c, cpi: row?.CPI_Pct, gdp: row?.RealGDP_Pct, unemp: row?.Unemployment_Pct }
  }).filter(r => r.cpi != null || r.gdp != null)

  return (
    <div className="bond-layout">
      <aside className="bond-sidebar">
        <div className="ctrl-section">
          <div className="ctrl-label">VIEW</div>
          <div className="pill-group">
            {(['timeseries','scatter'] as const).map(v => (
              <button key={v} className={`pill ${view===v?'active':''}`} onClick={() => setView(v)}>
                {v === 'timeseries' ? 'Time Series' : 'Scatter'}
              </button>
            ))}
          </div>
        </div>

        {view === 'timeseries' ? (
          <>
            <div className="ctrl-section">
              <div className="ctrl-label">CHART TYPE</div>
              <div className="pill-group">
                {(['lines','bars'] as const).map(m => (
                  <button key={m} className={`pill ${mode===m?'active':''}`} onClick={() => setMode(m)}>{m === 'lines' ? 'Lines' : 'Bars'}</button>
                ))}
              </div>
            </div>
            <div className="ctrl-section">
              <div className="ctrl-label">START YEAR</div>
              <input type="number" className="ctrl-input" value={startYear} min={2000} max={2024} onChange={e => setStartYear(+e.target.value)} />
            </div>
          </>
        ) : (
          <div className="ctrl-section">
            <div className="ctrl-label">YEAR</div>
            <select className="ctrl-select" value={scatterYear} onChange={e => setScatterYear(+e.target.value)}>
              {years.slice().reverse().map(y => <option key={y} value={y}>{y}</option>)}
            </select>
          </div>
        )}

        <div className="ctrl-section">
          <div className="ctrl-label">COUNTRIES</div>
          {COUNTRIES.map((c, i) => (
            <label key={c} style={{ display:'flex', alignItems:'center', gap:8, padding:'3px 0', cursor:'pointer', fontSize:12, color: selected.includes(c) ? PALETTE[i%PALETTE.length] : '#666' }}>
              <input type="checkbox" checked={selected.includes(c)} onChange={e => setSelected(s => e.target.checked ? [...s,c] : s.filter(x=>x!==c))} style={{ accentColor: PALETTE[i%PALETTE.length] }} />
              {c}
            </label>
          ))}
        </div>
      </aside>

      <div className="bond-main">
        {view === 'timeseries' ? (
          <>
            {/* CPI */}
            <div style={{ borderLeft:'3px solid #f39200', padding:'10px 14px', background:'rgba(243,146,0,0.04)', borderRadius:'0 6px 6px 0', marginBottom:12 }}>
              <div style={{ color:'#e8e8e8', fontWeight:600, fontSize:13, textTransform:'uppercase', letterSpacing:'0.04em' }}>CPI Inflation</div>
              <div style={{ color:'#888', fontSize:11, marginTop:4 }}>IMF WEO · annual · % YoY</div>
            </div>
            <Chart traces={makeTraces('CPI_Pct')} layout={{ barmode: mode==='bars'?'group':undefined, yaxis:{ ticksuffix:'%', title:{text:'CPI %', font:{color:'#666',size:11}} } }} />

            {/* Real GDP Growth */}
            <div style={{ borderLeft:'3px solid #00c087', padding:'10px 14px', background:'rgba(0,192,135,0.04)', borderRadius:'0 6px 6px 0', margin:'28px 0 12px' }}>
              <div style={{ color:'#e8e8e8', fontWeight:600, fontSize:13, textTransform:'uppercase', letterSpacing:'0.04em' }}>Real GDP Growth</div>
              <div style={{ color:'#888', fontSize:11, marginTop:4 }}>IMF WEO · annual · % change</div>
            </div>
            <Chart traces={makeTraces('RealGDP_Pct')} layout={{ barmode: mode==='bars'?'group':undefined, yaxis:{ ticksuffix:'%', title:{text:'Real GDP %', font:{color:'#666',size:11}} } }} />

            {/* Unemployment */}
            <div style={{ borderLeft:'3px solid #f87171', padding:'10px 14px', background:'rgba(248,113,113,0.04)', borderRadius:'0 6px 6px 0', margin:'28px 0 12px' }}>
              <div style={{ color:'#e8e8e8', fontWeight:600, fontSize:13, textTransform:'uppercase', letterSpacing:'0.04em' }}>Unemployment Rate</div>
              <div style={{ color:'#888', fontSize:11, marginTop:4 }}>IMF WEO · annual · %</div>
            </div>
            <Chart traces={makeTraces('Unemployment_Pct')} layout={{ barmode: mode==='bars'?'group':undefined, yaxis:{ ticksuffix:'%', title:{text:'Unemployment %', font:{color:'#666',size:11}} } }} />

            {/* Latest snapshot table */}
            <div style={{ marginTop:28, overflowX:'auto' }}>
              <div style={{ color:'#666', fontSize:10, textTransform:'uppercase', letterSpacing:'0.05em', marginBottom:8 }}>{latestYear} Snapshot</div>
              <table style={{ width:'100%', borderCollapse:'collapse', fontSize:12 }}>
                <thead>
                  <tr style={{ borderBottom:'1px solid #2a2a2a' }}>
                    {['Country','CPI %','Real GDP %','Unemployment %'].map(h => <th key={h} style={{ padding:'8px 12px', textAlign:'left', color:'#666', fontWeight:500, textTransform:'uppercase', fontSize:10, letterSpacing:'0.05em' }}>{h}</th>)}
                  </tr>
                </thead>
                <tbody>
                  {snapshot.map(({ c, cpi, gdp, unemp }) => (
                    <tr key={c} style={{ borderBottom:'1px solid #1f1f1f' }}>
                      <td style={{ padding:'8px 12px', color:'#e8e8e8' }}>{c}</td>
                      <td style={{ padding:'8px 12px', color: cpi != null && cpi > 5 ? '#ff4d4d' : cpi != null && cpi < 2 ? '#888' : '#f39200', fontVariantNumeric:'tabular-nums' }}>{cpi != null ? cpi.toFixed(1) + '%' : '—'}</td>
                      <td style={{ padding:'8px 12px', color: gdp != null && gdp > 0 ? '#00c087' : '#ff4d4d', fontVariantNumeric:'tabular-nums' }}>{gdp != null ? gdp.toFixed(1) + '%' : '—'}</td>
                      <td style={{ padding:'8px 12px', color:'#aaa', fontVariantNumeric:'tabular-nums' }}>{unemp != null ? unemp.toFixed(1) + '%' : '—'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </>
        ) : (
          <>
            {/* Stagflation Quadrant */}
            <div style={{ borderLeft:'3px solid #f39200', padding:'10px 14px', background:'rgba(243,146,0,0.04)', borderRadius:'0 6px 6px 0', marginBottom:12 }}>
              <div style={{ color:'#e8e8e8', fontWeight:600, fontSize:13, textTransform:'uppercase', letterSpacing:'0.04em' }}>Stagflation Quadrant — {scatterYear}</div>
              <div style={{ color:'#888', fontSize:11, marginTop:4 }}>CPI inflation vs Real GDP growth · dashed lines at 2% · IMF WEO</div>
            </div>
            <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr', gap:8, marginBottom:10, fontSize:10, color:'#666' }}>
              <div style={{ background:'rgba(255,77,77,0.05)', border:'1px solid #ff4d4d22', borderRadius:6, padding:'6px 10px' }}>↖ High CPI, Low Growth = Stagflation</div>
              <div style={{ background:'rgba(0,192,135,0.05)', border:'1px solid #00c08722', borderRadius:6, padding:'6px 10px' }}>↗ High CPI, High Growth = Boom</div>
              <div style={{ background:'rgba(96,165,250,0.05)', border:'1px solid #60a5fa22', borderRadius:6, padding:'6px 10px' }}>↙ Low CPI, Low Growth = Stagnation</div>
              <div style={{ background:'rgba(243,146,0,0.05)', border:'1px solid #f3920022', borderRadius:6, padding:'6px 10px' }}>↘ Low CPI, High Growth = Goldilocks</div>
            </div>
            <Chart
              traces={scatterData.length ? [stagflationTrace] : []}
              layout={{
                hovermode: 'closest',
                xaxis: { title:{ text:'Real GDP Growth (%)', font:{color:'#666',size:11} }, zeroline:false, ticksuffix:'%' },
                yaxis: { title:{ text:'CPI Inflation (%)', font:{color:'#666',size:11} }, zeroline:false, ticksuffix:'%' },
                shapes: quadrantShapes,
                legend: { showlegend: false },
              }}
              height={420} />

            {/* Phillips Curve */}
            <div style={{ borderLeft:'3px solid #a78bfa', padding:'10px 14px', background:'rgba(167,139,250,0.04)', borderRadius:'0 6px 6px 0', margin:'28px 0 12px' }}>
              <div style={{ color:'#e8e8e8', fontWeight:600, fontSize:13, textTransform:'uppercase', letterSpacing:'0.04em' }}>Phillips Curve — {scatterYear}</div>
              <div style={{ color:'#888', fontSize:11, marginTop:4 }}>Unemployment vs CPI inflation · inverse relationship · IMF WEO</div>
            </div>
            <Chart
              traces={phillipsData.length ? [phillipsTrace] : []}
              layout={{
                hovermode: 'closest',
                xaxis: { title:{ text:'Unemployment Rate (%)', font:{color:'#666',size:11} }, zeroline:false, ticksuffix:'%' },
                yaxis: { title:{ text:'CPI Inflation (%)', font:{color:'#666',size:11} }, zeroline:false, ticksuffix:'%' },
                legend: { showlegend: false },
              }}
              height={380} />
          </>
        )}
      </div>
    </div>
  )
}
