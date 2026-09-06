import { useState, useEffect, useRef } from 'react'
import apiFetch from '../api/client'

type PlotTrace = Record<string, unknown>
type PlotLayout = Record<string, unknown>

function Chart({ traces, layout, height = 380 }: { traces: PlotTrace[]; layout: PlotLayout; height?: number }) {
  const ref = useRef<HTMLDivElement>(null)
  useEffect(() => {
    if (!ref.current || !traces.length) return
    let cancelled = false
    import('plotly.js-dist-min').then(Plotly => {
      if (cancelled || !ref.current) return
      const base: PlotLayout = {
        paper_bgcolor: '#1a1a1a', plot_bgcolor: '#111111',
        font: { color: '#aaa', family: 'system-ui,sans-serif', size: 11 },
        margin: { t: 36, r: 16, b: 60, l: 62 },
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

interface CapRow {
  ISO3: string; Country: string; Region: string; Year: number
  Equity_USD: number | null; GDP_USD: number | null; Debt_GDP_Pct: number | null
  GovtBond_USD: number | null; Total_Cap_USD: number | null
  Equity_GDP_Pct: number | null; GovtBond_GDP_Pct: number | null
  Bond_Equity_Ratio: number | null; Listed_Cos: number | null
  Population: number | null; Turnover_Ratio: number | null
}

const COUNTRIES = ['United States','China','Japan','United Kingdom','Germany','France','India','Canada','Australia','Brazil']
const PALETTE   = ['#60a5fa','#f87171','#34d399','#22d3ee','#f39200','#a78bfa','#f472b6','#818cf8','#fb923c','#a3e635']

export default function CapitalMarketsPage() {
  const [data, setData] = useState<CapRow[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [tab, setTab] = useState<'equity'|'bond'|'ratio'>('equity')
  const [selectedYear, setSelectedYear] = useState(2023)

  useEffect(() => {
    apiFetch<CapRow[]>('/api/capital-markets')
      .then(d => {
        setData(d)
        const yrs = d.map(r => r.Year).filter(Boolean)
        if (yrs.length) setSelectedYear(Math.max(...yrs))
        setLoading(false)
      })
      .catch(err => { setError(err.message); setLoading(false) })
  }, [])

  if (loading) return <div className="content-wrap"><div style={{ color:'#aaa', textAlign:'center', padding: 80 }}><div style={{ width:32, height:32, border:'3px solid #f39200', borderTopColor:'transparent', borderRadius:'50%', animation:'spin 0.8s linear infinite', margin:'0 auto 16px' }}/> Loading capital markets data…</div></div>
  if (error)   return <div className="content-wrap"><div style={{ color:'#ff4d4d', padding: 40 }}>Error: {error}<br/><small style={{color:'#888'}}>Is the FastAPI backend running?</small></div></div>

  const years = Array.from(new Set(data.map(r => r.Year))).sort()

  const atYear = data.filter(r => r.Year === selectedYear)

  // Equity market cap (USD tn) bar
  const equityBar: PlotTrace = {
    type:'bar', name:'Equity Market Cap',
    x: COUNTRIES,
    y: COUNTRIES.map(c => { const r = atYear.find(d=>d.Country===c); return r?.Equity_USD != null ? +(r.Equity_USD).toFixed(3) : null }),
    marker: { color: PALETTE },
  }

  // Govt bond market bar
  const bondBar: PlotTrace = {
    type:'bar', name:'Govt Bond Market',
    x: COUNTRIES,
    y: COUNTRIES.map(c => { const r = atYear.find(d=>d.Country===c); return r?.GovtBond_USD != null ? +(r.GovtBond_USD).toFixed(3) : null }),
    marker: { color: PALETTE },
  }

  // Equity/GDP % bar
  const equityGdpBar: PlotTrace = {
    type:'bar', name:'Equity / GDP %',
    x: COUNTRIES,
    y: COUNTRIES.map(c => { const r = atYear.find(d=>d.Country===c); return r?.Equity_GDP_Pct != null ? +r.Equity_GDP_Pct.toFixed(1) : null }),
    marker: { color: COUNTRIES.map((c,i) => PALETTE[i]) },
  }

  // Historical equity time series
  const equityTraces: PlotTrace[] = COUNTRIES.map((c, i) => {
    const rows = data.filter(r => r.Country === c).sort((a,b) => a.Year - b.Year)
    return { type:'scatter', mode:'lines+markers', name:c, x:rows.map(r=>r.Year), y:rows.map(r=>r.Equity_USD), line:{color:PALETTE[i],width:1.5}, marker:{color:PALETTE[i],size:4} }
  })

  // Stacked equity + bond bars at year
  const stackedBars: PlotTrace[] = [
    { type:'bar', name:'Equity', x:COUNTRIES, y:COUNTRIES.map(c=>{const r=atYear.find(d=>d.Country===c);return r?.Equity_USD??null}), marker:{color:COUNTRIES.map((_,i)=>PALETTE[i])}, opacity:0.9 },
    { type:'bar', name:'Govt Bonds', x:COUNTRIES, y:COUNTRIES.map(c=>{const r=atYear.find(d=>d.Country===c);return r?.GovtBond_USD??null}), marker:{color:'rgba(255,255,255,0.15)'}, base:COUNTRIES.map(c=>{const r=atYear.find(d=>d.Country===c);return r?.Equity_USD??0}) },
  ]

  const tabDefs = [
    { key:'equity', label:'Equity Markets' },
    { key:'bond',   label:'Bond Markets' },
    { key:'ratio',  label:'Historical' },
  ] as const

  return (
    <div className="bond-layout">
      <aside className="bond-sidebar">
        <div className="ctrl-section">
          <div className="ctrl-label">VIEW</div>
          <div className="pill-group" style={{ flexWrap:'wrap' }}>
            {tabDefs.map(t => (
              <button key={t.key} className={`pill ${tab===t.key?'active':''}`} style={{ marginBottom:4 }} onClick={() => setTab(t.key)}>{t.label}</button>
            ))}
          </div>
        </div>
        <div className="ctrl-section">
          <div className="ctrl-label">SNAPSHOT YEAR</div>
          <select className="ctrl-select" value={selectedYear} onChange={e => setSelectedYear(+e.target.value)}>
            {years.reverse().map(y => <option key={y} value={y}>{y}</option>)}
          </select>
        </div>

        {/* KPIs */}
        <div className="ctrl-section">
          <div className="ctrl-label">TOTAL — {selectedYear}</div>
          {[
            { label:'Equity (USD tn)', val: atYear.reduce((s,r)=>s+(r.Equity_USD??0),0).toFixed(1) },
            { label:'Govt Bonds (USD tn)', val: atYear.reduce((s,r)=>s+(r.GovtBond_USD??0),0).toFixed(1) },
          ].map(({ label, val }) => (
            <div key={label} style={{ padding:'6px 0', borderBottom:'1px solid #1a1a1a' }}>
              <div style={{ color:'#888', fontSize:10, textTransform:'uppercase', letterSpacing:'0.06em' }}>{label}</div>
              <div style={{ color:'#f39200', fontSize:18, fontWeight:700, fontVariantNumeric:'tabular-nums', marginTop:2 }}>${val}tn</div>
            </div>
          ))}
        </div>
      </aside>

      <div className="bond-main">
        {tab === 'equity' && (
          <>
            <div style={{ borderLeft:'3px solid #f39200', padding:'10px 14px', background:'rgba(243,146,0,0.04)', borderRadius:'0 6px 6px 0', marginBottom:12 }}>
              <div style={{ color:'#e8e8e8', fontWeight:600, fontSize:13, textTransform:'uppercase', letterSpacing:'0.04em' }}>Equity Market Capitalisation — {selectedYear}</div>
              <div style={{ color:'#888', fontSize:11, marginTop:4 }}>World Bank · USD trillion</div>
            </div>
            <Chart traces={[equityBar]} layout={{ xaxis:{ tickangle:-30 }, yaxis:{ title:{text:'USD tn',font:{color:'#666',size:11}} } }} />

            <div style={{ borderLeft:'3px solid #f39200', padding:'10px 14px', background:'rgba(243,146,0,0.04)', borderRadius:'0 6px 6px 0', margin:'28px 0 12px' }}>
              <div style={{ color:'#e8e8e8', fontWeight:600, fontSize:13, textTransform:'uppercase', letterSpacing:'0.04em' }}>Equity Market Cap / GDP — {selectedYear}</div>
            </div>
            <Chart traces={[equityGdpBar]} layout={{ xaxis:{ tickangle:-30 }, yaxis:{ ticksuffix:'%', title:{text:'Equity / GDP %',font:{color:'#666',size:11}} } }} />
          </>
        )}

        {tab === 'bond' && (
          <>
            <div style={{ borderLeft:'3px solid #60a5fa', padding:'10px 14px', background:'rgba(96,165,250,0.04)', borderRadius:'0 6px 6px 0', marginBottom:12 }}>
              <div style={{ color:'#e8e8e8', fontWeight:600, fontSize:13, textTransform:'uppercase', letterSpacing:'0.04em' }}>Equity + Govt Bond Markets — {selectedYear}</div>
              <div style={{ color:'#888', fontSize:11, marginTop:4 }}>World Bank / IMF · stacked USD trillion</div>
            </div>
            <Chart traces={stackedBars} layout={{ barmode:'stack', xaxis:{ tickangle:-30 }, yaxis:{ title:{text:'USD tn',font:{color:'#666',size:11}} } }} />

            <div style={{ borderLeft:'3px solid #60a5fa', padding:'10px 14px', background:'rgba(96,165,250,0.04)', borderRadius:'0 6px 6px 0', margin:'28px 0 12px' }}>
              <div style={{ color:'#e8e8e8', fontWeight:600, fontSize:13, textTransform:'uppercase', letterSpacing:'0.04em' }}>Govt Bond Market Size — {selectedYear}</div>
            </div>
            <Chart traces={[bondBar]} layout={{ xaxis:{ tickangle:-30 }, yaxis:{ title:{text:'USD tn',font:{color:'#666',size:11}} } }} />
          </>
        )}

        {tab === 'ratio' && (
          <>
            <div style={{ borderLeft:'3px solid #34d399', padding:'10px 14px', background:'rgba(52,211,153,0.04)', borderRadius:'0 6px 6px 0', marginBottom:12 }}>
              <div style={{ color:'#e8e8e8', fontWeight:600, fontSize:13, textTransform:'uppercase', letterSpacing:'0.04em' }}>Equity Market Cap — Historical (2005–{Math.max(...years)})</div>
              <div style={{ color:'#888', fontSize:11, marginTop:4 }}>World Bank · USD trillion · 10 countries</div>
            </div>
            <Chart traces={equityTraces} layout={{ yaxis:{ title:{text:'USD tn',font:{color:'#666',size:11}} } }} height={420} />
          </>
        )}

        {/* Snapshot table */}
        <div style={{ marginTop:28, overflowX:'auto' }}>
          <table style={{ width:'100%', borderCollapse:'collapse', fontSize:12 }}>
            <thead>
              <tr style={{ borderBottom:'1px solid #2a2a2a' }}>
                {['Country','Equity (USD tn)','Govt Bond (USD tn)','Equity/GDP %','Debt/GDP %','Listed Cos'].map(h => <th key={h} style={{ padding:'8px 12px', textAlign:'left', color:'#666', fontWeight:500, textTransform:'uppercase', fontSize:10, letterSpacing:'0.05em', whiteSpace:'nowrap' }}>{h}</th>)}
              </tr>
            </thead>
            <tbody>
              {COUNTRIES.map((c, i) => {
                const r = atYear.find(d => d.Country === c)
                return (
                  <tr key={c} style={{ borderBottom:'1px solid #1f1f1f' }}>
                    <td style={{ padding:'8px 12px', color:PALETTE[i], fontWeight:500 }}>{c}</td>
                    <td style={{ padding:'8px 12px', color:'#e8e8e8', fontVariantNumeric:'tabular-nums' }}>{r?.Equity_USD != null ? r.Equity_USD.toFixed(2) : '—'}</td>
                    <td style={{ padding:'8px 12px', color:'#aaa', fontVariantNumeric:'tabular-nums' }}>{r?.GovtBond_USD != null ? r.GovtBond_USD.toFixed(2) : '—'}</td>
                    <td style={{ padding:'8px 12px', color:'#f39200', fontVariantNumeric:'tabular-nums' }}>{r?.Equity_GDP_Pct != null ? r.Equity_GDP_Pct.toFixed(1)+'%' : '—'}</td>
                    <td style={{ padding:'8px 12px', color:'#888', fontVariantNumeric:'tabular-nums' }}>{r?.Debt_GDP_Pct != null ? r.Debt_GDP_Pct.toFixed(1)+'%' : '—'}</td>
                    <td style={{ padding:'8px 12px', color:'#888', fontVariantNumeric:'tabular-nums' }}>{r?.Listed_Cos != null ? r.Listed_Cos.toLocaleString() : '—'}</td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
