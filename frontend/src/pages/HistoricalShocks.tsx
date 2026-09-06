import { useState, useEffect, useRef } from 'react'
import { evalFormula } from '../api/bond'

type PlotTrace = Record<string, unknown>
type PlotLayout = Record<string, unknown>

function Chart({ traces, layout, height = 360 }: { traces: PlotTrace[]; layout: PlotLayout; height?: number }) {
  const ref = useRef<HTMLDivElement>(null)
  useEffect(() => {
    if (!ref.current || !traces.length) return
    let cancelled = false
    import('plotly.js-dist-min').then(Plotly => {
      if (cancelled || !ref.current) return
      const base: PlotLayout = {
        paper_bgcolor:'#1a1a1a', plot_bgcolor:'#111111',
        font:{ color:'#aaa', family:'system-ui,sans-serif', size:11 },
        margin:{ t:36, r:16, b:44, l:62 },
        xaxis:{ gridcolor:'#2a2a2a', tickfont:{ color:'#777', size:10 } },
        yaxis:{ gridcolor:'#2a2a2a', tickfont:{ color:'#777', size:10 }, zerolinecolor:'#444' },
        legend:{ orientation:'h', y:1.12, x:0, font:{ color:'#aaa', size:10 }, bgcolor:'rgba(0,0,0,0)' },
        hovermode:'x unified',
        hoverlabel:{ bgcolor:'#1a1a1a', bordercolor:'#f39200', font:{ color:'#e8e8e8' } },
        ...layout,
      }
      Plotly.react(ref.current!, traces as never, base as never, { responsive:true, displayModeBar:false })
    })
    return () => { cancelled = true }
  }, [traces, layout])
  return <div ref={ref} style={{ width:'100%', height }} />
}

interface ShockEpisode {
  name: string
  start: string
  end: string
  color: string
  description: string
  eyebrow: string
  narrative: {
    context: string
    drivers: string[]
    marketDynamics: string
    lessons: string
  }
}

