import { useState, useMemo } from 'react'

// ── Bond universe (mirrors BondPortfolio.py) ──────────────────────────────────
const FACE = 100_000

interface Bond {
  id: string; name: string; country: string
  coupon: number; maturity: number; ytm: number; face: number; freq: number
}

const BOND_UNIVERSE: Bond[] = [
  { id: 'US-2Y',  name: 'US Treasury 2Y',    country: 'USA',            coupon: 4.625, maturity: 2,  ytm: 4.25,  face: FACE, freq: 2 },
  { id: 'US-5Y',  name: 'US Treasury 5Y',    country: 'USA',            coupon: 4.250, maturity: 5,  ytm: 4.10,  face: FACE, freq: 2 },
  { id: 'US-10Y', name: 'US Treasury 10Y',   country: 'USA',            coupon: 4.250, maturity: 10, ytm: 4.20,  face: FACE, freq: 2 },
  { id: 'US-30Y', name: 'US Treasury 30Y',   country: 'USA',            coupon: 4.625, maturity: 30, ytm: 4.50,  face: FACE, freq: 2 },
  { id: 'DE-2Y',  name: 'German Bund 2Y',    country: 'Germany',        coupon: 2.500, maturity: 2,  ytm: 2.40,  face: FACE, freq: 1 },
  { id: 'DE-5Y',  name: 'German Bund 5Y',    country: 'Germany',        coupon: 2.250, maturity: 5,  ytm: 2.35,  face: FACE, freq: 1 },
  { id: 'DE-10Y', name: 'German Bund 10Y',   country: 'Germany',        coupon: 2.600, maturity: 10, ytm: 2.65,  face: FACE, freq: 1 },
  { id: 'DE-30Y', name: 'German Bund 30Y',   country: 'Germany',        coupon: 2.700, maturity: 30, ytm: 2.90,  face: FACE, freq: 1 },
  { id: 'UK-2Y',  name: 'UK Gilt 2Y',        country: 'United Kingdom', coupon: 4.750, maturity: 2,  ytm: 4.35,  face: FACE, freq: 2 },
  { id: 'UK-10Y', name: 'UK Gilt 10Y',       country: 'United Kingdom', coupon: 4.250, maturity: 10, ytm: 4.45,  face: FACE, freq: 2 },
  { id: 'UK-30Y', name: 'UK Gilt 30Y',       country: 'United Kingdom', coupon: 4.125, maturity: 30, ytm: 4.70,  face: FACE, freq: 2 },
  { id: 'JP-2Y',  name: 'Japan JGB 2Y',      country: 'Japan',          coupon: 0.600, maturity: 2,  ytm: 0.65,  face: FACE, freq: 2 },
  { id: 'JP-10Y', name: 'Japan JGB 10Y',     country: 'Japan',          coupon: 1.100, maturity: 10, ytm: 1.00,  face: FACE, freq: 2 },
  { id: 'JP-30Y', name: 'Japan JGB 30Y',     country: 'Japan',          coupon: 1.800, maturity: 30, ytm: 2.00,  face: FACE, freq: 2 },
  { id: 'FR-5Y',  name: 'France OAT 5Y',     country: 'France',         coupon: 2.750, maturity: 5,  ytm: 3.00,  face: FACE, freq: 1 },
  { id: 'FR-10Y', name: 'France OAT 10Y',    country: 'France',         coupon: 3.000, maturity: 10, ytm: 3.45,  face: FACE, freq: 1 },
  { id: 'IT-3Y',  name: 'Italy BTP 3Y',      country: 'Italy',          coupon: 3.500, maturity: 3,  ytm: 3.40,  face: FACE, freq: 2 },
  { id: 'IT-10Y', name: 'Italy BTP 10Y',     country: 'Italy',          coupon: 4.000, maturity: 10, ytm: 3.70,  face: FACE, freq: 2 },
  { id: 'IT-30Y', name: 'Italy BTP 30Y',     country: 'Italy',          coupon: 4.500, maturity: 30, ytm: 4.20,  face: FACE, freq: 2 },
  { id: 'CA-2Y',  name: 'Canada GoC 2Y',     country: 'Canada',         coupon: 3.750, maturity: 2,  ytm: 3.05,  face: FACE, freq: 2 },
  { id: 'CA-10Y', name: 'Canada GoC 10Y',    country: 'Canada',         coupon: 3.250, maturity: 10, ytm: 3.10,  face: FACE, freq: 2 },
  { id: 'AU-3Y',  name: 'Australia ACGB 3Y', country: 'Australia',      coupon: 3.750, maturity: 3,  ytm: 3.85,  face: FACE, freq: 2 },
  { id: 'AU-10Y', name: 'Australia ACGB 10Y',country: 'Australia',      coupon: 4.250, maturity: 10, ytm: 4.30,  face: FACE, freq: 2 },
  { id: 'IN-5Y',  name: 'India G-Sec 5Y',    country: 'India',          coupon: 7.000, maturity: 5,  ytm: 6.85,  face: FACE, freq: 2 },
  { id: 'IN-10Y', name: 'India G-Sec 10Y',   country: 'India',          coupon: 7.180, maturity: 10, ytm: 6.95,  face: FACE, freq: 2 },
  { id: 'BR-2Y',  name: 'Brazil NTN-F 2Y',   country: 'Brazil',         coupon: 10.00, maturity: 2,  ytm: 12.00, face: FACE, freq: 2 },
  { id: 'BR-5Y',  name: 'Brazil NTN-F 5Y',   country: 'Brazil',         coupon: 10.00, maturity: 5,  ytm: 12.50, face: FACE, freq: 2 },
  { id: 'BR-10Y', name: 'Brazil NTN-F 10Y',  country: 'Brazil',         coupon: 10.00, maturity: 10, ytm: 12.90, face: FACE, freq: 2 },
  { id: 'CN-5Y',  name: 'China CGB 5Y',      country: 'China',          coupon: 2.200, maturity: 5,  ytm: 2.00,  face: FACE, freq: 2 },
  { id: 'CN-10Y', name: 'China CGB 10Y',     country: 'China',          coupon: 2.400, maturity: 10, ytm: 2.20,  face: FACE, freq: 2 },
]

