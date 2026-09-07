import { useState, useEffect, useRef, useMemo } from 'react'

// ── Bond math ─────────────────────────────────────────────────────────────
function bondPrice(coupon: number, freq: number, ytm: number, matYrs: number): number {
  const n = Math.round(matYrs * freq)
  const c = coupon / freq / 100
  const y = ytm / freq / 100
  if (Math.abs(y) < 1e-12) return 100 * (1 + c * n)
  let p = 0
  for (let t = 1; t <= n; t++) p += c * 100 / Math.pow(1 + y, t)
  return p + 100 / Math.pow(1 + y, n)
}

function macDuration(coupon: number, freq: number, ytm: number, matYrs: number): number {
  const n = Math.round(matYrs * freq)
  const c = coupon / freq / 100
  const y = ytm / freq / 100
  const p = bondPrice(coupon, freq, ytm, matYrs)
  if (p < 0.01) return 0
  let mac = 0
  for (let t = 1; t <= n; t++) mac += (t / freq) * c * 100 / Math.pow(1 + y, t)
  mac += (n / freq) * 100 / Math.pow(1 + y, n)
  return mac / p
}

function modDuration(coupon: number, freq: number, ytm: number, matYrs: number): number {
  const y = ytm / freq / 100
  return macDuration(coupon, freq, ytm, matYrs) / (1 + y)
}

function convexity(coupon: number, freq: number, ytm: number, matYrs: number): number {
  const n = Math.round(matYrs * freq)
  const c = coupon / freq / 100
  const y = ytm / freq / 100
  const p = bondPrice(coupon, freq, ytm, matYrs)
  if (p < 0.01) return 0
  let cx = 0
  for (let t = 1; t <= n; t++) {
    cx += (t * (t + 1)) * c * 100 / Math.pow(1 + y, t + 2)
  }
  cx += (n * (n + 1)) * 100 / Math.pow(1 + y, n + 2)
  return cx / (p * freq * freq)
}

// ── Plotly chart ───────────────────────────────────────────────────────────
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
        margin: { t: 36, r: 16, b: 48, l: 68 },
        xaxis: { gridcolor: '#2a2a2a', tickfont: { color: '#777', size: 10 } },
        yaxis: { gridcolor: '#2a2a2a', tickfont: { color: '#777', size: 10 }, zerolinecolor: '#444' },
        legend: { orientation: 'h', y: 1.14, x: 0, font: { color: '#aaa', size: 10 }, bgcolor: 'rgba(0,0,0,0)' },
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

type TabId = 'priceyield' | 'cashflows' | 'rateshock'
const TABS: { id: TabId; label: string }[] = [
  { id: 'priceyield', label: 'Price-Yield Curve' },
  { id: 'cashflows',  label: 'Cash Flows' },
  { id: 'rateshock',  label: 'Rate Shock Analysis' },
]

const FREQ_LABELS: Record<number, string> = { 1: 'Annual', 2: 'Semi-Annual', 4: 'Quarterly' }