const SHOCK_EPISODES: ShockEpisode[] = [
  {
    name: 'Asian Crisis 1997',
    start: '1997-01-01', end: '1998-12-31',
    color: '#e879f9',
    eyebrow: 'EM CONTAGION · CURRENCY CRISIS',
    description: 'Thai baht collapse July 1997 → contagion across Asia, Russia, LTCM',
    narrative: {
      context: 'The Asian Financial Crisis began with the collapse of the Thai baht on July 2, 1997, after the Thai government was forced to float the currency due to lack of foreign currency reserves. What followed was a rapid contagion across Southeast Asia and eventually global markets.',
      drivers: [
        'Excessive short-term foreign currency borrowing by Asian banks and corporates',
        'Fixed exchange rate pegs that masked currency mismatches and credit excess',
        'Current account deficits financed by hot money flows that reversed suddenly',
        'IMF austerity conditions worsened economic downturns in Thailand, Indonesia, South Korea',
        'Russian sovereign default (August 1998) and LTCM near-collapse amplified global risk-off',
      ],
      marketDynamics: 'US Treasuries rallied sharply as a safe-haven flight-to-quality trade, compressing 10Y yields by 150bps from peak to trough. Emerging market spreads blew out 600–1000bps. The S&P 500 sold off ~20% peak-to-trough. The Federal Reserve cut rates three times in late 1998 to backstop global liquidity. LTCM\'s near-failure in September 1998 required a Fed-orchestrated private sector bailout.',
      lessons: 'Currency peg regimes with unhedged foreign-currency debt create fragility. Flight-to-quality benefits long-duration sovereigns. EM crises tend to propagate in non-linear waves, not orderly repricing.',
    },
  },
  {
    name: 'Dot-Com & 9/11',
    start: '2000-01-01', end: '2002-12-31',
    color: '#22d3ee',
    eyebrow: 'EQUITY BUST · GEOPOLITICAL SHOCK',
    description: 'NASDAQ peak March 2000 → tech bust; September 11 attacks shock markets',
    narrative: {
      context: 'The dot-com bubble burst in March 2000 as speculative technology valuations collapsed under the weight of rising rates and deteriorating earnings. The September 11, 2001 terrorist attacks delivered a second shock, closing US equity markets for 4 days — the longest closure since 1933.',
      drivers: [
        'NASDAQ peaked at 5,048 in March 2000, having risen 400% since 1995 — P/Es were unsustainable',
        'Fed began raising rates in 1999 to cool speculative excess, bursting the bubble',
        '9/11 attacks created massive uncertainty, insurance losses, and airline/travel sector collapse',
        'Accounting scandals (Enron, WorldCom) in 2001–2002 destroyed corporate credit confidence',
        'Fed emergency cut of 50bps on 9/17/2001 — markets re-opened on 9/17 and sold off 7% that day',
      ],
      marketDynamics: 'Fixed income outperformed dramatically. The 10Y Treasury yield fell from 6.8% in January 2000 to 3.6% by mid-2003. The Fed cut rates from 6.5% to 1.0%. NASDAQ lost 78% of its value from peak to trough. Investment-grade credit held up relatively well; high yield saw moderate spread widening compared to later crises.',
      lessons: 'Bonds serve as powerful portfolio diversifiers when equities sell off due to valuation correction rather than inflation shock. Duration was rewarded handsomely in 2001–2003. Geopolitical events create short-lived spikes in volatility, not structural repricing.',
    },
  },
  {
    name: 'GFC 2008',
    start: '2007-06-01', end: '2009-06-30',
    color: '#ff4d4d',
    eyebrow: 'SYSTEMIC BANKING CRISIS · GREAT RECESSION',
    description: 'Global Financial Crisis · Lehman Brothers collapse September 2008',
    narrative: {
      context: 'The Global Financial Crisis was the most severe financial crisis since the Great Depression. It originated in the US subprime mortgage market, where low underwriting standards and rampant securitization had created trillions of dollars of opaque, leveraged credit exposure hidden inside structured products (CDOs, CLOs, MBS).',
      drivers: [
        'Subprime mortgage origination explosion 2003–2006: no-doc, NINJA loans packaged into AAA-rated CDOs',
        'Shadow banking system — Money Market Funds, SIVs, repo markets — was fragile and opaque',
        'Lehman Brothers filed for bankruptcy on September 15, 2008 with $613B in debt',
        'Reserve Primary Fund "broke the buck" on Sep 16, triggering a $300B run on money market funds',
        'Global interbank markets froze; LIBOR-OIS spread reached 365bps (vs ~10bps pre-crisis)',
      ],
      marketDynamics: 'US 10Y yields fell from 5.3% (June 2007) to 2.0% (December 2008) as the Fed cut to 0.25% and launched QE1. Investment-grade spreads peaked at 620bps; high yield at 1,950bps. S&P 500 lost 57% peak-to-trough. Gold surged. Long-duration Treasuries returned +25% in 2008. The crisis reshaped global banking regulation (Basel III, Dodd-Frank).',
      lessons: 'Systemic crises produce the most extreme safe-haven rallies. Duration was a near-perfect crisis hedge. Credit spreads can gap to levels that overwhelm historical models. Central bank balance sheets became the backstop of last resort.',
    },
  },
  {
    name: 'Euro Crisis',
    start: '2010-01-01', end: '2012-12-31',
    color: '#f39200',
    eyebrow: 'SOVEREIGN DEBT · EUROZONE FRAGMENTATION',
    description: 'European sovereign debt crisis · Greece / PIIGS · ECB "whatever it takes"',
    narrative: {
      context: 'The European sovereign debt crisis exposed deep structural fragilities in the eurozone architecture. Countries that had borrowed heavily during the 2003–2008 credit boom found themselves unable to roll debt at affordable yields once markets lost confidence. Unlike the US, eurozone member states lacked a domestic central bank as lender of last resort.',
      drivers: [
        'Greece revealed its deficit was 15.4% of GDP in 2009 — double initial estimates',
        'Contagion spread to Ireland (banking crisis), Portugal, Spain, and Italy through 2010–2011',
        'ECB\'s initial reluctance to backstop sovereigns amplified sell-off — spreads widened to crisis levels',
        'Austerity programmes imposed severe economic contractions, making debt dynamics worse',
        'Mario Draghi\'s "whatever it takes" speech on July 26, 2012 marked the turning point',
      ],
      marketDynamics: 'Greek 10Y yields peaked at 44% in March 2012. Italian and Spanish 10Y yields exceeded 7% — the perceived point of no return. German Bund yields fell to record lows (safe-haven compression). The ECB\'s OMT programme announcement in September 2012 ended the acute phase without a single bond purchase being made. US Treasuries and Bunds were the prime beneficiaries of eurozone fragmentation fear.',
      lessons: 'Currency union without fiscal union creates structural fragility. Central bank credibility and communication are themselves policy tools. Spreads can move far beyond fundamental value when redenomination risk enters the market.',
    },
  },
  {
    name: 'Taper Tantrum',
    start: '2013-05-01', end: '2013-12-31',
    color: '#fbbf24',
    eyebrow: 'COMMUNICATION SHOCK · RATES REPRICING',
    description: 'Fed taper signal May 22, 2013 → 100bp yield spike in weeks',
    narrative: {
      context: 'The "Taper Tantrum" of 2013 demonstrated how powerfully forward guidance shapes bond markets. On May 22, 2013, Federal Reserve Chairman Ben Bernanke suggested in congressional testimony that the Fed might "step down" its pace of asset purchases if economic improvement continued. Markets were caught completely off-guard.',
      drivers: [
        'QE3 (launched September 2012) had bought $85B/month of Treasuries and MBS, suppressing yields',
        'Markets had extrapolated "lower for longer" indefinitely — consensus was wrong',
        'Bernanke\'s May 22 comments triggered immediate bond selloff — 10Y yields jumped 40bps in days',
        'EM markets suffered most: EM currencies fell sharply as carry trades unwound simultaneously',
        'Federal Reserve delayed actual tapering until December 2013, but the expectation shift was enough',
      ],
      marketDynamics: 'US 10Y Treasury yields rose from 1.63% in early May 2013 to 3.0% by September — a 137bp move in four months. This translated into roughly -12% total return for long-duration bond holders. EM bonds and currencies suffered most severely. Despite the yield surge, there was no credit event — investment grade and high yield spreads were stable. The Fed\'s actual taper began December 2013 and was priced without drama.',
      lessons: 'Central bank communication is policy. Duration exposure in a QE-distorted market carries binary risk around guidance shifts. EM is disproportionately exposed to Fed policy normalization relative to DM credit.',
    },
  },
  {
    name: 'Oil Shock 2014',
    start: '2014-06-01', end: '2016-02-28',
    color: '#34d399',
    eyebrow: 'COMMODITY · EM STRESS · CREDIT',
    description: 'WTI crude oil falls 75% · Saudi price war · EM stress · HY blow-out',
    narrative: {
      context: 'Between June 2014 and February 2016, WTI crude oil collapsed from $107 to $26 per barrel — a 75% decline driven by the Saudi Arabia-led OPEC decision to maintain market share rather than defend prices in the face of the US shale revolution. The shock cascaded through EM sovereigns, energy high yield, and commodity-linked currencies.',
      drivers: [
        'US shale oil production surged from 5Mb/d in 2008 to 9Mb/d in 2015 — shattering OPEC\'s pricing power',
        'OPEC\'s November 2014 decision not to cut production signaled a market-share war against US shale',
        'Oil-dependent EM economies (Russia, Venezuela, Nigeria, Brazil) faced sovereign stress',
        'US energy high yield spread widened from 400bps to over 1,600bps; multiple E&P defaults',
        'China devaluation in August 2015 added a second shock — commodity demand fears compounded oil decline',
      ],
      marketDynamics: 'US Treasuries rallied modestly as deflationary impulse dominated. The 10Y yield fell from 2.6% to 1.6% by February 2016. High yield energy credit was devastated. EM oil exporters saw currency collapses (Russian ruble -50%, Brazilian real -45%). Investment-grade spreads widened 100bps. The Fed delayed its first rate hike until December 2015 in part due to EM and oil-induced disinflation.',
      lessons: 'Commodity price collapses create deflationary impulse that supports duration. Energy sector credit can experience equity-like drawdowns. EM vulnerability to commodity cycles is structural, not merely cyclical.',
    },
  },
  {
    name: 'China Shock 2015',
    start: '2015-06-01', end: '2016-06-30',
    color: '#f87171',
    eyebrow: 'EM · CHINA · DEVALUATION',
    description: 'CNY devaluation August 2015 → global risk-off · circuit breakers triggered',
    narrative: {
      context: 'China\'s shock devaluation of the renminbi on August 11, 2015 — the largest single-day move in 20 years — triggered a global market sell-off that persisted into early 2016. Combined with plunging commodity prices and fears of a hard landing in the world\'s second-largest economy, the episode tested central bank credibility globally.',
      drivers: [
        'People\'s Bank of China moved from a managed peg to a "market reference rate" system',
        'Markets interpreted the devaluation as a sign of weaker-than-reported economic growth',
        'China\'s equity market had already fallen 30% from its June 2015 peak on domestic credit tightening',
        'Global manufacturing PMIs weakened as demand fears spread; commodity producers hit hardest',
        'January 2016 circuit breakers in China\'s stock market (7% drop triggers halt) amplified panic',
      ],
      marketDynamics: 'S&P 500 fell 12% from August peak by end of September 2015, with another leg lower in January 2016. VIX spiked to 53 on August 24, 2015. US 10Y yields rallied from 2.3% to 1.5% by February 2016. The Fed was forced to pause its hiking cycle. EM equities and currencies sold off broadly. Safe-haven currencies (JPY, CHF) strengthened significantly.',
      lessons: 'China is now a systemic risk factor for global markets. Currency management signals matter as much as macro data. Fear of EM hard-landing amplifies DM safe-haven demand disproportionately to realized outcomes.',
    },
  },
  {
    name: 'Trade War 2018',
    start: '2018-01-01', end: '2019-06-30',
    color: '#60a5fa',
    eyebrow: 'GEOPOLITICAL · TARIFFS · INVERSION',
    description: 'US-China trade war · tariff escalation · yield curve inversion',
    narrative: {
      context: 'The US-China trade conflict that escalated through 2018–2019 introduced a new form of geopolitical risk into financial markets: systematic tariff escalation targeting the world\'s two largest economies. The US imposed tariffs on $360B of Chinese goods; China retaliated with tariffs on $110B of US goods. Business investment uncertainty surged.',
      drivers: [
        'Section 301 tariffs announced March 2018: 25% on $50B of Chinese goods (semiconductors, aerospace)',
        'China retaliated with 25% on US soybeans, autos, aircraft — targeting politically sensitive goods',
        'July 2018: another $200B escalation. October 2018: global equity selloff on earnings fears',
        'US yield curve inverted (3M/10Y) in March 2019 — signaling recession risk to bond markets',
        'Fed pivoted to rate cuts in mid-2019 despite earlier rate hikes, citing trade uncertainty',
      ],
      marketDynamics: 'US 10Y yields fell from 3.2% in November 2018 to 2.0% by June 2019 as the inversion trade gathered momentum and rate cut expectations built. S&P 500 fell 20% in Q4 2018 before recovering. High yield spreads widened 200bps then retraced. Emerging market bonds with China exposure saw elevated volatility. Gold and Treasuries benefited from safe-haven demand through the uncertainty.',
      lessons: 'Trade policy uncertainty damages investment intentions — a supply-side shock that cannot be resolved by easy monetary policy alone. Curve inversions in the 3M/10Y segment have historically been reliable recession predictors with 12–18 month lead times.',
    },
  },
  {
    name: 'COVID-19',
    start: '2020-01-01', end: '2021-06-30',
    color: '#a78bfa',
    eyebrow: 'PANDEMIC · EMERGENCY POLICY · QE∞',
    description: 'Global pandemic shock → emergency rate cuts → fiscal expansion → reflation',
    narrative: {
      context: 'The COVID-19 pandemic triggered the fastest market selloff in history — the S&P 500 fell 34% in 23 trading days — followed by the most aggressive monetary and fiscal policy response ever deployed in peacetime. The Federal Reserve moved to near-zero rates on March 15, 2020 and launched unlimited QE ("QE∞") three days later.',
      drivers: [
        'Global economic shutdown: Q2 2020 US GDP contracted 31.4% annualized — unprecedented since the Depression',
        'Fed cut rates 150bps in two emergency meetings (March 3 and March 15, 2020)',
        'CARES Act: $2.2T fiscal package signed March 27, 2020 — largest in US history at the time',
        'Fed expanded its balance sheet from $4.2T to $7.2T in three months',
        'Vaccine announcements (Pfizer Nov 9, 2020) triggered the largest-ever single-day rotation from bonds to equities',
      ],
      marketDynamics: 'US 10Y yields fell from 1.9% in January 2020 to 0.52% by August 2020 — an all-time low. Investment-grade spreads briefly widened to 400bps before Fed corporate bond purchasing collapsed them. High yield widened to 1,100bps before recovering. The "reflation trade" began in Q4 2020: yields rose, commodities surged, and inflation expectations (5Y5Y breakevens) returned to target levels.',
      lessons: 'Zero lower bound constrains monetary policy; fiscal dominance becomes inevitable. The Fed\'s corporate bond purchasing was more important as a signal than in actual volume. Pandemic-driven dislocations create once-in-a-generation entry points across asset classes for those who held nerve.',
    },
  },
  {
    name: 'Rate Hike Cycle',
    start: '2022-01-01', end: '2023-12-31',
    color: '#f87171',
    eyebrow: 'FASTEST HIKING CYCLE IN 40 YEARS',
    description: 'Fed + ECB fastest hiking cycle in 40 years · bonds -20% · inverted curve',
    narrative: {
      context: 'The 2022 rate hike cycle was the most aggressive Federal Reserve tightening in four decades. Starting from near zero in March 2022, the Fed raised rates by 525bps to 5.50% by July 2023. The Bloomberg US Aggregate Bond Index fell -13% in 2022 — its worst year since records began. Long-duration bonds fell over 30%.',
      drivers: [
        'Post-COVID inflation surge: CPI peaked at 9.1% in June 2022 — a 40-year high',
        'Persistent supply chain disruptions, fiscal stimulus overhang, and energy shock (Russia/Ukraine Feb 2022)',
        'Fed initially described inflation as "transitory" — delayed tightening until March 2022, then compressed the hiking cycle',
        'ECB hiked 450bps from July 2022 to September 2023 — its own historic cycle',
        'US 10Y yield surged from 1.5% (Jan 2022) to 5.0% (October 2023) — largest 2-year yield move since the Volcker era',
      ],
      marketDynamics: 'The 2022 bond selloff was historic: -20% for 20Y+ Treasuries (TLT). Duration was a major risk factor, not a hedge. The S&P 500 also fell 19% — providing no diversification benefit. Inflation-linked bonds (TIPS) outperformed nominal bonds. The yield curve inverted deeply (-100bps 2Y/10Y) through 2023. SVB (Silicon Valley Bank) failed in March 2023 partly due to mark-to-market losses on its long-duration Treasury portfolio.',
      lessons: 'When inflation is the primary risk, bonds lose their diversification role. Duration is the enemy in a hiking cycle. ALM (asset-liability mismatch) with long-duration assets and short-duration liabilities is existentially dangerous for institutions.',
    },
  },
  {
    name: 'SVB Crisis 2023',
    start: '2023-01-01', end: '2023-12-31',
    color: '#fb923c',
    eyebrow: 'BANKING STRESS · FLIGHT TO QUALITY',
    description: 'Silicon Valley Bank failure March 2023 → US regional bank stress · flight to quality',
    narrative: {
      context: 'Silicon Valley Bank\'s collapse on March 10, 2023 — the largest US bank failure since Washington Mutual in 2008 — triggered immediate contagion fear across US regional banks. SVB had accumulated a $120B portfolio of long-duration MBS and Treasuries, funded by short-duration deposits. Rising rates created massive mark-to-market losses that became realized when deposit outflows forced asset sales.',
      drivers: [
        'SVB held $120B in HTM securities with 5.6-year average duration — marked at cost, not fair value',
        'When HTM losses became public, depositor confidence collapsed: $42B withdrawn in 48 hours',
        'Signature Bank failed two days later; Credit Suisse required emergency merger with UBS (March 19)',
        'FDIC guaranteed all SVB deposits beyond FDIC limits — creating a precedent and moral hazard debate',
        'Fed launched Bank Term Funding Program (BTFP) on March 12: par-value lending against underwater securities',
      ],
      marketDynamics: 'Flight to quality drove the 2Y Treasury yield from 5.0% to 3.7% in three days — one of the largest short-term moves in modern history. Fed Funds futures pricing for 2023 year-end rates dropped by 100bps overnight. Regional bank equities (KRE ETF) fell 30% in a week. Gold rallied. The episode compressed the hiking cycle and brought forward rate cut expectations into 2024. Longer-end rates were more stable, steepening the curve modestly.',
      lessons: 'Duration mismatch is lethal when rates rise rapidly. Mark-to-market accounting in HTM portfolios is a fiction that markets see through. Deposit insurance gaps create binary run risks in a social-media era where information propagates instantly.',
    },
  },
  {
    name: 'Custom',
    start: '', end: '',
    color: '#60a5fa',
    eyebrow: 'USER-DEFINED DATE RANGE',
    description: 'Set your own date range',
    narrative: {
      context: 'Use the date range pickers to analyse any custom period of your choice.',
      drivers: [],
      marketDynamics: '',
      lessons: '',
    },
  },
]

