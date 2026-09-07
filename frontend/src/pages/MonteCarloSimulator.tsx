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
        margin: { t: 36, r: 16, b: 44, l: 70 },
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

interface SimResult {
  init_price: number
  mean_price: number
  std_price: number
  p5_price: number
  p25_price: number
  p50_price: number
  p75_price: number
  p95_price: number
  var95: number
  cvar95: number
  n_paths: number
  horizon_years: number
  step_labels: number[]
  ytm_paths: number[][]
  histogram: Array<{ price: number; count: number }>
}

export default function BondSimulator() {
  const [fv,         setFv]        = useState(1_000_000)
  const [coupon,     setCoupon]    = useState(5)
  const [freq,       setFreq]      = useState(2)
  const [ytm,        setYtm]       = useState(4.5)
  const [matYears,   setMatYears]  = useState(10)
  const [horizYears, setHorizYears] = useState(1)
  const [nPaths,     setNPaths]    = useState(500)
  const [vol,        setVol]       = useState(1.0)
  const [drift,      setDrift]     = useState(0.0)
  const [result,     setResult]    = useState<SimResult | null>(null)
  const [loading,    setLoading]   = useState(false)
  const [error,      setError]     = useState('')

  async function run() {
    setLoading(true); setError('')
    try {
      const res = await apiFetch<SimResult>('/api/bond/simulate', {
        method: 'POST',
        body: JSON.stringify({
          face_value: fv, coupon_pct: coupon, freq, ytm_pct: ytm,
          maturity_years: matYears, horizon_years: horizYears,
          n_paths: nPaths, vol_pct: vol, drift_pct: drift,
        }),
      })
      setResult(res)
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Error')
    }
    setLoading(false)
  }

  // Build chart traces from result
  const pathTraces: PlotTrace[] = result ? result.ytm_paths.map((path, i) => ({
    type: 'scatter', mode: 'lines', showlegend: false,
    x: result.step_labels, y: path,
    line: { color: `rgba(243,146,0,${i === 0 ? 0.6 : 0.08})`, width: 1 },
  })) : []

  const histTrace: PlotTrace = result ? {
    type: 'bar', name: 'Price distribution',
    x: result.histogram.map(h => h.price),
    y: result.histogram.map(h => h.count),
    marker: { color: '#f39200', opacity: 0.75 },
  } : {} as PlotTrace

  const percentileLines: PlotTrace[] = result ? [
    { type:'scatter', mode:'lines', name:'5th/95th', x:[result.p5_price,result.p5_price], y:[0, Math.max(...result.histogram.map(h=>h.count))], line:{color:'#ff4d4d',width:2,dash:'dot'} },
    { type:'scatter', mode:'lines', name:'Median',   x:[result.p50_price,result.p50_price], y:[0, Math.max(...result.histogram.map(h=>h.count))], line:{color:'#00c087',width:2,dash:'dash'} },
    { type:'scatter', mode:'lines', name:'95th',     x:[result.p95_price,result.p95_price], y:[0, Math.max(...result.histogram.map(h=>h.count))], line:{color:'#60a5fa',width:2,dash:'dot'}, showlegend:false },
  ] as PlotTrace[] : []

  const fmtCcy = (v: number) => v.toLocaleString('en-US', { minimumFractionDigits: 0, maximumFractionDigits: 0 })
  const fmtPct = (v: number) => (v >= 0 ? '+' : '') + (v / (result?.init_price || 1) * 100).toFixed(2) + '%'

  return (
    <div className="bond-layout">
      <aside className="bond-sidebar">
        <div className="ctrl-section">
          <div className="ctrl-label">BOND</div>
          <div style={{ display: 'grid', gap: 6 }}>
            {[
              { label: 'Face Value', val: fv,       set: setFv,       step: 100000 },
              { label: 'Coupon %',   val: coupon,    set: setCoupon,   step: 0.25   },
              { label: 'YTM %',      val: ytm,       set: setYtm,      step: 0.01   },
              { label: 'Mat. Years', val: matYears,  set: setMatYears, step: 0.5    },
            ].map(({ label, val, set, step }) => (
              <div key={label}>
                <div style={{ color: '#555', fontSize: 10, textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: 2 }}>{label}</div>
                <input type="number" className="ctrl-input" value={val} step={step} onChange={e => set(+e.target.value)} />
              </div>
            ))}
            <div>
              <div style={{ color: '#555', fontSize: 10, textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: 2 }}>Frequency</div>
              <select className="ctrl-select" value={freq} onChange={e => setFreq(+e.target.value)}>
                <option value={1}>Annual</option>
                <option value={2}>Semi-Annual</option>
                <option value={4}>Quarterly</option>
              </select>
            </div>
          </div>
        </div>

        <div className="ctrl-section">
          <div className="ctrl-label">SIMULATION</div>
          <div style={{ display: 'grid', gap: 6 }}>
            {[
              { label: 'Horizon (yrs)',    val: horizYears, set: setHorizYears, step: 0.25, min: 0.25 },
              { label: 'Paths',            val: nPaths,     set: setNPaths,     step: 100,  min: 50   },
              { label: 'Yield Vol % p.a.', val: vol,        set: setVol,        step: 0.1,  min: 0.1  },
              { label: 'Drift % p.a.',     val: drift,      set: setDrift,      step: 0.1,  min: -5   },
            ].map(({ label, val, set, step, min }) => (
              <div key={label}>
                <div style={{ color: '#555', fontSize: 10, textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: 2 }}>{label}</div>
                <input type="number" className="ctrl-input" value={val} step={step} min={min} onChange={e => set(+e.target.value)} />
              </div>
            ))}
          </div>
        </div>

        <button className="primary-button" style={{ width: '100%' }} onClick={run} disabled={loading}>
          {loading ? 'Simulating…' : `Run ${nPaths} Paths`}
        </button>
      </aside>

      <div className="bond-main">
        <div style={{ borderLeft: '3px solid #f39200', padding: '10px 14px', background: 'rgba(243,146,0,0.04)', borderRadius: '0 6px 6px 0', marginBottom: 20 }}>
          <div style={{ color: '#e8e8e8', fontWeight: 600, fontSize: 13, textTransform: 'uppercase', letterSpacing: '0.04em' }}>Monte Carlo Bond Simulator</div>
          <div style={{ color: '#888', fontSize: 11, marginTop: 4 }}>GBM yield simulation · lognormal model · price distribution at horizon</div>
        </div>

        {error && <div style={{ color: '#ff4d4d', fontSize: 12, marginBottom: 12 }}>Error: {error}<br /><small style={{ color: '#888' }}>Is the FastAPI backend running?</small></div>}

        {!result && !loading && (
          <div style={{ color: '#555', textAlign: 'center', padding: '60px 20px', fontSize: 13 }}>
            Configure the bond and simulation parameters, then press <strong style={{ color: '#f39200' }}>Run</strong>
          </div>
        )}

        {loading && (
          <div style={{ color: '#aaa', textAlign: 'center', padding: 60 }}>
            <div style={{ width: 32, height: 32, border: '3px solid #f39200', borderTopColor: 'transparent', borderRadius: '50%', animation: 'spin 0.8s linear infinite', margin: '0 auto 16px' }} />
            Running {nPaths} Monte Carlo paths…
          </div>
        )}

        {result && !loading && (
          <>
            {/* KPI strip */}
            <div className="kpi-strip" style={{ marginBottom: 20 }}>
              {[
                { label: 'Initial Price',  val: '$' + fmtCcy(result.init_price),  color: '#aaa' },
                { label: 'Mean Price',     val: '$' + fmtCcy(result.mean_price),  color: '#f39200' },
                { label: 'Median (P50)',   val: '$' + fmtCcy(result.p50_price),   color: '#00c087' },
                { label: 'Std Dev',        val: '$' + fmtCcy(result.std_price),   color: '#60a5fa' },
                { label: 'VaR 95% (P&L)', val: '$' + fmtCcy(result.var95),        color: '#ff4d4d' },
                { label: 'CVaR 95%',       val: '$' + fmtCcy(result.cvar95),       color: '#f87171' },
              ].map(({ label, val, color }) => (
                <div key={label} className="kpi-card">
                  <div style={{ color: '#888', fontSize: 10, textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 4 }}>{label}</div>
                  <div style={{ color, fontSize: 16, fontWeight: 700, fontVariantNumeric: 'tabular-nums' }}>{val}</div>
                </div>
              ))}
            </div>

            {/* Percentile table */}
            <div style={{ display: 'flex', gap: 8, marginBottom: 24, flexWrap: 'wrap' }}>
              {[5, 25, 50, 75, 95].map(p => {
                const key = `p${p}_price` as keyof SimResult
                const v = result[key] as number
                const pnl = v - result.init_price
                return (
                  <div key={p} style={{ flex: '1 1 120px', background: '#1a1a1a', border: '1px solid #2a2a2a', borderRadius: 6, padding: '10px 14px' }}>
                    <div style={{ color: '#555', fontSize: 10, textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 4 }}>P{p}</div>
                    <div style={{ color: '#e8e8e8', fontSize: 15, fontWeight: 700, fontVariantNumeric: 'tabular-nums' }}>${fmtCcy(v)}</div>
                    <div style={{ color: pnl >= 0 ? '#00c087' : '#ff4d4d', fontSize: 11, marginTop: 2 }}>{fmtPct(pnl)}</div>
                  </div>
                )
              })}
            </div>

            {/* YTM path fan */}
            <div style={{ borderLeft: '3px solid #f39200', padding: '10px 14px', background: 'rgba(243,146,0,0.04)', borderRadius: '0 6px 6px 0', marginBottom: 12 }}>
              <div style={{ color: '#e8e8e8', fontWeight: 600, fontSize: 13, textTransform: 'uppercase', letterSpacing: '0.04em' }}>Simulated Yield Paths</div>
              <div style={{ color: '#888', fontSize: 11, marginTop: 4 }}>{result.n_paths} paths · {result.horizon_years}yr horizon · vol {vol}% p.a.</div>
            </div>
            <Chart traces={pathTraces} layout={{ yaxis: { ticksuffix: '%', title: { text: 'YTM %', font: { color: '#666', size: 11 } } }, xaxis: { title: { text: 'Years', font: { color: '#666', size: 11 } } } }} />

            {/* Price distribution */}
            <div style={{ borderLeft: '3px solid #34d399', padding: '10px 14px', background: 'rgba(52,211,153,0.04)', borderRadius: '0 6px 6px 0', margin: '28px 0 12px' }}>
              <div style={{ color: '#e8e8e8', fontWeight: 600, fontSize: 13, textTransform: 'uppercase', letterSpacing: '0.04em' }}>Price Distribution at Horizon</div>
              <div style={{ color: '#888', fontSize: 11, marginTop: 4 }}>Red = 5th percentile (VaR) · Green = median · Blue = 95th percentile</div>
            </div>
            <Chart
              traces={[histTrace, ...percentileLines].filter(t => Object.keys(t).length > 0)}
              layout={{ barmode: 'overlay', xaxis: { title: { text: 'Bond Price', font: { color: '#666', size: 11 } } }, yaxis: { title: { text: 'Count', font: { color: '#666', size: 11 } } } }}
              height={300}
            />
          </>
        )}
      </div>
    </div>
  )
}
