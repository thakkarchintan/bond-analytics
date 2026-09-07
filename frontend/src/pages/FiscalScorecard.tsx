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

interface FiscalRow {
  Country: string; Year: number
  DebtGDP_Pct: number | null
  FiscalBal_Pct: number | null
  PrimaryBal_Pct: number | null
  CurrentAcct_Pct: number | null
  GDP_USD_Bn: number | null
}

const COUNTRIES = ['United States','Euro Area','United Kingdom','Japan','China','India','Canada','Brazil','Australia','South Korea','Switzerland','Sweden','Mexico','South Africa','Norway','New Zealand']
const PALETTE   = ['#60a5fa','#a78bfa','#22d3ee','#34d399','#f87171','#f472b6','#818cf8','#a3e635','#fb923c','#fbbf24','#e879f9','#2dd4bf','#c084fc','#f9a8d4','#67e8f9','#86efac']

function colorDebt(v: number | null) {
  if (v == null) return '#555'
  if (v > 130) return '#ff4d4d'
  if (v > 90)  return '#f39200'
  if (v > 60)  return '#fbbf24'
  return '#00c087'
}

function colorFiscal(v: number | null) {
  if (v == null) return '#555'
  return v >= 0 ? '#00c087' : v > -3 ? '#fbbf24' : '#ff4d4d'
}

