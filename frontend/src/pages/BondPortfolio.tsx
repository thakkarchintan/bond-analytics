import { useState, useEffect, useRef } from 'react'
import apiFetch from '../api/client'

// ── Bond math (client-side) ───────────────────────────────────────────────
function bondPrice(coupon: number, freq: number, ytm: number, matYrs: number): number {
  const n = Math.round(matYrs * freq)
  const c = coupon / freq / 100
  const y = ytm / freq / 100
  if (Math.abs(y) < 1e-12) return 100 * (1 + c * n)
  let price = 0
  for (let t = 1; t <= n; t++) price += c * 100 / Math.pow(1 + y, t)
  price += 100 / Math.pow(1 + y, n)
  return price
}

function modDuration(coupon: number, freq: number, ytm: number, matYrs: number): number {
  const n = Math.round(matYrs * freq)
  const c = coupon / freq / 100
  const y = ytm / freq / 100
  const price = bondPrice(coupon, freq, ytm, matYrs)
  if (price < 0.01) return 0
  let macD = 0
  for (let t = 1; t <= n; t++) macD += (t / freq) * c * 100 / Math.pow(1 + y, t)
  macD += (n / freq) * 100 / Math.pow(1 + y, n)
  return macD / price / (1 + y)
}

// ── Types ──────────────────────────────────────────────────────────────────
interface Position {
  id: number; name: string; face_value: number; coupon_pct: number
  freq: number; ytm_pct: number; maturity_years: number; notional: number
}
interface PositionResult extends Position {
  clean_price: number; market_value: number; mac_duration: number
  mod_duration: number; dv01: number; convexity: number; weight: number
}
interface PortfolioResponse {
  positions: PositionResult[]; total_mv: number
  portfolio_mac_duration: number; portfolio_mod_duration: number
  portfolio_dv01: number; portfolio_convexity: number
}

// ── Sovereign universe ─────────────────────────────────────────────────────
interface SovBond {
  country: string; flag: string; tenor: string
  coupon: number; freq: number; ytm: number; matYrs: number
  faceValue: number; currency: string
}
const SOVEREIGN: SovBond[] = [
  // United States
  { country:'US', flag:'🇺🇸', tenor:'2Y',  coupon:4.875, freq:2, ytm:4.80, matYrs:2,  faceValue:1e6, currency:'USD' },
  { country:'US', flag:'🇺🇸', tenor:'5Y',  coupon:4.375, freq:2, ytm:4.45, matYrs:5,  faceValue:1e6, currency:'USD' },
  { country:'US', flag:'🇺🇸', tenor:'10Y', coupon:4.250, freq:2, ytm:4.30, matYrs:10, faceValue:1e6, currency:'USD' },
  { country:'US', flag:'🇺🇸', tenor:'20Y', coupon:4.500, freq:2, ytm:4.60, matYrs:20, faceValue:1e6, currency:'USD' },
  { country:'US', flag:'🇺🇸', tenor:'30Y', coupon:4.375, freq:2, ytm:4.50, matYrs:30, faceValue:1e6, currency:'USD' },
  // Germany
  { country:'DE', flag:'🇩🇪', tenor:'2Y',  coupon:2.60, freq:1, ytm:2.50, matYrs:2,  faceValue:1e6, currency:'EUR' },
  { country:'DE', flag:'🇩🇪', tenor:'5Y',  coupon:2.30, freq:1, ytm:2.30, matYrs:5,  faceValue:1e6, currency:'EUR' },
  { country:'DE', flag:'🇩🇪', tenor:'10Y', coupon:2.50, freq:1, ytm:2.40, matYrs:10, faceValue:1e6, currency:'EUR' },
  { country:'DE', flag:'🇩🇪', tenor:'30Y', coupon:2.70, freq:1, ytm:2.70, matYrs:30, faceValue:1e6, currency:'EUR' },
  // United Kingdom
  { country:'UK', flag:'🇬🇧', tenor:'2Y',  coupon:4.50, freq:2, ytm:4.50, matYrs:2,  faceValue:1e6, currency:'GBP' },
  { country:'UK', flag:'🇬🇧', tenor:'5Y',  coupon:4.125,freq:2, ytm:4.20, matYrs:5,  faceValue:1e6, currency:'GBP' },
  { country:'UK', flag:'🇬🇧', tenor:'10Y', coupon:4.25, freq:2, ytm:4.30, matYrs:10, faceValue:1e6, currency:'GBP' },
  { country:'UK', flag:'🇬🇧', tenor:'30Y', coupon:5.00, freq:2, ytm:5.20, matYrs:30, faceValue:1e6, currency:'GBP' },
  // Japan
  { country:'JP', flag:'🇯🇵', tenor:'2Y',  coupon:0.50, freq:2, ytm:0.50, matYrs:2,  faceValue:1e8, currency:'JPY' },
  { country:'JP', flag:'🇯🇵', tenor:'10Y', coupon:1.10, freq:2, ytm:1.10, matYrs:10, faceValue:1e8, currency:'JPY' },
  { country:'JP', flag:'🇯🇵', tenor:'30Y', coupon:2.20, freq:2, ytm:2.20, matYrs:30, faceValue:1e8, currency:'JPY' },
  // France
  { country:'FR', flag:'🇫🇷', tenor:'2Y',  coupon:2.75, freq:1, ytm:2.80, matYrs:2,  faceValue:1e6, currency:'EUR' },
  { country:'FR', flag:'🇫🇷', tenor:'5Y',  coupon:2.75, freq:1, ytm:2.70, matYrs:5,  faceValue:1e6, currency:'EUR' },
  { country:'FR', flag:'🇫🇷', tenor:'10Y', coupon:3.00, freq:1, ytm:3.00, matYrs:10, faceValue:1e6, currency:'EUR' },
  // Italy
  { country:'IT', flag:'🇮🇹', tenor:'2Y',  coupon:3.25, freq:2, ytm:3.20, matYrs:2,  faceValue:1e6, currency:'EUR' },
  { country:'IT', flag:'🇮🇹', tenor:'5Y',  coupon:3.30, freq:2, ytm:3.30, matYrs:5,  faceValue:1e6, currency:'EUR' },
  { country:'IT', flag:'🇮🇹', tenor:'10Y', coupon:3.70, freq:2, ytm:3.70, matYrs:10, faceValue:1e6, currency:'EUR' },
  // Spain
  { country:'ES', flag:'🇪🇸', tenor:'2Y',  coupon:2.90, freq:1, ytm:2.90, matYrs:2,  faceValue:1e6, currency:'EUR' },
  { country:'ES', flag:'🇪🇸', tenor:'10Y', coupon:3.20, freq:1, ytm:3.20, matYrs:10, faceValue:1e6, currency:'EUR' },
  // Australia
  { country:'AU', flag:'🇦🇺', tenor:'2Y',  coupon:4.00, freq:2, ytm:4.00, matYrs:2,  faceValue:1e6, currency:'AUD' },
  { country:'AU', flag:'🇦🇺', tenor:'10Y', coupon:4.25, freq:2, ytm:4.30, matYrs:10, faceValue:1e6, currency:'AUD' },
  // Canada
  { country:'CA', flag:'🇨🇦', tenor:'2Y',  coupon:3.75, freq:2, ytm:3.70, matYrs:2,  faceValue:1e6, currency:'CAD' },
  { country:'CA', flag:'🇨🇦', tenor:'10Y', coupon:3.50, freq:2, ytm:3.60, matYrs:10, faceValue:1e6, currency:'CAD' },
  // Switzerland
  { country:'CH', flag:'🇨🇭', tenor:'10Y', coupon:0.80, freq:1, ytm:0.80, matYrs:10, faceValue:1e6, currency:'CHF' },
  // Netherlands
  { country:'NL', flag:'🇳🇱', tenor:'10Y', coupon:2.55, freq:1, ytm:2.55, matYrs:10, faceValue:1e6, currency:'EUR' },
]

