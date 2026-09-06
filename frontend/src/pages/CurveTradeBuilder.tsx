<title>Curve Trade Builder</title>
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

/* ── Tenor definitions with approx bond math parameters ── */
interface TenorDef { key: string; matYrs: number; coupon: number; freq: number; col: string }
const TENOR_DEFS: Record<string, TenorDef> = {
  'US 2Y':   { key:'US2Y',   matYrs:2,  coupon:4.625, freq:2, col:'#60a5fa' },
  'US 5Y':   { key:'US5Y',   matYrs:5,  coupon:4.25,  freq:2, col:'#818cf8' },
  'US 10Y':  { key:'US10Y',  matYrs:10, coupon:4.25,  freq:2, col:'#a78bfa' },
  'US 30Y':  { key:'US30Y',  matYrs:30, coupon:4.625, freq:2, col:'#c4b5fd' },
  'DE 2Y':   { key:'FGBSY',  matYrs:2,  coupon:2.5,   freq:1, col:'#34d399' },
  'DE 5Y':   { key:'FGBMY',  matYrs:5,  coupon:2.25,  freq:1, col:'#2dd4bf' },
  'DE 10Y':  { key:'FGBLY',  matYrs:10, coupon:2.6,   freq:1, col:'#22d3ee' },
  'DE 30Y':  { key:'FGBXY',  matYrs:30, coupon:2.7,   freq:1, col:'#67e8f9' },
  'UK 10Y':  { key:'UK10Y',  matYrs:10, coupon:4.25,  freq:2, col:'#fbbf24' },
  'AUS 10Y': { key:'AUS10Y', matYrs:10, coupon:4.25,  freq:2, col:'#fb923c' },
  'CAD 10Y': { key:'CAD10Y', matYrs:10, coupon:3.25,  freq:2, col:'#f87171' },
}

/* ── Bond math for DV01 ── */
function bondPrice(fv: number, coupon: number, freq: number, ytm: number, matYrs: number): number {
  const periods = Math.round(matYrs * freq)
  const c = (coupon / 100 / freq) * fv
  const r = ytm / 100 / freq
  if (Math.abs(r) < 1e-12) return fv + c * periods
  return c * (1 - Math.pow(1 + r, -periods)) / r + fv * Math.pow(1 + r, -periods)
}
function macDur(fv: number, coupon: number, freq: number, ytm: number, matYrs: number): number {
  const periods = Math.round(matYrs * freq)
  const c = (coupon / 100 / freq) * fv
  const r = ytm / 100 / freq
  let num = 0, den = 0
  for (let t = 1; t <= periods; t++) {
    const cf = t < periods ? c : c + fv
    const pv = cf / Math.pow(1 + r, t)
    num += t * pv; den += pv
  }
  return den > 0 ? num / den / freq : 0
}
function calcDV01(tenor: string, ytm: number): number {
  const def = TENOR_DEFS[tenor]
  if (!def) return 0
  const px = bondPrice(100, def.coupon, def.freq, ytm, def.matYrs)
  const md = macDur(100, def.coupon, def.freq, ytm, def.matYrs) / (1 + ytm / 100 / def.freq)
  return md * px / 10000
}

/* ── Curve shape presets ── */
const CURVE_SHAPES: { name: string; desc: string; shape: string }[] = [
  { name:'Normal',   shape:'Normal (upward sloping)', desc:'Short rates below long rates. Typical in mid-cycle. 2Y10Y spread positive — compensates for duration risk and expected growth.' },
  { name:'Flat',     shape:'Flat', desc:'Short and long rates near equal. Often seen mid-cycle or approaching inversion. Low term premium suggests market uncertainty about future growth.' },
  { name:'Inverted', shape:'Inverted (downward sloping)', desc:'Short rates above long rates. Historically the most reliable recession predictor (12–24 months lead). Fed overtightening compresses the long end.' },
  { name:'Humped',   shape:'Humped (peak at the belly)', desc:'Intermediate maturities yield more than either short or long end. Often precedes a bull flattening as the market prices in eventual rate cuts.' },
]

