<title>Bond Calculator</title>
import { useState, useCallback, useEffect, useRef } from 'react'

/* ── Bond math ───────────────────────────────────────────────────────────────── */
function bondPrice(fv: number, coupon: number, freq: number, ytm: number, periods: number): number {
  const c = (coupon / 100 / freq) * fv
  const r = ytm / 100 / freq
  if (Math.abs(r) < 1e-12) return fv + c * periods
  return c * (1 - Math.pow(1 + r, -periods)) / r + fv * Math.pow(1 + r, -periods)
}

function macaulayDuration(fv: number, coupon: number, freq: number, ytm: number, periods: number): number {
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

function convexityCalc(fv: number, coupon: number, freq: number, ytm: number, periods: number): number {
  const c = (coupon / 100 / freq) * fv
  const r = ytm / 100 / freq
  const p = bondPrice(fv, coupon, freq, ytm, periods)
  let conv = 0
  for (let t = 1; t <= periods; t++) {
    const cf = t < periods ? c : c + fv
    conv += cf * t * (t + 1) / Math.pow(1 + r, t + 2)
  }
  return p > 0 ? conv / (p * freq * freq) : 0
}

function yieldFromPrice(fv: number, coupon: number, freq: number, price: number, periods: number): number {
  let y = coupon / 100
  for (let i = 0; i < 200; i++) {
    const p = bondPrice(fv, coupon, freq, y * 100, periods)
    const dp = (bondPrice(fv, coupon, freq, (y + 1e-6) * 100, periods) - p) / 1e-6
    const err = p - price
    if (Math.abs(err) < 1e-8) break
    y -= err / dp
    if (y < -0.5) y = -0.5
    if (y > 5) y = 5
  }
  return y * 100
}

/* ── Plotly wrapper ──────────────────────────────────────────────────────────── */
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
        margin: { t: 36, r: 16, b: 48, l: 68 },
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

/* ── Types ───────────────────────────────────────────────────────────────────── */
type CalcMode = 'price' | 'yield'
type TabId = 'metrics' | 'priceyield' | 'cashflows' | 'rateshock' | 'evolution'

interface Result {
  price: number; ytm: number; macDur: number; modDur: number
  dv01: number; convex: number; periods: number; fullPrice: number
  fv: number; coupon: number; freq: number; matYears: number
}

const fmt = (v: number, dec = 4) => v.toFixed(dec)
const fmtCcy = (v: number) => v.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })

const TABS: { id: TabId; label: string }[] = [
  { id: 'metrics',    label: 'Metrics' },
  { id: 'priceyield', label: 'Price-Yield Curve' },
  { id: 'cashflows',  label: 'Cash Flows' },
  { id: 'rateshock',  label: 'Rate Shock Analysis' },
  { id: 'evolution',  label: 'Rate Evolution' },
]

