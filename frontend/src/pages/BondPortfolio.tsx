import { useState } from 'react'
import apiFetch from '../api/client'

interface Position {
  id: number
  name: string
  face_value: number
  coupon_pct: number
  freq: number
  ytm_pct: number
  maturity_years: number
  notional: number
}

interface PositionResult extends Position {
  clean_price: number
  market_value: number
  mac_duration: number
  mod_duration: number
  dv01: number
  convexity: number
  weight: number
}

interface PortfolioResponse {
  positions: PositionResult[]
  total_mv: number
  portfolio_mac_duration: number
  portfolio_mod_duration: number
  portfolio_dv01: number
  portfolio_convexity: number
}

let _id = 1
function newPos(): Position {
  return { id: _id++, name: `Bond ${_id - 1}`, face_value: 1_000_000, coupon_pct: 5, freq: 2, ytm_pct: 4.5, maturity_years: 10, notional: 1 }
}

const FREQ_LABELS: Record<number, string> = { 1: 'Annual', 2: 'Semi', 4: 'Quarterly', 12: 'Monthly' }
const col = (v: number, thr1: number, thr2: number) => v > thr1 ? '#f39200' : v > thr2 ? '#fbbf24' : '#00c087'

export default function BondPortfolio() {
  const [positions, setPositions] = useState<Position[]>([newPos()])
  const [result, setResult]       = useState<PortfolioResponse | null>(null)
  const [loading, setLoading]     = useState(false)
  const [error, setError]         = useState('')

  function addPosition() { setPositions(p => [...p, newPos()]) }
  function removePosition(id: number) { setPositions(p => p.filter(x => x.id !== id)) }
  function update(id: number, field: keyof Position, val: string | number) {
    setPositions(p => p.map(x => x.id === id ? { ...x, [field]: val } : x))
  }

  async function analyse() {
    setLoading(true); setError('')
    try {
      const res = await apiFetch<PortfolioResponse>('/api/bond/portfolio', {
        method: 'POST',
        body: JSON.stringify({ positions: positions.map(({ id: _id, ...p }) => p) }),
      })
      setResult(res)
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Error')
    }
    setLoading(false)
  }

  const inputStyle = { background: '#111', border: '1px solid #333', borderRadius: 4, color: '#e8e8e8', padding: '4px 8px', fontSize: 12, width: '100%' }

  return (
    <div className="content-wrap" style={{ maxWidth: 1100 }}>
      <div style={{ borderLeft: '3px solid #f39200', padding: '10px 14px', background: 'rgba(243,146,0,0.04)', borderRadius: '0 6px 6px 0', marginBottom: 24 }}>
        <div style={{ color: '#e8e8e8', fontWeight: 600, fontSize: 13, textTransform: 'uppercase', letterSpacing: '0.04em' }}>Bond Portfolio Analytics</div>
        <div style={{ color: '#888', fontSize: 11, marginTop: 4 }}>Enter positions → Analyse → get market value, duration, DV01, convexity</div>
      </div>

      {/* Position editor */}
      <div style={{ overflowX: 'auto', marginBottom: 16 }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 12 }}>
          <thead>
            <tr style={{ borderBottom: '1px solid #2a2a2a' }}>
              {['Name', 'Face Value', 'Coupon %', 'Freq', 'YTM %', 'Maturity (yrs)', 'Notional (×)', ''].map(h => (
                <th key={h} style={{ padding: '8px 10px', textAlign: 'left', color: '#666', fontWeight: 500, textTransform: 'uppercase', fontSize: 10, letterSpacing: '0.05em', whiteSpace: 'nowrap' }}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {positions.map(pos => (
              <tr key={pos.id} style={{ borderBottom: '1px solid #1a1a1a' }}>
                <td style={{ padding: '6px 8px' }}>
                  <input style={inputStyle} value={pos.name} onChange={e => update(pos.id, 'name', e.target.value)} />
                </td>
                <td style={{ padding: '6px 8px' }}>
                  <input style={inputStyle} type="number" value={pos.face_value} step={100000} onChange={e => update(pos.id, 'face_value', +e.target.value)} />
                </td>
                <td style={{ padding: '6px 8px' }}>
                  <input style={inputStyle} type="number" value={pos.coupon_pct} step={0.25} onChange={e => update(pos.id, 'coupon_pct', +e.target.value)} />
                </td>
                <td style={{ padding: '6px 8px' }}>
                  <select style={{ ...inputStyle, width: 90 }} value={pos.freq} onChange={e => update(pos.id, 'freq', +e.target.value)}>
                    {Object.entries(FREQ_LABELS).map(([v, l]) => <option key={v} value={+v}>{l}</option>)}
                  </select>
                </td>
                <td style={{ padding: '6px 8px' }}>
                  <input style={inputStyle} type="number" value={pos.ytm_pct} step={0.01} onChange={e => update(pos.id, 'ytm_pct', +e.target.value)} />
                </td>
                <td style={{ padding: '6px 8px' }}>
                  <input style={inputStyle} type="number" value={pos.maturity_years} step={0.5} min={0.5} onChange={e => update(pos.id, 'maturity_years', +e.target.value)} />
                </td>
                <td style={{ padding: '6px 8px' }}>
                  <input style={inputStyle} type="number" value={pos.notional} step={1} min={0.01} onChange={e => update(pos.id, 'notional', +e.target.value)} />
                </td>
                <td style={{ padding: '6px 8px' }}>
                  <button onClick={() => removePosition(pos.id)} style={{ background: 'transparent', border: 'none', color: '#ff4d4d', cursor: 'pointer', fontSize: 16, padding: '2px 6px' }}>×</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div style={{ display: 'flex', gap: 10, marginBottom: 24 }}>
        <button onClick={addPosition} style={{ background: 'transparent', border: '1px solid #2a2a2a', borderRadius: 6, color: '#aaa', padding: '8px 16px', fontSize: 12, cursor: 'pointer' }}>
          + Add Position
        </button>
        <button className="primary-button" onClick={analyse} disabled={loading || positions.length === 0}>
          {loading ? 'Analysing…' : 'Analyse Portfolio'}
        </button>
      </div>

      {error && <div style={{ color: '#ff4d4d', fontSize: 12, marginBottom: 16 }}>Error: {error}<br /><small style={{ color: '#888' }}>Is the FastAPI backend running?</small></div>}

      {result && (
        <>
          {/* Portfolio KPIs */}
          <div className="kpi-strip" style={{ marginBottom: 24 }}>
            {[
              { label: 'Total Market Value', val: '$' + result.total_mv.toLocaleString('en-US', { maximumFractionDigits: 0 }), color: '#f39200' },
              { label: 'Mac. Duration', val: result.portfolio_mac_duration.toFixed(2) + ' yrs', color: '#60a5fa' },
              { label: 'Mod. Duration', val: result.portfolio_mod_duration.toFixed(2) + ' yrs', color: '#60a5fa' },
              { label: 'Portfolio DV01', val: '$' + result.portfolio_dv01.toLocaleString('en-US', { maximumFractionDigits: 0 }), color: '#a78bfa' },
              { label: 'Convexity', val: result.portfolio_convexity.toFixed(2), color: '#34d399' },
            ].map(({ label, val, color }) => (
              <div key={label} className="kpi-card">
                <div style={{ color: '#888', fontSize: 10, textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 4 }}>{label}</div>
                <div style={{ color, fontSize: 18, fontWeight: 700, fontVariantNumeric: 'tabular-nums' }}>{val}</div>
              </div>
            ))}
          </div>

          {/* Position breakdown */}
          <div style={{ borderLeft: '3px solid #f39200', padding: '10px 14px', background: 'rgba(243,146,0,0.04)', borderRadius: '0 6px 6px 0', marginBottom: 12 }}>
            <div style={{ color: '#e8e8e8', fontWeight: 600, fontSize: 13, textTransform: 'uppercase', letterSpacing: '0.04em' }}>Position Breakdown</div>
          </div>
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 12 }}>
              <thead>
                <tr style={{ borderBottom: '1px solid #2a2a2a' }}>
                  {['Bond', 'YTM', 'Clean Price', 'Market Value', 'Weight', 'Mac Dur', 'Mod Dur', 'DV01', 'Convexity'].map(h => (
                    <th key={h} style={{ padding: '8px 10px', textAlign: 'left', color: '#666', fontWeight: 500, textTransform: 'uppercase', fontSize: 10, letterSpacing: '0.05em', whiteSpace: 'nowrap' }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {result.positions.map((p, i) => (
                  <tr key={i} style={{ borderBottom: '1px solid #1f1f1f' }}>
                    <td style={{ padding: '8px 10px', color: '#e8e8e8', fontWeight: 500 }}>{p.name}</td>
                    <td style={{ padding: '8px 10px', color: '#aaa', fontVariantNumeric: 'tabular-nums' }}>{p.ytm_pct.toFixed(2)}%</td>
                    <td style={{ padding: '8px 10px', color: p.clean_price >= p.face_value ? '#00c087' : '#f87171', fontVariantNumeric: 'tabular-nums', fontWeight: 600 }}>
                      {p.clean_price.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                    </td>
                    <td style={{ padding: '8px 10px', color: '#f39200', fontVariantNumeric: 'tabular-nums' }}>
                      ${p.market_value.toLocaleString('en-US', { maximumFractionDigits: 0 })}
                    </td>
                    <td style={{ padding: '8px 10px', color: '#888', fontVariantNumeric: 'tabular-nums' }}>{(p.weight * 100).toFixed(1)}%</td>
                    <td style={{ padding: '8px 10px', color: col(p.mac_duration, 10, 5), fontVariantNumeric: 'tabular-nums' }}>{p.mac_duration.toFixed(2)}</td>
                    <td style={{ padding: '8px 10px', color: col(p.mod_duration, 10, 5), fontVariantNumeric: 'tabular-nums' }}>{p.mod_duration.toFixed(2)}</td>
                    <td style={{ padding: '8px 10px', color: '#a78bfa', fontVariantNumeric: 'tabular-nums' }}>${p.dv01.toLocaleString('en-US', { maximumFractionDigits: 0 })}</td>
                    <td style={{ padding: '8px 10px', color: '#34d399', fontVariantNumeric: 'tabular-nums' }}>{p.convexity.toFixed(2)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* P&L sensitivity strip */}
          <div style={{ borderLeft: '3px solid #a78bfa', padding: '10px 14px', background: 'rgba(167,139,250,0.04)', borderRadius: '0 6px 6px 0', margin: '28px 0 12px' }}>
            <div style={{ color: '#e8e8e8', fontWeight: 600, fontSize: 13, textTransform: 'uppercase', letterSpacing: '0.04em' }}>Portfolio P&L Sensitivity</div>
            <div style={{ color: '#888', fontSize: 11, marginTop: 4 }}>Estimated P&L using portfolio DV01 (parallel shift)</div>
          </div>
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 12 }}>
              <thead>
                <tr style={{ borderBottom: '1px solid #2a2a2a' }}>
                  {['Δ Yield (bps)', 'Est. P&L (Duration)', 'Est. P&L (Dur+Convex)', '% of Portfolio'].map(h => (
                    <th key={h} style={{ padding: '8px 12px', textAlign: 'left', color: '#666', fontWeight: 500, textTransform: 'uppercase', fontSize: 10, letterSpacing: '0.05em', whiteSpace: 'nowrap' }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {[-100, -50, -25, -10, 10, 25, 50, 100].map(bps => {
                  const dy       = bps / 10000
                  const durPnl   = -result.portfolio_mod_duration * result.total_mv * dy
                  const convPnl  = 0.5 * result.portfolio_convexity * result.total_mv * dy * dy
                  const total    = durPnl + convPnl
                  const pct      = result.total_mv > 0 ? total / result.total_mv * 100 : 0
                  const clr      = bps < 0 ? '#00c087' : '#ff4d4d'
                  return (
                    <tr key={bps} style={{ borderBottom: '1px solid #1f1f1f' }}>
                      <td style={{ padding: '7px 12px', color: clr, fontWeight: 600, fontVariantNumeric: 'tabular-nums' }}>{bps > 0 ? '+' : ''}{bps}</td>
                      <td style={{ padding: '7px 12px', color: clr, fontVariantNumeric: 'tabular-nums' }}>{durPnl > 0 ? '+' : ''}${Math.abs(durPnl).toLocaleString('en-US', { maximumFractionDigits: 0 })}</td>
                      <td style={{ padding: '7px 12px', color: clr, fontVariantNumeric: 'tabular-nums', fontWeight: 600 }}>{total > 0 ? '+' : ''}${Math.abs(total).toLocaleString('en-US', { maximumFractionDigits: 0 })}</td>
                      <td style={{ padding: '7px 12px', color: clr, fontVariantNumeric: 'tabular-nums' }}>{pct > 0 ? '+' : ''}{pct.toFixed(3)}%</td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        </>
      )}
    </div>
  )
}
