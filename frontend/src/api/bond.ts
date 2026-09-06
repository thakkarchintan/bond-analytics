import apiFetch from './client'

export interface SparkPoint { date: string; value: number }

export interface SpreadCard {
  name: string
  formula: string
  last: number
  change: number
  change_pct: number
  sparkline: SparkPoint[]
}

export interface SeriesPoint { date: string; value: number }

export function fetchSpreadGrid(start?: string, end?: string): Promise<SpreadCard[]> {
  const params = new URLSearchParams()
  if (start) params.set('start', start)
  if (end) params.set('end', end)
  const qs = params.toString() ? `?${params}` : ''
  return apiFetch<SpreadCard[]>(`/api/bond/spread-grid${qs}`)
}

export function fetchColumns(): Promise<string[]> {
  return apiFetch<string[]>('/api/bond/columns')
}

export function fetchSeries(cols: string[], start?: string, end?: string): Promise<Record<string, SeriesPoint[]>> {
  const params = new URLSearchParams({ cols: cols.join(',') })
  if (start) params.set('start', start)
  if (end) params.set('end', end)
  return apiFetch<Record<string, SeriesPoint[]>>(`/api/bond/series?${params}`)
}

export function evalFormula(formula: string, start?: string, end?: string): Promise<SeriesPoint[]> {
  return apiFetch<SeriesPoint[]>('/api/bond/formula', {
    method: 'POST',
    body: JSON.stringify({ formula, start, end }),
  })
}