const BOND_BY_ID = Object.fromEntries(BOND_UNIVERSE.map(b => [b.id, b]))

// ── Bond math ─────────────────────────────────────────────────────────────────

function bondPrice(face: number, couponRate: number, maturity: number, ytm: number, freq: number): number {
  const n = Math.round(maturity * freq)
  const c = (couponRate * face) / freq
  const r = ytm / freq
  if (r === 0) return c * n + face
  const pv = c * (1 - (1 + r) ** -n) / r + face * (1 + r) ** -n
  return pv
}

function macDuration(face: number, couponRate: number, maturity: number, ytm: number, freq: number): number {
  const n = Math.round(maturity * freq)
  const c = (couponRate * face) / freq
  const r = ytm / freq
  let pv = 0, weightedTime = 0
  for (let t = 1; t <= n; t++) {
    const cf = t === n ? c + face : c
    const pvCf = cf / (1 + r) ** t
    pv += pvCf
    weightedTime += (t / freq) * pvCf
  }
  return pv === 0 ? 0 : weightedTime / pv
}

function convexity(face: number, couponRate: number, maturity: number, ytm: number, freq: number): number {
  const n = Math.round(maturity * freq)
  const c = (couponRate * face) / freq
  const r = ytm / freq
  const px = bondPrice(face, couponRate, maturity, ytm, freq)
  let cvx = 0
  for (let t = 1; t <= n; t++) {
    const cf = t === n ? c + face : c
    cvx += cf * t * (t + 1) / (1 + r) ** (t + 2)
  }
  return px === 0 ? 0 : cvx / (px * freq * freq)
}

function bondMetrics(b: Bond) {
  const c = b.coupon / 100, y = b.ytm / 100
  const px  = bondPrice(b.face, c, b.maturity, y, b.freq)
  const mac = macDuration(b.face, c, b.maturity, y, b.freq)
  const mod = mac / (1 + y / b.freq)
  const cvx = convexity(b.face, c, b.maturity, y, b.freq)
  const dv01 = mod * px * 0.0001
  return { px, mac, mod, cvx, dv01 }
}

// ── Strategy definitions ──────────────────────────────────────────────────────