export default function FiscalScorecard() {
  const [data, setData] = useState<FiscalRow[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [selected, setSelected] = useState<string[]>(['United States','Euro Area','United Kingdom','Japan','China','India','Canada','Brazil'])
  const [startYear, setStartYear] = useState(2010)
  const [scoreYear, setScoreYear] = useState(2024)

  useEffect(() => {
    apiFetch<FiscalRow[]>('/api/macro/fiscal')
      .then(d => {
        setData(d)
        const years = d.map(r => r.Year).filter(Boolean)
        if (years.length) setScoreYear(Math.max(...years))
        setLoading(false)
      })
      .catch(err => { setError(err.message); setLoading(false) })
  }, [])

  if (loading) return <div className="content-wrap"><div style={{ color:'#aaa', textAlign:'center', padding: 80 }}><div style={{ width:32, height:32, border:'3px solid #f39200', borderTopColor:'transparent', borderRadius:'50%', animation:'spin 0.8s linear infinite', margin:'0 auto 16px' }}/> Loading fiscal data…</div></div>
  if (error)   return <div className="content-wrap"><div style={{ color:'#ff4d4d', padding: 40 }}>Error: {error}<br/><small style={{color:'#888'}}>Is the FastAPI backend running?</small></div></div>

  const years = Array.from(new Set(data.map(r => r.Year))).sort()

  function makeTraces(field: keyof FiscalRow): PlotTrace[] {
    return selected.map((c, i) => {
      const color = PALETTE[COUNTRIES.indexOf(c) % PALETTE.length]
      const rows = data.filter(r => r.Country === c && r.Year >= startYear).sort((a,b) => a.Year - b.Year)
      return { type:'scatter', mode:'lines+markers', name:c, x:rows.map(r=>r.Year), y:rows.map(r=>r[field] as number|null), line:{color,width:1.5}, marker:{color,size:4} }
    })
  }

  const scoreRows = COUNTRIES.map(c => {
    const row = data.find(r => r.Country === c && r.Year === scoreYear) ?? data.filter(r => r.Country === c).sort((a,b)=>b.Year-a.Year)[0]
    return { c, ...row }
  })

  // Bar chart: debt vs GDP at scoreYear
  const debtBar: PlotTrace = {
    type:'bar', name:`Debt/GDP ${scoreYear}`,
    x: scoreRows.filter(r=>r.DebtGDP_Pct!=null).map(r=>r.c),
    y: scoreRows.filter(r=>r.DebtGDP_Pct!=null).map(r=>r.DebtGDP_Pct!),
    marker: { color: scoreRows.filter(r=>r.DebtGDP_Pct!=null).map(r=>colorDebt(r.DebtGDP_Pct!)) },
  }

  // Debt sustainability scatter: x = FiscalBal, y = DebtGDP, size = GDP_USD_Bn
  const sustainScatter: PlotTrace[] = selected.map((c, i) => {
    const row = data.find(r => r.Country === c && r.Year === scoreYear)
    if (!row || row.FiscalBal_Pct == null || row.DebtGDP_Pct == null) return null
    const color = PALETTE[COUNTRIES.indexOf(c) % PALETTE.length]
    const sz = row.GDP_USD_Bn ? Math.max(10, Math.min(50, row.GDP_USD_Bn / 500)) : 14
    return {
      type:'scatter', mode:'markers+text', name:c,
      x:[row.FiscalBal_Pct], y:[row.DebtGDP_Pct],
      text:[c.replace('United States','US').replace('United Kingdom','UK').replace('Euro Area','EA')],
      textposition:'top center', textfont:{ size:10, color:'#aaa' },
      marker:{ color, size: sz, opacity:0.85, line:{color:'#111',width:1} },
      hovertemplate:`<b>${c}</b><br>Fiscal Bal: %{x:.1f}%<br>Debt/GDP: %{y:.1f}%<extra></extra>`,
    }
  }).filter(Boolean) as PlotTrace[]

  return (
    <div className="bond-layout">
      <aside className="bond-sidebar">
        <div className="ctrl-section">
          <div className="ctrl-label">SCORECARD YEAR</div>
          <select className="ctrl-select" value={scoreYear} onChange={e => setScoreYear(+e.target.value)}>
            {years.filter(y=>y>=2015).reverse().map(y => <option key={y} value={y}>{y}</option>)}
          </select>
        </div>
        <div className="ctrl-section">
          <div className="ctrl-label">CHART START YEAR</div>
          <input type="number" className="ctrl-input" value={startYear} min={2000} max={2024} onChange={e => setStartYear(+e.target.value)} />
        </div>
        <div className="ctrl-section">
          <div className="ctrl-label">COUNTRIES</div>
          {COUNTRIES.map((c, i) => (
            <label key={c} style={{ display:'flex', alignItems:'center', gap:8, padding:'3px 0', cursor:'pointer', fontSize:12, color: selected.includes(c) ? PALETTE[i%PALETTE.length] : '#666' }}>
              <input type="checkbox" checked={selected.includes(c)} onChange={e => setSelected(s => e.target.checked ? [...s,c] : s.filter(x=>x!==c))} style={{ accentColor: PALETTE[i%PALETTE.length] }} />
              {c}
            </label>
          ))}
        </div>

        {/* Debt legend */}
        <div className="ctrl-section">
          <div className="ctrl-label">DEBT/GDP SIGNAL</div>
          {[['> 130%','#ff4d4d','Critical'],['> 90%','#f39200','High'],['> 60%','#fbbf24','Elevated'],['≤ 60%','#00c087','Sustainable']].map(([lbl,clr,txt]) => (
            <div key={lbl} style={{ display:'flex', alignItems:'center', gap:6, padding:'3px 0', fontSize:11 }}>
              <div style={{ width:10, height:10, borderRadius:2, background:clr }} />
              <span style={{ color:clr }}>{lbl}</span>
              <span style={{ color:'#555' }}>{txt}</span>
            </div>
          ))}
        </div>
      </aside>

      <div className="bond-main">
        {/* Scorecard table */}
        <div style={{ borderLeft:'3px solid #f39200', padding:'10px 14px', background:'rgba(243,146,0,0.04)', borderRadius:'0 6px 6px 0', marginBottom:16 }}>
          <div style={{ color:'#e8e8e8', fontWeight:600, fontSize:13, textTransform:'uppercase', letterSpacing:'0.04em' }}>Fiscal Scorecard — {scoreYear}</div>
          <div style={{ color:'#888', fontSize:11, marginTop:4 }}>IMF WEO · Debt/GDP, Fiscal Balance, Primary Balance, Current Account</div>
        </div>
        <div style={{ overflowX:'auto', marginBottom:28 }}>
          <table style={{ width:'100%', borderCollapse:'collapse', fontSize:12 }}>
            <thead>
              <tr style={{ borderBottom:'1px solid #2a2a2a' }}>
                {['Country','Debt / GDP','Fiscal Bal.','Primary Bal.','Current Acct.','GDP (USD bn)'].map(h => <th key={h} style={{ padding:'8px 12px', textAlign:'left', color:'#666', fontWeight:500, textTransform:'uppercase', fontSize:10, letterSpacing:'0.05em', whiteSpace:'nowrap' }}>{h}</th>)}
              </tr>
            </thead>
            <tbody>
              {scoreRows.map(({ c, DebtGDP_Pct, FiscalBal_Pct, PrimaryBal_Pct, CurrentAcct_Pct, GDP_USD_Bn }) => (
                <tr key={c} style={{ borderBottom:'1px solid #1f1f1f' }}>
                  <td style={{ padding:'8px 12px', color:'#e8e8e8', fontWeight:500, whiteSpace:'nowrap' }}>{c}</td>
                  <td style={{ padding:'8px 12px', color:colorDebt(DebtGDP_Pct??null), fontVariantNumeric:'tabular-nums', fontWeight:600 }}>{DebtGDP_Pct != null ? DebtGDP_Pct.toFixed(1)+'%' : '—'}</td>
                  <td style={{ padding:'8px 12px', color:colorFiscal(FiscalBal_Pct??null), fontVariantNumeric:'tabular-nums' }}>{FiscalBal_Pct != null ? (FiscalBal_Pct>0?'+':'')+FiscalBal_Pct.toFixed(1)+'%' : '—'}</td>
                  <td style={{ padding:'8px 12px', color:colorFiscal(PrimaryBal_Pct??null), fontVariantNumeric:'tabular-nums' }}>{PrimaryBal_Pct != null ? (PrimaryBal_Pct>0?'+':'')+PrimaryBal_Pct.toFixed(1)+'%' : '—'}</td>
                  <td style={{ padding:'8px 12px', color:'#aaa', fontVariantNumeric:'tabular-nums' }}>{CurrentAcct_Pct != null ? (CurrentAcct_Pct>0?'+':'')+CurrentAcct_Pct.toFixed(1)+'%' : '—'}</td>
                  <td style={{ padding:'8px 12px', color:'#888', fontVariantNumeric:'tabular-nums' }}>{GDP_USD_Bn != null ? GDP_USD_Bn.toLocaleString('en-US',{maximumFractionDigits:0}) : '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Debt Sustainability Scatter */}
        <div style={{ borderLeft:'3px solid #a78bfa', padding:'10px 14px', background:'rgba(167,139,250,0.04)', borderRadius:'0 6px 6px 0', marginBottom:12 }}>
          <div style={{ color:'#e8e8e8', fontWeight:600, fontSize:13, textTransform:'uppercase', letterSpacing:'0.04em' }}>Debt Sustainability — {scoreYear}</div>
          <div style={{ color:'#888', fontSize:11, marginTop:4 }}>Fiscal Balance (x) vs Debt/GDP (y) · bubble size = GDP · top-left = most stressed</div>
        </div>
        <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr', gap:8, marginBottom:10, fontSize:10, color:'#666' }}>
          <div style={{ background:'rgba(255,77,77,0.05)', border:'1px solid #ff4d4d22', borderRadius:6, padding:'5px 10px' }}>↖ High Debt + Deficit = Most Stressed</div>
          <div style={{ background:'rgba(0,192,135,0.05)', border:'1px solid #00c08722', borderRadius:6, padding:'5px 10px' }}>↗ High Debt + Surplus = Deleveraging</div>
          <div style={{ background:'rgba(96,165,250,0.05)', border:'1px solid #60a5fa22', borderRadius:6, padding:'5px 10px' }}>↙ Low Debt + Deficit = Manageable</div>
          <div style={{ background:'rgba(0,192,135,0.05)', border:'1px solid #00c08722', borderRadius:6, padding:'5px 10px' }}>↘ Low Debt + Surplus = Strongest</div>
        </div>
        <Chart
          traces={sustainScatter}
          layout={{
            hovermode:'closest', showlegend:false,
            xaxis:{ title:{text:'Fiscal Balance (% GDP)  ← deficit | surplus →',font:{color:'#666',size:11}}, ticksuffix:'%', zeroline:true, zerolinecolor:'#444' },
            yaxis:{ title:{text:'Debt / GDP (%)',font:{color:'#666',size:11}}, ticksuffix:'%' },
            shapes:[{ type:'line', x0:-20, x1:5, y0:90, y1:90, line:{color:'#ff4d4d44',width:1,dash:'dot'} }],
          }}
          height={380} />

        {/* Debt/GDP bar */}
        <div style={{ borderLeft:'3px solid #f39200', padding:'10px 14px', background:'rgba(243,146,0,0.04)', borderRadius:'0 6px 6px 0', margin:'28px 0 12px' }}>
          <div style={{ color:'#e8e8e8', fontWeight:600, fontSize:13, textTransform:'uppercase', letterSpacing:'0.04em' }}>Debt / GDP Comparison — {scoreYear}</div>
        </div>
        <Chart traces={[debtBar]} layout={{ xaxis:{ tickangle:-30 }, yaxis:{ ticksuffix:'%', title:{text:'Debt/GDP %',font:{color:'#666',size:11}} } }} />

        {/* Debt/GDP over time */}
        <div style={{ borderLeft:'3px solid #f39200', padding:'10px 14px', background:'rgba(243,146,0,0.04)', borderRadius:'0 6px 6px 0', margin:'28px 0 12px' }}>
          <div style={{ color:'#e8e8e8', fontWeight:600, fontSize:13, textTransform:'uppercase', letterSpacing:'0.04em' }}>Debt / GDP History</div>
        </div>
        <Chart traces={makeTraces('DebtGDP_Pct')} layout={{ yaxis:{ ticksuffix:'%', title:{text:'Debt/GDP %',font:{color:'#666',size:11}} } }} />

        {/* Fiscal balance */}
        <div style={{ borderLeft:'3px solid #f87171', padding:'10px 14px', background:'rgba(248,113,113,0.04)', borderRadius:'0 6px 6px 0', margin:'28px 0 12px' }}>
          <div style={{ color:'#e8e8e8', fontWeight:600, fontSize:13, textTransform:'uppercase', letterSpacing:'0.04em' }}>Fiscal Balance (% GDP)</div>
        </div>
        <Chart traces={makeTraces('FiscalBal_Pct')} layout={{ yaxis:{ ticksuffix:'%', title:{text:'Fiscal Bal. %',font:{color:'#666',size:11}}, zerolinecolor:'#555' } }} />

        {/* Primary balance */}
        <div style={{ borderLeft:'3px solid #22d3ee', padding:'10px 14px', background:'rgba(34,211,238,0.04)', borderRadius:'0 6px 6px 0', margin:'28px 0 12px' }}>
          <div style={{ color:'#e8e8e8', fontWeight:600, fontSize:13, textTransform:'uppercase', letterSpacing:'0.04em' }}>Primary Balance (% GDP)</div>
          <div style={{ color:'#888', fontSize:11, marginTop:4 }}>Fiscal balance excluding interest payments · positive = revenue covers non-interest spending</div>
        </div>
        <Chart traces={makeTraces('PrimaryBal_Pct')} layout={{ yaxis:{ ticksuffix:'%', title:{text:'Primary Bal. %',font:{color:'#666',size:11}}, zerolinecolor:'#555' } }} />

        {/* Current account */}
        <div style={{ borderLeft:'3px solid #34d399', padding:'10px 14px', background:'rgba(52,211,153,0.04)', borderRadius:'0 6px 6px 0', margin:'28px 0 12px' }}>
          <div style={{ color:'#e8e8e8', fontWeight:600, fontSize:13, textTransform:'uppercase', letterSpacing:'0.04em' }}>Current Account Balance (% GDP)</div>
          <div style={{ color:'#888', fontSize:11, marginTop:4 }}>Surplus (+) = net exporter · Deficit (−) = net importer</div>
        </div>
        <Chart traces={makeTraces('CurrentAcct_Pct')} layout={{ yaxis:{ ticksuffix:'%', title:{text:'Current Acct. %',font:{color:'#666',size:11}}, zerolinecolor:'#555' } }} />
      </div>
    </div>
  )
}