/* ── Main component ──────────────────────────────────────────────────────────── */
export default function BondCalculator() {
  const [mode, setMode]         = useState<CalcMode>('price')
  const [fv, setFv]             = useState(1000)
  const [coupon, setCoupon]     = useState(5)
  const [freq, setFreq]         = useState(2)
  const [ytm, setYtm]           = useState(4.5)
  const [price, setPrice]       = useState(1043.76)
  const [matYears, setMatYears] = useState(10)
  const [result, setResult]     = useState<Result | null>(null)
  const [activeTab, setActiveTab] = useState<TabId>('metrics')
  const [conceptOpen, setConceptOpen] = useState(false)

  const calculate = useCallback(() => {
    const periods = Math.round(matYears * freq)
    let calcPrice = price, calcYtm = ytm
    if (mode === 'price') calcPrice = bondPrice(fv, coupon, freq, ytm, periods)
    else calcYtm = yieldFromPrice(fv, coupon, freq, price, periods)
    const macDur = macaulayDuration(fv, coupon, freq, calcYtm, periods)
    const modDur = macDur / (1 + calcYtm / 100 / freq)
    const dv01   = modDur * calcPrice / 10000
    const convex = convexityCalc(fv, coupon, freq, calcYtm, periods)
    setResult({ price: calcPrice, ytm: calcYtm, macDur, modDur, dv01, convex, periods, fullPrice: calcPrice, fv, coupon, freq, matYears })
    setActiveTab('metrics')
  }, [mode, fv, coupon, freq, ytm, price, matYears])

  const kpiStyle = { background: '#1a1a1a', border: '1px solid #2a2a2a', borderRadius: 8, padding: '16px 20px' }
  const labelStyle = { color: '#666', fontSize: 10, textTransform: 'uppercase' as const, letterSpacing: '0.06em', marginBottom: 4 }
  const valStyle   = { color: '#f39200', fontSize: 22, fontWeight: 700, fontVariantNumeric: 'tabular-nums' as const }

  /* ── Price-Yield curve data ── */
  const pyTraces: PlotTrace[] = result ? (() => {
    const { fv: fvR, coupon: cr, freq: fR, ytm: ytmR, price: pR, modDur, convex } = result
    const periods = Math.round(result.matYears * fR)
    const yLo = Math.max(0.1, ytmR - 8), yHi = Math.min(25, ytmR + 8)
    const ys = Array.from({ length: 200 }, (_, i) => yLo + (yHi - yLo) * i / 199)
    const prices = ys.map(y => bondPrice(fvR, cr, fR, y, periods))
    const durLine = ys.map(y => pR - modDur * pR * (y - ytmR) / 100)
    const convLine = ys.map(y => { const dy = (y - ytmR) / 100; return pR + pR * (-modDur * dy + 0.5 * convex * dy * dy) })
    return [
      { type:'scatter', mode:'lines', name:'Actual Price', x:ys, y:prices, line:{color:'#60a5fa',width:2.5} },
      { type:'scatter', mode:'lines', name:'Duration Estimate', x:ys, y:durLine, line:{color:'#f39200',width:1.5,dash:'dash'} },
      { type:'scatter', mode:'lines', name:'Convexity-Adjusted', x:ys, y:convLine, line:{color:'#00c087',width:1.5,dash:'dot'} },
      { type:'scatter', mode:'markers', name:'Current', x:[ytmR], y:[pR], marker:{color:'#ff4d4d',size:10,symbol:'circle'} },
    ]
  })() : []

  /* ── Cash flow data ── */
  const { cfTimes, cfCoupons, cfPrincipals, cfPVs, cfRows } = result ? (() => {
    const { fv: fvR, coupon: cr, freq: fR, ytm: ytmR, matYears: mat, price: pR } = result
    const periods = Math.round(mat * fR)
    const r = ytmR / 100 / fR
    const cpn = (cr / 100 / fR) * fvR
    const times: number[] = [], coupons: number[] = [], principals: number[] = [], pvs: number[] = []
    const rows: { t: string; cf: string; disc: string; pv: string; pct: string; cumDur: string }[] = []
    for (let t = 1; t <= periods; t++) {
      const tYr = t / fR
      const cfAmt = t < periods ? cpn : cpn + fvR
      const pv = cfAmt / Math.pow(1 + r, t)
      times.push(tYr); coupons.push(cpn); principals.push(t === periods ? fvR : 0); pvs.push(pv)
      rows.push({ t: tYr.toFixed(2), cf: fmtCcy(cfAmt), disc: (pv/cfAmt).toFixed(6), pv: fmtCcy(pv), pct: (pv/pR*100).toFixed(2)+'%', cumDur: (tYr*pv/pR).toFixed(4) })
    }
    return { cfTimes: times, cfCoupons: coupons, cfPrincipals: principals, cfPVs: pvs, cfRows: rows }
  })() : { cfTimes:[], cfCoupons:[], cfPrincipals:[], cfPVs:[], cfRows:[] }

  const cfTraces: PlotTrace[] = result ? [
    { type:'bar', name:'Coupon', x:cfTimes, y:cfCoupons, marker:{color:'#60a5fa',opacity:0.85} },
    { type:'bar', name:'Principal', x:cfTimes, y:cfPrincipals, marker:{color:'#f39200',opacity:0.85} },
    { type:'scatter', mode:'lines+markers', name:'Present Value', x:cfTimes, y:cfPVs, line:{color:'#00c087',width:2}, marker:{size:5} },
  ] : []

  /* ── Rate shock data ── */
  const shockData = result ? (() => {
    const { fv: fvR, coupon: cr, freq: fR, ytm: ytmR, price: pR, modDur, convex } = result
    const periods = Math.round(result.matYears * fR)
    return Array.from({ length: 26 }, (_, i) => {
      const bp = -300 + i * 25
      const newYtm = Math.max(0.01, ytmR + bp / 100)
      const actual = bondPrice(fvR, cr, fR, newYtm, periods)
      const dy = bp / 10000
      const durPx = pR + pR * (-modDur * dy)
      const convPx = pR + pR * (-modDur * dy + 0.5 * convex * dy * dy)
      return { bp, newYtm: newYtm.toFixed(2), actual: fmtCcy(actual), dAct: fmtCcy(actual - pR), dDur: fmtCcy(durPx - pR), dConv: fmtCcy(convPx - pR), durErr: fmtCcy((actual - pR) - (durPx - pR)), _actual: actual, _dur: durPx, _conv: convPx }
    })
  })() : []

  const shockTraces: PlotTrace[] = result ? [
    { type:'scatter', mode:'lines', name:'Actual Price', x:shockData.map(r=>r.bp), y:shockData.map(r=>r._actual), line:{color:'#60a5fa',width:2.5} },
    { type:'scatter', mode:'lines', name:'Duration Estimate', x:shockData.map(r=>r.bp), y:shockData.map(r=>r._dur), line:{color:'#f39200',width:1.5,dash:'dash'} },
    { type:'scatter', mode:'lines', name:'Convexity-Adjusted', x:shockData.map(r=>r.bp), y:shockData.map(r=>r._conv), line:{color:'#00c087',width:1.5,dash:'dot'} },
  ] : []

  /* ── Rate evolution (quarterly over holding period) ── */
  const evolData = result ? (() => {
    const { fv: fvR, coupon: cr, freq: fR, ytm: ytmR, matYears: mat } = result
    const quarters: number[] = []
    const evolPrices: number[] = [], evolModDur: number[] = [], evolDv01: number[] = []
    const step = 0.25
    for (let q = 0; q <= mat; q += step) {
      const remaining = mat - q
      const periods = Math.max(1, Math.round(remaining * fR))
      const px = bondPrice(fvR, cr, fR, ytmR, periods)
      const mac = macaulayDuration(fvR, cr, fR, ytmR, periods)
      const mod = mac / (1 + ytmR / 100 / fR)
      const dv = mod * px / 10000
      quarters.push(q); evolPrices.push(px); evolModDur.push(mod); evolDv01.push(dv)
    }
    return { quarters, evolPrices, evolModDur, evolDv01 }
  })() : { quarters:[], evolPrices:[], evolModDur:[], evolDv01:[] }

  const evolTraces1: PlotTrace[] = result ? [{ type:'scatter', mode:'lines', name:'Price', x:evolData.quarters, y:evolData.evolPrices, line:{color:'#f39200',width:2}, fill:'tozeroy', fillcolor:'rgba(243,146,0,0.06)' }] : []
  const evolTraces2: PlotTrace[] = result ? [{ type:'scatter', mode:'lines', name:'Modified Duration', x:evolData.quarters, y:evolData.evolModDur, line:{color:'#60a5fa',width:2} }] : []
  const evolTraces3: PlotTrace[] = result ? [{ type:'scatter', mode:'lines', name:'DV01 ($)', x:evolData.quarters, y:evolData.evolDv01, line:{color:'#a78bfa',width:2}, fill:'tozeroy', fillcolor:'rgba(167,139,250,0.06)' }] : []

  const shockColor = (bp: number) => bp < 0 ? '#00c087' : bp > 0 ? '#ff4d4d' : '#888'

  return (
    <div className="bond-layout">
      {/* ── Sidebar ── */}
      <aside className="bond-sidebar">
        <div className="ctrl-section">
          <div className="ctrl-label">SOLVE FOR</div>
          <div className="pill-group">
            {(['price', 'yield'] as const).map(m => (
              <button key={m} className={`pill ${mode === m ? 'active' : ''}`} onClick={() => setMode(m)}>
                {m === 'price' ? 'Clean Price' : 'YTM'}
              </button>
            ))}
          </div>
        </div>
        <div className="ctrl-section">
          <div className="ctrl-label">FACE VALUE</div>
          <input type="number" className="ctrl-input" value={fv} onChange={e => setFv(+e.target.value)} />
        </div>
        <div className="ctrl-section">
          <div className="ctrl-label">COUPON RATE (%)</div>
          <input type="number" className="ctrl-input" value={coupon} step={0.25} onChange={e => setCoupon(+e.target.value)} />
        </div>
        <div className="ctrl-section">
          <div className="ctrl-label">FREQUENCY</div>
          <select className="ctrl-select" value={freq} onChange={e => setFreq(+e.target.value)}>
            <option value={1}>Annual</option>
            <option value={2}>Semi-Annual</option>
            <option value={4}>Quarterly</option>
            <option value={12}>Monthly</option>
          </select>
        </div>
        <div className="ctrl-section">
          <div className="ctrl-label">MATURITY (YEARS)</div>
          <input type="number" className="ctrl-input" value={matYears} step={0.5} min={0.5} onChange={e => setMatYears(+e.target.value)} />
        </div>
        {mode === 'price' ? (
          <div className="ctrl-section">
            <div className="ctrl-label">YTM (%)</div>
            <input type="number" className="ctrl-input" value={ytm} step={0.01} onChange={e => setYtm(+e.target.value)} />
          </div>
        ) : (
          <div className="ctrl-section">
            <div className="ctrl-label">CLEAN PRICE</div>
            <input type="number" className="ctrl-input" value={price} step={0.01} onChange={e => setPrice(+e.target.value)} />
          </div>
        )}
        <button className="primary-button" style={{ width: '100%', marginTop: 8 }} onClick={calculate}>
          Calculate
        </button>

        {/* Concept guide */}
        <div style={{ marginTop: 24, borderTop: '1px solid #2a2a2a', paddingTop: 16 }}>
          <button
            onClick={() => setConceptOpen(o => !o)}
            style={{ background:'transparent', border:'1px solid #2a2a2a', borderRadius:6, color:'#888', padding:'6px 12px', fontSize:11, cursor:'pointer', width:'100%', textAlign:'left' }}
          >
            {conceptOpen ? '▾' : '▸'} Concept Guide
          </button>
          {conceptOpen && (
            <div style={{ fontSize:11, color:'#777', lineHeight:1.6, marginTop:10 }}>
              <p><strong style={{color:'#aaa'}}>Macaulay Duration</strong> — Weighted average time to receive cash flows, measured in years. Longer = more interest-rate sensitive.</p>
              <p><strong style={{color:'#aaa'}}>Modified Duration</strong> — Mac.Dur / (1 + YTM/freq). Approximates % price change per 1% yield move: ΔP/P ≈ −ModDur × ΔY.</p>
              <p><strong style={{color:'#aaa'}}>DV01</strong> — Dollar value of a 1bp (0.01%) yield change. DV01 = ModDur × Price / 10,000. Used for hedging.</p>
              <p><strong style={{color:'#aaa'}}>Convexity</strong> — 2nd-order curvature. Adds ½ × Convexity × P × ΔY² to the duration estimate. Positive convexity = bond outperforms linear estimate in both up/down moves.</p>
              <p><strong style={{color:'#aaa'}}>Pull-to-Par</strong> — As a bond approaches maturity, its price converges to face value regardless of coupon vs YTM.</p>
              <p><strong style={{color:'#aaa'}}>Convexity gain</strong> — At ±200bp, the actual price exceeds the duration estimate. The difference is the convexity gain.</p>
            </div>
          )}
        </div>
      </aside>

      {/* ── Results ── */}
      <div className="bond-main">
        <div style={{ borderLeft:'3px solid #f39200', padding:'10px 14px', background:'rgba(243,146,0,0.04)', borderRadius:'0 6px 6px 0', marginBottom:20 }}>
          <div style={{ color:'#e8e8e8', fontWeight:600, fontSize:13, textTransform:'uppercase', letterSpacing:'0.04em' }}>Bond Calculator</div>
          <div style={{ color:'#888', fontSize:11, marginTop:4 }}>Price · Yield · Duration · DV01 · Convexity · Price-Yield Curve · Cash Flows · Shock Analysis</div>
        </div>

        {!result && (
          <div style={{ color:'#555', textAlign:'center', padding:'60px 20px', fontSize:13 }}>
            Set inputs on the left and press <strong style={{ color:'#f39200' }}>Calculate</strong>
          </div>
        )}

        {result && (
          <>
            {/* Tab bar */}
            <div style={{ display:'flex', gap:4, marginBottom:20, flexWrap:'wrap' }}>
              {TABS.map(t => (
                <button key={t.id}
                  onClick={() => setActiveTab(t.id)}
                  style={{ padding:'6px 14px', fontSize:11, borderRadius:6, border:'1px solid', cursor:'pointer', fontWeight:activeTab===t.id?700:400, background:activeTab===t.id?'#f39200':'transparent', color:activeTab===t.id?'#000':'#888', borderColor:activeTab===t.id?'#f39200':'#2a2a2a' }}>
                  {t.label}
                </button>
              ))}
            </div>

            {/* ── Tab: Metrics ── */}
            {activeTab === 'metrics' && (
              <>
                <div style={{ display:'grid', gridTemplateColumns:'repeat(auto-fit,minmax(160px,1fr))', gap:12, marginBottom:24 }}>
                  <div style={kpiStyle}>
                    <div style={labelStyle}>{mode === 'price' ? 'Clean Price' : 'YTM'}</div>
                    <div style={{ ...valStyle, color:'#00c087' }}>
                      {mode === 'price' ? fmtCcy(result.price) : fmt(result.ytm, 4) + '%'}
                    </div>
                  </div>
                  <div style={kpiStyle}><div style={labelStyle}>Full Price</div><div style={valStyle}>{fmtCcy(result.fullPrice)}</div></div>
                  <div style={kpiStyle}><div style={labelStyle}>Periods</div><div style={valStyle}>{result.periods}</div></div>
                </div>
                <div style={{ fontWeight:600, fontSize:12, textTransform:'uppercase', letterSpacing:'0.06em', margin:'24px 0 12px', color:'#666' }}>Risk Metrics</div>
                <div style={{ display:'grid', gridTemplateColumns:'repeat(auto-fit,minmax(160px,1fr))', gap:12, marginBottom:28 }}>
                  {[
                    { label:'Macaulay Duration', val: fmt(result.macDur, 3)+' yrs' },
                    { label:'Modified Duration', val: fmt(result.modDur, 3)+' yrs' },
                    { label:'DV01',              val: '$'+fmt(result.dv01, 4) },
                    { label:'Convexity',         val: fmt(result.convex, 3) },
                  ].map(({ label, val }) => (
                    <div key={label} style={kpiStyle}>
                      <div style={labelStyle}>{label}</div>
                      <div style={{ color:'#60a5fa', fontSize:20, fontWeight:700, fontVariantNumeric:'tabular-nums', marginTop:4 }}>{val}</div>
                    </div>
                  ))}
                </div>
                <div style={{ borderLeft:'3px solid #60a5fa', padding:'10px 14px', background:'rgba(96,165,250,0.04)', borderRadius:'0 6px 6px 0', marginBottom:12 }}>
                  <div style={{ color:'#e8e8e8', fontWeight:600, fontSize:13, textTransform:'uppercase', letterSpacing:'0.04em' }}>Price Sensitivity — ΔYield</div>
                  <div style={{ color:'#888', fontSize:11, marginTop:4 }}>Estimated P&L per $1,000 face using duration + convexity approximation</div>
                </div>
                <div style={{ overflowX:'auto' }}>
                  <table style={{ width:'100%', borderCollapse:'collapse', fontSize:12 }}>
                    <thead>
                      <tr style={{ borderBottom:'1px solid #2a2a2a' }}>
                        {['Δ Yield (bps)','ΔPrice (Duration)','ΔPrice (Dur+Convex)','% Change'].map(h => (
                          <th key={h} style={{ padding:'8px 12px', textAlign:'left', color:'#666', fontWeight:500, textTransform:'uppercase', fontSize:10, letterSpacing:'0.05em', whiteSpace:'nowrap' }}>{h}</th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {[-100,-50,-25,-10,-1,1,10,25,50,100].map(bps => {
                        const dy = bps/10000
                        const dPriceDur    = -result.modDur * result.price * dy
                        const dPriceConvex = 0.5 * result.convex * result.price * dy * dy
                        const total = dPriceDur + dPriceConvex
                        const pct   = result.price > 0 ? total/result.price*100 : 0
                        const clr   = bps<0?'#00c087':'#ff4d4d'
                        return (
                          <tr key={bps} style={{ borderBottom:'1px solid #1f1f1f' }}>
                            <td style={{ padding:'7px 12px', color:clr, fontWeight:600, fontVariantNumeric:'tabular-nums' }}>{bps>0?'+':''}{bps}</td>
                            <td style={{ padding:'7px 12px', color:clr, fontVariantNumeric:'tabular-nums' }}>{dPriceDur>0?'+':''}{fmtCcy(dPriceDur)}</td>
                            <td style={{ padding:'7px 12px', color:clr, fontVariantNumeric:'tabular-nums', fontWeight:600 }}>{total>0?'+':''}{fmtCcy(total)}</td>
                            <td style={{ padding:'7px 12px', color:clr, fontVariantNumeric:'tabular-nums' }}>{pct>0?'+':''}{pct.toFixed(3)}%</td>
                          </tr>
                        )
                      })}
                    </tbody>
                  </table>
                </div>
              </>
            )}

            {/* ── Tab: Price-Yield Curve ── */}
            {activeTab === 'priceyield' && (
              <>
                <div style={{ borderLeft:'3px solid #60a5fa', padding:'10px 14px', background:'rgba(96,165,250,0.04)', borderRadius:'0 6px 6px 0', marginBottom:12 }}>
                  <div style={{ color:'#e8e8e8', fontWeight:600, fontSize:13, textTransform:'uppercase', letterSpacing:'0.04em' }}>Price-Yield Relationship</div>
                  <div style={{ color:'#888', fontSize:11, marginTop:4 }}>Actual price (blue) vs duration estimate (dashed) vs convexity-adjusted (dotted) · red dot = current</div>
                </div>
                <Chart traces={pyTraces} layout={{ xaxis:{ title:{text:'YTM (%)',font:{color:'#666',size:11}}, ticksuffix:'%' }, yaxis:{ title:{text:'Price ($)',font:{color:'#666',size:11}} }, barmode:'overlay' }} height={420} />
                <p style={{ color:'#666', fontSize:11, marginTop:8, lineHeight:1.6 }}>
                  The <span style={{color:'#f39200'}}>dashed orange line</span> (duration) is a linear approximation — it underestimates price when yields rise and overestimates when they fall.
                  The <span style={{color:'#00c087'}}>dotted green line</span> (convexity-adjusted) adds the curvature correction.
                  Bonds with higher convexity outperform in both directions — they fall less when yields rise and gain more when yields fall.
                </p>
              </>
            )}

            {/* ── Tab: Cash Flows ── */}
            {activeTab === 'cashflows' && (
              <>
                <div style={{ borderLeft:'3px solid #00c087', padding:'10px 14px', background:'rgba(0,192,135,0.04)', borderRadius:'0 6px 6px 0', marginBottom:12 }}>
                  <div style={{ color:'#e8e8e8', fontWeight:600, fontSize:13, textTransform:'uppercase', letterSpacing:'0.04em' }}>Cash Flows & Present Values</div>
                  <div style={{ color:'#888', fontSize:11, marginTop:4 }}>Stacked: coupon (blue) + principal at maturity (orange) · green line = discounted PV at current YTM</div>
                </div>
                <Chart traces={cfTraces} layout={{ barmode:'stack', xaxis:{ title:{text:'Time (years)',font:{color:'#666',size:11}} }, yaxis:{ title:{text:'Amount ($)',font:{color:'#666',size:11}} } }} height={380} />
                <div style={{ overflowX:'auto', marginTop:20 }}>
                  <table style={{ width:'100%', borderCollapse:'collapse', fontSize:11 }}>
                    <thead>
                      <tr style={{ borderBottom:'1px solid #2a2a2a' }}>
                        {['Period (yr)','Cash Flow ($)','Disc. Factor','PV ($)','% of Price','Cum. Duration'].map(h => (
                          <th key={h} style={{ padding:'7px 10px', textAlign:'left', color:'#666', fontWeight:500, textTransform:'uppercase', fontSize:9, letterSpacing:'0.05em', whiteSpace:'nowrap' }}>{h}</th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {cfRows.map((r, i) => (
                        <tr key={i} style={{ borderBottom:'1px solid #1a1a1a' }}>
                          <td style={{ padding:'6px 10px', color:'#aaa', fontVariantNumeric:'tabular-nums' }}>{r.t}</td>
                          <td style={{ padding:'6px 10px', color:'#e8e8e8', fontVariantNumeric:'tabular-nums' }}>{r.cf}</td>
                          <td style={{ padding:'6px 10px', color:'#666', fontVariantNumeric:'tabular-nums' }}>{r.disc}</td>
                          <td style={{ padding:'6px 10px', color:'#00c087', fontVariantNumeric:'tabular-nums' }}>{r.pv}</td>
                          <td style={{ padding:'6px 10px', color:'#888', fontVariantNumeric:'tabular-nums' }}>{r.pct}</td>
                          <td style={{ padding:'6px 10px', color:'#60a5fa', fontVariantNumeric:'tabular-nums' }}>{r.cumDur}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                <p style={{ color:'#666', fontSize:11, marginTop:8, lineHeight:1.6 }}>
                  Macaulay duration is the sum of (time × PV weight) — the last row in the "Cum. Duration" column equals Mac.Dur = {fmt(result.macDur, 2)} yrs. The principal payment at maturity dominates for long-dated bonds.
                </p>
              </>
            )}

            {/* ── Tab: Rate Shock Analysis ── */}
            {activeTab === 'rateshock' && (
              <>
                <div style={{ borderLeft:'3px solid #f87171', padding:'10px 14px', background:'rgba(248,113,113,0.04)', borderRadius:'0 6px 6px 0', marginBottom:12 }}>
                  <div style={{ color:'#e8e8e8', fontWeight:600, fontSize:13, textTransform:'uppercase', letterSpacing:'0.04em' }}>Rate Shock Analysis — −300 to +300 bp</div>
                  <div style={{ color:'#888', fontSize:11, marginTop:4 }}>Actual re-priced bond vs duration and convexity approximations across the full shock range</div>
                </div>
                <Chart traces={shockTraces} layout={{ xaxis:{ title:{text:'Yield Shock (bp)',font:{color:'#666',size:11}}, zeroline:true, zerolinecolor:'#444' }, yaxis:{ title:{text:'Price ($)',font:{color:'#666',size:11}} } }} height={380} />
                <div style={{ overflowX:'auto', marginTop:20 }}>
                  <table style={{ width:'100%', borderCollapse:'collapse', fontSize:11 }}>
                    <thead>
                      <tr style={{ borderBottom:'1px solid #2a2a2a' }}>
                        {['Shock (bp)','New YTM (%)','Actual Price','ΔP Actual','ΔP Duration','ΔP Conv.Adj.','Dur. Error'].map(h => (
                          <th key={h} style={{ padding:'7px 10px', textAlign:'left', color:'#666', fontWeight:500, textTransform:'uppercase', fontSize:9, letterSpacing:'0.05em', whiteSpace:'nowrap' }}>{h}</th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {shockData.filter((_,i) => i%2===0).map(r => (
                        <tr key={r.bp} style={{ borderBottom:'1px solid #1a1a1a' }}>
                          <td style={{ padding:'6px 10px', color:shockColor(r.bp), fontWeight:600, fontVariantNumeric:'tabular-nums' }}>{r.bp>0?'+':''}{r.bp}</td>
                          <td style={{ padding:'6px 10px', color:'#aaa', fontVariantNumeric:'tabular-nums' }}>{r.newYtm}%</td>
                          <td style={{ padding:'6px 10px', color:'#e8e8e8', fontVariantNumeric:'tabular-nums' }}>{r.actual}</td>
                          <td style={{ padding:'6px 10px', color:shockColor(r.bp), fontVariantNumeric:'tabular-nums', fontWeight:600 }}>{r.dAct}</td>
                          <td style={{ padding:'6px 10px', color:shockColor(r.bp), fontVariantNumeric:'tabular-nums' }}>{r.dDur}</td>
                          <td style={{ padding:'6px 10px', color:shockColor(r.bp), fontVariantNumeric:'tabular-nums' }}>{r.dConv}</td>
                          <td style={{ padding:'6px 10px', color:'#a78bfa', fontVariantNumeric:'tabular-nums' }}>{r.durErr}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                <p style={{ color:'#666', fontSize:11, marginTop:8, lineHeight:1.6 }}>
                  Duration error = Actual ΔP − Duration ΔP. It is always positive (bonds outperform the linear estimate) because of convexity — the larger the shock, the bigger the error. This is why investors pay a premium for convexity.
                </p>
              </>
            )}

            {/* ── Tab: Rate Evolution ── */}
            {activeTab === 'evolution' && (
              <>
                <div style={{ borderLeft:'3px solid #a78bfa', padding:'10px 14px', background:'rgba(167,139,250,0.04)', borderRadius:'0 6px 6px 0', marginBottom:12 }}>
                  <div style={{ color:'#e8e8e8', fontWeight:600, fontSize:13, textTransform:'uppercase', letterSpacing:'0.04em' }}>Rate Scenario — Risk Evolution Over Time</div>
                  <div style={{ color:'#888', fontSize:11, marginTop:4 }}>How price, duration, and DV01 change quarterly as the bond approaches maturity (holding YTM constant at {fmt(result.ytm,2)}%)</div>
                </div>
                <div style={{ color:'#888', fontSize:11, marginBottom:16 }}>
                  <strong style={{color:'#aaa'}}>Pull-to-Par:</strong> As time passes, the bond price converges to face value regardless of coupon vs YTM.
                </div>
                <Chart traces={evolTraces1} layout={{ xaxis:{ title:{text:'Time elapsed (years)',font:{color:'#666',size:11}} }, yaxis:{ title:{text:'Price ($)',font:{color:'#666',size:11}} } }} height={260} />

                <div style={{ borderLeft:'3px solid #60a5fa', padding:'10px 14px', background:'rgba(96,165,250,0.04)', borderRadius:'0 6px 6px 0', margin:'24px 0 12px' }}>
                  <div style={{ color:'#e8e8e8', fontWeight:600, fontSize:12, textTransform:'uppercase', letterSpacing:'0.04em' }}>Modified Duration Decline</div>
                  <div style={{ color:'#888', fontSize:11, marginTop:4 }}>Duration decreases as the bond shortens — less price sensitivity as maturity approaches</div>
                </div>
                <Chart traces={evolTraces2} layout={{ xaxis:{ title:{text:'Time elapsed (years)',font:{color:'#666',size:11}} }, yaxis:{ title:{text:'Modified Duration',font:{color:'#666',size:11}} } }} height={260} />

                <div style={{ borderLeft:'3px solid #a78bfa', padding:'10px 14px', background:'rgba(167,139,250,0.04)', borderRadius:'0 6px 6px 0', margin:'24px 0 12px' }}>
                  <div style={{ color:'#e8e8e8', fontWeight:600, fontSize:12, textTransform:'uppercase', letterSpacing:'0.04em' }}>DV01 Dollar Risk</div>
                  <div style={{ color:'#888', fontSize:11, marginTop:4 }}>Dollar risk per basis point shrinks as both price and duration fall</div>
                </div>
                <Chart traces={evolTraces3} layout={{ xaxis:{ title:{text:'Time elapsed (years)',font:{color:'#666',size:11}} }, yaxis:{ title:{text:'DV01 ($)',font:{color:'#666',size:11}} } }} height={260} />
              </>
            )}
          </>
        )}
      </div>
    </div>
  )
}