const STRATEGIES = {
  Ladder: {
    emoji: '🪜', color: '#3b82f6',
    tagline: 'Equal allocation spread evenly across short, medium and long maturities.',
    useWhen: 'Steady income · no strong rate view · want to reduce reinvestment risk',
    mechanics: 'As each rung matures, proceeds roll into the long end — keeping the ladder intact. No single maturity dominates, so you\'re never fully exposed to one point on the curve.',
    watch: 'Lower convexity than Barbell. Won\'t outperform in sharp rate moves.',
  },
  Bullet: {
    emoji: '🎯', color: '#f39200',
    tagline: 'All bonds concentrated around a single target maturity date.',
    useWhen: 'Known future liability · pension payment · project funding in N years',
    mechanics: 'All bonds mature near the same date, matching a specific obligation. Immunises price risk for that horizon — but coupons face high reinvestment risk.',
    watch: 'Lowest convexity of the three. Underperforms in volatile rate environments.',
  },
  Barbell: {
    emoji: '🏋️', color: '#00c087',
    tagline: 'Short-end + long-end only — avoid the belly of the curve.',
    useWhen: 'Rate volatility expected · curve flattener/steepener bet · maximise convexity',
    mechanics: 'Short bonds provide liquidity; long bonds provide yield. Together they produce higher convexity than a Bullet of equal duration — so the portfolio benefits more from large rate moves in either direction.',
    watch: 'Underperforms Bullet when the curve stays flat and volatility is low.',
  },
} as const

type StratName = keyof typeof STRATEGIES

// ── Auto-build helpers ────────────────────────────────────────────────────────

function autoLadder(investment: number, countries: string[]): Record<string, number> {
  const buckets = [[0, 2.5], [2.5, 7.0], [7.0, 15.0], [15.0, 50.0]]
  const alloc = investment / buckets.length
  const result: Record<string, number> = {}
  for (const [lo, hi] of buckets) {
    const cands = BOND_UNIVERSE.filter(b => lo < b.maturity && b.maturity <= hi && countries.includes(b.country))
    if (!cands.length) continue
    const b = cands.find(x => x.country === 'USA') ?? cands[0]
    const { px } = bondMetrics(b)
    result[b.id] = Math.max(1, Math.round(alloc / px))
  }
  return result
}

function autoBullet(investment: number, countries: string[], target: number): Record<string, number> {
  let lo = 0, hi = 2.5
  if (target > 15) [lo, hi] = [15, 50]
  else if (target > 7) [lo, hi] = [7, 15]
  else if (target > 2.5) [lo, hi] = [2.5, 7]
  const cands = BOND_UNIVERSE
    .filter(b => lo < b.maturity && b.maturity <= hi && countries.includes(b.country))
    .sort((a, b) => Math.abs(a.maturity - target) - Math.abs(b.maturity - target))
    .slice(0, 3)
  if (!cands.length) return {}
  const perBond = investment / cands.length
  return Object.fromEntries(cands.map(b => {
    const { px } = bondMetrics(b)
    return [b.id, Math.max(1, Math.round(perBond / px))]
  }))
}

function autoBarbell(investment: number, countries: string[], shortPct: number): Record<string, number> {
  const result: Record<string, number> = {}
  for (const [lo, hi, alloc] of [[0, 2.5, investment * shortPct], [15, 50, investment * (1 - shortPct)]] as [number, number, number][]) {
    const cands = BOND_UNIVERSE.filter(b => lo < b.maturity && b.maturity <= hi && countries.includes(b.country))
    if (!cands.length) continue
    const b = cands.find(x => x.country === 'USA') ?? cands[0]
    const { px } = bondMetrics(b)
    result[b.id] = Math.max(1, Math.round(alloc / px))
  }
  return result
}

// ── Portfolio computation ─────────────────────────────────────────────────────

interface PortMetrics {
  totalMv: number; ytm: number; macDur: number; modDur: number
  conv: number; dv01: number; avgMat: number; nBonds: number
}