/* ── Scenario profiles with tenor shifts ── */
const SCENARIOS: { name: string; desc: string; shifts: Record<string, number> }[] = [
  { name:'Bear Steepening', desc:'Long-end yields rise more than short end. Common in reflationary environments or when term premium expands.', shifts:{'US 2Y':10,'US 5Y':30,'US 10Y':60,'US 30Y':90,'DE 2Y':10,'DE 5Y':25,'DE 10Y':50,'DE 30Y':75,'UK 10Y':55,'AUS 10Y':55,'CAD 10Y':55} },
  { name:'Bull Steepening', desc:'Short-end yields fall more than long end. Classic pre-easing scenario — market prices in Fed cuts, long end anchored.', shifts:{'US 2Y':-80,'US 5Y':-50,'US 10Y':-25,'US 30Y':-10,'DE 2Y':-70,'DE 5Y':-45,'DE 10Y':-20,'DE 30Y':-8,'UK 10Y':-20,'AUS 10Y':-20,'CAD 10Y':-20} },
  { name:'Bear Flattening', desc:'Short-end yields rise more. Typical early hiking cycle — Fed raises overnight, long end moves less as inflation expectations remain anchored.', shifts:{'US 2Y':80,'US 5Y':60,'US 10Y':35,'US 30Y':15,'DE 2Y':70,'DE 5Y':50,'DE 10Y':30,'DE 30Y':12,'UK 10Y':30,'AUS 10Y':30,'CAD 10Y':30} },
  { name:'Bull Flattening', desc:'Long-end yields fall more. Risk-off flight to safety or growth fears — 30Y rallies hard, short end constrained by policy floor.', shifts:{'US 2Y':-15,'US 5Y':-30,'US 10Y':-55,'US 30Y':-80,'DE 2Y':-12,'DE 5Y':-25,'DE 10Y':-50,'DE 30Y':-75,'UK 10Y':-50,'AUS 10Y':-50,'CAD 10Y':-50} },
  { name:'Parallel +50bp',  desc:'All tenors shift up 50bp simultaneously. Represents an undifferentiated rate shock — inflation surprise or supply shock.', shifts:Object.fromEntries(Object.keys(TENOR_DEFS).map(k=>[k,50])) },
  { name:'Parallel −50bp',  desc:'All tenors shift down 50bp. Risk-off, recession fears, or policy pivot signal.', shifts:Object.fromEntries(Object.keys(TENOR_DEFS).map(k=>[k,-50])) },
]

