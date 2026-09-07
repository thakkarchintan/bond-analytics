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

interface CbRateRow { Country: string; Date: string; Rate_Pct: number }
interface CbBalRow  { Date: string; CB: string; Assets_USD_bn: number }
interface MmktRow   { Date: string; Series: string; Rate_Pct: number }

const CB_COLORS: Record<string,string> = {
  'Euro Area': '#a78bfa', 'United States': '#60a5fa',
  'Federal Reserve': '#60a5fa', 'ECB': '#a78bfa',
  'Bank of Japan': '#34d399', 'Bank of England': '#22d3ee',
  'PBoC': '#f87171', 'Bank of Canada': '#818cf8',
  'RBA': '#fb923c', 'SNB': '#e879f9',
}

const MMKT_COLORS: Record<string,string> = {
  'Fed Funds (Eff.)': '#60a5fa',
  'SOFR': '#34d399',
}

const ALL_CBS = ['Federal Reserve','ECB','Bank of Japan','Bank of England','PBoC','Bank of Canada','RBA','SNB']

export default function CentralBankRates() {
  const [rates, setRates] = useState<CbRateRow[]>([])
  const [balance, setBalance] = useState<CbBalRow[]>([])
  const [mmkt, setMmkt] = useState<MmktRow[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [startYear, setStartYear] = useState(2000)
  const [selectedCBs, setSelectedCBs] = useState<string[]>(ALL_CBS)

  useEffect(() => {
    Promise.all([
      apiFetch<CbRateRow[]>('/api/macro/cb-rates'),
      apiFetch<CbBalRow[]>('/api/macro/cb-balance'),
      apiFetch<MmktRow[]>('/api/macro/mmkt'),
    ]).then(([r, b, m]) => {
      setRates(r)
      setBalance(b)
      setMmkt(m)
      setLoading(false)
    }).catch(err => { setError(err.message); setLoading(false) })
  }, [])

  if (loading) return <div className="content-wrap"><div style={{ color:'#aaa', textAlign:'center', padding: 80 }}><div style={{ width:32, height:32, border:'3px solid #f39200', borderTopColor:'transparent', borderRadius:'50%', animation:'spin 0.8s linear infinite', margin:'0 auto 16px' }}/> Loading central bank data…</div></div>
  if (error)   return <div className="content-wrap"><div style={{ color:'#ff4d4d', padding: 40 }}>Error: {error}<br/><small style={{color:'#888'}}>Is the FastAPI backend running?</small></div></div>

  const startDate = `${startYear}-01-01`
  const rateCountries = Array.from(new Set(rates.map(r => r.Country)))

  // Policy rate traces
  const rateTraces: PlotTrace[] = rateCountries.map(c => {
    const rows = rates.filter(r => r.Country === c && r.Date >= startDate).sort((a,b) => a.Date.localeCompare(b.Date))
    return { type:'scatter', mode:'lines', name:c, x:rows.map(r=>r.Date), y:rows.map(r=>r.Rate_Pct), line:{color:CB_COLORS[c]??'#888',width:2} }
  })

  // Balance sheet traces
  const balTraces: PlotTrace[] = selectedCBs.filter(cb => balance.some(r => r.CB === cb)).map(cb => {
    const rows = balance.filter(r => r.CB === cb && r.Date >= startDate).sort((a,b) => a.Date.localeCompare(b.Date))
    return { type:'scatter', mode:'lines', name:cb, x:rows.map(r=>r.Date), y:rows.map(r=>r.Assets_USD_bn), line:{color:CB_COLORS[cb]??'#888',width:1.5} }
  })

  // Money market traces
  const mmktSeries = Array.from(new Set(mmkt.map(r => r.Series)))
  const mmktTraces: PlotTrace[] = mmktSeries.map(s => {
    const rows = mmkt.filter(r => r.Series === s && r.Date >= startDate).sort((a,b) => a.Date.localeCompare(b.Date))
    return { type:'scatter', mode:'lines', name:s, x:rows.map(r=>r.Date), y:rows.map(r=>r.Rate_Pct), line:{color:MMKT_COLORS[s]??'#888',width:1.5} }
  })

  // Latest snapshot with 1yr change
  const latestRates = rateCountries.map(c => {
    const rows = rates.filter(r => r.Country === c).sort((a,b) => b.Date.localeCompare(a.Date))
    const latest = rows[0]
    if (!latest) return { cb: c, rate: undefined as number|undefined, date: undefined as string|undefined, change1y: null as number|null }
    // Find rate ~365 days ago
    const latestTs = new Date(latest.Date).getTime()
    const targetTs = latestTs - 365 * 86400000
    const yearAgoRow = rows.reduce((best, r) => {
      const d = Math.abs(new Date(r.Date).getTime() - targetTs)
      return d < Math.abs(new Date(best.Date).getTime() - targetTs) ? r : best
    }, rows[rows.length - 1])
    const change1y = yearAgoRow && Math.abs(new Date(yearAgoRow.Date).getTime() - targetTs) < 200 * 86400000
      ? latest.Rate_Pct - yearAgoRow.Rate_Pct
      : null
    return { cb: c, rate: latest.Rate_Pct, date: latest.Date, change1y }
  })

  const latestBal = ALL_CBS.map(cb => {
    const rows = balance.filter(r => r.CB === cb).sort((a,b) => b.Date.localeCompare(a.Date))
    return { cb, assets: rows[0]?.Assets_USD_bn, date: rows[0]?.Date }
  }).filter(r => r.assets != null)

  // Latest money market values
  const latestMmkt = mmktSeries.map(s => {
    const rows = mmkt.filter(r => r.Series === s).sort((a,b) => b.Date.localeCompare(a.Date))
    return { s, rate: rows[0]?.Rate_Pct, date: rows[0]?.Date }
  })

  return (
    <div className="bond-layout">
      {/* ── Sidebar ── */}
      <aside className="bond-sidebar">
        <div className="ctrl-section">
          <div className="ctrl-label">START YEAR</div>
          <input type="number" className="ctrl-input" value={startYear} min={1990} max={2024}
            onChange={e => setStartYear(+e.target.value)} />
        </div>
        <div className="ctrl-section">
          <div className="ctrl-label">BALANCE SHEET CBs</div>
          {ALL_CBS.map(cb => (
            <label key={cb} style={{ display:'flex', alignItems:'center', gap:8, padding:'3px 0', cursor:'pointer', fontSize:12, color: selectedCBs.includes(cb) ? CB_COLORS[cb]??'#e8e8e8' : '#666' }}>
              <input type="checkbox" checked={selectedCBs.includes(cb)} onChange={e => setSelectedCBs(s => e.target.checked ? [...s,cb] : s.filter(x=>x!==cb))} style={{ accentColor: CB_COLORS[cb] }} />
              {cb}
            </label>
          ))}
        </div>
      </aside>

      {/* ── Main ── */}
      <div className="bond-main">
        {/* KPI strip with 1yr change */}
        <div className="kpi-strip" style={{ marginBottom:20 }}>
          {latestRates.map(({ cb, rate, date, change1y }) => (
            <div key={cb} className="kpi-card">
              <div style={{ color:'#888', fontSize:10, textTransform:'uppercase', letterSpacing:'0.06em', marginBottom:4 }}>{cb}</div>
              <div style={{ color: rate != null && rate <= 0.5 ? '#00c087' : rate != null && rate >= 4 ? '#ff4d4d' : '#f39200', fontSize:22, fontWeight:700, fontVariantNumeric:'tabular-nums' }}>
                {rate != null ? rate.toFixed(2) + '%' : '—'}
              </div>
              {change1y != null && (
                <div style={{ color: change1y > 0 ? '#ff4d4d' : change1y < 0 ? '#00c087' : '#555', fontSize:11, fontVariantNumeric:'tabular-nums', marginTop:2 }}>
                  {change1y > 0 ? '▲' : change1y < 0 ? '▼' : ''}
                  {' '}{Math.abs(change1y).toFixed(2)}% 1yr
                </div>
              )}
              <div style={{ color:'#555', fontSize:10, marginTop:2 }}>{date ?? ''}</div>
            </div>
          ))}
        </div>

        {/* Policy rates chart */}
        <div style={{ borderLeft:'3px solid #f39200', padding:'10px 14px', background:'rgba(243,146,0,0.04)', borderRadius:'0 6px 6px 0', marginBottom:12 }}>
          <div style={{ color:'#e8e8e8', fontWeight:600, fontSize:13, textTransform:'uppercase', letterSpacing:'0.04em' }}>Central Bank Policy Rates</div>
          <div style={{ color:'#888', fontSize:11, marginTop:4 }}>BIS · monthly · {rateCountries.join(', ')}</div>
        </div>
        <Chart traces={rateTraces} layout={{ yaxis: { ticksuffix:'%', title:{ text:'Rate (%)', font:{color:'#666',size:11} } } }} />

        {/* Money Market Rates */}
        {mmktTraces.length > 0 && (
          <>
            <div style={{ borderLeft:'3px solid #34d399', padding:'10px 14px', background:'rgba(52,211,153,0.04)', borderRadius:'0 6px 6px 0', margin:'28px 0 12px' }}>
              <div style={{ color:'#e8e8e8', fontWeight:600, fontSize:13, textTransform:'uppercase', letterSpacing:'0.04em' }}>Money Market Rates</div>
              <div style={{ color:'#888', fontSize:11, marginTop:4 }}>FRED · daily · Fed Funds (Eff.) &amp; SOFR</div>
            </div>
            {/* MMKT KPIs */}
            <div style={{ display:'flex', gap:12, marginBottom:12, flexWrap:'wrap' }}>
              {latestMmkt.map(({ s, rate, date }) => (
                <div key={s} style={{ background:'#1a1a1a', border:'1px solid #2a2a2a', borderRadius:8, padding:'10px 16px', minWidth:160 }}>
                  <div style={{ color:'#666', fontSize:10, textTransform:'uppercase', letterSpacing:'0.05em', marginBottom:4 }}>{s}</div>
                  <div style={{ color: MMKT_COLORS[s] ?? '#f39200', fontSize:22, fontWeight:700, fontVariantNumeric:'tabular-nums' }}>
                    {rate != null ? rate.toFixed(2) + '%' : '—'}
                  </div>
                  <div style={{ color:'#555', fontSize:10, marginTop:2 }}>{date ?? ''}</div>
                </div>
              ))}
            </div>
            <Chart traces={mmktTraces} layout={{ yaxis: { ticksuffix:'%', title:{ text:'Rate (%)', font:{color:'#666',size:11} } } }} />
          </>
        )}

        {/* Balance sheets */}
        <div style={{ borderLeft:'3px solid #f39200', padding:'10px 14px', background:'rgba(243,146,0,0.04)', borderRadius:'0 6px 6px 0', margin:'28px 0 12px' }}>
          <div style={{ color:'#e8e8e8', fontWeight:600, fontSize:13, textTransform:'uppercase', letterSpacing:'0.04em' }}>Central Bank Balance Sheets</div>
          <div style={{ color:'#888', fontSize:11, marginTop:4 }}>DBnomics · total assets (USD bn)</div>
        </div>
        <Chart traces={balTraces} layout={{ yaxis: { title:{ text:'Assets (USD bn)', font:{color:'#666',size:11} } } }} />

        {/* Latest balance sheet snapshot */}
        <div style={{ marginTop:28, overflowX:'auto' }}>
          <table style={{ width:'100%', borderCollapse:'collapse', fontSize:12 }}>
            <thead>
              <tr style={{ borderBottom:'1px solid #2a2a2a' }}>
                {['Central Bank','Total Assets (USD bn)','As of'].map(h => (
                  <th key={h} style={{ padding:'8px 12px', textAlign:'left', color:'#666', fontWeight:500, textTransform:'uppercase', fontSize:10, letterSpacing:'0.05em' }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {latestBal.sort((a,b) => (b.assets??0)-(a.assets??0)).map(({ cb, assets, date }) => (
                <tr key={cb} style={{ borderBottom:'1px solid #1f1f1f' }}>
                  <td style={{ padding:'8px 12px', color: CB_COLORS[cb]??'#e8e8e8', fontWeight:500 }}>{cb}</td>
                  <td style={{ padding:'8px 12px', color:'#e8e8e8', fontVariantNumeric:'tabular-nums' }}>{assets != null ? assets.toLocaleString('en-US', { maximumFractionDigits:0 }) : '—'}</td>
                  <td style={{ padding:'8px 12px', color:'#555', fontSize:11 }}>{date ?? ''}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