function computePortfolio(bondIds: Record<string, number>): { rows: (Bond & { qty: number; mv: number; weight: number; px: number; mac: number; mod: number; cvx: number; dv01: number })[]; port: PortMetrics | null } {
  const rows = Object.entries(bondIds).flatMap(([id, qty]) => {
    const b = BOND_BY_ID[id]
    if (!b || qty === 0) return []
    const m = bondMetrics(b)
    return [{ ...b, qty, mv: m.px * qty, px: m.px, mac: m.mac, mod: m.mod, cvx: m.cvx, dv01: m.dv01, weight: 0 }]
  })
  if (!rows.length) return { rows: [], port: null }
  const totalMv = rows.reduce((s, r) => s + r.mv, 0)
  rows.forEach(r => { r.weight = r.mv / totalMv })
  const port: PortMetrics = {
    totalMv,
    ytm:    rows.reduce((s, r) => s + r.ytm    * r.weight, 0),
    macDur: rows.reduce((s, r) => s + r.mac     * r.weight, 0),
    modDur: rows.reduce((s, r) => s + r.mod     * r.weight, 0),
    conv:   rows.reduce((s, r) => s + r.cvx     * r.weight, 0),
    dv01:   rows.reduce((s, r) => s + r.dv01    * r.qty,    0),
    avgMat: rows.reduce((s, r) => s + r.maturity * r.weight, 0),
    nBonds: rows.reduce((s, r) => s + r.qty, 0),
  }
  return { rows, port }
}

function approxDeltaMv(rows: ReturnType<typeof computePortfolio>['rows'], dyBps: number): number {
  const dy = dyBps / 10000
  return rows.reduce((s, r) => {
    const deltaPx = -r.mod * r.px * dy + 0.5 * r.cvx * r.px * dy * dy
    return s + deltaPx * r.qty
  }, 0)
}

// ── Components ────────────────────────────────────────────────────────────────

const ALL_COUNTRIES = [...new Set(BOND_UNIVERSE.map(b => b.country))].sort()
const SHOCK_BPS = [-200, -100, -50, -25, 25, 50, 100, 200]

function StrategyBanner({ name }: { name: StratName }) {
  const s = STRATEGIES[name]
  return (
    <div style={{ background: '#1a1a1a', border: `1px solid #2a2a2a`, borderLeft: `4px solid ${s.color}`, borderRadius: '0 8px 8px 0', padding: '12px 16px', marginBottom: 16 }}>
      <div style={{ fontSize: 13, fontWeight: 600, color: '#f0f0f0', marginBottom: 6 }}>{s.tagline}</div>
      <div style={{ fontSize: 11, color: '#888', marginBottom: 3 }}><strong style={{ color: s.color }}>Use when:</strong> {s.useWhen}</div>
      <div style={{ fontSize: 11, color: '#888', marginBottom: 3 }}><strong style={{ color: '#e0e0e0' }}>How it works:</strong> {s.mechanics}</div>
      <div style={{ fontSize: 11, color: '#ff4d4d' }}><strong>Watch out:</strong> {s.watch}</div>
    </div>
  )
}

function MetricCard({ label, value, sub, color = '#3b82f6' }: { label: string; value: string; sub?: string; color?: string }) {
  return (
    <div style={{ background: '#1a1a1a', border: '1px solid #2a2a2a', borderLeft: `3px solid ${color}`, borderRadius: 8, padding: 12 }}>
      <div style={{ fontSize: 10, color: '#888', textTransform: 'uppercase', letterSpacing: '0.1em', marginBottom: 4 }}>{label}</div>
      <div style={{ fontSize: 18, fontWeight: 700, color: '#f0f0f0' }}>{value}</div>
      {sub && <div style={{ fontSize: 10, color: '#555', marginTop: 3 }}>{sub}</div>}
    </div>
  )
}

