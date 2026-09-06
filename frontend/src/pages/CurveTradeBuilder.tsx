import { useState, useEffect, useRef, useCallback } from 'react'
import { evalFormula } from '../api/bond'

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

interface SeriesPoint { date: string; value: number }

type TradeType = 'spread' | 'butterfly'

const TENORS: Record<string, string> = {
  'US 2Y':  'US2Y',   'US 5Y':  'US5Y',   'US 10Y': 'US10Y',  'US 30Y': 'US30Y',
  'DE 2Y':  'FGBSY',  'DE 5Y':  'FGBMY',  'DE 10Y': 'FGBLY',  'DE 30Y': 'FGBXY',
  'UK 10Y': 'UK10Y',  'AUS 10Y':'AUS10Y',  'CAD 10Y':'CAD10Y',
}

export default function CurveTradeBuilder() {
  const [tradeType, setTradeType] = useState<TradeType>('spread')

  // Spread legs
  const [longLeg,  setLongLeg]  = useState('US 10Y')
  const [shortLeg, setShortLeg] = useState('US 2Y')

  // Butterfly legs
  const [frontLeg, setFrontLeg] = useState('US 2Y')
  const [bellyLeg, setBellyLeg] = useState('US 10Y')
  const [backLeg,  setBackLeg]  = useState('US 30Y')

  // Common
  const [startYear, setStartYear] = useState(2015)
  const [notional, setNotional]   = useState(10_000_000)
  const [loading, setLoading]     = useState(false)
  const [error,   setError]       = useState('')
  const [spread,  setSpread]      = useState<SeriesPoint[]>([])
  const [formula, setFormula]     = useState('')

  const buildFormula = useCallback(() => {
    const tl = TENORS[longLeg]; const ts = TENORS[shortLeg]
    const tf = TENORS[frontLeg]; const tb = TENORS[bellyLeg]; const tbk = TENORS[backLeg]
    if (tradeType === 'spread') return `${tl} - ${ts}`
    // 2*belly - front - back (equal-weighted butterfly)
    return `2 * ${tb} - ${tf} - ${tbk}`
  }, [tradeType, longLeg, shortLeg, frontLeg, bellyLeg, backLeg])

  async function compute() {
    const f = buildFormula()
    setFormula(f)
    setLoading(true); setError('')
    try {
      const data = await evalFormula(f, `${startYear}-01-01`)
      setSpread(data)
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Error')
    }
    setLoading(false)
  }

  // Stats
  const vals = spread.map(p=>p.value).filter(v=>isFinite(v))
  const latest = vals[vals.length-1]
  const mean   = vals.length ? vals.reduce((a,b)=>a+b,0)/vals.length : NaN
  const peak   = vals.length ? Math.max(...vals) : NaN
  const trough = vals.length ? Math.min(...vals) : NaN
  const pct5   = vals.length ? [...vals].sort((a,b)=>a-b)[Math.floor(vals.length*0.05)] : NaN
  const pct95  = vals.length ? [...vals].sort((a,b)=>a-b)[Math.floor(vals.length*0.95)] : NaN

  // P&L for steepener (long long, short short): +1bp spread = +DV01 × notional
  // Rough DV01 per $1mm: ~$90 for 10Y, ~$20 for 2Y, simplify to 1bp = notional/1e6 * 90 approx
  const dv01PerMm = tradeType === 'spread' ? 70 : 90 // rough bps
  const currentChg = spread.length > 1 ? (spread[spread.length-1].value - spread[spread.length-2].value) * 100 : NaN
  const dailyPnl   = isNaN(currentChg) ? NaN : currentChg * (notional / 1_000_000) * dv01PerMm

  const spreadTrace: PlotTrace = {
    type:'scatter', mode:'lines', name: formula,
    x: spread.map(p=>p.date), y: spread.map(p=>p.value),
    line:{color:'#f39200',width:1.5},
    fill:'tozeroy', fillcolor:'rgba(243,146,0,0.06)',
  }

  // Historical z-score
  const zVals = vals.length && mean && !isNaN(pct5) ? vals.map(v => {
    const std = Math.sqrt(vals.reduce((a,b)=>a+(b-mean)**2,0)/vals.length)
    return std > 0 ? (v - mean) / std : 0
  }) : []
  const zTrace: PlotTrace = {
    type:'scatter', mode:'lines', name:'Z-score',
    x: spread.map(p=>p.date), y: zVals,
    line:{color:'#60a5fa',width:1.5},
    fill:'tozeroy', fillcolor:'rgba(96,165,250,0.06)',
  }

  const tenorOptions = Object.keys(TENORS)

  return (
    <div className="bond-layout">
      <aside className="bond-sidebar">
        <div className="ctrl-section">
          <div className="ctrl-label">TRADE TYPE</div>
          <div className="pill-group">
            {(['spread','butterfly'] as const).map(t => (
              <button key={t} className={`pill ${tradeType===t?'active':''}`} onClick={() => setTradeType(t)}>
                {t === 'spread' ? '2-Leg Spread' : '3-Leg Butterfly'}
              </button>
            ))}
          </div>
        </div>

        {tradeType === 'spread' ? (
          <>
            <div className="ctrl-section">
              <div className="ctrl-label">LONG LEG</div>
              <select className="ctrl-select" value={longLeg} onChange={e=>setLongLeg(e.target.value)}>
                {tenorOptions.map(t=><option key={t} value={t}>{t}</option>)}
              </select>
            </div>
            <div className="ctrl-section">
              <div className="ctrl-label">SHORT LEG</div>
              <select className="ctrl-select" value={shortLeg} onChange={e=>setShortLeg(e.target.value)}>
                {tenorOptions.map(t=><option key={t} value={t}>{t}</option>)}
              </select>
            </div>
          </>
        ) : (
          <>
            <div className="ctrl-section">
              <div className="ctrl-label">FRONT (SHORT)</div>
              <select className="ctrl-select" value={frontLeg} onChange={e=>setFrontLeg(e.target.value)}>
                {tenorOptions.map(t=><option key={t} value={t}>{t}</option>)}
              </select>
            </div>
            <div className="ctrl-section">
              <div className="ctrl-label">BELLY (LONG × 2)</div>
              <select className="ctrl-select" value={bellyLeg} onChange={e=>setBellyLeg(e.target.value)}>
                {tenorOptions.map(t=><option key={t} value={t}>{t}</option>)}
              </select>
            </div>
            <div className="ctrl-section">
              <div className="ctrl-label">BACK (SHORT)</div>
              <select className="ctrl-select" value={backLeg} onChange={e=>setBackLeg(e.target.value)}>
                {tenorOptions.map(t=><option key={t} value={t}>{t}</option>)}
              </select>
            </div>
          </>
        )}

        <div className="ctrl-section">
          <div className="ctrl-label">START YEAR</div>
          <input type="number" className="ctrl-input" value={startYear} min={1994} max={2025} onChange={e=>setStartYear(+e.target.value)} />
        </div>

        <div className="ctrl-section">
          <div className="ctrl-label">NOTIONAL (USD)</div>
          <input type="number" className="ctrl-input" value={notional} step={1000000} onChange={e=>setNotional(+e.target.value)} />
          <div style={{ color:'#555', fontSize:10, marginTop:4 }}>${(notional/1e6).toFixed(0)}mm</div>
        </div>

        <button className="primary-button" style={{ width:'100%', marginTop:8 }} onClick={compute} disabled={loading}>
          {loading ? 'Loading…' : 'Build Trade'}
        </button>
      </aside>

      <div className="bond-main">
        <div style={{ borderLeft:'3px solid #f39200', padding:'10px 14px', background:'rgba(243,146,0,0.04)', borderRadius:'0 6px 6px 0', marginBottom: 20 }}>
          <div style={{ color:'#e8e8e8', fontWeight:600, fontSize:13, textTransform:'uppercase', letterSpacing:'0.04em' }}>
            {tradeType === 'spread'
              ? `${longLeg} / ${shortLeg} Spread`
              : `${bellyLeg} Butterfly (${frontLeg} | ${bellyLeg} | ${backLeg})`}
          </div>
          {formula && <div style={{ color:'#666', fontSize:11, marginTop:4, fontFamily:'monospace' }}>{formula}</div>}
        </div>

        {error && <div style={{ color:'#ff4d4d', fontSize:12, marginBottom:12 }}>Error: {error}<br/><small style={{color:'#888'}}>Is the FastAPI backend running?</small></div>}

        {!spread.length && !loading && (
          <div style={{ color:'#555', textAlign:'center', padding:'60px 20px', fontSize:13 }}>
            Configure the trade on the left and press <strong style={{ color:'#f39200' }}>Build Trade</strong>
          </div>
        )}

        {loading && <div style={{ color:'#aaa', textAlign:'center', padding:60 }}><div style={{ width:32, height:32, border:'3px solid #f39200', borderTopColor:'transparent', borderRadius:'50%', animation:'spin 0.8s linear infinite', margin:'0 auto 16px' }}/>Loading series…</div>}

        {spread.length > 0 && !loading && (
          <>
            {/* KPI strip */}
            <div className="kpi-strip" style={{ marginBottom:20 }}>
              {[
                { label:'Current Level', val: isFinite(latest) ? latest.toFixed(2)+'%' : '—', color:'#f39200' },
                { label:'Historical Mean', val: isNaN(mean) ? '—' : mean.toFixed(2)+'%', color:'#aaa' },
                { label:'5th Pctile', val: isNaN(pct5) ? '—' : pct5.toFixed(2)+'%', color:'#f87171' },
                { label:'95th Pctile', val: isNaN(pct95) ? '—' : pct95.toFixed(2)+'%', color:'#60a5fa' },
                { label:'Daily Move (bps)', val: isNaN(currentChg) ? '—' : (currentChg>=0?'+':'')+currentChg.toFixed(1), color: isNaN(currentChg)?'#aaa':currentChg>=0?'#00c087':'#ff4d4d' },
                { label:'Est. Daily P&L', val: isNaN(dailyPnl) ? '—' : `$${Math.abs(dailyPnl).toFixed(0)}`, color: isNaN(dailyPnl)?'#aaa':dailyPnl>=0?'#00c087':'#ff4d4d' },
              ].map(({ label, val, color }) => (
                <div key={label} className="kpi-card">
                  <div style={{ color:'#888', fontSize:10, textTransform:'uppercase', letterSpacing:'0.06em', marginBottom:4 }}>{label}</div>
                  <div style={{ color, fontSize:18, fontWeight:700, fontVariantNumeric:'tabular-nums' }}>{val}</div>
                </div>
              ))}
            </div>

            {/* Spread history */}
            <div style={{ borderLeft:'3px solid #f39200', padding:'10px 14px', background:'rgba(243,146,0,0.04)', borderRadius:'0 6px 6px 0', marginBottom:12 }}>
              <div style={{ color:'#e8e8e8', fontWeight:600, fontSize:13, textTransform:'uppercase', letterSpacing:'0.04em' }}>Spread History</div>
              <div style={{ color:'#888', fontSize:11, marginTop:4 }}>Basis points · {spread.length} observations</div>
            </div>
            <Chart traces={[spreadTrace]} layout={{ yaxis:{ ticksuffix:'%', title:{text:'Spread (%)',font:{color:'#666',size:11}} } }} />

            {/* Z-score */}
            <div style={{ borderLeft:'3px solid #60a5fa', padding:'10px 14px', background:'rgba(96,165,250,0.04)', borderRadius:'0 6px 6px 0', margin:'28px 0 12px' }}>
              <div style={{ color:'#e8e8e8', fontWeight:600, fontSize:13, textTransform:'uppercase', letterSpacing:'0.04em' }}>Historical Z-Score</div>
              <div style={{ color:'#888', fontSize:11, marginTop:4 }}>Spread relative to historical mean · 0 = average, ±2 = extreme</div>
            </div>
            <Chart traces={[zTrace,
              { type:'scatter', mode:'lines', name:'+2σ', x:spread.map(p=>p.date), y:spread.map(()=>2), line:{color:'#ff4d4d',width:1,dash:'dot'}, showlegend:false } as PlotTrace,
              { type:'scatter', mode:'lines', name:'-2σ', x:spread.map(p=>p.date), y:spread.map(()=>-2), line:{color:'#00c087',width:1,dash:'dot'}, showlegend:false } as PlotTrace,
            ]} layout={{ yaxis:{ title:{text:'Z-score',font:{color:'#666',size:11}}, zeroline:true, zerolinecolor:'#444' } }} />

            {/* Distribution */}
            <div style={{ borderLeft:'3px solid #a78bfa', padding:'10px 14px', background:'rgba(167,139,250,0.04)', borderRadius:'0 6px 6px 0', margin:'28px 0 12px' }}>
              <div style={{ color:'#e8e8e8', fontWeight:600, fontSize:13, textTransform:'uppercase', letterSpacing:'0.04em' }}>Level Distribution</div>
            </div>
            <Chart traces={[{
              type:'histogram', name:'Distribution',
              x: vals, nbinsx:40,
              marker:{color:'#f39200',opacity:0.7},
            } as PlotTrace,
            isFinite(latest) ? {
              type:'scatter', mode:'lines', name:'Current',
              x:[latest,latest], y:[0,vals.length/5],
              line:{color:'#ff4d4d',width:2,dash:'dash'},
            } as PlotTrace : {} as PlotTrace,
            ].filter(t=>Object.keys(t).length>0)}
            layout={{ barmode:'overlay', xaxis:{ticksuffix:'%'}, yaxis:{title:{text:'Count',font:{color:'#666',size:11}}} }} height={260} />
          </>
        )}
      </div>
    </div>
  )
}
