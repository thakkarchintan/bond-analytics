import { useState, useEffect, useRef, useCallback } from 'react'
import { fetchColumns, fetchSeries } from '../api/bond'

type PlotTrace = Record<string, unknown>
type PlotLayout = Record<string, unknown>

function Chart({ traces, layout, height = 500 }: { traces: PlotTrace[]; layout: PlotLayout; height?: number }) {
  const ref = useRef<HTMLDivElement>(null)
  useEffect(() => {
    if (!ref.current || !traces.length) return
    let cancelled = false
    import('plotly.js-dist-min').then(Plotly => {
      if (cancelled || !ref.current) return
      const base: PlotLayout = {
        paper_bgcolor: '#1a1a1a', plot_bgcolor: '#111111',
        font: { color: '#aaa', family: 'system-ui,sans-serif', size: 11 },
        margin: { t: 36, r: 16, b: 80, l: 80 },
        ...layout,
      }
      Plotly.react(ref.current!, traces as never, base as never, { responsive: true, displayModeBar: false })
    })
    return () => { cancelled = true }
  }, [traces, layout])
  return <div ref={ref} style={{ width: '100%', height }} />
}

const ALL_COLS = ['US2Y','US5Y','US10Y','US30Y','FGBSY','FGBMY','FGBLY','UK10Y','AUS10Y','CAD10Y','Gold (USD)','SPX','DIJA','BTC (USD)']
const DEFAULT_COLS = ['US2Y','US5Y','US10Y','US30Y','FGBSY','FGBMY','FGBLY','UK10Y']

function pearson(xs: number[], ys: number[]): number {
  const n = xs.length
  if (n < 2) return NaN
  const mx = xs.reduce((a,b)=>a+b,0)/n
  const my = ys.reduce((a,b)=>a+b,0)/n
  let num=0, dx=0, dy=0
  for (let i=0;i<n;i++) { num+=(xs[i]-mx)*(ys[i]-my); dx+=(xs[i]-mx)**2; dy+=(ys[i]-my)**2 }
  return Math.sqrt(dx*dy) > 0 ? num/Math.sqrt(dx*dy) : NaN
}