function StrategyTab({ name, investment, countries }: { name: StratName; investment: number; countries: string[] }) {
  const s = STRATEGIES[name]
  const [bondIds, setBondIds] = useState<Record<string, number>>({})
  const [bulletTarget, setBulletTarget] = useState(10)
  const [barbellShort, setBarbellShort] = useState(50)

  const autoBuild = () => {
    if (name === 'Ladder')  setBondIds(autoLadder(investment, countries))
    if (name === 'Bullet')  setBondIds(autoBullet(investment, countries, bulletTarget))
    if (name === 'Barbell') setBondIds(autoBarbell(investment, countries, barbellShort / 100))
  }

  const available = BOND_UNIVERSE.filter(b => countries.includes(b.country))
  const { rows, port } = useMemo(() => computePortfolio(bondIds), [bondIds])

  return (
    <div>
      <StrategyBanner name={name} />

      {/* Controls */}
      <div style={{ display: 'flex', gap: 12, alignItems: 'flex-end', flexWrap: 'wrap', marginBottom: 16 }}>
        {name === 'Bullet' && (
          <div>
            <label style={{ fontSize: 11, color: '#888', display: 'block', marginBottom: 4 }}>TARGET MATURITY</label>
            <select value={bulletTarget} onChange={e => setBulletTarget(+e.target.value)}
              style={{ background: '#1a1a1a', border: '1px solid #2a2a2a', color: '#e0e0e0', padding: '6px 10px', borderRadius: 6, fontSize: 13 }}>
              {[2, 5, 10, 30].map(t => <option key={t} value={t}>{t}Y</option>)}
            </select>
          </div>
        )}
        {name === 'Barbell' && (
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <div>
              <label style={{ fontSize: 11, color: '#888', display: 'block', marginBottom: 4 }}>SHORT-END %</label>
              <input type="range" min={20} max={80} step={5} value={barbellShort}
                onChange={e => setBarbellShort(+e.target.value)} style={{ width: 120 }} />
            </div>
            <span style={{ fontSize: 12, color: '#888' }}>{barbellShort}% ≤2Y · {100 - barbellShort}% ≥30Y</span>
          </div>
        )}
        <button onClick={autoBuild} style={{
          padding: '7px 18px', borderRadius: 6, fontSize: 13, fontWeight: 600, cursor: 'pointer',
          background: s.color + '22', border: `1px solid ${s.color}`, color: s.color,
        }}>Auto-build</button>
      </div>

      {/* Manual bond picker */}
      <details style={{ marginBottom: 16 }}>
        <summary style={{ fontSize: 12, color: '#888', cursor: 'pointer', padding: '8px 0' }}>Manual Bond Selection / Override</summary>
        <div style={{ paddingTop: 10 }}>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, marginBottom: 12 }}>
            {available.map(b => {
              const sel = b.id in bondIds
              return (
                <button key={b.id} onClick={() => {
                  setBondIds(prev => {
                    const next = { ...prev }
                    if (sel) delete next[b.id]
                    else {
                      const { px } = bondMetrics(b)
                      next[b.id] = Math.max(1, Math.round(investment / available.length / px))
                    }
                    return next
                  })
                }} style={{
                  padding: '3px 10px', borderRadius: 12, fontSize: 11, cursor: 'pointer',
                  border: `1px solid ${sel ? s.color : '#2a2a2a'}`,
                  background: sel ? s.color + '22' : 'transparent',
                  color: sel ? s.color : '#555',
                }}>{b.name}</button>
              )
            })}
          </div>
          {Object.keys(bondIds).length > 0 && (
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(160px,1fr))', gap: 8 }}>
              {Object.entries(bondIds).map(([id, qty]) => (
                <div key={id}>
                  <label style={{ fontSize: 10, color: '#888', display: 'block', marginBottom: 3 }}>{BOND_BY_ID[id]?.name}</label>
                  <input type="number" min={1} value={qty}
                    onChange={e => setBondIds(prev => ({ ...prev, [id]: +e.target.value }))}
                    style={{ background: '#111', border: '1px solid #2a2a2a', color: '#e0e0e0', padding: '4px 8px', borderRadius: 6, fontSize: 12, width: '100%' }} />
                </div>
              ))}
            </div>
          )}
        </div>
      </details>

      {!port ? (
        <div style={{ color: '#888', fontSize: 13, padding: '20px 0' }}>
          Click <strong>Auto-build</strong> to generate a {name} portfolio, or manually select bonds above.
        </div>
      ) : (
        <>
          {/* Portfolio metrics */}
          <div style={{ fontSize: 12, color: '#888', marginBottom: 8 }}>
            {Object.keys(bondIds).length} ISINs · {port.nBonds} bonds · ${(port.totalMv / 1e6).toFixed(2)}M invested
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4,1fr)', gap: 10, marginBottom: 8 }}>
            <MetricCard label="Market Value"  value={`$${(port.totalMv/1e6).toFixed(2)}M`} sub={`${port.nBonds} bonds`}          color={s.color} />
            <MetricCard label="Wtd Avg YTM"   value={`${port.ytm.toFixed(3)}%`}             sub="by market value"                 color="#f39200" />
            <MetricCard label="Avg Maturity"  value={`${port.avgMat.toFixed(1)} yrs`}       sub="weighted by MV"                  color="#888" />
            <MetricCard label="Mac Duration"  value={`${port.macDur.toFixed(3)} yrs`}       sub="avg cash-flow timing"            color="#f39200" />
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3,1fr)', gap: 10, marginBottom: 20 }}>
            <MetricCard label="Mod Duration"  value={port.modDur.toFixed(3)}               sub="% Δpx per 1% Δyield"             color="#f39200" />
            <MetricCard label="DV01"          value={`$${port.dv01.toFixed(0)}`}           sub="$ per 1bp parallel shift"         color="#ff4d4d" />
            <MetricCard label="Convexity"     value={port.conv.toFixed(2)}                 sub="higher = benefits from rate moves" color="#00c087" />
          </div>

          {/* Rate shock table */}
          <div style={{ fontSize: 12, color: '#888', marginBottom: 8 }}>QUICK RATE SHOCK — parallel yield curve shift · duration + convexity approximation</div>
          <div style={{ overflowX: 'auto', marginBottom: 20 }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
              <thead>
                <tr style={{ borderBottom: '1px solid #2a2a2a' }}>
                  {['Shock (bps)', 'ΔMV ($)', 'ΔMV (%)'].map(h => (
                    <th key={h} style={{ textAlign: 'left', padding: '7px 12px', color: '#888', fontSize: 11, fontWeight: 600 }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {SHOCK_BPS.map(bp => {
                  const dmv = approxDeltaMv(rows, bp)
                  const pct = dmv / port.totalMv * 100
                  const pos = bp < 0
                  return (
                    <tr key={bp} style={{ borderBottom: '1px solid #111', background: pos ? 'rgba(0,192,135,0.04)' : 'rgba(255,77,77,0.04)' }}>
                      <td style={{ padding: '6px 12px', color: pos ? '#00c087' : '#ff4d4d' }}>{bp > 0 ? `+${bp}` : bp}</td>
                      <td style={{ padding: '6px 12px', color: pos ? '#00c087' : '#ff4d4d' }}>{dmv >= 0 ? '+' : ''}${dmv.toLocaleString('en', { maximumFractionDigits: 0 })}</td>
                      <td style={{ padding: '6px 12px', color: pos ? '#00c087' : '#ff4d4d' }}>{pct >= 0 ? '+' : ''}{pct.toFixed(3)}%</td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>

          {/* Holdings detail */}
          <details>
            <summary style={{ fontSize: 12, color: '#888', cursor: 'pointer', padding: '8px 0' }}>Holdings Detail</summary>
            <div style={{ overflowX: 'auto', paddingTop: 10 }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 12 }}>
                <thead>
                  <tr style={{ borderBottom: '1px solid #2a2a2a' }}>
                    {['Bond','Country','Mat (Y)','Cpn %','YTM %','Price','Qty','MV ($)','Wt','Mod Dur','DV01'].map(h => (
                      <th key={h} style={{ textAlign: 'left', padding: '6px 10px', color: '#888', fontSize: 10, fontWeight: 600 }}>{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {rows.map(r => (
                    <tr key={r.id} style={{ borderBottom: '1px solid #111' }}>
                      <td style={{ padding: '5px 10px', color: '#e0e0e0' }}>{r.name}</td>
                      <td style={{ padding: '5px 10px', color: '#888' }}>{r.country}</td>
                      <td style={{ padding: '5px 10px', color: '#888' }}>{r.maturity}</td>
                      <td style={{ padding: '5px 10px', color: '#888' }}>{r.coupon}%</td>
                      <td style={{ padding: '5px 10px', color: '#888' }}>{r.ytm}%</td>
                      <td style={{ padding: '5px 10px', color: '#888' }}>{r.px.toFixed(2)}</td>
                      <td style={{ padding: '5px 10px', color: '#e0e0e0' }}>{r.qty}</td>
                      <td style={{ padding: '5px 10px', color: '#e0e0e0' }}>${r.mv.toLocaleString('en', { maximumFractionDigits: 0 })}</td>
                      <td style={{ padding: '5px 10px', color: '#888' }}>{(r.weight * 100).toFixed(1)}%</td>
                      <td style={{ padding: '5px 10px', color: '#888' }}>{r.mod.toFixed(3)}</td>
                      <td style={{ padding: '5px 10px', color: '#888' }}>${r.dv01.toFixed(0)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </details>
        </>
      )}
    </div>
  )
}

function CompareTab({ investment, countries }: { investment: number; countries: string[] }) {
  const defaults = useMemo(() => ({
    Ladder:  autoLadder(investment, countries),
    Bullet:  autoBullet(investment, countries, 10),
    Barbell: autoBarbell(investment, countries, 0.5),
  }), [investment, countries])

  const portfolios = useMemo(() =>
    Object.fromEntries(
      Object.entries(defaults).map(([name, ids]) => [name, computePortfolio(ids)])
    ) as Record<StratName, ReturnType<typeof computePortfolio>>
  , [defaults])

  const shockBps = SHOCK_BPS

  return (
    <div>
      <p style={{ color: '#888', fontSize: 13, marginBottom: 16 }}>
        Auto-built defaults for each strategy at the selected investment amount.
        Customise individual strategies in their tabs, then return here to compare.
      </p>

      {/* Side-by-side metrics */}
      <div style={{ fontSize: 12, color: '#888', marginBottom: 8 }}>SIDE-BY-SIDE METRICS</div>
      <div style={{ overflowX: 'auto', marginBottom: 24 }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
          <thead>
            <tr style={{ borderBottom: '1px solid #2a2a2a' }}>
              {['Strategy','Market Value','Wtd YTM','Avg Maturity','Mac Duration','Mod Duration','Convexity','DV01 ($)'].map(h => (
                <th key={h} style={{ textAlign: 'left', padding: '8px 12px', color: '#888', fontSize: 11, fontWeight: 600 }}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {(['Ladder','Bullet','Barbell'] as StratName[]).map(name => {
              const { port } = portfolios[name]
              if (!port) return null
              const s = STRATEGIES[name]
              return (
                <tr key={name} style={{ borderBottom: '1px solid #111' }}>
                  <td style={{ padding: '7px 12px', color: s.color, fontWeight: 600 }}>{s.emoji} {name}</td>
                  <td style={{ padding: '7px 12px', color: '#e0e0e0' }}>${(port.totalMv/1e6).toFixed(2)}M</td>
                  <td style={{ padding: '7px 12px', color: '#888' }}>{port.ytm.toFixed(3)}%</td>
                  <td style={{ padding: '7px 12px', color: '#888' }}>{port.avgMat.toFixed(1)}Y</td>
                  <td style={{ padding: '7px 12px', color: '#888' }}>{port.macDur.toFixed(3)}</td>
                  <td style={{ padding: '7px 12px', color: '#888' }}>{port.modDur.toFixed(3)}</td>
                  <td style={{ padding: '7px 12px', color: '#00c087' }}>{port.conv.toFixed(2)}</td>
                  <td style={{ padding: '7px 12px', color: '#ff4d4d' }}>${port.dv01.toFixed(0)}</td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>

      {/* Rate sensitivity table */}
      <div style={{ fontSize: 12, color: '#888', marginBottom: 8 }}>RATE SENSITIVITY — ΔMV (%) by parallel shock</div>
      <div style={{ overflowX: 'auto' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
          <thead>
            <tr style={{ borderBottom: '1px solid #2a2a2a' }}>
              <th style={{ textAlign: 'left', padding: '7px 12px', color: '#888', fontSize: 11, fontWeight: 600 }}>Shock (bps)</th>
              {(['Ladder','Bullet','Barbell'] as StratName[]).map(name => (
                <th key={name} style={{ textAlign: 'left', padding: '7px 12px', color: STRATEGIES[name].color, fontSize: 11, fontWeight: 600 }}>
                  {STRATEGIES[name].emoji} {name}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {shockBps.map(bp => (
              <tr key={bp} style={{ borderBottom: '1px solid #111', background: bp < 0 ? 'rgba(0,192,135,0.03)' : 'rgba(255,77,77,0.03)' }}>
                <td style={{ padding: '6px 12px', color: bp < 0 ? '#00c087' : '#ff4d4d' }}>{bp > 0 ? `+${bp}` : bp}</td>
                {(['Ladder','Bullet','Barbell'] as StratName[]).map(name => {
                  const { rows, port } = portfolios[name]
                  if (!port) return <td key={name} style={{ padding: '6px 12px', color: '#555' }}>—</td>
                  const dmv = approxDeltaMv(rows, bp)
                  const pct = dmv / port.totalMv * 100
                  const pos = bp < 0
                  return (
                    <td key={name} style={{ padding: '6px 12px', color: pos ? '#00c087' : '#ff4d4d' }}>
                      {pct >= 0 ? '+' : ''}{pct.toFixed(3)}%
                    </td>
                  )
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

// ── Main ──────────────────────────────────────────────────────────────────────

type TabName = 'Ladder' | 'Bullet' | 'Barbell' | 'Compare'

export default function BondInvestmentStrategiesPage() {
  const [investment, setInvestment] = useState(1_000_000)
  const [countries, setCountries] = useState(['USA','Germany','United Kingdom','Japan'])
  const [activeTab, setActiveTab] = useState<TabName>('Ladder')

  const toggleCountry = (c: string) =>
    setCountries(prev => prev.includes(c) ? prev.filter(x => x !== c) : [...prev, c])

  return (
    <div className="content-wrap">
      {/* Settings bar */}
      <div style={{ display: 'flex', gap: 16, alignItems: 'flex-start', flexWrap: 'wrap', marginBottom: 20 }}>
        <div>
          <label style={{ fontSize: 11, color: '#888', display: 'block', marginBottom: 6 }}>TOTAL INVESTMENT ($)</label>
          <input type="number" value={investment} step={100_000} min={100_000}
            onChange={e => setInvestment(+e.target.value)}
            style={{ background: '#1a1a1a', border: '1px solid #2a2a2a', color: '#e0e0e0', padding: '6px 10px', borderRadius: 6, fontSize: 13, width: 180 }} />
        </div>
        <div>
          <label style={{ fontSize: 11, color: '#888', display: 'block', marginBottom: 6 }}>COUNTRIES</label>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 5 }}>
            {ALL_COUNTRIES.map(c => (
              <button key={c} onClick={() => toggleCountry(c)} style={{
                padding: '3px 10px', borderRadius: 12, fontSize: 11, cursor: 'pointer',
                border: `1px solid ${countries.includes(c) ? '#f39200' : '#2a2a2a'}`,
                background: countries.includes(c) ? 'rgba(243,146,0,0.15)' : 'transparent',
                color: countries.includes(c) ? '#f39200' : '#555',
              }}>{c}</button>
            ))}
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div style={{ display: 'flex', gap: 4, marginBottom: 20, borderBottom: '1px solid #2a2a2a' }}>
        {(['Ladder','Bullet','Barbell','Compare'] as TabName[]).map(t => {
          const s = t === 'Compare' ? null : STRATEGIES[t as StratName]
          const active = activeTab === t
          return (
            <button key={t} onClick={() => setActiveTab(t)} style={{
              padding: '8px 16px', fontSize: 13, cursor: 'pointer', border: 'none',
              borderBottom: active ? `2px solid ${s ? s.color : '#f39200'}` : '2px solid transparent',
              background: 'transparent',
              color: active ? '#f0f0f0' : '#666',
              fontWeight: active ? 600 : 400,
            }}>
              {s ? `${s.emoji} ${t}` : `⚖️ ${t}`}
            </button>
          )
        })}
      </div>

      {countries.length === 0 ? (
        <p style={{ color: '#888' }}>Select at least one country above to get started.</p>
      ) : activeTab === 'Compare' ? (
        <CompareTab investment={investment} countries={countries} />
      ) : (
        <StrategyTab name={activeTab as StratName} investment={investment} countries={countries} />
      )}
    </div>
  )
}
