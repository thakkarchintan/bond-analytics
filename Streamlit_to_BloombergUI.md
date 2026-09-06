# Streamlit → Bloomberg UI Migration Plan

## Current Status (as of this handover)

**Branch:** `claude/bond-analytics-fred-api-gm3g6s`  
**Repo:** `thakkarchintan/bond-analytics`

### Completed ✅
- FastAPI backend (`api/`) — all routers created and wired
- Bond Analytics page — real data from `Final.xlsx` via `/api/bond/spread-grid`, `/formula`, `/series`
- Plotly.js added to frontend for interactive charts
- Macro Dashboard page (`MacroDashboard.tsx`) — wired to `/api/macro/dashboard`
- `render.yaml` for Render deployment
- `requirements-api.txt` for FastAPI dependencies
- `start.bat` — unified launcher (starts API + React + opens browser)
- `start-api.bat` — standalone API launcher
- Vite dev proxy: `/api` → `localhost:8000`

### Pages Done
| Page | Status | API route |
|---|---|---|
| Bond Analytics | ✅ Real data | `/api/bond/spread-grid`, `/formula`, `/series` |
| Macro Dashboard | ✅ Real data | `/api/macro/dashboard` |
| Global Capital Markets | 🔲 Placeholder only | `/api/capital-markets` |

### Pages Remaining
| # | Page | API route (already exists) |
|---|---|---|
| 1 | Yield Curves | `/api/macro/yields` + `/api/macro/ecb-curve` |
| 2 | Central Bank Rates | `/api/macro/cb-rates` + `/api/macro/cb-balance` |
| 3 | Credit Spreads | `/api/macro/credit-spreads` |
| 4 | FX Currencies | `/api/macro/fx` + `/api/macro/reer` |
| 5 | Cross Asset | `/api/macro/cross-asset` |
| 6 | Leading Indicators | `/api/macro/leading` + `/api/macro/oecd-bc` |
| 7 | Inflation & Growth | `/api/macro/inflation` |
| 8 | Fiscal Scorecard | `/api/macro/fiscal` |
| 9 | Global Capital Markets | `/api/capital-markets` |
| 10 | Bond Calculator | Client-side math only |
| 11 | Historical Shocks | `/api/bond/formula` |
| 12 | Curve Trade Builder | `/api/bond/formula` |
| 13 | Heatmap | `/api/bond/series` |
| 14 | News Summary | `/api/news` (not yet implemented) |
| 15 | Bond Portfolio | `/api/bond/portfolio` (not yet implemented) |
| 16 | Bond Simulator | `/api/bond/simulate` (not yet implemented) |
| 17 | GridTab / CustomTab | `/api/bond/formula` + `/api/formulas` |

---

## ⚠️ Known Local Issue

When starting the API, **check for zombie processes on port 8000** before starting. 
Old uvicorn processes sometimes survive window close on Windows and block the new server.

**Fix before every API start:**
```
netstat -ano | findstr :8000
taskkill /PID <number> /F
```

Then start the API:
```
start-api.bat
```

Or use the unified launcher (kills nothing automatically — fix zombie first):
```
start.bat
```

---

## Local Dev Setup

Two cmd windows needed (or use `start.bat` for both at once):

**Window 1 — API (port 8000):**
```
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

**Window 2 — React (port 5175):**
```
cd frontend
npm run dev
```

Open: `http://localhost:5175`  
API docs: `http://localhost:8000/docs`

Vite proxies `/api/*` → `http://localhost:8000` in dev mode.

---

## Architecture

```
┌─────────────────────────────────┐     ┌──────────────────────────────────────┐
│   React / Vite  (frontend/)     │     │   FastAPI  (api/)                    │
│                                 │◄───►│                                      │
│  • Bloomberg dark theme         │     │  • /api/bond/*      → Final.xlsx     │
│  • lucide-react icons           │     │  • /api/macro/*     → FRED / BIS     │
│  • Plotly.js charts             │     │  • /api/capital/*   → World Bank/IMF │
│  • fetch with credentials       │     │  • /api/news/*      → NewsAPI + LLM  │
└─────────────────────────────────┘     │  • /api/auth/*      → Google OAuth   │
                                        │  • Firebase Firestore (formulas)     │
                                        └──────────────────────────────────────┘
                                                       │
                               ┌───────────────────────┼──────────────────────┐
                               │                       │                      │
                          Final.xlsx           Parquet caches          External APIs
                                           (13 files in repo)       FRED · BIS · IMF
                                                                    DBnomics · World Bank
```