export default function BondSimulator() {
  const [coupon,   setCoupon]   = useState(5.0)
  const [freq,     setFreq]     = useState(2)
  const [ytm,      setYtm]      = useState(4.5)
  const [matYrs,   setMatYrs]   = useState(10)
  const [faceVal,  setFaceVal]  = useState(1_000_000)
  const [activeTab, setActiveTab] = useState<TabId>('priceyield')

  // ── Derived analytics (recompute whenever inputs change) ─────────────────
  const analytics = useMemo(() => {
    const price   = bondPrice(coupon, freq, ytm, matYrs)
    const mac     = macDuration(coupon, freq, ytm, matYrs)
    const modDur  = modDuration(coupon, freq, ytm, matYrs)
    const cx      = convexity(coupon, freq, ytm, matYrs)
    const dv01    = modDur * price / 10000
    return { price, mac, modDur, cx, dv01 }
  }, [coupon, freq, ytm, matYrs])

  // ── Price-Yield curve data ────────────────────────────────────────────────
  const pyData = useMemo(() => {
    const minY = Math.max(0.1, ytm - 8)
    const maxY = ytm + 8
    const N = 200
    const ytms = Array.from({ length: N }, (_, i) => minY + (maxY - minY) * i / (N - 1))
    const prices    = ytms.map(y => bondPrice(coupon, freq, y, matYrs))
    const durApprox = ytms.map(y => {
      const dy = y - ytm
      return analytics.price * (1 - analytics.modDur * dy)
    })
    const cxApprox = ytms.map(y => {
      const dy = y - ytm
      return analytics.price * (1 - analytics.modDur * dy + 0.5 * analytics.cx * dy * dy)
    })
    return { ytms, prices, durApprox, cxApprox }
  }, [coupon, freq, ytm, matYrs, analytics])

  const pyTraces: PlotTrace[] = [
    { type: 'scatter', mode: 'lines', name: 'Actual Price',
      x: pyData.ytms, y: pyData.prices, line: { color: '#f39200', width: 2 } },
    { type: 'scatter', mode: 'lines', name: 'Duration Approx.',
      x: pyData.ytms, y: pyData.durApprox, line: { color: '#60a5fa', width: 1.5, dash: 'dash' } },
    { type: 'scatter', mode: 'lines', name: 'Convexity Adjusted',
      x: pyData.ytms, y: pyData.cxApprox, line: { color: '#34d399', width: 1.5, dash: 'dot' } },
    { type: 'scatter', mode: 'markers', name: 'Current YTM',
      x: [ytm], y: [analytics.price],
      marker: { color: '#ff4d4d', size: 10, symbol: 'circle', line: { color: '#fff', width: 1.5 } },
      showlegend: true },
  ]

  // ── Cash flow data ────────────────────────────────────────────────────────
  const cfData = useMemo(() => {
    const n = Math.round(matYrs * freq)
    const c = coupon / freq / 100 * 100  // coupon per period per 100 face
    const y = ytm / freq / 100
    const times: number[] = []
    const cfCoupons: number[] = []
    const cfPrincipals: number[] = []
    const cfPVs: number[] = []
    for (let t = 1; t <= n; t++) {
      const time = t / freq
      const principal = t === n ? 100 : 0
      const cf = c + principal
      const pv = cf / Math.pow(1 + y, t)
      times.push(time)
      cfCoupons.push(c)
      cfPrincipals.push(principal)
      cfPVs.push(pv)
    }
    return { times, cfCoupons, cfPrincipals, cfPVs }
  }, [coupon, freq, ytm, matYrs])

  const cfTraces: PlotTrace[] = [
    { type: 'bar', name: 'Coupon CF',
      x: cfData.times, y: cfData.cfCoupons,
      marker: { color: '#f39200', opacity: 0.8 } },
    { type: 'bar', name: 'Principal CF',
      x: cfData.times, y: cfData.cfPrincipals,
      marker: { color: '#60a5fa', opacity: 0.8 } },
    { type: 'scatter', mode: 'markers+lines', name: 'PV of CF',
      x: cfData.times, y: cfData.cfPVs,
      marker: { color: '#34d399', size: 7 },
      line: { color: '#34d399', width: 1, dash: 'dot' },
      yaxis: 'y2' },
  ]
  const cfLayout: PlotLayout = {
    barmode: 'stack',
    xaxis: { title: { text: 'Years to Payment', font: { color: '#666', size: 11 } } },
    yaxis: { title: { text: 'Cash Flow (per 100 face)', font: { color: '#666', size: 11 } } },
    yaxis2: { title: { text: 'PV (per 100 face)', font: { color: '#666', size: 11 } }, overlaying: 'y', side: 'right', gridcolor: 'transparent', tickfont: { color: '#34d399', size: 10 } },
  }

  // ── Rate shock table + chart ──────────────────────────────────────────────
  const shockBps = Array.from({ length: 25 }, (_, i) => -300 + i * 25)
  const shockRows = shockBps.map(bps => {
    const newYtm    = ytm + bps / 100
    const newPrice  = bondPrice(coupon, freq, newYtm, matYrs)
    const dy        = bps / 10000
    const durPnl    = -analytics.modDur * analytics.price * dy
    const cxPnl     = 0.5 * analytics.cx * analytics.price * dy * dy
    const totalPnl  = durPnl + cxPnl
    const actualPnl = newPrice - analytics.price
    const pctChg    = (newPrice - analytics.price) / analytics.price * 100
    return { bps, newYtm, newPrice, durPnl, cxPnl, totalPnl, actualPnl, pctChg }
  })

  const shockTraces: PlotTrace[] = [
    { type: 'scatter', mode: 'lines', name: 'Actual ΔPrice',
      x: shockBps, y: shockRows.map(r => r.actualPnl),
      line: { color: '#f39200', width: 2 } },
    { type: 'scatter', mode: 'lines', name: 'Duration Approx.',
      x: shockBps, y: shockRows.map(r => r.durPnl),
      line: { color: '#60a5fa', width: 1.5, dash: 'dash' } },
    { type: 'scatter', mode: 'lines', name: 'Dur + Convexity',
      x: shockBps, y: shockRows.map(r => r.totalPnl),
      line: { color: '#34d399', width: 1.5, dash: 'dot' } },
  ]

  const fmtN = (n: number, d = 2) => n.toFixed(d)
  const fmtMV = (n: number) => {
    const abs = Math.abs(n) * faceVal / 100
    return (n >= 0 ? '+' : '-') + '$' + abs.toLocaleString('en-US', { maximumFractionDigits: 0 })
  }

  return (
    <div className="bond-layout">
      {/* ── Sidebar ── */}
      <aside className="bond-sidebar">
        <div className="ctrl-section">
          <div className="ctrl-label">BOND PARAMETERS</div>
          <div style={{ display: 'grid', gap: 8 }}>
            <div>
              <div style={{ color: '#555', fontSize: 10, textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: 3 }}>Coupon %</div>
              <input type="number" className="ctrl-input" value={coupon} step={0.25} min={0} onChange={e => setCoupon(+e.target.value)} />
            </div>
            <div>
              <div style={{ color: '#555', fontSize: 10, textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: 3 }}>YTM %</div>
              <input type="number" className="ctrl-input" value={ytm} step={0.01} min={0.01} onChange={e => setYtm(+e.target.value)} />
            </div>
            <div>
              <div style={{ color: '#555', fontSize: 10, textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: 3 }}>Maturity (yrs)</div>
              <input type="number" className="ctrl-input" value={matYrs} step={0.5} min={0.5} onChange={e => setMatYrs(+e.target.value)} />
            </div>
            <div>
              <div style={{ color: '#555', fontSize: 10, textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: 3 }}>Frequency</div>
              <select className="ctrl-select" value={freq} onChange={e => setFreq(+e.target.value)}>
                {Object.entries(FREQ_LABELS).map(([v, l]) => <option key={v} value={+v}>{l}</option>)}
              </select>
            </div>
            <div>
              <div style={{ color: '#555', fontSize: 10, textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: 3 }}>Face Value</div>
              <input type="number" className="ctrl-input" value={faceVal} step={100000} min={1000} onChange={e => setFaceVal(+e.target.value)} />
            </div>
          </div>
        </div>

        {/* Live metrics */}
        <div className="ctrl-section">
          <div className="ctrl-label">LIVE METRICS</div>
          <div style={{ display: 'grid', gap: 6 }}>
            {[
              { label: 'Clean Price', val: fmtN(analytics.price) + ' / 100', color: analytics.price >= 100 ? '#00c087' : '#f87171' },
              { label: 'Mac. Duration', val: fmtN(analytics.mac) + ' yrs', color: '#60a5fa' },
              { label: 'Mod. Duration', val: fmtN(analytics.modDur) + ' yrs', color: '#60a5fa' },
              { label: 'DV01 (per 100)', val: '$' + fmtN(analytics.dv01 * faceVal / 100, 0), color: '#a78bfa' },
              { label: 'Convexity', val: fmtN(analytics.cx), color: '#34d399' },
            ].map(({ label, val, color }) => (
              <div key={label} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', padding: '4px 0', borderBottom: '1px solid #1a1a1a' }}>
                <span style={{ color: '#555', fontSize: 10, textTransform: 'uppercase', letterSpacing: '0.04em' }}>{label}</span>
                <span style={{ color, fontSize: 12, fontWeight: 600, fontVariantNumeric: 'tabular-nums' }}>{val}</span>
              </div>
            ))}
          </div>
        </div>

        <div style={{ background: 'rgba(243,146,0,0.06)', border: '1px solid rgba(243,146,0,0.15)', borderRadius: 6, padding: '10px 12px', fontSize: 11, color: '#888', lineHeight: 1.55 }}>
          Charts update live as you adjust inputs — no calculate button needed.
        </div>
      </aside>

      {/* ── Main ── */}
      <div className="bond-main">
        {/* Header */}
        <div style={{ borderLeft: '3px solid #f39200', padding: '10px 14px', background: 'rgba(243,146,0,0.04)', borderRadius: '0 6px 6px 0', marginBottom: 20 }}>
          <div style={{ color: '#e8e8e8', fontWeight: 600, fontSize: 13, textTransform: 'uppercase', letterSpacing: '0.04em' }}>Bond Price Explorer</div>
          <div style={{ color: '#888', fontSize: 11, marginTop: 4 }}>
            Interactive price-yield relationship · cash flow timeline · rate shock analysis · client-side, live updates
          </div>
        </div>

        {/* Tab bar */}
        <div style={{ display: 'flex', gap: 4, marginBottom: 20, borderBottom: '1px solid #2a2a2a' }}>
          {TABS.map(t => (
            <button key={t.id} onClick={() => setActiveTab(t.id)}
              style={{ background: 'transparent', border: 'none', borderBottom: activeTab === t.id ? '2px solid #f39200' : '2px solid transparent', color: activeTab === t.id ? '#f39200' : '#555', padding: '7px 16px', fontSize: 11, cursor: 'pointer', fontWeight: activeTab === t.id ? 600 : 400, letterSpacing: '0.05em', textTransform: 'uppercase', transition: 'color 0.15s' }}>
              {t.label}
            </button>
          ))}
        </div>

        {/* ── Price-Yield Curve ─────────────────────────────────────────── */}
        {activeTab === 'priceyield' && (
          <>
            <div style={{ display: 'flex', gap: 12, marginBottom: 16, flexWrap: 'wrap' }}>
              {[
                { label: 'Current Price', val: fmtN(analytics.price), suffix: '/ 100', color: '#f39200' },
                { label: 'Mod. Duration', val: fmtN(analytics.modDur), suffix: 'yrs', color: '#60a5fa' },
                { label: 'Convexity', val: fmtN(analytics.cx), suffix: '', color: '#34d399' },
                { label: 'YTM Range', val: `${fmtN(Math.max(0.1, ytm-8))}% – ${fmtN(ytm+8)}%`, suffix: '', color: '#aaa' },
              ].map(({ label, val, suffix, color }) => (
                <div key={label} style={{ background: '#1a1a1a', border: '1px solid #2a2a2a', borderRadius: 6, padding: '8px 14px', flex: '1 1 120px' }}>
                  <div style={{ color: '#555', fontSize: 10, textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: 3 }}>{label}</div>
                  <div style={{ color, fontSize: 15, fontWeight: 700, fontVariantNumeric: 'tabular-nums' }}>{val} <span style={{ color: '#555', fontSize: 11, fontWeight: 400 }}>{suffix}</span></div>
                </div>
              ))}
            </div>
            <Chart traces={pyTraces} layout={{
              xaxis: { title: { text: 'YTM (%)', font: { color: '#666', size: 11 } }, ticksuffix: '%' },
              yaxis: { title: { text: 'Clean Price (per 100)', font: { color: '#666', size: 11 } } },
            }} height={380} />
            <div style={{ marginTop: 12, padding: '10px 14px', background: '#141414', borderRadius: 6, fontSize: 11, color: '#666', lineHeight: 1.65 }}>
              <strong style={{ color: '#aaa' }}>Reading the chart:</strong> The orange curve shows the actual (convex) price-yield relationship.
              The blue dashed line is the linear duration approximation — accurate only for small yield changes.
              The green dotted curve adds the convexity correction, which accounts for the curve's non-linearity and
              is a better approximation for large moves. The red dot marks your current YTM and price.
            </div>
          </>
        )}

        {/* ── Cash Flows ────────────────────────────────────────────────── */}
        {activeTab === 'cashflows' && (
          <>
            <div style={{ display: 'flex', gap: 12, marginBottom: 16, flexWrap: 'wrap' }}>
              {[
                { label: 'Total Cash Flows', val: '$' + ((coupon / freq / 100 * Math.round(matYrs * freq) + 1) * faceVal).toLocaleString('en-US', { maximumFractionDigits: 0 }), color: '#f39200' },
                { label: 'Clean Price', val: '$' + (analytics.price / 100 * faceVal).toLocaleString('en-US', { maximumFractionDigits: 0 }), color: '#60a5fa' },
                { label: 'Mac. Duration', val: fmtN(analytics.mac) + ' yrs', color: '#a78bfa' },
                { label: 'Periods', val: Math.round(matYrs * freq).toString(), color: '#aaa' },
              ].map(({ label, val, color }) => (
                <div key={label} style={{ background: '#1a1a1a', border: '1px solid #2a2a2a', borderRadius: 6, padding: '8px 14px', flex: '1 1 120px' }}>
                  <div style={{ color: '#555', fontSize: 10, textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: 3 }}>{label}</div>
                  <div style={{ color, fontSize: 15, fontWeight: 700, fontVariantNumeric: 'tabular-nums' }}>{val}</div>
                </div>
              ))}
            </div>
            <Chart traces={cfTraces} layout={cfLayout} height={340} />
            <div style={{ marginTop: 20, overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 12 }}>
                <thead>
                  <tr style={{ borderBottom: '1px solid #2a2a2a' }}>
                    {['Period', 'Year', 'Coupon CF', 'Principal', 'Total CF', 'Disc. Factor', 'PV', '% of Price', 'Cum. Dur (yrs)'].map(h => (
                      <th key={h} style={{ padding: '7px 10px', textAlign: 'left', color: '#555', fontWeight: 500, textTransform: 'uppercase', fontSize: 9, letterSpacing: '0.05em', whiteSpace: 'nowrap' }}>{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {(() => {
                    const n = Math.round(matYrs * freq)
                    const y = ytm / freq / 100
                    let cumDur = 0
                    return cfData.times.map((t, i) => {
                      const cf     = cfData.cfCoupons[i] + cfData.cfPrincipals[i]
                      const df     = 1 / Math.pow(1 + y, i + 1)
                      const pv     = cfData.cfPVs[i]
                      const pctPV  = analytics.price > 0 ? pv / analytics.price * 100 : 0
                      cumDur += pctPV / 100 * t
                      return (
                        <tr key={i} style={{ borderBottom: '1px solid #1a1a1a', background: i === n - 1 ? 'rgba(243,146,0,0.04)' : 'transparent' }}>
                          <td style={{ padding: '6px 10px', color: '#888', fontVariantNumeric: 'tabular-nums' }}>{i + 1}</td>
                          <td style={{ padding: '6px 10px', color: '#aaa', fontVariantNumeric: 'tabular-nums' }}>{fmtN(t)}</td>
                          <td style={{ padding: '6px 10px', color: '#f39200', fontVariantNumeric: 'tabular-nums' }}>{fmtN(cfData.cfCoupons[i])}</td>
                          <td style={{ padding: '6px 10px', color: '#60a5fa', fontVariantNumeric: 'tabular-nums' }}>{cfData.cfPrincipals[i] > 0 ? fmtN(cfData.cfPrincipals[i]) : '—'}</td>
                          <td style={{ padding: '6px 10px', color: '#e8e8e8', fontWeight: 500, fontVariantNumeric: 'tabular-nums' }}>{fmtN(cf)}</td>
                          <td style={{ padding: '6px 10px', color: '#555', fontVariantNumeric: 'tabular-nums' }}>{df.toFixed(4)}</td>
                          <td style={{ padding: '6px 10px', color: '#34d399', fontVariantNumeric: 'tabular-nums' }}>{fmtN(pv)}</td>
                          <td style={{ padding: '6px 10px', color: '#777', fontVariantNumeric: 'tabular-nums' }}>{pctPV.toFixed(2)}%</td>
                          <td style={{ padding: '6px 10px', color: '#a78bfa', fontVariantNumeric: 'tabular-nums' }}>{fmtN(cumDur, 3)}</td>
                        </tr>
                      )
                    })
                  })()}
                </tbody>
              </table>
            </div>
          </>
        )}

        {/* ── Rate Shock Analysis ───────────────────────────────────────── */}
        {activeTab === 'rateshock' && (
          <>
            <Chart traces={shockTraces} layout={{
              xaxis: { title: { text: 'Yield Shock (bps)', font: { color: '#666', size: 11 } }, ticksuffix: 'bp' },
              yaxis: { title: { text: 'ΔPrice (per 100 face)', font: { color: '#666', size: 11 } }, zerolinecolor: '#444' },
              shapes: [{ type: 'line', x0: 0, x1: 0, y0: 0, y1: 1, yref: 'paper', line: { color: '#333', width: 1, dash: 'dot' } }],
            }} height={320} />

            <div style={{ marginTop: 20, overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 11 }}>
                <thead>
                  <tr style={{ borderBottom: '1px solid #2a2a2a' }}>
                    {['Δ bps', 'New YTM', 'Price', 'ΔPrice', 'Dur. P&L', 'Cx. P&L', 'Total P&L (MV)', '% Change'].map(h => (
                      <th key={h} style={{ padding: '7px 10px', textAlign: 'left', color: '#555', fontWeight: 500, textTransform: 'uppercase', fontSize: 9, letterSpacing: '0.05em', whiteSpace: 'nowrap' }}>{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {shockRows.map(r => {
                    const clr = r.bps < 0 ? '#00c087' : r.bps > 0 ? '#ff4d4d' : '#aaa'
                    return (
                      <tr key={r.bps} style={{ borderBottom: '1px solid #1a1a1a', background: r.bps === 0 ? 'rgba(255,255,255,0.02)' : 'transparent', fontWeight: r.bps === 0 ? 600 : 400 }}>
                        <td style={{ padding: '5px 10px', color: clr, fontVariantNumeric: 'tabular-nums', fontWeight: 600 }}>{r.bps > 0 ? '+' : ''}{r.bps}</td>
                        <td style={{ padding: '5px 10px', color: '#aaa', fontVariantNumeric: 'tabular-nums' }}>{fmtN(r.newYtm)}%</td>
                        <td style={{ padding: '5px 10px', color: '#e8e8e8', fontVariantNumeric: 'tabular-nums' }}>{fmtN(r.newPrice)}</td>
                        <td style={{ padding: '5px 10px', color: clr, fontVariantNumeric: 'tabular-nums' }}>{r.actualPnl > 0 ? '+' : ''}{fmtN(r.actualPnl)}</td>
                        <td style={{ padding: '5px 10px', color: '#60a5fa', fontVariantNumeric: 'tabular-nums' }}>{fmtMV(r.durPnl)}</td>
                        <td style={{ padding: '5px 10px', color: '#34d399', fontVariantNumeric: 'tabular-nums' }}>{fmtMV(r.cxPnl)}</td>
                        <td style={{ padding: '5px 10px', color: clr, fontVariantNumeric: 'tabular-nums', fontWeight: 600 }}>{fmtMV(r.actualPnl)}</td>
                        <td style={{ padding: '5px 10px', color: clr, fontVariantNumeric: 'tabular-nums' }}>{r.pctChg > 0 ? '+' : ''}{fmtN(r.pctChg)}%</td>
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
