import { useEffect, useState, useMemo } from 'react'

interface BCRow {
  Date: string
  Country: string
  ISO: string
  Indicator: 'BCI' | 'CCI' | 'CLI'
  Value: number
}

const INDICATOR_META = {
  BCI: { label: 'Business Confidence Index', desc: 'Surveys of industrial sentiment. Above 100 = businesses more optimistic than long-run average.' },
  CCI: { label: 'Consumer Confidence Index', desc: 'Household economic expectations. Above 100 = consumers more confident than long-run average.' },
  CLI: { label: 'Composite Leading Indicator', desc: 'Aggregates multiple early-warning series. Designed to turn 6–9 months before the economy.' },
}

const IND_COLORS: Record<string, string> = { BCI: '#3b82f6', CCI: '#f39200', CLI: '#00c087' }

const COUNTRY_COLORS = [
  '#60a5fa','#f87171','#34d399','#fbbf24','#a78bfa',
  '#fb923c','#22d3ee','#f472b6','#818cf8','#a3e635',
  '#e879f9','#4ade80','#38bdf8','#facc15','#94a3b8',
  '#cbd5e1','#7dd3fc','#86efac','#fde68a','#f472b6',
]

const DEFAULT_COUNTRIES = ['United States','Euro Area','China','Germany','Japan','United Kingdom','South Korea','OECD Total']

type Tab = 'snapshot' | 'timeseries' | 'heatmap' | 'deepdive'

export default function GlobalBusinessCyclePage() {
  const [rows, setRows] = useState<BCRow[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [indicator, setIndicator] = useState<'BCI'|'CCI'|'CLI'>('CLI')
  const [tab, setTab] = useState<Tab>('snapshot')
  const [fromYear, setFromYear] = useState(2005)
  const [selectedCountries, setSelectedCountries] = useState<string[]>(DEFAULT_COUNTRIES)
  const [deepDiveCountry, setDeepDiveCountry] = useState('United States')

  useEffect(() => {
    fetch('/api/macro/oecd-bc')
      .then(r => r.json())
      .then((data: BCRow[]) => { setRows(data); setLoading(false) })
      .catch(() => { setError('Failed to load OECD data.'); setLoading(false) })
  }, [])

  const allCountries = useMemo(() => {
    const set = new Set<string>()
    rows.filter(r => r.Indicator === indicator).forEach(r => set.add(r.Country))
    return [...set].sort()
  }, [rows, indicator])

  const toggleCountry = (c: string) => {
    setSelectedCountries(prev =>
      prev.includes(c) ? prev.filter(x => x !== c) : [...prev, c]
    )
  }

  if (loading) return <div className="content-wrap"><p style={{ color: '#888', paddingTop: 40 }}>Loading OECD data…</p></div>
  if (error)   return <div className="content-wrap"><p style={{ color: '#ff4d4d' }}>{error}</p></div>

  return (
    <div className="content-wrap">
      {/* Controls */}
      <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap', marginBottom: 20, alignItems: 'center' }}>
        <div style={{ display: 'flex', gap: 6 }}>
          {(['CLI','BCI','CCI'] as const).map(ind => (
            <button
              key={ind}
              onClick={() => setIndicator(ind)}
              style={{
                padding: '6px 16px', borderRadius: 6, fontSize: 13, fontWeight: 600, cursor: 'pointer',
                border: '1px solid',
                borderColor: indicator === ind ? IND_COLORS[ind] : '#2a2a2a',
                background: indicator === ind ? IND_COLORS[ind] + '22' : 'transparent',
                color: indicator === ind ? IND_COLORS[ind] : '#888',
              }}
            >
              {ind}
            </button>
          ))}
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginLeft: 'auto' }}>
          <span style={{ color: '#888', fontSize: 12 }}>From year</span>
          <input
            type="range" min={1990} max={2020} value={fromYear}
            onChange={e => setFromYear(+e.target.value)}
            style={{ width: 100 }}
          />
          <span style={{ color: '#ccc', fontSize: 13, minWidth: 36 }}>{fromYear}</span>
        </div>
      </div>

      {/* Tabs */}
      <div style={{ display: 'flex', gap: 4, marginBottom: 20, borderBottom: '1px solid #2a2a2a', paddingBottom: 0 }}>
        {([['snapshot','Latest Snapshot'],['timeseries','Time Series'],['heatmap','Heatmap'],['deepdive','Country Deep-Dive']] as [Tab,string][]).map(([t, label]) => (
          <button key={t} onClick={() => setTab(t)} style={{
            padding: '8px 16px', fontSize: 13, cursor: 'pointer',
            border: 'none', borderBottom: tab === t ? `2px solid ${IND_COLORS[indicator]}` : '2px solid transparent',
            background: 'transparent', color: tab === t ? '#f0f0f0' : '#666', fontWeight: tab === t ? 600 : 400,
          }}>{label}</button>
        ))}
      </div>

      {tab === 'snapshot' && <SnapshotTab rows={rows} indicator={indicator} />}
      {tab === 'timeseries' && (
        <TimeSeriesTab
          rows={rows} indicator={indicator} fromYear={fromYear}
          countries={selectedCountries} allCountries={allCountries}
          onToggle={toggleCountry}
        />
      )}
      {tab === 'heatmap' && <HeatmapTab rows={rows} indicator={indicator} />}
      {tab === 'deepdive' && (
        <DeepDiveTab
          rows={rows} country={deepDiveCountry} fromYear={fromYear}
          allCountries={allCountries} onSelect={setDeepDiveCountry}
        />
      )}

      <p style={{ color: '#555', fontSize: 11, marginTop: 24 }}>
        Source: OECD via DBnomics (OECD/DP_LIVE). Long-Term Trend Index — 100 = long-run average.
        BCI = Business Confidence · CCI = Consumer Confidence · CLI = Composite Leading Indicator.
        Data lag: approximately 2–3 years behind current date.
      </p>
    </div>
  )
}