### Deployment on Render
- Single Render web service (existing URL kept)
- FastAPI serves the built React `dist/` as static files at `/`
- API routes at `/api/*`
- GitHub push to `main` triggers auto-deploy
- `render.yaml` already in repo root

---

## File Structure (what exists now)

```
api/
  main.py            ✅ FastAPI app, mounts React dist/, CORS
  config.py          ✅ env vars
  deps.py            ✅ load_final() with lru_cache
  routers/
    bond.py          ✅ /api/bond/spread-grid, /series, /columns, /formula
    macro.py         ✅ all 13 macro endpoints + /api/macro/dashboard
    capital.py       ✅ /api/capital-markets
    auth.py          ✅ Google OAuth + JWT cookie
    firebase.py      ✅ saved formulas CRUD
    news.py          🔲 not yet created

frontend/src/
  App.tsx            ✅ nav: Bond Analytics, Macro Dashboard, Capital Markets + stubs
  styles.css         ✅ Bloomberg dark theme
  pages/
    BondAnalytics.tsx     ✅ real data, Plotly custom charts, spread grid
    MacroDashboard.tsx    ✅ real data, 9 chart sections, scorecard table
    CapitalMarkets.tsx    🔲 placeholder only
    YieldCurves.tsx       🔲 not yet created
    CentralBankRates.tsx  🔲 not yet created
    CreditSpreads.tsx     🔲 not yet created
    CrossAsset.tsx        🔲 not yet created
    FXCurrencies.tsx      🔲 not yet created
    LeadingIndicators.tsx 🔲 not yet created
    InflationGrowth.tsx   🔲 not yet created
    FiscalScorecard.tsx   🔲 not yet created
    BondCalculator.tsx    🔲 not yet created
    HistoricalShocks.tsx  🔲 not yet created
    CurveTradeBuilder.tsx 🔲 not yet created
    Heatmap.tsx           🔲 not yet created
    NewsSummary.tsx       🔲 not yet created
    BondPortfolio.tsx     🔲 not yet created
    BondSimulator.tsx     🔲 not yet created
    GridTab.tsx           🔲 not yet created
    CustomTab.tsx         🔲 not yet created
  api/
    client.ts        ✅ fetch wrapper with credentials
    bond.ts          ✅ typed functions for bond routes

render.yaml          ✅ Render single-service deploy config
requirements-api.txt ✅ FastAPI + uvicorn + pyarrow + pyjwt etc.
start.bat            ✅ unified launcher (API + React + browser)
start-api.bat        ✅ standalone API launcher
start-react.bat      ✅ standalone React launcher
```

---

## Parquet Caches (all in repo root, pre-built)

| File | Contents |
|---|---|
| `gmacro_annual_cache.parquet` | IMF: GDP, growth, inflation, debt, fiscal (16 countries, 2000–2026) |
| `gmacro_yields_cache.parquet` | FRED: 10Y govt yields monthly (11 countries) |
| `gmacro_cb_rates_cache.parquet` | BIS: CB policy rates monthly (40+ CBs) |
| `gmacro_fx_cache.parquet` | FRED: FX spot vs USD (15 pairs) |
| `gmacro_spreads_cache.parquet` | ICE BofA OAS credit spreads |
| `gmacro_cross_asset_cache.parquet` | VIX, WTI, S&P 500 |
| `gmacro_leading_cache.parquet` | Claims, INDPRO, T10Y2Y, USREC |
| `gmacro_breakeven_cache.parquet` | TIPS breakeven + real yields |
| `gmacro_mmkt_cache.parquet` | Money market rates |
| `dbn_cbpol_cache.parquet` | DBnomics: CB policy rates (25 CBs) |
| `dbn_cbta_cache.parquet` | DBnomics: CB balance sheets (8 CBs) |
| `dbn_ecb_yc_cache.parquet` | DBnomics: ECB Svensson yield curve |
| `dbn_eer_cache.parquet` | DBnomics: BIS REER (14 currencies) |
| `dbn_oecd_bc_cache.parquet` | OECD: BCI/CCI/CLI (29 countries) |
| `capital_markets_cache.parquet` | World Bank equity + IMF debt |

---

## Bloomberg Theme Reference