// Build list of all country-tenor pairs for scenario grid
const COUNTRIES = ['US','DE','UK','JP','FR','IT','ES','AU','CA','CH','NL']
const TENORS = ['2Y','5Y','10Y','20Y','30Y']

type ShockGrid = Record<string, Record<string, number>> // country → tenor → bps

function emptyGrid(): ShockGrid {
  const g: ShockGrid = {}
  for (const c of COUNTRIES) { g[c] = {}; for (const t of TENORS) g[c][t] = 0 }
  return g
}

function applyPreset(name: string): ShockGrid {
  const g = emptyGrid()
  const bonds2Y  = ['2Y']
  const bondsLong= ['20Y','30Y']
  const all      = TENORS
  if (name === '+25') { for (const c of COUNTRIES) for (const t of all) g[c][t] = 25 }
  else if (name === '+50') { for (const c of COUNTRIES) for (const t of all) g[c][t] = 50 }
  else if (name === '+100') { for (const c of COUNTRIES) for (const t of all) g[c][t] = 100 }
  else if (name === '-25') { for (const c of COUNTRIES) for (const t of all) g[c][t] = -25 }
  else if (name === '-50') { for (const c of COUNTRIES) for (const t of all) g[c][t] = -50 }
  else if (name === '-100') { for (const c of COUNTRIES) for (const t of all) g[c][t] = -100 }
  else if (name === 'BearSteep') {
    for (const c of COUNTRIES) {
      g[c]['2Y'] = 50; g[c]['5Y'] = 65; g[c]['10Y'] = 80; g[c]['20Y'] = 90; g[c]['30Y'] = 100
    }
  } else if (name === 'BullFlat') {
    for (const c of COUNTRIES) {
      g[c]['2Y'] = -100; g[c]['5Y'] = -80; g[c]['10Y'] = -55; g[c]['20Y'] = -35; g[c]['30Y'] = -20
    }
  } else if (name === 'BearFlat') {
    for (const c of COUNTRIES) {
      g[c]['2Y'] = 100; g[c]['5Y'] = 80; g[c]['10Y'] = 55; g[c]['20Y'] = 35; g[c]['30Y'] = 20
    }
  } else if (name === 'BullSteep') {
    for (const c of COUNTRIES) {
      g[c]['2Y'] = -100; g[c]['5Y'] = -70; g[c]['10Y'] = -40; g[c]['20Y'] = -20; g[c]['30Y'] = -10
    }
  }
  void bonds2Y; void bondsLong
  return g
}

// ── Plotly chart ───────────────────────────────────────────────────────────
type PlotTrace = Record<string, unknown>
type PlotLayout = Record<string, unknown>