const PRESET_FORMULAS: Record<string, string> = {
  'US 2-10 Spread':    'US10Y - US2Y',
  'Eurex 5-10 Spread': 'FGBLY - FGBMY',
  'US 10Y Yield':      'US10Y',
  'US 2Y Yield':       'US2Y',
  'DE 10Y Yield':      'FGBLY',
  'UK 10Y Yield':      'UK10Y',
  'US-DE 10Y Spread':  'US10Y - FGBLY',
  'S&P 500':           'SPX',
  'Gold':              'Gold (USD)',
}

interface SeriesPoint { date: string; value: number }

export default function HistoricalShocks() {
  const [episode, setEpisode]           = useState<ShockEpisode>(SHOCK_EPISODES[2]) // GFC default
  const [customStart, setCustomStart]   = useState('2020-01-01')
  const [customEnd,   setCustomEnd]     = useState('2021-12-31')
  const [selectedFormulas, setSelectedFormulas] = useState<string[]>(['US 2-10 Spread','US 10Y Yield','S&P 500'])
  const [customFormula, setCustomFormula] = useState('')
  const [seriesData, setSeriesData]     = useState<Record<string, SeriesPoint[]>>({})
  const [loading, setLoading]           = useState(false)
  const [error, setError]               = useState('')
  const [showNarrative, setShowNarrative] = useState(true)

  const start = episode.name === 'Custom' ? customStart : episode.start
  const end   = episode.name === 'Custom' ? customEnd   : episode.end

  async function load() {
    setLoading(true); setError('')
    const formulas = [
      ...selectedFormulas.map(f => ({ name: f, expr: PRESET_FORMULAS[f] })),
      ...(customFormula.trim() ? [{ name: customFormula, expr: customFormula }] : []),
    ]
    try {
      const results: Record<string, SeriesPoint[]> = {}
      await Promise.all(formulas.map(async ({ name, expr }) => {
        results[name] = await evalFormula(expr, start, end)
      }))
      setSeriesData(results)
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Error loading data')
    }
    setLoading(false)
  }

  function normalise(pts: SeriesPoint[]): SeriesPoint[] {
    if (!pts.length) return []
    const base = pts[0].value
    if (base === 0) return pts
    return pts.map(p => ({ ...p, value: p.value / base * 100 }))
  }

  const PALETTE = ['#f39200','#60a5fa','#34d399','#f87171','#a78bfa','#fbbf24','#22d3ee','#e879f9']
  const names = Object.keys(seriesData)
  const rawTraces: PlotTrace[] = names.map((n, i) => ({
    type:'scatter', mode:'lines', name:n,
    x: seriesData[n].map(p=>p.date),
    y: seriesData[n].map(p=>p.value),
    line:{ color:PALETTE[i%PALETTE.length], width:1.5 },
  }))
  const normTraces: PlotTrace[] = names.map((n, i) => ({
    type:'scatter', mode:'lines', name:n+' (idx)',
    x: normalise(seriesData[n]).map(p=>p.date),
    y: normalise(seriesData[n]).map(p=>p.value),
    line:{ color:PALETTE[i%PALETTE.length], width:1.5 },
  }))
  const stats = names.map(n => {
    const vals = seriesData[n].map(p=>p.value).filter(v=>isFinite(v))
    if (!vals.length) return null
    const chg    = vals[vals.length-1] - vals[0]
    const chgPct = vals[0] !== 0 ? chg / Math.abs(vals[0]) * 100 : NaN
    return { n, start:vals[0], end:vals[vals.length-1], chg, chgPct, peak:Math.max(...vals), trough:Math.min(...vals) }
  }).filter(Boolean)

  const ep = episode

  return (
    <div className="bond-layout">
      {/* ── Sidebar ── */}
      <aside className="bond-sidebar">
        <div className="ctrl-section">
          <div className="ctrl-label">SHOCK EPISODE</div>
          {SHOCK_EPISODES.map(e => (
            <button key={e.name}
              className={`pill ${episode.name===e.name?'active':''}`}
              style={{ marginBottom:4, width:'100%', textAlign:'left', justifyContent:'flex-start', fontSize:11 }}
              onClick={() => { setEpisode(e); setShowNarrative(true) }}>
              <span style={{ display:'inline-block', width:8, height:8, borderRadius:'50%', background:e.color, marginRight:6, flexShrink:0 }} />
              {e.name}
            </button>
          ))}
        </div>

        {episode.name === 'Custom' && (
          <div className="ctrl-section">
            <div className="ctrl-label">CUSTOM RANGE</div>
            <input type="date" className="ctrl-input" value={customStart} onChange={e=>setCustomStart(e.target.value)} style={{ marginBottom:6 }} />
            <input type="date" className="ctrl-input" value={customEnd}   onChange={e=>setCustomEnd(e.target.value)} />
          </div>
        )}

        <div className="ctrl-section">
          <div className="ctrl-label">SERIES</div>
          {Object.keys(PRESET_FORMULAS).map(f => (
            <label key={f} style={{ display:'flex', alignItems:'center', gap:8, padding:'3px 0', cursor:'pointer', fontSize:12, color: selectedFormulas.includes(f)?'#f39200':'#666' }}>
              <input type="checkbox" checked={selectedFormulas.includes(f)} onChange={e => setSelectedFormulas(s => e.target.checked ? [...s,f] : s.filter(x=>x!==f))} style={{ accentColor:'#f39200' }} />
              {f}
            </label>
          ))}
        </div>

        <div className="ctrl-section">
          <div className="ctrl-label">CUSTOM FORMULA</div>
          <input className="ctrl-input" placeholder="e.g. US10Y - UK10Y" value={customFormula} onChange={e=>setCustomFormula(e.target.value)} />
        </div>

        <button className="primary-button" style={{ width:'100%', marginTop:8 }} onClick={load} disabled={loading}>
          {loading ? 'Loading…' : 'Load Episode'}
        </button>
      </aside>

      {/* ── Main ── */}
      <div className="bond-main">
        {/* Episode header */}
        <div style={{ borderLeft:`3px solid ${ep.color}`, padding:'10px 14px', background:`rgba(0,0,0,0.2)`, borderRadius:'0 6px 6px 0', marginBottom:16 }}>
          <div style={{ color:'#555', fontSize:10, textTransform:'uppercase', letterSpacing:'0.08em', marginBottom:4 }}>{ep.eyebrow}</div>
          <div style={{ color:'#e8e8e8', fontWeight:600, fontSize:15, textTransform:'uppercase', letterSpacing:'0.04em' }}>{ep.name}</div>
          <div style={{ color:'#888', fontSize:11, marginTop:4 }}>{ep.description}{ep.name!=='Custom' ? ` · ${ep.start} → ${ep.end}` : ''}</div>
        </div>

        {/* Narrative panel */}
        {ep.name !== 'Custom' && ep.narrative.context && (
          <div style={{ background:'#141414', border:'1px solid #2a2a2a', borderRadius:8, marginBottom:20, overflow:'hidden' }}>
            <button
              onClick={() => setShowNarrative(v => !v)}
              style={{ width:'100%', background:'transparent', border:'none', borderBottom: showNarrative?'1px solid #2a2a2a':'none', padding:'10px 16px', display:'flex', justifyContent:'space-between', alignItems:'center', cursor:'pointer' }}>
              <span style={{ color:'#aaa', fontSize:12, fontWeight:600, textTransform:'uppercase', letterSpacing:'0.06em' }}>Episode Narrative</span>
              <span style={{ color:'#555', fontSize:16, lineHeight:1 }}>{showNarrative ? '−' : '+'}</span>
            </button>
            {showNarrative && (
              <div style={{ padding:'16px 18px' }}>
                <p style={{ color:'#ccc', fontSize:12, lineHeight:1.7, margin:'0 0 16px' }}>{ep.narrative.context}</p>

                {ep.narrative.drivers.length > 0 && (
                  <>
                    <div style={{ color:'#f39200', fontSize:10, textTransform:'uppercase', letterSpacing:'0.08em', fontWeight:600, marginBottom:8 }}>Key Drivers</div>
                    <ul style={{ margin:'0 0 16px', paddingLeft:18 }}>
                      {ep.narrative.drivers.map((d, i) => (
                        <li key={i} style={{ color:'#aaa', fontSize:12, lineHeight:1.65, marginBottom:4 }}>{d}</li>
                      ))}
                    </ul>
                  </>
                )}

                {ep.narrative.marketDynamics && (
                  <>
                    <div style={{ color:'#60a5fa', fontSize:10, textTransform:'uppercase', letterSpacing:'0.08em', fontWeight:600, marginBottom:8 }}>Market Dynamics</div>
                    <p style={{ color:'#aaa', fontSize:12, lineHeight:1.7, margin:'0 0 16px' }}>{ep.narrative.marketDynamics}</p>
                  </>
                )}

                {ep.narrative.lessons && (
                  <>
                    <div style={{ color:'#34d399', fontSize:10, textTransform:'uppercase', letterSpacing:'0.08em', fontWeight:600, marginBottom:8 }}>Key Lessons</div>
                    <p style={{ color:'#aaa', fontSize:12, lineHeight:1.7, margin:0 }}>{ep.narrative.lessons}</p>
                  </>
                )}
              </div>
            )}
          </div>
        )}

        {error && <div style={{ color:'#ff4d4d', fontSize:12, marginBottom:12 }}>Error: {error}<br/><small style={{color:'#888'}}>Is the FastAPI backend running?</small></div>}

        {!names.length && !loading && (
          <div style={{ color:'#555', textAlign:'center', padding:'60px 20px', fontSize:13 }}>
            Select an episode and series, then press <strong style={{ color:'#f39200' }}>Load Episode</strong>
          </div>
        )}

        {loading && (
          <div style={{ color:'#aaa', textAlign:'center', padding:60 }}>
            <div style={{ width:32, height:32, border:'3px solid #f39200', borderTopColor:'transparent', borderRadius:'50%', animation:'spin 0.8s linear infinite', margin:'0 auto 16px' }} />
            Loading series…
          </div>
        )}

        {names.length > 0 && !loading && (
          <>
            {/* Stats strip */}
            <div className="kpi-strip" style={{ marginBottom:20 }}>
              {stats.map(s => s && (
                <div key={s.n} className="kpi-card">
                  <div style={{ color:'#888', fontSize:10, textTransform:'uppercase', letterSpacing:'0.06em', marginBottom:4 }}>{s.n}</div>
                  <div style={{ color: s.chg>=0?'#00c087':'#ff4d4d', fontSize:18, fontWeight:700, fontVariantNumeric:'tabular-nums' }}>
                    {s.chg>=0?'+':''}{s.chg.toFixed(2)}
                  </div>
                  <div style={{ color:'#555', fontSize:10 }}>{isNaN(s.chgPct)?'':`${s.chgPct>=0?'+':''}${s.chgPct.toFixed(1)}%`}</div>
                </div>
              ))}
            </div>

            {/* Raw values chart */}
            <div style={{ borderLeft:'3px solid #f39200', padding:'10px 14px', background:'rgba(243,146,0,0.04)', borderRadius:'0 6px 6px 0', marginBottom:12 }}>
              <div style={{ color:'#e8e8e8', fontWeight:600, fontSize:13, textTransform:'uppercase', letterSpacing:'0.04em' }}>Raw Values</div>
            </div>
            <Chart traces={rawTraces} layout={{ yaxis:{ title:{ text:'Value', font:{ color:'#666', size:11 } } } }} />

            {/* Normalised chart */}
            <div style={{ borderLeft:'3px solid #60a5fa', padding:'10px 14px', background:'rgba(96,165,250,0.04)', borderRadius:'0 6px 6px 0', margin:'28px 0 12px' }}>
              <div style={{ color:'#e8e8e8', fontWeight:600, fontSize:13, textTransform:'uppercase', letterSpacing:'0.04em' }}>Indexed to 100 (start of episode)</div>
              <div style={{ color:'#888', fontSize:11, marginTop:4 }}>All series rebased to 100 at {start} for cross-series comparison</div>
            </div>
            <Chart traces={normTraces} layout={{ yaxis:{ title:{ text:'Index (base=100)', font:{ color:'#666', size:11 } } } }} />

            {/* Stats table */}
            <div style={{ marginTop:24, overflowX:'auto' }}>
              <table style={{ width:'100%', borderCollapse:'collapse', fontSize:12 }}>
                <thead>
                  <tr style={{ borderBottom:'1px solid #2a2a2a' }}>
                    {['Series','Start','End','Change','% Change','Peak','Trough'].map(h => (
                      <th key={h} style={{ padding:'8px 12px', textAlign:'left', color:'#666', fontWeight:500, textTransform:'uppercase', fontSize:10, letterSpacing:'0.05em', whiteSpace:'nowrap' }}>{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {stats.map(s => s && (
                    <tr key={s.n} style={{ borderBottom:'1px solid #1f1f1f' }}>
                      <td style={{ padding:'8px 12px', color:'#f39200', fontWeight:500 }}>{s.n}</td>
                      <td style={{ padding:'8px 12px', color:'#aaa', fontVariantNumeric:'tabular-nums' }}>{s.start.toFixed(2)}</td>
                      <td style={{ padding:'8px 12px', color:'#aaa', fontVariantNumeric:'tabular-nums' }}>{s.end.toFixed(2)}</td>
                      <td style={{ padding:'8px 12px', color: s.chg>=0?'#00c087':'#ff4d4d', fontVariantNumeric:'tabular-nums', fontWeight:600 }}>{s.chg>=0?'+':''}{s.chg.toFixed(2)}</td>
                      <td style={{ padding:'8px 12px', color: s.chg>=0?'#00c087':'#ff4d4d', fontVariantNumeric:'tabular-nums' }}>{isNaN(s.chgPct)?'—':(s.chgPct>=0?'+':'')+s.chgPct.toFixed(1)+'%'}</td>
                      <td style={{ padding:'8px 12px', color:'#60a5fa', fontVariantNumeric:'tabular-nums' }}>{s.peak.toFixed(2)}</td>
                      <td style={{ padding:'8px 12px', color:'#f87171', fontVariantNumeric:'tabular-nums' }}>{s.trough.toFixed(2)}</td>
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