```
Sidebar bg:     #0d0d0d
Page bg:        #111111
Card bg:        #1a1a1a
Border:         #2a2a2a
Primary text:   #e8e8e8
Secondary text: #aaaaaa
Muted text:     #888888
Accent orange:  #f39200   ← Bloomberg orange (NOT navy/teal)
Green:          #00c087
Red:            #ff4d4d
```

Plotly chart template:
```
paper_bgcolor: '#1a1a1a'
plot_bgcolor:  '#111111'
font.color:    '#aaaaaa'
gridcolor:     '#2a2a2a'
accent:        '#f39200'
```

---

## Page Pattern (copy for each new page)

Each new page follows this pattern:

1. **API call** on mount with `useEffect` → `apiFetch('/api/macro/...')`
2. **Loading state** → spinner with `spin` animation
3. **Error state** → red error + "Is the FastAPI backend running?"
4. **Left sidebar** (`bond-sidebar` class) → filter controls
5. **Main content** (`bond-main` class) → charts via `<Chart>` component
6. **Plotly chart** → lazy `import('plotly.js-dist-min')` inside `useEffect`

Shared CSS classes: `bond-layout`, `bond-sidebar`, `bond-main`, `ctrl-section`, `ctrl-label`, `ctrl-select`, `ctrl-input`, `pill`, `pill-group`, `primary-button`, `kpi-strip`, `kpi-card`, `surface-tabs`, `surface-tab`, `spread-card`, `section-header`, `placeholder-state`

The `Chart` component pattern (copy from `MacroDashboard.tsx`):
```tsx
function Chart({ traces, layout }: { traces: PlotTrace[]; layout: PlotLayout }) {
  const ref = useRef<HTMLDivElement>(null)
  useEffect(() => {
    if (!ref.current || !traces.length) return
    let cancelled = false
    import('plotly.js-dist-min').then(Plotly => {
      if (cancelled || !ref.current) return
      const base = { paper_bgcolor: '#1a1a1a', plot_bgcolor: '#111111', ... }
      Plotly.react(ref.current!, traces, { ...base, ...layout }, { responsive: true, displayModeBar: false })
    })
    return () => { cancelled = true }
  }, [traces, layout])
  return <div ref={ref} style={{ width: '100%', height: 340 }} />
}
```

---

## Environment Variables (no changes from current)

| Variable | Used by | Notes |
|---|---|---|
| `ALLOWED_USERS` | Auth | Comma-separated emails |
| `ADMINS` | Auth | Comma-separated admin emails |
| `TOKEN_KEY` | JWT | Secret key |
| `GOOGLE_CLIENT_ID` | OAuth | Google app client ID |
| `GOOGLE_CLIENT_SECRET` | OAuth | JSON string or file path |
| `FIREBASE_KEY_JSON` | Firestore | JSON string |
| `NEWS_API_KEY` | News | NewsAPI key |
| `COHERE_API_KEY` | News LLM | Cohere key |
| `OPENROUTER_API_KEY` | News LLM | OpenRouter key |
| `OAUTH_REDIRECT_URI` | OAuth | Callback URL |
| `LOCAL_DEV` | Auth | `true` bypasses auth in dev |

---

## Deployment (when ready)

1. `npm run build` in `frontend/` → produces `frontend/dist/`
2. Commit `frontend/dist/` (or let Render build it)
3. Merge `claude/bond-analytics-fred-api-gm3g6s` → `main`
4. Render auto-deploys: runs `pip install -r requirements-api.txt && cd frontend && npm install && npm run build`, then `uvicorn api.main:app`
5. FastAPI serves React at `/`, API at `/api/*` — same URL, zero downtime

---

## Suggested Next Steps for New Chat

1. Kill zombie port 8000 processes (see ⚠️ section above)
2. Start fresh with `start.bat`
3. Verify Bond Analytics and Macro Dashboard load with real data
4. Build pages in this order (all API routes already exist):
   - **Yield Curves** → `/api/macro/yields` (monthly 10Y, 11 countries) + `/api/macro/ecb-curve`
   - **Central Bank Rates** → `/api/macro/cb-rates` + `/api/macro/cb-balance`
   - **Credit Spreads** → `/api/macro/credit-spreads`
   - **FX Currencies** → `/api/macro/fx` + `/api/macro/reer`
   - **Cross Asset** → `/api/macro/cross-asset`
   - **Leading Indicators** → `/api/macro/leading` + `/api/macro/oecd-bc`