function Chart({ traces, layout, height = 320 }: { traces: PlotTrace[]; layout: PlotLayout; height?: number }) {
  const ref = useRef<HTMLDivElement>(null)
  useEffect(() => {
    if (!ref.current || !traces.length) return
    let cancelled = false
    import('plotly.js-dist-min').then(Plotly => {
      if (cancelled || !ref.current) return
      const base: PlotLayout = {
        paper_bgcolor:'#1a1a1a', plot_bgcolor:'#111111',
        font:{ color:'#aaa', family:'system-ui,sans-serif', size:11 },
        margin:{ t:36, r:16, b:60, l:80 },
        xaxis:{ gridcolor:'#2a2a2a', tickfont:{ color:'#777', size:10 } },
        yaxis:{ gridcolor:'#2a2a2a', tickfont:{ color:'#777', size:10 }, zerolinecolor:'#444' },
        legend:{ orientation:'h', y:1.12, x:0, font:{ color:'#aaa', size:10 }, bgcolor:'rgba(0,0,0,0)' },
        hovermode:'closest',
        hoverlabel:{ bgcolor:'#1a1a1a', bordercolor:'#f39200', font:{ color:'#e8e8e8' } },
        ...layout,
      }
      Plotly.react(ref.current!, traces as never, base as never, { responsive:true, displayModeBar:false })
    })
    return () => { cancelled = true }
  }, [traces, layout])
  return <div ref={ref} style={{ width:'100%', height }} />
}

// ── Helpers ────────────────────────────────────────────────────────────────
let _id = 1
function newPos(): Position {
  return { id: _id++, name:`Bond ${_id-1}`, face_value:1_000_000, coupon_pct:5, freq:2, ytm_pct:4.5, maturity_years:10, notional:1 }
}
const FREQ_LABELS: Record<number, string> = { 1:'Annual', 2:'Semi', 4:'Quarterly', 12:'Monthly' }
const durCol = (v: number) => v > 10 ? '#f39200' : v > 5 ? '#fbbf24' : '#00c087'
const inputStyle = { background:'#111', border:'1px solid #333', borderRadius:4, color:'#e8e8e8', padding:'4px 8px', fontSize:12, width:'100%' } as const
const fmt = (n: number, d = 2) => n.toLocaleString('en-US', { minimumFractionDigits:d, maximumFractionDigits:d })
const fmtMV = (n: number) => (Math.abs(n) >= 1e6 ? `${(n/1e6).toFixed(2)}M` : Math.abs(n) >= 1e3 ? `${(n/1e3).toFixed(0)}K` : n.toFixed(0))

// Pre-compute sovereign analytics
interface SovResult extends SovBond {
  price: number; mv: number; modDur: number; dv01: number
}
const SOV_RESULTS: SovResult[] = SOVEREIGN.map(b => {
  const price  = bondPrice(b.coupon, b.freq, b.ytm, b.matYrs)
  const mv     = price / 100 * b.faceValue
  const mDur   = modDuration(b.coupon, b.freq, b.ytm, b.matYrs)
  const dv01   = mDur * price / 100 * b.faceValue / 10000
  return { ...b, price, mv, modDur: mDur, dv01 }
})

type Tab = 'custom' | 'sovereign' | 'scenario'