function SnapshotTab({ rows, indicator }: { rows: BCRow[]; indicator: string }) {
  const latest = useMemo(() => {
    const filtered = rows.filter(r => r.Indicator === indicator)
    const map = new Map<string, BCRow>()
    for (const r of filtered) {
      const existing = map.get(r.Country)
      if (!existing || r.Date > existing.Date) map.set(r.Country, r)
    }
    return [...map.values()].sort((a, b) => b.Value - a.Value)
  }, [rows, indicator])

  return (
    <div>
      <p style={{ color: '#888', fontSize: 12, marginBottom: 12 }}>
        Latest available reading. Index = Long-Term Trend · 100 = neutral ·{' '}
        <span style={{ color: '#00c087' }}>green &gt;100 (above trend)</span> ·{' '}
        <span style={{ color: '#ff4d4d' }}>red &lt;100 (below trend)</span>
      </p>
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, marginBottom: 20 }}>
        {latest.map(r => {
          const above = r.Value > 100
          return (
            <div key={r.Country} style={{
              background: above ? 'rgba(0,192,135,0.08)' : 'rgba(255,77,77,0.08)',
              border: `1px solid ${above ? 'rgba(0,192,135,0.3)' : 'rgba(255,77,77,0.3)'}`,
              borderRadius: 8, padding: '8px 12px', minWidth: 120,
            }}>
              <div style={{ fontSize: 10, color: '#888', marginBottom: 2 }}>{r.Country}</div>
              <div style={{ fontSize: '1.2rem', fontWeight: 700, color: above ? '#00c087' : '#ff4d4d' }}>
                {r.Value.toFixed(1)}
              </div>
              <div style={{ fontSize: 9, color: '#555' }}>
                {new Date(r.Date).toLocaleDateString('en', { month: 'short', year: 'numeric' })}
              </div>
            </div>
          )
        })}
      </div>

      {/* Table */}
      <div style={{ overflowX: 'auto' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
          <thead>
            <tr style={{ borderBottom: '1px solid #2a2a2a' }}>
              {['Country','ISO',indicator,'As of','Signal'].map(h => (
                <th key={h} style={{ textAlign: 'left', padding: '8px 12px', color: '#888', fontWeight: 600, fontSize: 11 }}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {latest.map(r => {
              const above = r.Value > 100
              return (
                <tr key={r.Country} style={{ borderBottom: '1px solid #1a1a1a', background: above ? 'rgba(0,192,135,0.04)' : 'rgba(255,77,77,0.04)' }}>
                  <td style={{ padding: '7px 12px', color: '#e0e0e0' }}>{r.Country}</td>
                  <td style={{ padding: '7px 12px', color: '#888' }}>{r.ISO}</td>
                  <td style={{ padding: '7px 12px', fontWeight: 600, color: above ? '#00c087' : '#ff4d4d' }}>{r.Value.toFixed(2)}</td>
                  <td style={{ padding: '7px 12px', color: '#888' }}>{new Date(r.Date).toLocaleDateString('en', { month: 'short', year: 'numeric' })}</td>
                  <td style={{ padding: '7px 12px', color: above ? '#00c087' : '#ff4d4d' }}>{above ? '▲ Above trend' : '▼ Below trend'}</td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
    </div>
  )
}

function TimeSeriesTab({
  rows, indicator, fromYear, countries, allCountries, onToggle,
}: {
  rows: BCRow[]; indicator: string; fromYear: number
  countries: string[]; allCountries: string[]
  onToggle: (c: string) => void
}) {
  const filtered = useMemo(() =>
    rows.filter(r => r.Indicator === indicator && countries.includes(r.Country) && new Date(r.Date).getFullYear() >= fromYear)
  , [rows, indicator, fromYear, countries])

  useEffect(() => {
    if (!filtered.length) return
    const grouped: Record<string, { x: string[]; y: number[] }> = {}
    for (const r of filtered) {
      if (!grouped[r.Country]) grouped[r.Country] = { x: [], y: [] }
      grouped[r.Country].x.push(r.Date)
      grouped[r.Country].y.push(r.Value)
    }
    const traces = Object.entries(grouped).map(([country, { x, y }], i) => ({
      type: 'scatter', mode: 'lines', name: country, x, y,
      line: { color: COUNTRY_COLORS[i % COUNTRY_COLORS.length], width: 1.8 },
    }))
    const layout = {
      paper_bgcolor: '#1a1a1a', plot_bgcolor: '#111111',
      font: { color: '#e0e0e0', size: 12 },
      margin: { l: 60, r: 20, t: 40, b: 44 },
      height: 440,
      title: { text: `${INDICATOR_META[indicator as keyof typeof INDICATOR_META]?.label} — country comparison`, font: { size: 13, color: '#e0e0e0' }, x: 0 },
      xaxis: { gridcolor: '#2a2a2a', tickfont: { color: '#888' } },
      yaxis: { gridcolor: '#2a2a2a', tickfont: { color: '#888' }, title: 'Index (100 = neutral)' },
      legend: { font: { color: '#ccc' }, bgcolor: 'rgba(0,0,0,0)' },
      shapes: [{ type: 'line', x0: 0, x1: 1, xref: 'paper', y0: 100, y1: 100, line: { color: '#555', dash: 'dot', width: 1.2 } }],
    }
    import('plotly.js-dist-min').then(Plotly => {
      Plotly.react('gbc-ts-chart', traces, layout, { responsive: true, displayModeBar: false })
    })
  }, [filtered, indicator])

  return (
    <div>
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, marginBottom: 14 }}>
        {allCountries.map((c, i) => {
          const sel = countries.includes(c)
          return (
            <button key={c} onClick={() => onToggle(c)} style={{
              padding: '3px 10px', borderRadius: 12, fontSize: 11, cursor: 'pointer',
              border: '1px solid',
              borderColor: sel ? COUNTRY_COLORS[i % COUNTRY_COLORS.length] : '#2a2a2a',
              background: sel ? COUNTRY_COLORS[i % COUNTRY_COLORS.length] + '22' : 'transparent',
              color: sel ? COUNTRY_COLORS[i % COUNTRY_COLORS.length] : '#666',
            }}>{c}</button>
          )
        })}
      </div>
      <div id="gbc-ts-chart" style={{ width: '100%', minHeight: 440 }} />
      <p style={{ color: '#555', fontSize: 11, marginTop: 8 }}>{INDICATOR_META[indicator as keyof typeof INDICATOR_META]?.desc}</p>
    </div>
  )
}

function HeatmapTab({ rows, indicator }: { rows: BCRow[]; indicator: string }) {
  useEffect(() => {
    const filtered = rows.filter(r => r.Indicator === indicator)
    if (!filtered.length) return

    // Build pivot: country → month → value
    const pivot: Record<string, Record<string, number>> = {}
    for (const r of filtered) {
      const ym = r.Date.slice(0, 7)
      if (!pivot[r.Country]) pivot[r.Country] = {}
      pivot[r.Country][ym] = r.Value
    }
    const countries = Object.keys(pivot).sort()

    // Last 36 months present in data
    const allMonths = [...new Set(filtered.map(r => r.Date.slice(0, 7)))].sort()
    const months = allMonths.slice(-36)

    const z = countries.map(c => months.map(m => (pivot[c][m] ?? 100) - 100))

    const layout = {
      paper_bgcolor: '#1a1a1a', plot_bgcolor: '#111111',
      font: { color: '#e0e0e0', size: 11 },
      margin: { l: 160, r: 80, t: 50, b: 80 },
      height: Math.max(300, countries.length * 28 + 100),
      title: { text: `${INDICATOR_META[indicator as keyof typeof INDICATOR_META]?.label} — deviation from 100 (last 36 months)`, font: { size: 13 }, x: 0 },
      xaxis: { tickfont: { color: '#888', size: 9 }, tickangle: -45 },
      yaxis: { tickfont: { color: '#e0e0e0' } },
    }
    const trace = {
      type: 'heatmap', z, x: months, y: countries,
      colorscale: [[0, '#ff4d4d'], [0.5, '#1a1a1a'], [1, '#00c087']],
      zmid: 0,
      colorbar: { title: 'vs 100', tickfont: { color: '#ccc' }, titlefont: { color: '#ccc' } },
      hovertemplate: '%{y}<br>%{x}: %{z:+.2f} vs 100<extra></extra>',
    }
    import('plotly.js-dist-min').then(Plotly => {
      Plotly.react('gbc-heatmap', [trace], layout, { responsive: true, displayModeBar: false })
    })
  }, [rows, indicator])

  return (
    <div>
      <div id="gbc-heatmap" style={{ width: '100%', minHeight: 400 }} />
      <p style={{ color: '#555', fontSize: 11, marginTop: 8 }}>Green = above long-run trend (expanding). Red = below trend (contracting).</p>
    </div>
  )
}

function DeepDiveTab({
  rows, country, fromYear, allCountries, onSelect,
}: {
  rows: BCRow[]; country: string; fromYear: number
  allCountries: string[]; onSelect: (c: string) => void
}) {
  useEffect(() => {
    const filtered = rows.filter(r => r.Country === country && new Date(r.Date).getFullYear() >= fromYear)
    if (!filtered.length) return
    const colors: Record<string, string> = { BCI: '#3b82f6', CCI: '#f39200', CLI: '#00c087' }
    const traces = (['BCI','CCI','CLI'] as const).map(ind => {
      const sub = filtered.filter(r => r.Indicator === ind).sort((a, b) => a.Date.localeCompare(b.Date))
      return {
        type: 'scatter', mode: 'lines', name: INDICATOR_META[ind].label,
        x: sub.map(r => r.Date), y: sub.map(r => r.Value),
        line: { color: colors[ind], width: 2 },
      }
    })
    const layout = {
      paper_bgcolor: '#1a1a1a', plot_bgcolor: '#111111',
      font: { color: '#e0e0e0', size: 12 },
      margin: { l: 60, r: 20, t: 40, b: 44 },
      height: 400,
      title: { text: `${country} — BCI · CCI · CLI`, font: { size: 13, color: '#e0e0e0' }, x: 0 },
      xaxis: { gridcolor: '#2a2a2a', tickfont: { color: '#888' } },
      yaxis: { gridcolor: '#2a2a2a', tickfont: { color: '#888' }, title: 'Index (100 = neutral)' },
      legend: { font: { color: '#ccc' }, bgcolor: 'rgba(0,0,0,0)' },
      shapes: [{ type: 'line', x0: 0, x1: 1, xref: 'paper', y0: 100, y1: 100, line: { color: '#555', dash: 'dot', width: 1.2 } }],
    }
    import('plotly.js-dist-min').then(Plotly => {
      Plotly.react('gbc-deepdive', traces, layout, { responsive: true, displayModeBar: false })
    })
  }, [rows, country, fromYear])

  const latestByInd = useMemo(() => {
    const result: Record<string, BCRow | undefined> = {}
    for (const ind of ['BCI','CCI','CLI'] as const) {
      const sub = rows.filter(r => r.Country === country && r.Indicator === ind).sort((a, b) => b.Date.localeCompare(a.Date))
      result[ind] = sub[0]
    }
    return result
  }, [rows, country])

  return (
    <div>
      <div style={{ marginBottom: 14 }}>
        <label style={{ color: '#888', fontSize: 12, marginRight: 8 }}>Country</label>
        <select
          value={country} onChange={e => onSelect(e.target.value)}
          style={{ background: '#1a1a1a', border: '1px solid #2a2a2a', color: '#e0e0e0', padding: '6px 12px', borderRadius: 6, fontSize: 13 }}
        >
          {allCountries.map(c => <option key={c} value={c}>{c}</option>)}
        </select>
      </div>
      <div id="gbc-deepdive" style={{ width: '100%', minHeight: 400 }} />

      <div style={{ display: 'flex', gap: 10, marginTop: 16 }}>
        {(['BCI','CCI','CLI'] as const).map(ind => {
          const r = latestByInd[ind]
          if (!r) return null
          const above = r.Value > 100
          return (
            <div key={ind} style={{ flex: 1, background: '#1a1a1a', border: '1px solid #2a2a2a', borderRadius: 8, padding: 14 }}>
              <div style={{ fontSize: 10, color: '#888', marginBottom: 4 }}>{INDICATOR_META[ind].label}</div>
              <div style={{ fontSize: '1.4rem', fontWeight: 700, color: above ? '#00c087' : '#ff4d4d' }}>{r.Value.toFixed(2)}</div>
              <div style={{ fontSize: 11, color: '#555', marginTop: 4 }}>
                {new Date(r.Date).toLocaleDateString('en', { month: 'short', year: 'numeric' })} · {above ? '▲ Above trend' : '▼ Below trend'}
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
