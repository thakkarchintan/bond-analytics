import { useState, useEffect } from 'react'
import apiFetch from '../api/client'

interface Article {
  title: string
  description: string
  url: string
  source: string
  publishedAt: string
  urlToImage: string
}

interface NewsResponse {
  query: string
  articles: Article[]
  summary: string
  has_news_key: boolean
  has_llm_key: boolean
  article_count: number
}

const PRESET_QUERIES = [
  'bonds interest rates central bank',
  'Federal Reserve ECB monetary policy',
  'treasury yields inflation',
  'credit spreads corporate bonds',
  'emerging markets debt',
  'IMF World Bank global economy',
]

function timeAgo(iso: string): string {
  try {
    const diff = Date.now() - new Date(iso).getTime()
    const h = Math.floor(diff / 3_600_000)
    const d = Math.floor(h / 24)
    if (d > 0) return `${d}d ago`
    if (h > 0) return `${h}h ago`
    return 'just now'
  } catch { return '' }
}

export default function NewsSummary() {
  const [query, setQuery]     = useState(PRESET_QUERIES[0])
  const [data, setData]       = useState<NewsResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError]     = useState('')

  async function load(q: string) {
    setLoading(true); setError(''); setQuery(q)
    try {
      const d = await apiFetch<NewsResponse>(`/api/news?q=${encodeURIComponent(q)}`)
      setData(d)
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Error loading news')
    }
    setLoading(false)
  }

  useEffect(() => { load(query) }, [])

  return (
    <div className="bond-layout">
      <aside className="bond-sidebar">
        <div className="ctrl-section">
          <div className="ctrl-label">SEARCH</div>
          <input
            className="ctrl-input"
            value={query}
            onChange={e => setQuery(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && load(query)}
            placeholder="bonds, rates, ECB…"
          />
          <button className="primary-button" style={{ width: '100%', marginTop: 8 }} onClick={() => load(query)} disabled={loading}>
            {loading ? 'Loading…' : 'Search'}
          </button>
        </div>

        <div className="ctrl-section">
          <div className="ctrl-label">PRESETS</div>
          {PRESET_QUERIES.map(q => (
            <button
              key={q}
              onClick={() => load(q)}
              style={{
                display: 'block', width: '100%', textAlign: 'left',
                padding: '6px 8px', marginBottom: 4, borderRadius: 4,
                background: query === q ? 'rgba(243,146,0,0.12)' : 'transparent',
                border: `1px solid ${query === q ? '#f39200' : '#2a2a2a'}`,
                color: query === q ? '#f39200' : '#888',
                fontSize: 11, cursor: 'pointer', lineHeight: 1.4,
              }}
            >
              {q}
            </button>
          ))}
        </div>

        {data && (
          <div className="ctrl-section">
            <div className="ctrl-label">STATUS</div>
            <div style={{ fontSize: 11, color: '#555', lineHeight: 1.6 }}>
              <div style={{ color: data.has_news_key ? '#00c087' : '#ff4d4d' }}>
                {data.has_news_key ? '✓' : '✗'} NewsAPI key
              </div>
              <div style={{ color: data.has_llm_key ? '#00c087' : '#888' }}>
                {data.has_llm_key ? '✓' : '–'} LLM summary
              </div>
              <div style={{ color: '#555', marginTop: 4 }}>{data.article_count} articles found</div>
            </div>
          </div>
        )}
      </aside>

      <div className="bond-main">
        <div style={{ borderLeft: '3px solid #f39200', padding: '10px 14px', background: 'rgba(243,146,0,0.04)', borderRadius: '0 6px 6px 0', marginBottom: 20 }}>
          <div style={{ color: '#e8e8e8', fontWeight: 600, fontSize: 13, textTransform: 'uppercase', letterSpacing: '0.04em' }}>News Summary</div>
          <div style={{ color: '#888', fontSize: 11, marginTop: 4 }}>NewsAPI · last 7 days · {query}</div>
        </div>

        {error && (
          <div style={{ color: '#ff4d4d', padding: '12px 16px', background: 'rgba(255,77,77,0.08)', borderRadius: 6, marginBottom: 16, fontSize: 12 }}>
            {error}<br />
            <small style={{ color: '#888' }}>Is the FastAPI backend running? Check NEWS_API_KEY is set.</small>
          </div>
        )}

        {loading && (
          <div style={{ color: '#aaa', textAlign: 'center', padding: 60 }}>
            <div style={{ width: 32, height: 32, border: '3px solid #f39200', borderTopColor: 'transparent', borderRadius: '50%', animation: 'spin 0.8s linear infinite', margin: '0 auto 16px' }} />
            Fetching latest news…
          </div>
        )}

        {data && !loading && (
          <>
            {/* No key notice */}
            {!data.has_news_key && (
              <div style={{ padding: '16px', background: 'rgba(243,146,0,0.08)', border: '1px solid rgba(243,146,0,0.3)', borderRadius: 6, marginBottom: 20, fontSize: 12, color: '#f39200' }}>
                <strong>NEWS_API_KEY not set.</strong> Add it to your environment variables to fetch live articles.
                Get a free key at <span style={{ color: '#60a5fa' }}>newsapi.org</span>
              </div>
            )}

            {/* LLM Summary */}
            {data.summary && (
              <>
                <div style={{ borderLeft: '3px solid #60a5fa', padding: '10px 14px', background: 'rgba(96,165,250,0.04)', borderRadius: '0 6px 6px 0', marginBottom: 12 }}>
                  <div style={{ color: '#e8e8e8', fontWeight: 600, fontSize: 13, textTransform: 'uppercase', letterSpacing: '0.04em' }}>AI Summary</div>
                  <div style={{ color: '#888', fontSize: 11, marginTop: 4 }}>Generated by LLM from top articles</div>
                </div>
                <div style={{ background: '#1a1a1a', border: '1px solid #2a2a2a', borderRadius: 8, padding: '16px 20px', marginBottom: 24, color: '#e8e8e8', fontSize: 13, lineHeight: 1.7, whiteSpace: 'pre-wrap' }}>
                  {data.summary}
                </div>
              </>
            )}

            {/* Articles grid */}
            {data.articles.length > 0 ? (
              <>
                <div style={{ borderLeft: '3px solid #f39200', padding: '10px 14px', background: 'rgba(243,146,0,0.04)', borderRadius: '0 6px 6px 0', marginBottom: 16 }}>
                  <div style={{ color: '#e8e8e8', fontWeight: 600, fontSize: 13, textTransform: 'uppercase', letterSpacing: '0.04em' }}>Articles</div>
                  <div style={{ color: '#888', fontSize: 11, marginTop: 4 }}>{data.articles.length} results · last 7 days</div>
                </div>
                <div style={{ display: 'grid', gap: 12 }}>
                  {data.articles.map((a, i) => (
                    <a
                      key={i}
                      href={a.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      style={{ textDecoration: 'none' }}
                    >
                      <div style={{
                        background: '#1a1a1a', border: '1px solid #2a2a2a', borderRadius: 8,
                        padding: '14px 16px', cursor: 'pointer',
                        transition: 'border-color 0.15s',
                      }}
                        onMouseEnter={e => (e.currentTarget.style.borderColor = '#f39200')}
                        onMouseLeave={e => (e.currentTarget.style.borderColor = '#2a2a2a')}
                      >
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 12 }}>
                          <div style={{ flex: 1, minWidth: 0 }}>
                            <div style={{ color: '#e8e8e8', fontWeight: 600, fontSize: 13, lineHeight: 1.4, marginBottom: 6 }}>
                              {a.title}
                            </div>
                            {a.description && (
                              <div style={{ color: '#888', fontSize: 12, lineHeight: 1.5, overflow: 'hidden', display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical' }}>
                                {a.description}
                              </div>
                            )}
                            <div style={{ display: 'flex', gap: 12, marginTop: 8 }}>
                              <span style={{ color: '#f39200', fontSize: 10, textTransform: 'uppercase', letterSpacing: '0.06em' }}>{a.source}</span>
                              <span style={{ color: '#555', fontSize: 10 }}>{timeAgo(a.publishedAt)}</span>
                            </div>
                          </div>
                          {a.urlToImage && (
                            <img
                              src={a.urlToImage}
                              alt=""
                              style={{ width: 80, height: 60, objectFit: 'cover', borderRadius: 4, flexShrink: 0 }}
                              onError={e => { (e.target as HTMLImageElement).style.display = 'none' }}
                            />
                          )}
                        </div>
                      </div>
                    </a>
                  ))}
                </div>
              </>
            ) : data.has_news_key ? (
              <div style={{ color: '#555', textAlign: 'center', padding: '40px 20px', fontSize: 13 }}>
                No articles found for "{data.query}". Try a different search.
              </div>
            ) : null}
          </>
        )}
      </div>
    </div>
  )
}