// ── Main component ─────────────────────────────────────────────────────────
export default function BondPortfolio() {
  const [tab, setTab] = useState<Tab>('custom')

  // Custom portfolio state
  const [positions, setPositions] = useState<Position[]>([newPos()])
  const [result, setResult]       = useState<PortfolioResponse | null>(null)
  const [loading, setLoading]     = useState(false)
  const [error, setError]         = useState('')

  // Sovereign universe state
  const [sovFilter, setSovFilter] = useState<string>('ALL')

  // Scenario builder state
  const [shocks, setShocks]       = useState<ShockGrid>(emptyGrid())
  const [scenRan, setScenRan]     = useState(false)

  // ── Custom portfolio handlers ───────────────────────────────────────────
  function addPosition() { setPositions(p => [...p, newPos()]) }
  function removePosition(id: number) { setPositions(p => p.filter(x => x.id !== id)) }
  function update(id: number, field: keyof Position, val: string | number) {
    setPositions(p => p.map(x => x.id === id ? { ...x, [field]: val } : x))
  }
  async function analyse() {
    setLoading(true); setError('')
    try {
      const res = await apiFetch<PortfolioResponse>('/api/bond/portfolio', {
        method:'POST',
        body: JSON.stringify({ positions: positions.map(({ id: _id2, ...p }) => p) }),
      })
      setResult(res)
    } catch (e: unknown) { setError(e instanceof Error ? e.message : 'Error') }
    setLoading(false)
  }

  // ── Scenario builder helpers ────────────────────────────────────────────
  function setShock(country: string, tenor: string, val: number) {
    setShocks(prev => ({ ...prev, [country]: { ...prev[country], [tenor]: isNaN(val) ? 0 : val } }))
    setScenRan(false)
  }
  function applyScenPreset(name: string) { setShocks(applyPreset(name)); setScenRan(false) }

  // Compute scenario impact
  const scenImpacts = SOV_RESULTS.map(b => {
    const bps = shocks[b.country]?.[b.tenor] ?? 0
    const deltaYtm = bps / 10000
    const durationPnl = -b.modDur * b.price / 100 * b.faceValue * deltaYtm
    const convexity   = 0 // simplified — convexity second-order effect is small
    return { ...b, bps, deltaMV: durationPnl + convexity }
  })
  const totalDeltaMV = scenImpacts.reduce((s, x) => s + x.deltaMV, 0)
  const biggestGain  = scenImpacts.reduce((a, b) => b.deltaMV > a.deltaMV ? b : a)
  const biggestLoss  = scenImpacts.reduce((a, b) => b.deltaMV < a.deltaMV ? b : a)
  const countryDelta: Record<string, number> = {}
  for (const x of scenImpacts) countryDelta[x.country] = (countryDelta[x.country] ?? 0) + x.deltaMV
  const sortedCountries = Object.entries(countryDelta).sort((a, b) => b[1] - a[1])

  const waterfallTraces: PlotTrace[] = [{
    type:'bar', orientation:'v',
    x: sortedCountries.map(([c]) => c),
    y: sortedCountries.map(([, v]) => v / 1e3),
    marker:{ color: sortedCountries.map(([, v]) => v >= 0 ? '#00c087' : '#ff4d4d') },
    text: sortedCountries.map(([, v]) => `${v >= 0 ? '+' : ''}${fmtMV(v)}`),
    textposition:'outside',
    hovertemplate:'%{x}: %{y:.1f}K<extra></extra>',
  }]

  // ── Render ──────────────────────────────────────────────────────────────
  const TABS: { id: Tab; label: string }[] = [
    { id:'custom',   label:'Custom Portfolio' },
    { id:'sovereign',label:'Sovereign Universe' },
    { id:'scenario', label:'Scenario Builder' },
  ]

  return (
    <div className="content-wrap" style={{ maxWidth:1200 }}>
      {/* Tab bar */}
      <div style={{ display:'flex', gap:4, marginBottom:24, borderBottom:'1px solid #2a2a2a', paddingBottom:0 }}>
        {TABS.map(t => (
          <button key={t.id} onClick={() => setTab(t.id)}
            style={{ background:'transparent', border:'none', borderBottom: tab===t.id ? '2px solid #f39200' : '2px solid transparent', color: tab===t.id ? '#f39200' : '#666', padding:'8px 18px', fontSize:12, cursor:'pointer', fontWeight: tab===t.id ? 600 : 400, letterSpacing:'0.04em', textTransform:'uppercase', transition:'color 0.15s' }}>
            {t.label}
          </button>
        ))}
      </div>

      {/* ── TAB 1: Custom Portfolio ────────────────────────────────────── */}
      {tab === 'custom' && (
        <>
          <div style={{ borderLeft:'3px solid #f39200', padding:'10px 14px', background:'rgba(243,146,0,0.04)', borderRadius:'0 6px 6px 0', marginBottom:24 }}>
            <div style={{ color:'#e8e8e8', fontWeight:600, fontSize:13, textTransform:'uppercase', letterSpacing:'0.04em' }}>Custom Bond Portfolio</div>
            <div style={{ color:'#888', fontSize:11, marginTop:4 }}>Enter positions → Analyse → market value, duration, DV01, convexity, P&L sensitivity</div>
          </div>

          <div style={{ overflowX:'auto', marginBottom:16 }}>
            <table style={{ width:'100%', borderCollapse:'collapse', fontSize:12 }}>
              <thead>
                <tr style={{ borderBottom:'1px solid #2a2a2a' }}>
                  {['Name','Face Value','Coupon %','Freq','YTM %','Maturity (yrs)','Notional (×)',''].map(h => (
                    <th key={h} style={{ padding:'8px 10px', textAlign:'left', color:'#666', fontWeight:500, textTransform:'uppercase', fontSize:10, letterSpacing:'0.05em', whiteSpace:'nowrap' }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {positions.map(pos => (
                  <tr key={pos.id} style={{ borderBottom:'1px solid #1a1a1a' }}>
                    <td style={{ padding:'6px 8px' }}><input style={inputStyle} value={pos.name} onChange={e => update(pos.id,'name',e.target.value)} /></td>
                    <td style={{ padding:'6px 8px' }}><input style={inputStyle} type="number" value={pos.face_value} step={100000} onChange={e => update(pos.id,'face_value',+e.target.value)} /></td>
                    <td style={{ padding:'6px 8px' }}><input style={inputStyle} type="number" value={pos.coupon_pct} step={0.25} onChange={e => update(pos.id,'coupon_pct',+e.target.value)} /></td>
                    <td style={{ padding:'6px 8px' }}>
                      <select style={{ ...inputStyle, width:90 }} value={pos.freq} onChange={e => update(pos.id,'freq',+e.target.value)}>
                        {Object.entries(FREQ_LABELS).map(([v,l]) => <option key={v} value={+v}>{l}</option>)}
                      </select>
                    </td>
                    <td style={{ padding:'6px 8px' }}><input style={inputStyle} type="number" value={pos.ytm_pct} step={0.01} onChange={e => update(pos.id,'ytm_pct',+e.target.value)} /></td>
                    <td style={{ padding:'6px 8px' }}><input style={inputStyle} type="number" value={pos.maturity_years} step={0.5} min={0.5} onChange={e => update(pos.id,'maturity_years',+e.target.value)} /></td>
                    <td style={{ padding:'6px 8px' }}><input style={inputStyle} type="number" value={pos.notional} step={1} min={0.01} onChange={e => update(pos.id,'notional',+e.target.value)} /></td>
                    <td style={{ padding:'6px 8px' }}><button onClick={() => removePosition(pos.id)} style={{ background:'transparent', border:'none', color:'#ff4d4d', cursor:'pointer', fontSize:16, padding:'2px 6px' }}>×</button></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div style={{ display:'flex', gap:10, marginBottom:24 }}>
            <button onClick={addPosition} style={{ background:'transparent', border:'1px solid #2a2a2a', borderRadius:6, color:'#aaa', padding:'8px 16px', fontSize:12, cursor:'pointer' }}>+ Add Position</button>
            <button className="primary-button" onClick={analyse} disabled={loading || positions.length===0}>{loading ? 'Analysing…' : 'Analyse Portfolio'}</button>
          </div>

          {error && <div style={{ color:'#ff4d4d', fontSize:12, marginBottom:16 }}>Error: {error}<br /><small style={{ color:'#888' }}>Is the FastAPI backend running?</small></div>}

          {result && (
            <>
              <div className="kpi-strip" style={{ marginBottom:24 }}>
                {[
                  { label:'Total Market Value', val:'$'+result.total_mv.toLocaleString('en-US',{maximumFractionDigits:0}), color:'#f39200' },
                  { label:'Mac. Duration', val:result.portfolio_mac_duration.toFixed(2)+' yrs', color:'#60a5fa' },
                  { label:'Mod. Duration', val:result.portfolio_mod_duration.toFixed(2)+' yrs', color:'#60a5fa' },
                  { label:'Portfolio DV01', val:'$'+result.portfolio_dv01.toLocaleString('en-US',{maximumFractionDigits:0}), color:'#a78bfa' },
                  { label:'Convexity', val:result.portfolio_convexity.toFixed(2), color:'#34d399' },
                ].map(({ label, val, color }) => (
                  <div key={label} className="kpi-card">
                    <div style={{ color:'#888', fontSize:10, textTransform:'uppercase', letterSpacing:'0.06em', marginBottom:4 }}>{label}</div>
                    <div style={{ color, fontSize:18, fontWeight:700, fontVariantNumeric:'tabular-nums' }}>{val}</div>
                  </div>
                ))}
              </div>

              <div style={{ borderLeft:'3px solid #f39200', padding:'10px 14px', background:'rgba(243,146,0,0.04)', borderRadius:'0 6px 6px 0', marginBottom:12 }}>
                <div style={{ color:'#e8e8e8', fontWeight:600, fontSize:13, textTransform:'uppercase', letterSpacing:'0.04em' }}>Position Breakdown</div>
              </div>
              <div style={{ overflowX:'auto' }}>
                <table style={{ width:'100%', borderCollapse:'collapse', fontSize:12 }}>
                  <thead>
                    <tr style={{ borderBottom:'1px solid #2a2a2a' }}>
                      {['Bond','YTM','Clean Price','Market Value','Weight','Mac Dur','Mod Dur','DV01','Convexity'].map(h => (
                        <th key={h} style={{ padding:'8px 10px', textAlign:'left', color:'#666', fontWeight:500, textTransform:'uppercase', fontSize:10, letterSpacing:'0.05em', whiteSpace:'nowrap' }}>{h}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {result.positions.map((p, i) => (
                      <tr key={i} style={{ borderBottom:'1px solid #1f1f1f' }}>
                        <td style={{ padding:'8px 10px', color:'#e8e8e8', fontWeight:500 }}>{p.name}</td>
                        <td style={{ padding:'8px 10px', color:'#aaa', fontVariantNumeric:'tabular-nums' }}>{p.ytm_pct.toFixed(2)}%</td>
                        <td style={{ padding:'8px 10px', color: p.clean_price>=p.face_value?'#00c087':'#f87171', fontVariantNumeric:'tabular-nums', fontWeight:600 }}>{p.clean_price.toLocaleString('en-US',{minimumFractionDigits:2,maximumFractionDigits:2})}</td>
                        <td style={{ padding:'8px 10px', color:'#f39200', fontVariantNumeric:'tabular-nums' }}>${p.market_value.toLocaleString('en-US',{maximumFractionDigits:0})}</td>
                        <td style={{ padding:'8px 10px', color:'#888', fontVariantNumeric:'tabular-nums' }}>{(p.weight*100).toFixed(1)}%</td>
                        <td style={{ padding:'8px 10px', color:durCol(p.mac_duration), fontVariantNumeric:'tabular-nums' }}>{p.mac_duration.toFixed(2)}</td>
                        <td style={{ padding:'8px 10px', color:durCol(p.mod_duration), fontVariantNumeric:'tabular-nums' }}>{p.mod_duration.toFixed(2)}</td>
                        <td style={{ padding:'8px 10px', color:'#a78bfa', fontVariantNumeric:'tabular-nums' }}>${p.dv01.toLocaleString('en-US',{maximumFractionDigits:0})}</td>
                        <td style={{ padding:'8px 10px', color:'#34d399', fontVariantNumeric:'tabular-nums' }}>{p.convexity.toFixed(2)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              <div style={{ borderLeft:'3px solid #a78bfa', padding:'10px 14px', background:'rgba(167,139,250,0.04)', borderRadius:'0 6px 6px 0', margin:'28px 0 12px' }}>
                <div style={{ color:'#e8e8e8', fontWeight:600, fontSize:13, textTransform:'uppercase', letterSpacing:'0.04em' }}>Portfolio P&L Sensitivity</div>
                <div style={{ color:'#888', fontSize:11, marginTop:4 }}>Estimated P&L using portfolio DV01 (parallel shift)</div>
              </div>
              <div style={{ overflowX:'auto' }}>
                <table style={{ width:'100%', borderCollapse:'collapse', fontSize:12 }}>
                  <thead>
                    <tr style={{ borderBottom:'1px solid #2a2a2a' }}>
                      {['Δ Yield (bps)','Est. P&L (Duration)','Est. P&L (Dur+Convex)','% of Portfolio'].map(h => (
                        <th key={h} style={{ padding:'8px 12px', textAlign:'left', color:'#666', fontWeight:500, textTransform:'uppercase', fontSize:10, letterSpacing:'0.05em', whiteSpace:'nowrap' }}>{h}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {[-100,-50,-25,-10,10,25,50,100].map(bps => {
                      const dy = bps/10000
                      const durPnl = -result.portfolio_mod_duration * result.total_mv * dy
                      const convPnl = 0.5 * result.portfolio_convexity * result.total_mv * dy * dy
                      const total = durPnl + convPnl
                      const pct = result.total_mv > 0 ? total/result.total_mv*100 : 0
                      const clr = bps < 0 ? '#00c087' : '#ff4d4d'
                      return (
                        <tr key={bps} style={{ borderBottom:'1px solid #1f1f1f' }}>
                          <td style={{ padding:'7px 12px', color:clr, fontWeight:600, fontVariantNumeric:'tabular-nums' }}>{bps>0?'+':''}{bps}</td>
                          <td style={{ padding:'7px 12px', color:clr, fontVariantNumeric:'tabular-nums' }}>{durPnl>0?'+$':'-$'}{Math.abs(durPnl).toLocaleString('en-US',{maximumFractionDigits:0})}</td>
                          <td style={{ padding:'7px 12px', color:clr, fontVariantNumeric:'tabular-nums', fontWeight:600 }}>{total>0?'+$':'-$'}{Math.abs(total).toLocaleString('en-US',{maximumFractionDigits:0})}</td>
                          <td style={{ padding:'7px 12px', color:clr, fontVariantNumeric:'tabular-nums' }}>{pct>0?'+':''}{pct.toFixed(3)}%</td>
                        </tr>
                      )
                    })}
                  </tbody>
                </table>
              </div>
            </>
          )}
        </>
      )}

      {/* ── TAB 2: Sovereign Universe ─────────────────────────────────────── */}
      {tab === 'sovereign' && (
        <>
          <div style={{ borderLeft:'3px solid #60a5fa', padding:'10px 14px', background:'rgba(96,165,250,0.04)', borderRadius:'0 6px 6px 0', marginBottom:20 }}>
            <div style={{ color:'#e8e8e8', fontWeight:600, fontSize:13, textTransform:'uppercase', letterSpacing:'0.04em' }}>Sovereign Universe — 30 Benchmark Bonds</div>
            <div style={{ color:'#888', fontSize:11, marginTop:4 }}>Representative on-the-run sovereigns across 11 countries · yields approximate as of mid-2025 · client-side analytics</div>
          </div>

          {/* Country filter */}
          <div style={{ display:'flex', flexWrap:'wrap', gap:6, marginBottom:20 }}>
            {['ALL',...COUNTRIES].map(c => (
              <button key={c} onClick={() => setSovFilter(c)}
                style={{ background: sovFilter===c ? '#f39200' : 'transparent', border:`1px solid ${sovFilter===c?'#f39200':'#333'}`, borderRadius:4, color: sovFilter===c ? '#000' : '#888', padding:'4px 12px', fontSize:11, cursor:'pointer', fontWeight: sovFilter===c?600:400 }}>
                {c==='ALL' ? 'All Countries' : c}
              </button>
            ))}
          </div>

          {/* KPI summary */}
          <div className="kpi-strip" style={{ marginBottom:20 }}>
            {[
              { label:'Total Bonds', val:SOV_RESULTS.filter(b=>sovFilter==='ALL'||b.country===sovFilter).length.toString(), color:'#f39200' },
              { label:'Avg Yield', val: fmt(SOV_RESULTS.filter(b=>sovFilter==='ALL'||b.country===sovFilter).reduce((s,b)=>s+b.ytm,0)/SOV_RESULTS.filter(b=>sovFilter==='ALL'||b.country===sovFilter).length)+'%', color:'#60a5fa' },
              { label:'Avg Mod Duration', val: fmt(SOV_RESULTS.filter(b=>sovFilter==='ALL'||b.country===sovFilter).reduce((s,b)=>s+b.modDur,0)/SOV_RESULTS.filter(b=>sovFilter==='ALL'||b.country===sovFilter).length)+' yrs', color:'#fbbf24' },
              { label:'Total DV01', val: '$'+fmt(SOV_RESULTS.filter(b=>sovFilter==='ALL'||b.country===sovFilter).reduce((s,b)=>s+b.dv01,0),0), color:'#a78bfa' },
            ].map(({ label, val, color }) => (
              <div key={label} className="kpi-card">
                <div style={{ color:'#888', fontSize:10, textTransform:'uppercase', letterSpacing:'0.06em', marginBottom:4 }}>{label}</div>
                <div style={{ color, fontSize:18, fontWeight:700, fontVariantNumeric:'tabular-nums' }}>{val}</div>
              </div>
            ))}
          </div>

          <div style={{ overflowX:'auto' }}>
            <table style={{ width:'100%', borderCollapse:'collapse', fontSize:12 }}>
              <thead>
                <tr style={{ borderBottom:'1px solid #2a2a2a' }}>
                  {['Country','Tenor','Coupon','YTM','Clean Price','Market Value','Mod. Duration','DV01','Currency'].map(h => (
                    <th key={h} style={{ padding:'8px 10px', textAlign:'left', color:'#666', fontWeight:500, textTransform:'uppercase', fontSize:10, letterSpacing:'0.05em', whiteSpace:'nowrap' }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {SOV_RESULTS.filter(b=>sovFilter==='ALL'||b.country===sovFilter).map((b, i) => (
                  <tr key={i} style={{ borderBottom:'1px solid #1f1f1f' }}>
                    <td style={{ padding:'8px 10px', color:'#e8e8e8', fontWeight:500 }}>{b.flag} {b.country}</td>
                    <td style={{ padding:'8px 10px', color:'#f39200', fontWeight:600 }}>{b.tenor}</td>
                    <td style={{ padding:'8px 10px', color:'#aaa', fontVariantNumeric:'tabular-nums' }}>{fmt(b.coupon)}%</td>
                    <td style={{ padding:'8px 10px', color:'#60a5fa', fontVariantNumeric:'tabular-nums', fontWeight:600 }}>{fmt(b.ytm)}%</td>
                    <td style={{ padding:'8px 10px', color: b.price>=100?'#00c087':'#f87171', fontVariantNumeric:'tabular-nums' }}>{fmt(b.price)}</td>
                    <td style={{ padding:'8px 10px', color:'#aaa', fontVariantNumeric:'tabular-nums' }}>{fmtMV(b.mv)}</td>
                    <td style={{ padding:'8px 10px', color:durCol(b.modDur), fontVariantNumeric:'tabular-nums' }}>{fmt(b.modDur)}</td>
                    <td style={{ padding:'8px 10px', color:'#a78bfa', fontVariantNumeric:'tabular-nums' }}>{fmtMV(b.dv01)}</td>
                    <td style={{ padding:'8px 10px', color:'#555', fontSize:11 }}>{b.currency}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}

      {/* ── TAB 3: Scenario Builder ───────────────────────────────────────── */}
      {tab === 'scenario' && (
        <>
          <div style={{ borderLeft:'3px solid #34d399', padding:'10px 14px', background:'rgba(52,211,153,0.04)', borderRadius:'0 6px 6px 0', marginBottom:20 }}>
            <div style={{ color:'#e8e8e8', fontWeight:600, fontSize:13, textTransform:'uppercase', letterSpacing:'0.04em' }}>Yield Shock Scenario Builder</div>
            <div style={{ color:'#888', fontSize:11, marginTop:4 }}>Set per-country, per-tenor yield shifts (bps) → see impact across the sovereign universe</div>
          </div>

          {/* Preset buttons */}
          <div style={{ marginBottom:20 }}>
            <div style={{ color:'#666', fontSize:10, textTransform:'uppercase', letterSpacing:'0.06em', marginBottom:8 }}>Presets</div>
            <div style={{ display:'flex', flexWrap:'wrap', gap:6 }}>
              {[
                { id:'+25', label:'Parallel +25bp' },
                { id:'+50', label:'Parallel +50bp' },
                { id:'+100', label:'Parallel +100bp' },
                { id:'-25', label:'Parallel −25bp' },
                { id:'-50', label:'Parallel −50bp' },
                { id:'-100', label:'Parallel −100bp' },
                { id:'BearSteep', label:'Bear Steepening' },
                { id:'BullFlat', label:'Bull Flattening' },
                { id:'BearFlat', label:'Bear Flattening' },
                { id:'BullSteep', label:'Bull Steepening' },
              ].map(p => (
                <button key={p.id} onClick={() => applyScenPreset(p.id)}
                  style={{ background:'transparent', border:'1px solid #333', borderRadius:4, color:'#aaa', padding:'5px 12px', fontSize:11, cursor:'pointer' }}>
                  {p.label}
                </button>
              ))}
              <button onClick={() => { setShocks(emptyGrid()); setScenRan(false) }}
                style={{ background:'transparent', border:'1px solid #ff4d4d', borderRadius:4, color:'#ff4d4d', padding:'5px 12px', fontSize:11, cursor:'pointer' }}>
                Reset
              </button>
            </div>
          </div>

          {/* Shock grid */}
          <div style={{ overflowX:'auto', marginBottom:20 }}>
            <table style={{ borderCollapse:'collapse', fontSize:11 }}>
              <thead>
                <tr style={{ borderBottom:'1px solid #2a2a2a' }}>
                  <th style={{ padding:'8px 14px', textAlign:'left', color:'#666', fontWeight:500, textTransform:'uppercase', fontSize:10, letterSpacing:'0.05em' }}>Country</th>
                  {TENORS.map(t => (
                    <th key={t} style={{ padding:'8px 14px', textAlign:'center', color:'#666', fontWeight:500, textTransform:'uppercase', fontSize:10, letterSpacing:'0.05em', minWidth:80 }}>{t}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {COUNTRIES.map(c => {
                  const countryBonds = SOVEREIGN.filter(b => b.country === c)
                  const availTenors = new Set(countryBonds.map(b => b.tenor))
                  const flag = SOVEREIGN.find(b=>b.country===c)?.flag ?? ''
                  return (
                    <tr key={c} style={{ borderBottom:'1px solid #1a1a1a' }}>
                      <td style={{ padding:'6px 14px', color:'#e8e8e8', fontWeight:500, whiteSpace:'nowrap' }}>{flag} {c}</td>
                      {TENORS.map(t => (
                        <td key={t} style={{ padding:'4px 8px', textAlign:'center' }}>
                          {availTenors.has(t) ? (
                            <input
                              type="number" step={5}
                              value={shocks[c]?.[t] ?? 0}
                              onChange={e => setShock(c, t, parseFloat(e.target.value))}
                              style={{ width:72, background:'#111', border:`1px solid ${(shocks[c]?.[t]??0)!==0?'#f39200':'#333'}`, borderRadius:4, color: (shocks[c]?.[t]??0)>0?'#ff4d4d':(shocks[c]?.[t]??0)<0?'#00c087':'#888', padding:'3px 6px', fontSize:11, textAlign:'center', fontVariantNumeric:'tabular-nums' }}
                            />
                          ) : (
                            <span style={{ color:'#333', fontSize:11 }}>—</span>
                          )}
                        </td>
                      ))}
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>

          <button className="primary-button" onClick={() => setScenRan(true)} style={{ marginBottom:28 }}>
            Run Scenario
          </button>

          {scenRan && (
            <>
              {/* Impact KPIs */}
              <div className="kpi-strip" style={{ marginBottom:24 }}>
                {[
                  { label:'Total ΔMV', val:(totalDeltaMV>=0?'+':'')+fmtMV(totalDeltaMV), color: totalDeltaMV>=0?'#00c087':'#ff4d4d' },
                  { label:'Biggest Gain', val:`${biggestGain.flag} ${biggestGain.country} ${biggestGain.tenor}`, color:'#00c087' },
                  { label:'Gain ΔMV', val:'+'+fmtMV(biggestGain.deltaMV), color:'#00c087' },
                  { label:'Biggest Loss', val:`${biggestLoss.flag} ${biggestLoss.country} ${biggestLoss.tenor}`, color:'#ff4d4d' },
                  { label:'Loss ΔMV', val:fmtMV(biggestLoss.deltaMV), color:'#ff4d4d' },
                ].map(({ label, val, color }) => (
                  <div key={label} className="kpi-card">
                    <div style={{ color:'#888', fontSize:10, textTransform:'uppercase', letterSpacing:'0.06em', marginBottom:4 }}>{label}</div>
                    <div style={{ color, fontSize:16, fontWeight:700, fontVariantNumeric:'tabular-nums' }}>{val}</div>
                  </div>
                ))}
              </div>

              {/* Country waterfall */}
              <div style={{ borderLeft:'3px solid #34d399', padding:'10px 14px', background:'rgba(52,211,153,0.04)', borderRadius:'0 6px 6px 0', marginBottom:12 }}>
                <div style={{ color:'#e8e8e8', fontWeight:600, fontSize:13, textTransform:'uppercase', letterSpacing:'0.04em' }}>ΔMV by Country (000s local ccy)</div>
              </div>
              <Chart traces={waterfallTraces} layout={{ yaxis:{ title:{ text:'ΔMV (000s)', font:{ color:'#666', size:11 } } } }} height={280} />

              {/* Bond breakdown table */}
              <div style={{ borderLeft:'3px solid #f39200', padding:'10px 14px', background:'rgba(243,146,0,0.04)', borderRadius:'0 6px 6px 0', margin:'28px 0 12px' }}>
                <div style={{ color:'#e8e8e8', fontWeight:600, fontSize:13, textTransform:'uppercase', letterSpacing:'0.04em' }}>Bond-Level Impact</div>
                <div style={{ color:'#888', fontSize:11, marginTop:4 }}>ΔMV = −ModDur × Price × FaceValue × (Δy)</div>
              </div>
              <div style={{ overflowX:'auto' }}>
                <table style={{ width:'100%', borderCollapse:'collapse', fontSize:12 }}>
                  <thead>
                    <tr style={{ borderBottom:'1px solid #2a2a2a' }}>
                      {['Bond','Tenor','Shock (bps)','YTM','Mod. Dur','DV01','ΔMV'].map(h => (
                        <th key={h} style={{ padding:'8px 10px', textAlign:'left', color:'#666', fontWeight:500, textTransform:'uppercase', fontSize:10, letterSpacing:'0.05em', whiteSpace:'nowrap' }}>{h}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {scenImpacts.filter(b=>b.bps!==0||true).sort((a,b2)=>b2.deltaMV-a.deltaMV).map((b, i) => (
                      <tr key={i} style={{ borderBottom:'1px solid #1f1f1f', opacity: b.bps===0?0.4:1 }}>
                        <td style={{ padding:'7px 10px', color:'#e8e8e8', fontWeight:500 }}>{b.flag} {b.country}</td>
                        <td style={{ padding:'7px 10px', color:'#f39200', fontWeight:600 }}>{b.tenor}</td>
                        <td style={{ padding:'7px 10px', color: b.bps>0?'#ff4d4d':b.bps<0?'#00c087':'#555', fontVariantNumeric:'tabular-nums', fontWeight:600 }}>{b.bps>0?'+':''}{b.bps}</td>
                        <td style={{ padding:'7px 10px', color:'#aaa', fontVariantNumeric:'tabular-nums' }}>{fmt(b.ytm)}%</td>
                        <td style={{ padding:'7px 10px', color:durCol(b.modDur), fontVariantNumeric:'tabular-nums' }}>{fmt(b.modDur)}</td>
                        <td style={{ padding:'7px 10px', color:'#a78bfa', fontVariantNumeric:'tabular-nums' }}>{fmtMV(b.dv01)}</td>
                        <td style={{ padding:'7px 10px', color: b.deltaMV>=0?'#00c087':'#ff4d4d', fontVariantNumeric:'tabular-nums', fontWeight:600 }}>{b.deltaMV>=0?'+':''}{fmtMV(b.deltaMV)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </>
          )}
        </>
      )}
    </div>
  )
}
