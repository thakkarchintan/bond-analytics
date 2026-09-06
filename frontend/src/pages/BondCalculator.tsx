import { useState, useCallback } from 'react'

/* ── Bond math ───────────────────────────────────────────────────────────────── */
function bondPrice(fv: number, coupon: number, freq: number, ytm: number, periods: number): number {
  const c = (coupon / 100 / freq) * fv
  const r = ytm / 100 / freq
  if (Math.abs(r) < 1e-12) return fv + c * periods
  const pv = c * (1 - Math.pow(1 + r, -periods)) / r + fv * Math.pow(1 + r, -periods)
  return pv
}

function macaulayDuration(fv: number, coupon: number, freq: number, ytm: number, periods: number): number {
  const c = (coupon / 100 / freq) * fv
  const r = ytm / 100 / freq
  let num = 0, den = 0
  for (let t = 1; t <= periods; t++) {
    const cf = t < periods ? c : c + fv
    const pv = cf / Math.pow(1 + r, t)
    num += t * pv
    den += pv
  }
  return den > 0 ? num / den / freq : 0
}

function convexity(fv: number, coupon: number, freq: number, ytm: number, periods: number): number {
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
  // Newton-Raphson
  let y = (coupon / 100)
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

/* ── UI ──────────────────────────────────────────────────────────────────────── */
type CalcMode = 'price' | 'yield'

interface Result {
  price: number
  ytm: number
  macDur: number
  modDur: number
  dv01: number
  convex: number
  periods: number
  accrued: number
  fullPrice: number
}

const fmt = (v: number, dec = 4) => v.toFixed(dec)
const fmtCcy = (v: number) => v.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })

