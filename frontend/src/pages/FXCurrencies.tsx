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

interface FxRow   { Date: string; Country: string; LocalPerUSD: number }
interface ReerRow { Date: string; Currency: string; EER: number }

const FX_COUNTRIES = ['Australia','Brazil','Canada','China','Euro Area','India','Japan','Mexico','Norway','South Africa','South Korea','Sweden','Switzerland','United Kingdom']
const REER_CURRENCIES = ['AUD','BRL','CAD','CHF','CNY','EUR','GBP','INR','JPY','KRW','MXN','NOK','SEK','USD']

const PALETTE = ['#60a5fa','#f87171','#34d399','#a78bfa','#f39200','#22d3ee','#fbbf24','#fb923c','#818cf8','#e879f9','#67e8f9','#2dd4bf','#86efac','#f9a8d4']

export default function FXCurrencies() {
  const [fx, setFx] = useState<FxRow[]>([])
  const [reer, setReer] = useState<ReerRow[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [tab, setTab] = useState<'spot'|'reer'>('spot')
  const [startYear, setStartYear] = useState(2015)
  const [selectedFx, setSelectedFx] = useState<string[]>(['Euro Area','Japan','China','United Kingdom','Australia','Canada'])
  const [selectedReer, setSelectedReer] = useState<string[]>(['EUR','JPY','CNY','GBP','USD','AUD'])

  useEffect(() => {
    Promise.all([
      apiFetch<FxRow[]>('/api/macro/fx'),
      apiFetch<ReerRow[]>('/api/macro/reer'),
    ]).then(([f, r]) => { setFx(f); setReer(r); setLoading(false) })
      .catch(err => { setError(err.message); setLoading(false) })
  }, [])

  if (loading) return <div className="content-wrap"><div style={{ color:'#aaa', textAlign:'center', padding: 80 }}><div style={{ width:32, height:32, border:'3px solid #f39200', borderTopColor:'transparent', borderRadius:'50%', animation:'spin 0.8s linear infinite', margin:'0 auto 16px' }}/> Loading FX data…</div></div>
  if (error)   return <div className="content-wrap"><div style={{ color:'#ff4d4d', padding: 40 }}>Error: {error}<br/><small style={{color:'#888'}}>Is the FastAPI backend running?</small></div></div>

  const startDate = `${startYear}-01-01`

  const fxTraces: PlotTrace[] = selectedFx.map((c, i) => {
    const rows = fx.filter(r => r.Country === c && r.Date >= startDate).sort((a,b) => a.Date.localeCompare(b.Date))
    return { type:'scatter', mode:'lines', name:c, x:rows.map(r=>r.Date), y:rows.map(r=>r.LocalPerUSD), line:{color:PALETTE[i%PALETTE.length],width:1.5} }
  })

  const reerTraces: PlotTrace[] = selectedReer.map((c, i) => {
    const rows = reer.filter(r => r.Currency === c && r.Date >= startDate).sort((a,b) => a.Date.localeCompare(b.Date))
    return { type:'scatter', mode:'lines', name:c, x:rows.map(r=>r.Date), y:rows.map(r=>r.EER), line:{color:PALETTE[i%PALETTE.length],width:1.5} }
  })

  // Latest values
  const latestFx = FX_COUNTRIES.map(c => {
    const rows = fx.filter(r => r.Country === c).sort((a,b) => b.Date.localeCompare(a.Date))
    return { country: c, val: rows[0]?.LocalPerUSD, date: rows[0]?.Date }
  })

  return (
    <div className="bond-layout">
      <aside className="bond-sidebar">
        <div className="ctrl-section">
          <div className="ctrl-label">VIEW</div>
          <div className="pill-group">
            {(['spot','reer'] as const).map(t => (
              <button key={t} className={`pill ${tab===t?'active':''}`} onClick={() => setTab(t)}>
                {t === 'spot' ? 'Spot vs USD' : 'REER'}
              </button>
            ))}
          </div>
        </div>
        <div className="ctrl-section">
          <div className="ctrl-label">START YEAR</div>
          <input type="number" className="ctrl-input" value={startYear} min={2000} max={2024} onChange={e => setStartYear(+e.target.value)} />
        </div>

        {tab === 'spot' ? (
          <div className="ctrl-section">
            <div className="ctrl-label">CURRENCIES</div>
            {FX_COUNTRIES.map((c, i) => (
              <label key={c} style={{ display:'flex', alignItems:'center', gap:8, padding:'3px 0', cursor:'pointer', fontSize:12, color: selectedFx.includes(c) ? PALETTE[i%PALETTE.length] : '#666' }}>
                <input type="checkbox" checked={selectedFx.includes(c)} onChange={e => setSelectedFx(s => e.target.checked ? [...s,c] : s.filter(x=>x!==c))} style={{ accentColor: PALETTE[i%PALETTE.length] }} />
                {c}
              </label>
            ))}
          </div>
        ) : (
          <div className="ctrl-section">
            <div className="ctrl-label">CURRENCIES</div>
            {REER_CURRENCIES.map((c, i) => (
              <label key={c} style={{ display:'flex', alignItems:'center', gap:8, padding:'3px 0', cursor:'pointer', fontSize:12, color: selectedReer.includes(c) ? PALETTE[i%PALETTE.length] : '#666' }}>
                <input type="checkbox" checked={selectedReer.includes(c)} onChange={e => setSelectedReer(s => e.target.checked ? [...s,c] : s.filter(x=>x!==c))} style={{ accentColor: PALETTE[i%PALETTE.length] }} />
                {c}
              </label>
            ))}
          </div>
        )}
      </aside>

      <div className="bond-main">
        {tab === 'spot' ? (
          <>
            <div style={{ borderLeft:'3px solid #f39200', padding:'10px 14px', background:'rgba(243,146,0,0.04)', borderRadius:'0 6px 6px 0', marginBottom:12 }}>
              <div style={{ color:'#e8e8e8', fontWeight:600, fontSize:13, textTransform:'uppercase', letterSpacing:'0.04em' }}>FX Spot vs USD</div>
              <div style={{ color:'#888', fontSize:11, marginTop:4 }}>FRED · daily · local currency per 1 USD</div>
            </div>
            <Chart traces={fxTraces} layout={{ yaxis: { title:{ text:'Local per USD', font:{color:'#666',size:11} } } }} />

            {/* Latest snapshot table */}
            <div style={{ marginTop:24, overflowX:'auto' }}>
              <table style={{ width:'100%', borderCollapse:'collapse', fontSize:12 }}>
                <thead>
                  <tr style={{ borderBottom:'1px solid #2a2a2a' }}>
                    {['Currency','Rate (vs USD)','Date'].map(h => <th key={h} style={{ padding:'8px 12px', textAlign:'left', color:'#666', fontWeight:500, textTransform:'uppercase', fontSize:10, letterSpacing:'0.05em' }}>{h}</th>)}
                  </tr>
                </thead>
                <tbody>
                  {latestFx.map(({ country, val, date }) => (
                    <tr key={country} style={{ borderBottom:'1px solid #1f1f1f' }}>
                      <td style={{ padding:'8px 12px', color:'#e8e8e8' }}>{country}</td>
                      <td style={{ padding:'8px 12px', color:'#f39200', fontVariantNumeric:'tabular-nums' }}>{val != null ? val.toFixed(4) : '—'}</td>
                      <td style={{ padding:'8px 12px', color:'#555', fontSize:11 }}>{date ?? ''}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </>
        ) : (
          <>
            <div style={{ borderLeft:'3px solid #f39200', padding:'10px 14px', background:'rgba(243,146,0,0.04)', borderRadius:'0 6px 6px 0', marginBottom:12 }}>
              <div style={{ color:'#e8e8e8', fontWeight:600, fontSize:13, textTransform:'uppercase', letterSpacing:'0.04em' }}>Real Effective Exchange Rate (REER)</div>
              <div style={{ color:'#888', fontSize:11, marginTop:4 }}>BIS via DBnomics · index, base = 2020</div>
            </div>
            <Chart traces={reerTraces} layout={{ yaxis: { title:{ text:'REER Index', font:{color:'#666',size:11} } } }} height={400} />
          </>
        )}
      </div>
    </div>
  )
}