export default function CurveTradeBuilder() {
  const [tradeType, setTradeType] = useState<TradeType>('spread')
  const [longLeg,  setLongLeg]   = useState('US 10Y')
  const [shortLeg, setShortLeg]  = useState('US 2Y')
  const [frontLeg, setFrontLeg]  = useState('US 2Y')
  const [bellyLeg, setBellyLeg]  = useState('US 10Y')
  const [backLeg,  setBackLeg]   = useState('US 30Y')
  const [startYear, setStartYear] = useState(2015)
  const [notional,  setNotional]  = useState(10_000_000)
  const [loading, setLoading]     = useState(false)
  const [error,   setError]       = useState('')
  const [spread,  setSpread]      = useState<SeriesPoint[]>([])
  const [formula, setFormula]     = useState('')
  const [curveShape, setCurveShape]   = useState<string | null>(null)
  const [activeScenario, setActiveScenario] = useState<string | null>(null)
  const [currentYtm, setCurrentYtm] = useState(4.2)

  const buildFormula = useCallback(() => {
    const tl = TENOR_DEFS[longLeg]?.key; const ts = TENOR_DEFS[shortLeg]?.key
    const tf = TENOR_DEFS[frontLeg]?.key; const tb = TENOR_DEFS[bellyLeg]?.key; const tbk = TENOR_DEFS[backLeg]?.key
    if (tradeType === 'spread') return `${tl} - ${ts}`
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

  /* ── DV01 per leg at current YTM ── */
  const dv01Long  = calcDV01(longLeg,  currentYtm) * (notional / 100)
  const dv01Short = calcDV01(shortLeg, currentYtm) * (notional / 100)
  const dv01Front = calcDV01(frontLeg, currentYtm) * (notional / 100)
  const dv01Belly = calcDV01(bellyLeg, currentYtm) * (notional / 100)
  const dv01Back  = calcDV01(backLeg,  currentYtm) * (notional / 100)

  /* ── DV01-neutral hedge ratio for spread ── */
  const hedgeRatio = dv01Long > 0 && dv01Short > 0 ? dv01Long / dv01Short : NaN
  const neutralShortNotional = !isNaN(hedgeRatio) ? notional * hedgeRatio : NaN

  /* ── Stats ── */
  const vals   = spread.map(p => p.value).filter(v => isFinite(v))
  const latest = vals[vals.length - 1]
  const mean   = vals.length ? vals.reduce((a, b) => a + b, 0) / vals.length : NaN
  const peak   = vals.length ? Math.max(...vals) : NaN
  const trough = vals.length ? Math.min(...vals) : NaN
  const pct5   = vals.length ? [...vals].sort((a, b) => a - b)[Math.floor(vals.length * 0.05)] : NaN
  const pct95  = vals.length ? [...vals].sort((a, b) => a - b)[Math.floor(vals.length * 0.95)] : NaN

  /* ── P&L using actual DV01 ── */
  const currentChg = spread.length > 1 ? (spread[spread.length - 1].value - spread[spread.length - 2].value) * 100 : NaN
  const spreadDv01 = tradeType === 'spread' ? Math.min(dv01Long, dv01Short) : Math.min(dv01Front, dv01Back)
  const dailyPnl   = isNaN(currentChg) ? NaN : currentChg * spreadDv01

  /* ── Scenario P&L ── */
  const scenarioPnl = (scenName: string) => {
    const sc = SCENARIOS.find(s => s.name === scenName)
    if (!sc) return NaN
    if (tradeType === 'spread') {
      const dLong  = (sc.shifts[longLeg]  ?? 0) / 100 * dv01Long
      const dShort = (sc.shifts[shortLeg] ?? 0) / 100 * dv01Short
      return -dLong + dShort  // long bond hurts when yields rise
    } else {
      const dFront = (sc.shifts[frontLeg] ?? 0) / 100 * dv01Front
      const dBelly = (sc.shifts[bellyLeg] ?? 0) / 100 * dv01Belly
      const dBack  = (sc.shifts[backLeg]  ?? 0) / 100 * dv01Back
      return -2 * dBelly + dFront + dBack
    }
  }

  const spreadTrace: PlotTrace = {
    type:'scatter', mode:'lines', name: formula || 'Spread',
    x: spread.map(p => p.date), y: spread.map(p => p.value),
    line:{ color:'#f39200', width:1.5 },
    fill:'tozeroy', fillcolor:'rgba(243,146,0,0.06)',
  }

  const zVals = vals.length && !isNaN(mean) ? (() => {
    const std = Math.sqrt(vals.reduce((a, b) => a + (b - mean) ** 2, 0) / vals.length)
    return std > 0 ? vals.map(v => (v - mean) / std) : vals.map(() => 0)
  })() : []
  const zTrace: PlotTrace = {
    type:'scatter', mode:'lines', name:'Z-score',
    x: spread.map(p => p.date), y: zVals,
    line:{ color:'#60a5fa', width:1.5 },
    fill:'tozeroy', fillcolor:'rgba(96,165,250,0.06)',
  }

  const tenorOptions = Object.keys(TENOR_DEFS)
  const fmtM = (v: number) => '$' + (Math.abs(v) / 1e6).toFixed(2) + 'M'

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
              <select className="ctrl-select" value={longLeg} onChange={e => setLongLeg(e.target.value)}>
                {tenorOptions.map(t => <option key={t} value={t}>{t}</option>)}
              </select>
              <div style={{ color:'#555', fontSize:10, marginTop:3 }}>DV01: ${(dv01Long).toFixed(2)}/bp per $100 notional</div>
            </div>
            <div className="ctrl-section">
              <div className="ctrl-label">SHORT LEG</div>
              <select className="ctrl-select" value={shortLeg} onChange={e => setShortLeg(e.target.value)}>
                {tenorOptions.map(t => <option key={t} value={t}>{t}</option>)}
              </select>
              <div style={{ color:'#555', fontSize:10, marginTop:3 }}>DV01: ${(dv01Short).toFixed(2)}/bp per $100 notional</div>
            </div>
          </>
        ) : (
          <>
            <div className="ctrl-section">
              <div className="ctrl-label">FRONT (SHORT)</div>
              <select className="ctrl-select" value={frontLeg} onChange={e => setFrontLeg(e.target.value)}>
                {tenorOptions.map(t => <option key={t} value={t}>{t}</option>)}
              </select>
            </div>
            <div className="ctrl-section">
              <div className="ctrl-label">BELLY (LONG × 2)</div>
              <select className="ctrl-select" value={bellyLeg} onChange={e => setBellyLeg(e.target.value)}>
                {tenorOptions.map(t => <option key={t} value={t}>{t}</option>)}
              </select>
            </div>
            <div className="ctrl-section">
              <div className="ctrl-label">BACK (SHORT)</div>
              <select className="ctrl-select" value={backLeg} onChange={e => setBackLeg(e.target.value)}>
                {tenorOptions.map(t => <option key={t} value={t}>{t}</option>)}
              </select>
            </div>
          </>
        )}

        <div className="ctrl-section">
          <div className="ctrl-label">CURRENT YTM (%) — for DV01</div>
          <input type="number" className="ctrl-input" value={currentYtm} step={0.05} min={0.1} max={20} onChange={e => setCurrentYtm(+e.target.value)} />
        </div>

        <div className="ctrl-section">
          <div className="ctrl-label">START YEAR</div>
          <input type="number" className="ctrl-input" value={startYear} min={1994} max={2025} onChange={e => setStartYear(+e.target.value)} />
        </div>

        <div className="ctrl-section">
          <div className="ctrl-label">NOTIONAL (USD)</div>
          <input type="number" className="ctrl-input" value={notional} step={1000000} onChange={e => setNotional(+e.target.value)} />
          <div style={{ color:'#555', fontSize:10, marginTop:4 }}>${(notional/1e6).toFixed(0)}mm</div>
        </div>

        <button className="primary-button" style={{ width:'100%', marginTop:8 }} onClick={compute} disabled={loading}>
          {loading ? 'Loading…' : 'Build Trade'}
        </button>
      </aside>

      <div className="bond-main">
        <div style={{ borderLeft:'3px solid #f39200', padding:'10px 14px', background:'rgba(243,146,0,0.04)', borderRadius:'0 6px 6px 0', marginBottom:20 }}>
          <div style={{ color:'#e8e8e8', fontWeight:600, fontSize:13, textTransform:'uppercase', letterSpacing:'0.04em' }}>
            {tradeType === 'spread'
              ? `${longLeg} / ${shortLeg} Steepener`
              : `${bellyLeg} Butterfly (${frontLeg} | ${bellyLeg} | ${backLeg})`}
          </div>
          {formula && <div style={{ color:'#666', fontSize:11, marginTop:4, fontFamily:'monospace' }}>{formula}</div>}
        </div>

        {/* ── Curve Shape Presets ── */}
        <div style={{ borderLeft:'3px solid #34d399', padding:'10px 14px', background:'rgba(52,211,153,0.04)', borderRadius:'0 6px 6px 0', marginBottom:12 }}>
          <div style={{ color:'#e8e8e8', fontWeight:600, fontSize:12, textTransform:'uppercase', letterSpacing:'0.04em' }}>Curve Shape Reference</div>
        </div>
        <div style={{ display:'flex', gap:8, flexWrap:'wrap', marginBottom:16 }}>
          {CURVE_SHAPES.map(cs => (
            <button key={cs.name}
              onClick={() => setCurveShape(curveShape === cs.name ? null : cs.name)}
              style={{ padding:'5px 12px', fontSize:11, borderRadius:6, border:'1px solid', cursor:'pointer', background:curveShape===cs.name?'rgba(52,211,153,0.15)':'transparent', color:curveShape===cs.name?'#34d399':'#888', borderColor:curveShape===cs.name?'#34d399':'#2a2a2a' }}>
              {cs.name}
            </button>
          ))}
        </div>
        {curveShape && (() => {
          const cs = CURVE_SHAPES.find(c => c.name === curveShape)
          return cs ? (
            <div style={{ background:'rgba(52,211,153,0.07)', border:'1px solid rgba(52,211,153,0.2)', borderRadius:8, padding:'12px 16px', marginBottom:20, fontSize:12, color:'#bbb', lineHeight:1.6 }}>
              <strong style={{color:'#34d399'}}>{cs.shape}</strong> — {cs.desc}
            </div>
          ) : null
        })()}

        {/* ── Scenario Profiles ── */}
        <div style={{ borderLeft:'3px solid #a78bfa', padding:'10px 14px', background:'rgba(167,139,250,0.04)', borderRadius:'0 6px 6px 0', marginBottom:12 }}>
          <div style={{ color:'#e8e8e8', fontWeight:600, fontSize:12, textTransform:'uppercase', letterSpacing:'0.04em' }}>Scenario Profiles — P&L Impact</div>
          <div style={{ color:'#888', fontSize:11, marginTop:4 }}>Click a scenario to see estimated P&L for the current trade at ${(notional/1e6).toFixed(0)}mm notional</div>
        </div>
        <div style={{ display:'flex', gap:6, flexWrap:'wrap', marginBottom:12 }}>
          {SCENARIOS.map(sc => {
            const pnl = scenarioPnl(sc.name)
            const isActive = activeScenario === sc.name
            return (
              <button key={sc.name}
                onClick={() => setActiveScenario(isActive ? null : sc.name)}
                style={{ padding:'5px 12px', fontSize:11, borderRadius:6, border:'1px solid', cursor:'pointer', background:isActive?'rgba(167,139,250,0.15)':'transparent', color:isActive?'#a78bfa':'#888', borderColor:isActive?'#a78bfa':'#2a2a2a' }}>
                {sc.name}
              </button>
            )
          })}
        </div>
        {activeScenario && (() => {
          const sc = SCENARIOS.find(s => s.name === activeScenario)
          const pnl = scenarioPnl(activeScenario)
          return sc ? (
            <div style={{ background:'rgba(167,139,250,0.07)', border:'1px solid rgba(167,139,250,0.2)', borderRadius:8, padding:'12px 16px', marginBottom:20 }}>
              <div style={{ display:'flex', alignItems:'center', justifyContent:'space-between', marginBottom:8 }}>
                <strong style={{color:'#a78bfa', fontSize:13}}>{sc.name}</strong>
                <span style={{ color: isNaN(pnl)?'#888':pnl>=0?'#00c087':'#ff4d4d', fontSize:16, fontWeight:700, fontVariantNumeric:'tabular-nums' }}>
                  {isNaN(pnl) ? '—' : (pnl>=0?'+':'')+fmtM(pnl)}
                </span>
              </div>
              <div style={{ color:'#bbb', fontSize:12, lineHeight:1.6 }}>{sc.desc}</div>
              <div style={{ color:'#666', fontSize:11, marginTop:6 }}>
                Estimated P&L = sum of (shift × DV01) per leg. Uses bond-math DV01 at YTM {currentYtm}%.
              </div>
            </div>
          ) : null
        })()}

        {/* ── DV01 Summary ── */}
        {tradeType === 'spread' && (
          <div style={{ background:'#1a1a1a', border:'1px solid #2a2a2a', borderRadius:8, padding:'14px 16px', marginBottom:20 }}>
            <div style={{ color:'#888', fontSize:10, textTransform:'uppercase', letterSpacing:'0.06em', marginBottom:10 }}>DV01 Analysis at YTM {currentYtm}%</div>
            <div style={{ display:'grid', gridTemplateColumns:'repeat(auto-fit,minmax(160px,1fr))', gap:10 }}>
              {[
                { label:`${longLeg} DV01`, val:'$'+dv01Long.toFixed(2)+'/bp', sub:'per $100 face', color:'#60a5fa' },
                { label:`${shortLeg} DV01`, val:'$'+dv01Short.toFixed(2)+'/bp', sub:'per $100 face', color:'#f87171' },
                { label:'DV01-Neutral Ratio', val: isNaN(hedgeRatio)?'—':hedgeRatio.toFixed(3)+'×', sub:`short ${isNaN(hedgeRatio)?'—':fmtM(neutralShortNotional)}`, color:'#f39200' },
                { label:`Trade DV01 @${(notional/1e6).toFixed(0)}mm`, val:'$'+(Math.min(dv01Long,dv01Short)*(notional/100)).toFixed(0)+'/bp', sub:'approx net per 1bp spread move', color:'#34d399' },
              ].map(({ label, val, sub, color }) => (
                <div key={label}>
                  <div style={{ color:'#666', fontSize:10, textTransform:'uppercase', letterSpacing:'0.05em', marginBottom:3 }}>{label}</div>
                  <div style={{ color, fontSize:16, fontWeight:700, fontVariantNumeric:'tabular-nums' }}>{val}</div>
                  <div style={{ color:'#555', fontSize:10, marginTop:2 }}>{sub}</div>
                </div>
              ))}
            </div>
          </div>
        )}

        {error && <div style={{ color:'#ff4d4d', fontSize:12, marginBottom:12 }}>Error: {error}<br/><small style={{color:'#888'}}>Is the FastAPI backend running?</small></div>}

        {!spread.length && !loading && (
          <div style={{ color:'#555', textAlign:'center', padding:'40px 20px', fontSize:13 }}>
            Configure the trade above and press <strong style={{ color:'#f39200' }}>Build Trade</strong> to load historical data
          </div>
        )}

        {loading && <div style={{ color:'#aaa', textAlign:'center', padding:60 }}><div style={{ width:32, height:32, border:'3px solid #f39200', borderTopColor:'transparent', borderRadius:'50%', animation:'spin 0.8s linear infinite', margin:'0 auto 16px' }}/>Loading series…</div>}

        {spread.length > 0 && !loading && (
          <>
            {/* KPI strip */}
            <div className="kpi-strip" style={{ marginBottom:20 }}>
              {[
                { label:'Current Level',    val: isFinite(latest)?latest.toFixed(2)+'%':'—',            color:'#f39200' },
                { label:'Historical Mean',  val: isNaN(mean)?'—':mean.toFixed(2)+'%',                   color:'#aaa' },
                { label:'5th Pctile',       val: isNaN(pct5)?'—':pct5.toFixed(2)+'%',                  color:'#f87171' },
                { label:'95th Pctile',      val: isNaN(pct95)?'—':pct95.toFixed(2)+'%',                color:'#60a5fa' },
                { label:'Daily Move (bp)',  val: isNaN(currentChg)?'—':(currentChg>=0?'+':'')+currentChg.toFixed(1), color:isNaN(currentChg)?'#aaa':currentChg>=0?'#00c087':'#ff4d4d' },
                { label:'Est. Daily P&L',   val: isNaN(dailyPnl)?'—':'$'+Math.abs(dailyPnl).toFixed(0), color:isNaN(dailyPnl)?'#aaa':dailyPnl>=0?'#00c087':'#ff4d4d' },
              ].map(({ label, val, color }) => (
                <div key={label} className="kpi-card">
                  <div style={{ color:'#888', fontSize:10, textTransform:'uppercase', letterSpacing:'0.06em', marginBottom:4 }}>{label}</div>
                  <div style={{ color, fontSize:18, fontWeight:700, fontVariantNumeric:'tabular-nums' }}>{val}</div>
                </div>
              ))}
            </div>

            <div style={{ borderLeft:'3px solid #f39200', padding:'10px 14px', background:'rgba(243,146,0,0.04)', borderRadius:'0 6px 6px 0', marginBottom:12 }}>
              <div style={{ color:'#e8e8e8', fontWeight:600, fontSize:13, textTransform:'uppercase', letterSpacing:'0.04em' }}>Spread History</div>
              <div style={{ color:'#888', fontSize:11, marginTop:4 }}>{spread.length} observations · basis points (×100)</div>
            </div>
            <Chart traces={[spreadTrace]} layout={{ yaxis:{ ticksuffix:'%', title:{text:'Spread (%)',font:{color:'#666',size:11}} } }} />

            <div style={{ borderLeft:'3px solid #60a5fa', padding:'10px 14px', background:'rgba(96,165,250,0.04)', borderRadius:'0 6px 6px 0', margin:'28px 0 12px' }}>
              <div style={{ color:'#e8e8e8', fontWeight:600, fontSize:13, textTransform:'uppercase', letterSpacing:'0.04em' }}>Historical Z-Score</div>
              <div style={{ color:'#888', fontSize:11, marginTop:4 }}>Spread relative to historical mean · ±2 = extreme · today = {isFinite(latest)&&!isNaN(mean)?((latest-mean)/Math.max(Math.sqrt(vals.reduce((a,b)=>a+(b-mean)**2,0)/vals.length),1e-9)).toFixed(2)+'σ':'—'}</div>
            </div>
            <Chart traces={[zTrace,
              { type:'scatter', mode:'lines', name:'+2σ', x:spread.map(p=>p.date), y:spread.map(()=>2),  line:{color:'#ff4d4d',width:1,dash:'dot'}, showlegend:false } as PlotTrace,
              { type:'scatter', mode:'lines', name:'-2σ', x:spread.map(p=>p.date), y:spread.map(()=>-2), line:{color:'#00c087',width:1,dash:'dot'}, showlegend:false } as PlotTrace,
            ]} layout={{ yaxis:{ title:{text:'Z-score',font:{color:'#666',size:11}}, zeroline:true, zerolinecolor:'#444' } }} />

            <div style={{ borderLeft:'3px solid #a78bfa', padding:'10px 14px', background:'rgba(167,139,250,0.04)', borderRadius:'0 6px 6px 0', margin:'28px 0 12px' }}>
              <div style={{ color:'#e8e8e8', fontWeight:600, fontSize:13, textTransform:'uppercase', letterSpacing:'0.04em' }}>Level Distribution</div>
            </div>
            <Chart traces={[
              { type:'histogram', name:'Distribution', x:vals, nbinsx:40, marker:{color:'#f39200',opacity:0.7} } as PlotTrace,
              isFinite(latest) ? { type:'scatter', mode:'lines', name:'Current', x:[latest,latest], y:[0,vals.length/5], line:{color:'#ff4d4d',width:2,dash:'dash'} } as PlotTrace : {} as PlotTrace,
            ].filter(t=>Object.keys(t).length>0)}
            layout={{ barmode:'overlay', xaxis:{ticksuffix:'%'}, yaxis:{title:{text:'Count',font:{color:'#666',size:11}}} }} height={260} />

            {/* ── Scenario P&L table ── */}
            <div style={{ borderLeft:'3px solid #34d399', padding:'10px 14px', background:'rgba(52,211,153,0.04)', borderRadius:'0 6px 6px 0', margin:'28px 0 12px' }}>
              <div style={{ color:'#e8e8e8', fontWeight:600, fontSize:13, textTransform:'uppercase', letterSpacing:'0.04em' }}>Scenario P&L Summary</div>
              <div style={{ color:'#888', fontSize:11, marginTop:4 }}>All 6 scenarios · {(notional/1e6).toFixed(0)}mm notional · DV01 at YTM {currentYtm}%</div>
            </div>
            <div style={{ overflowX:'auto' }}>
              <table style={{ width:'100%', borderCollapse:'collapse', fontSize:12 }}>
                <thead>
                  <tr style={{ borderBottom:'1px solid #2a2a2a' }}>
                    {['Scenario','Description','Est. P&L'].map(h => (
                      <th key={h} style={{ padding:'8px 12px', textAlign:'left', color:'#666', fontWeight:500, textTransform:'uppercase', fontSize:10, letterSpacing:'0.05em', whiteSpace:'nowrap' }}>{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {SCENARIOS.map(sc => {
                    const pnl = scenarioPnl(sc.name)
                    return (
                      <tr key={sc.name} style={{ borderBottom:'1px solid #1f1f1f' }}>
                        <td style={{ padding:'8px 12px', color:'#a78bfa', fontWeight:600, whiteSpace:'nowrap' }}>{sc.name}</td>
                        <td style={{ padding:'8px 12px', color:'#666', fontSize:11 }}>{sc.desc}</td>
                        <td style={{ padding:'8px 12px', color:isNaN(pnl)?'#888':pnl>=0?'#00c087':'#ff4d4d', fontWeight:700, fontVariantNumeric:'tabular-nums', whiteSpace:'nowrap' }}>
                          {isNaN(pnl)?'—':(pnl>=0?'+':'')+fmtM(pnl)}
                        </td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>
          </>
        )}
      </div>
    </div>
  )
}