export default function BondCalculator() {
  const [mode, setMode] = useState<CalcMode>('price')
  const [fv, setFv]         = useState(1000)
  const [coupon, setCoupon] = useState(5)
  const [freq, setFreq]     = useState(2)
  const [ytm, setYtm]       = useState(4.5)
  const [price, setPrice]   = useState(1043.76)
  const [matYears, setMatYears] = useState(10)
  const [result, setResult] = useState<Result | null>(null)

  const calculate = useCallback(() => {
    const periods = Math.round(matYears * freq)
    let calcPrice = price
    let calcYtm   = ytm

    if (mode === 'price') {
      calcPrice = bondPrice(fv, coupon, freq, ytm, periods)
    } else {
      calcYtm = yieldFromPrice(fv, coupon, freq, price, periods)
    }

    const macDur  = macaulayDuration(fv, coupon, freq, calcYtm, periods)
    const modDur  = macDur / (1 + calcYtm / 100 / freq)
    const dv01    = modDur * calcPrice / 10000
    const convex  = convexity(fv, coupon, freq, calcYtm, periods)
    const accrued = 0 // simplified: assume settlement on coupon date
    const fullPrice = calcPrice + accrued

    setResult({ price: calcPrice, ytm: calcYtm, macDur, modDur, dv01, convex, periods, accrued, fullPrice })
  }, [mode, fv, coupon, freq, ytm, price, matYears])

  const kpiStyle = { background: '#1a1a1a', border: '1px solid #2a2a2a', borderRadius: 8, padding: '16px 20px' }
  const labelStyle = { color: '#666', fontSize: 10, textTransform: 'uppercase' as const, letterSpacing: '0.06em', marginBottom: 4 }
  const valStyle   = { color: '#f39200', fontSize: 22, fontWeight: 700, fontVariantNumeric: 'tabular-nums' as const }

  return (
    <div className="bond-layout">
      {/* ── Sidebar inputs ── */}
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
      </aside>

      {/* ── Results ── */}
      <div className="bond-main">
        <div style={{ borderLeft: '3px solid #f39200', padding: '10px 14px', background: 'rgba(243,146,0,0.04)', borderRadius: '0 6px 6px 0', marginBottom: 24 }}>
          <div style={{ color: '#e8e8e8', fontWeight: 600, fontSize: 13, textTransform: 'uppercase', letterSpacing: '0.04em' }}>Bond Calculator</div>
          <div style={{ color: '#888', fontSize: 11, marginTop: 4 }}>Price · Yield · Duration · DV01 · Convexity — client-side math, no API required</div>
        </div>

        {!result && (
          <div style={{ color: '#555', textAlign: 'center', padding: '60px 20px', fontSize: 13 }}>
            Set the inputs on the left and press <strong style={{ color: '#f39200' }}>Calculate</strong>
          </div>
        )}

        {result && (
          <>
            {/* Primary output */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))', gap: 12, marginBottom: 24 }}>
              <div style={kpiStyle}>
                <div style={labelStyle}>{mode === 'price' ? 'Clean Price' : 'YTM'}</div>
                <div style={{ ...valStyle, color: '#00c087' }}>
                  {mode === 'price' ? fmtCcy(result.price) : fmt(result.ytm, 4) + '%'}
                </div>
              </div>
              <div style={kpiStyle}>
                <div style={labelStyle}>Full Price</div>
                <div style={valStyle}>{fmtCcy(result.fullPrice)}</div>
              </div>
              <div style={kpiStyle}>
                <div style={labelStyle}>Periods</div>
                <div style={valStyle}>{result.periods}</div>
              </div>
            </div>

            {/* Risk metrics */}
            <div style={{ fontWeight: 600, fontSize: 12, textTransform: 'uppercase', letterSpacing: '0.06em', margin: '24px 0 12px', color: '#666' }}>Risk Metrics</div>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))', gap: 12, marginBottom: 28 }}>
              {[
                { label: 'Macaulay Duration', val: fmt(result.macDur, 3) + ' yrs' },
                { label: 'Modified Duration', val: fmt(result.modDur, 3) + ' yrs' },
                { label: 'DV01', val: '$' + fmt(result.dv01, 4) },
                { label: 'Convexity', val: fmt(result.convex, 3) },
              ].map(({ label, val }) => (
                <div key={label} style={kpiStyle}>
                  <div style={labelStyle}>{label}</div>
                  <div style={{ color: '#60a5fa', fontSize: 20, fontWeight: 700, fontVariantNumeric: 'tabular-nums', marginTop: 4 }}>{val}</div>
                </div>
              ))}
            </div>

            {/* P&L sensitivity table */}
            <div style={{ borderLeft: '3px solid #60a5fa', padding: '10px 14px', background: 'rgba(96,165,250,0.04)', borderRadius: '0 6px 6px 0', marginBottom: 12 }}>
              <div style={{ color: '#e8e8e8', fontWeight: 600, fontSize: 13, textTransform: 'uppercase', letterSpacing: '0.04em' }}>Price Sensitivity — ΔYield</div>
              <div style={{ color: '#888', fontSize: 11, marginTop: 4 }}>Estimated P&L per $1,000 face using duration + convexity approximation</div>
            </div>
            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 12 }}>
                <thead>
                  <tr style={{ borderBottom: '1px solid #2a2a2a' }}>
                    {['Δ Yield (bps)', 'ΔPrice (Duration)', 'ΔPrice (Dur+Convex)', '% Change'].map(h => (
                      <th key={h} style={{ padding: '8px 12px', textAlign: 'left', color: '#666', fontWeight: 500, textTransform: 'uppercase', fontSize: 10, letterSpacing: '0.05em', whiteSpace: 'nowrap' }}>{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {[-100, -50, -25, -10, -1, 1, 10, 25, 50, 100].map(bps => {
                    const dy = bps / 10000
                    const dPriceDur   = -result.modDur * result.price * dy
                    const dPriceConvex = 0.5 * result.convex * result.price * dy * dy
                    const total = dPriceDur + dPriceConvex
                    const pct   = result.price > 0 ? total / result.price * 100 : 0
                    const col   = bps < 0 ? '#00c087' : '#ff4d4d'
                    return (
                      <tr key={bps} style={{ borderBottom: '1px solid #1f1f1f' }}>
                        <td style={{ padding: '7px 12px', color: bps < 0 ? '#00c087' : '#ff4d4d', fontWeight: 600, fontVariantNumeric: 'tabular-nums' }}>{bps > 0 ? '+' : ''}{bps}</td>
                        <td style={{ padding: '7px 12px', color: col, fontVariantNumeric: 'tabular-nums' }}>{dPriceDur > 0 ? '+' : ''}{fmtCcy(dPriceDur)}</td>
                        <td style={{ padding: '7px 12px', color: col, fontVariantNumeric: 'tabular-nums', fontWeight: 600 }}>{total > 0 ? '+' : ''}{fmtCcy(total)}</td>
                        <td style={{ padding: '7px 12px', color: col, fontVariantNumeric: 'tabular-nums' }}>{pct > 0 ? '+' : ''}{pct.toFixed(3)}%</td>
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