export default function Heatmap() {
  const [allCols, setAllCols] = useState<string[]>(ALL_COLS)
  const [selected, setSelected] = useState<string[]>(DEFAULT_COLS)
  const [startYear, setStartYear] = useState(2018)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [corrMatrix, setCorrMatrix] = useState<number[][]>([])
  const [cols, setCols] = useState<string[]>([])

  useEffect(() => {
    fetchColumns().then(c => setAllCols(c.filter(x => ALL_COLS.includes(x) || c.includes(x)))).catch(() => {})
  }, [])

  const compute = useCallback(async () => {
    if (selected.length < 2) return
    setLoading(true); setError('')
    try {
      const start = `${startYear}-01-01`
      const data = await fetchSeries(selected, start)
      // Align by date
      const dateSets = selected.map(c => new Set((data[c] ?? []).map(p => p.date)))
      const commonDates = [...dateSets[0]].filter(d => dateSets.every(s => s.has(d))).sort()
      const matrix: number[][] = Array.from({ length: selected.length }, (_, i) =>
        Array.from({ length: selected.length }, (__, j) => {
          const xs = commonDates.map(d => data[selected[i]]?.find(p => p.date === d)?.value ?? NaN).filter(v => !isNaN(v))
          const ys = commonDates.map(d => data[selected[j]]?.find(p => p.date === d)?.value ?? NaN).filter(v => !isNaN(v))
          const minLen = Math.min(xs.length, ys.length)
          return pearson(xs.slice(0, minLen), ys.slice(0, minLen))
        })
      )
      setCorrMatrix(matrix)
      setCols([...selected])
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Error fetching data')
    }
    setLoading(false)
  }, [selected, startYear])

  const heatTrace: PlotTrace = corrMatrix.length ? {
    type: 'heatmap',
    z: corrMatrix,
    x: cols,
    y: cols,
    colorscale: [
      [0,   '#ff4d4d'],
      [0.5, '#111111'],
      [1,   '#00c087'],
    ],
    zmin: -1, zmax: 1,
    text: corrMatrix.map(row => row.map(v => isNaN(v) ? '' : v.toFixed(2))),
    texttemplate: '%{text}',
    textfont: { color: '#e8e8e8', size: 11 },
    hovertemplate: '%{y} × %{x}: %{z:.3f}<extra></extra>',
    showscale: true,
    colorbar: { tickfont: { color: '#aaa', size: 10 }, outlinecolor: '#2a2a2a', bgcolor: '#1a1a1a' },
  } : {} as PlotTrace

  return (
    <div className="bond-layout">
      <aside className="bond-sidebar">
        <div className="ctrl-section">
          <div className="ctrl-label">START YEAR</div>
          <input type="number" className="ctrl-input" value={startYear} min={1994} max={2025} onChange={e => setStartYear(+e.target.value)} />
        </div>

        <div className="ctrl-section">
          <div className="ctrl-label">INSTRUMENTS</div>
          {allCols.map(c => (
            <label key={c} style={{ display:'flex', alignItems:'center', gap:8, padding:'3px 0', cursor:'pointer', fontSize:12, color: selected.includes(c) ? '#f39200' : '#666' }}>
              <input type="checkbox" checked={selected.includes(c)} onChange={e => setSelected(s => e.target.checked ? [...s,c] : s.filter(x=>x!==c))} style={{ accentColor:'#f39200' }} />
              {c}
            </label>
          ))}
        </div>

        <button className="primary-button" style={{ width:'100%', marginTop:8 }} onClick={compute} disabled={loading || selected.length < 2}>
          {loading ? 'Computing…' : 'Compute Correlations'}
        </button>
        {selected.length < 2 && <div style={{ color:'#555', fontSize:11, marginTop:6 }}>Select at least 2 instruments</div>}
      </aside>

      <div className="bond-main">
        <div style={{ borderLeft:'3px solid #f39200', padding:'10px 14px', background:'rgba(243,146,0,0.04)', borderRadius:'0 6px 6px 0', marginBottom:12 }}>
          <div style={{ color:'#e8e8e8', fontWeight:600, fontSize:13, textTransform:'uppercase', letterSpacing:'0.04em' }}>Correlation Heatmap</div>
          <div style={{ color:'#888', fontSize:11, marginTop:4 }}>Pearson correlation of daily returns · select instruments + date range → Compute</div>
        </div>

        {error && <div style={{ color:'#ff4d4d', padding:'12px 0', fontSize:12 }}>Error: {error}</div>}

        {!corrMatrix.length && !loading && (
          <div style={{ color:'#555', textAlign:'center', padding:'60px 20px', fontSize:13 }}>
            Select instruments on the left and press <strong style={{ color:'#f39200' }}>Compute Correlations</strong>
          </div>
        )}

        {loading && (
          <div style={{ color:'#aaa', textAlign:'center', padding:80 }}>
            <div style={{ width:32, height:32, border:'3px solid #f39200', borderTopColor:'transparent', borderRadius:'50%', animation:'spin 0.8s linear infinite', margin:'0 auto 16px' }}/>
            Fetching series and computing correlations…
          </div>
        )}

        {corrMatrix.length > 0 && !loading && (
          <>
            <Chart
              traces={[heatTrace]}
              layout={{
                xaxis: { tickangle: -30, tickfont: { color:'#aaa', size:10 } },
                yaxis: { tickfont: { color:'#aaa', size:10 }, autorange:'reversed' },
                margin: { t:20, r:80, b:100, l:100 },
              }}
              height={Math.max(400, cols.length * 52 + 120)}
            />

            {/* Correlation table */}
            <div style={{ marginTop:24, overflowX:'auto' }}>
              <table style={{ borderCollapse:'collapse', fontSize:11 }}>
                <thead>
                  <tr style={{ borderBottom:'1px solid #2a2a2a' }}>
                    <th style={{ padding:'6px 10px', color:'#555', fontWeight:400 }}></th>
                    {cols.map(c => <th key={c} style={{ padding:'6px 10px', color:'#888', fontWeight:500, textAlign:'center', whiteSpace:'nowrap', fontSize:10 }}>{c}</th>)}
                  </tr>
                </thead>
                <tbody>
                  {cols.map((row, i) => (
                    <tr key={row} style={{ borderBottom:'1px solid #1a1a1a' }}>
                      <td style={{ padding:'6px 10px', color:'#888', fontSize:10, fontWeight:500, whiteSpace:'nowrap' }}>{row}</td>
                      {cols.map((_, j) => {
                        const v = corrMatrix[i][j]
                        const clr = isNaN(v) ? '#555' : v > 0.7 ? '#00c087' : v > 0.3 ? '#6ee7b7' : v < -0.7 ? '#ff4d4d' : v < -0.3 ? '#fca5a5' : '#888'
                        return (
                          <td key={j} style={{ padding:'6px 10px', textAlign:'center', color: i===j ? '#f39200' : clr, fontVariantNumeric:'tabular-nums', fontWeight: i===j ? 700 : 400 }}>
                            {isNaN(v) ? '—' : v.toFixed(2)}
                          </td>
                        )
                      })}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </>
        )}
      </div>
    </div>
  )
}
