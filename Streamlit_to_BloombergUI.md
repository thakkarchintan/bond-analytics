# Streamlit → Bloomberg UI Migration Plan

## Overview

Migrate the existing 23-page Streamlit app to a React/Vite frontend with a FastAPI backend,
deployed on Render via GitHub. Bloomberg black + orange (`#f39200`) theme throughout.

**Current stack:** Python · Streamlit · Firebase · Parquet caches · Final.xlsx  
**Target stack:** React 18 · Vite · TypeScript · FastAPI · Firebase (kept) · Render (existing URL)

---

## Architecture

```
┌─────────────────────────────────┐     ┌──────────────────────────────────────┐
│   React / Vite  (frontend/)     │     │   FastAPI  (api/)                    │
│                                 │◄───►│                                      │
│  • Bloomberg dark theme         │     │  • /api/bond/*      → Final.xlsx     │
│  • lucide-react icons           │     │  • /api/macro/*     → FRED / BIS     │
│  • React Router (page routing)  │     │  • /api/capital/*   → World Bank/IMF │
│  • Recharts or Plotly.js        │     │  • /api/news/*      → NewsAPI + LLM  │
│  • Axios for API calls          │     │  • /api/auth/*      → Google OAuth   │
└─────────────────────────────────┘     │  • Firebase Firestore (formulas)     │
                                        └──────────────────────────────────────┘
                                                       │
                               ┌───────────────────────┼──────────────────────┐
                               │                       │                      │
                          Final.xlsx           Parquet caches          External APIs
                       (→ convert to          (13 files, already       FRED · BIS · IMF
                         parquet or DB)        committed to repo)     DBnomics · World Bank
                                                                      NewsAPI · Cohere
```

### Deployment on Render
- Single Render web service (existing URL kept)
- FastAPI serves the built React `dist/` as static files at `/`
- API routes at `/api/*`
- GitHub push to `main` triggers auto-deploy (same as current Streamlit setup)
- Environment variables stay in Render dashboard (no changes needed)

---

## Phase 1 — FastAPI Backend

**Goal:** All data accessible via REST API. React pages call `/api/*` instead of reading files directly.

### Step 1.1 — Project structure
```
api/
  main.py            # FastAPI app, mounts static React build
  routers/
    bond.py          # /api/bond/series, /api/bond/formula
    macro.py         # /api/macro/yields, cb-rates, fx, credit-spreads, etc.
    capital.py       # /api/capital-markets
    news.py          # /api/news
    auth.py          # /api/auth/login, /api/auth/callback, /api/auth/me
    firebase.py      # /api/formulas (saved user formulas from Firestore)
  deps.py            # shared: current_user, cache helpers
  config.py          # env vars (FRED key, Firebase, Google OAuth, etc.)
```

### Step 1.2 — Core bond data routes
Reuses existing `data.py` logic:
```
GET  /api/bond/series?cols=US10Y,US2Y&start=1994-01-03&end=2025-11-06
GET  /api/bond/columns          → list of all column names in Final.xlsx
POST /api/bond/formula          → { formula: "US10Y - US2Y", start, end } → series JSON
GET  /api/bond/spread-grid      → all 20 preset formulas, last value + daily change
```

### Step 1.3 — Macro data routes
Reuses `global_macro_data.py`, `dbnomics_data.py`, `capital_markets_data.py`:
```
GET /api/macro/yields           → 10Y govt yields, 11 countries
GET /api/macro/cb-rates         → CB policy rates, 40+ central banks
GET /api/macro/fx               → 15 FX spot pairs vs USD
GET /api/macro/credit-spreads   → ICE BofA OAS (IG/HY/AAA-CCC)
GET /api/macro/cross-asset      → VIX, WTI, S&P 500
GET /api/macro/leading          → Claims, INDPRO, T10Y2Y, USREC
GET /api/macro/breakeven        → TIPS breakeven + real yields
GET /api/macro/inflation        → IMF inflation/growth annual
GET /api/macro/fiscal           → IMF debt/GDP, fiscal balance
GET /api/macro/oecd-bc          → OECD BCI/CCI/CLI, 29 countries
GET /api/macro/cb-balance       → CB balance sheets (BIS/DBnomics)
GET /api/macro/ecb-curve        → ECB Svensson yield curve
GET /api/macro/reer             → BIS REER, 14 currencies
GET /api/capital-markets        → World Bank equity + IMF debt/GDP
```

### Step 1.4 — Auth routes
Mirrors existing `auth/authenticator.py`:
```
GET  /api/auth/login            → redirect to Google OAuth
GET  /api/auth/callback         → exchange code → JWT cookie
GET  /api/auth/me               → current user info (email, is_admin)
POST /api/auth/logout           → clear cookie
```
JWT secret from `TOKEN_KEY` env var. Allowed users from `ALLOWED_USERS` env var (comma-separated).
Admin check from `ADMINS` env var. `LOCAL_DEV=true` bypasses auth (same as Streamlit).

### Step 1.5 — Firebase / formulas routes
```
GET    /api/formulas            → user's saved formulas from Firestore
POST   /api/formulas            → save a formula
DELETE /api/formulas/{id}       → delete a formula
GET    /api/instruments/meta    → instrument metadata (asset class, tags)
PUT    /api/instruments/meta    → save instrument metadata (admin only)
```

### Step 1.6 — News routes
```
GET /api/news?q=bonds           → NewsAPI articles + Cohere/OpenRouter summary
```

### Step 1.7 — Static file serving
FastAPI serves the React build so there's one process on Render:
```python
from fastapi.staticfiles import StaticFiles
app.mount("/", StaticFiles(directory="frontend/dist", html=True), name="static")
```

---

## Phase 2 — React Pages (priority order)

Each page: React component + API calls replacing Streamlit logic.
Charts: **Plotly.js** (matches existing Plotly Python charts 1:1 in look/feel) or Recharts.

### 2.1 Bond Analytics ✅ (shell done — needs API wiring)
- Wire spread grid to `GET /api/bond/spread-grid` (real data from Final.xlsx)
- Wire custom formula to `POST /api/bond/formula`
- Wire instrument selector to `GET /api/bond/columns`
- Add saved formulas via `GET/POST /api/formulas`

### 2.2 Yield Curves
- US Treasury curve (multiple maturities) from FRED cache
- ECB Svensson curve from DBnomics
- Historical curve animation (date slider)
- Source: `GET /api/macro/yields` + `GET /api/macro/ecb-curve`

### 2.3 Central Bank Rates
- Policy rates line chart, 40+ CBs
- CB balance sheet chart (8 CBs)
- Source: `GET /api/macro/cb-rates` + `GET /api/macro/cb-balance`

### 2.4 Global Capital Markets
- Equity market cap vs GDP bar chart
- Govt bond market size
- Historical evolution 2005–2023
- Source: `GET /api/capital-markets`

### 2.5 Credit Spreads
- ICE BofA OAS line charts (IG/HY/AAA–CCC)
- Source: `GET /api/macro/credit-spreads`

### 2.6 Cross Asset
- VIX / WTI / S&P 500 vs yield charts
- Correlation matrix heatmap
- Source: `GET /api/macro/cross-asset`

### 2.7 FX Currencies
- FX spot pairs vs USD
- BIS REER chart
- Source: `GET /api/macro/fx` + `GET /api/macro/reer`

### 2.8 Leading Indicators
- Claims, INDPRO, T10Y2Y, USREC recession shading
- OECD CLI/BCI/CCI, 29 countries
- Source: `GET /api/macro/leading` + `GET /api/macro/oecd-bc`

### 2.9 Macro Dashboard
- Multi-section: GDP, inflation, debt, current account
- Source: `GET /api/macro/inflation` + `GET /api/macro/fiscal`

### 2.10 Bond Calculator
- Pure math: price/yield/duration/DV01/convexity
- No API needed — all computed client-side or via `POST /api/bond/calculate`

### 2.11 Historical Shocks
- User-defined shock comparison charts
- Firebase saved formulas
- Source: `GET /api/bond/formula` + `GET /api/formulas`

### 2.12 Curve Trade Builder
- Spread/butterfly trade P&L
- Source: `POST /api/bond/formula`

### 2.13 Fiscal Scorecard
- Country scorecard table
- Source: `GET /api/macro/fiscal`

### 2.14 Inflation & Growth
- IMF inflation/growth line and bar charts
- Source: `GET /api/macro/inflation`

### 2.15 Heatmap
- Correlation heatmap, user-selectable instruments
- Firebase saved configs
- Source: `GET /api/bond/series` + `GET /api/formulas`

### 2.16 News Summary
- NewsAPI articles with Cohere/OpenRouter LLM summaries
- Source: `GET /api/news`

### 2.17 Bond Portfolio & Simulator
- Portfolio P&L, duration, convexity tables
- Monte Carlo / scenario simulation charts
- Source: `POST /api/bond/portfolio` + `POST /api/bond/simulate`

### 2.18 GridTab / CustomTab
- User-defined formula grids with Firebase persistence
- Source: `GET /api/bond/formula` + `GET/POST /api/formulas`

---

## Phase 3 — Auth, Admin & Polish

- Google OAuth login page (replaces Streamlit auth flow)
- JWT cookie auth on all API routes + React route guards
- Admin-only pages: Data Sources catalog, Changelog, Roadmap
- Dark Plotly.js chart theme consistent with Bloomberg palette
- Mobile-responsive layout improvements
- Error boundaries + loading skeletons on all pages

---

## Phase 4 — Deploy on Render

### Render configuration (`render.yaml`)
```yaml
services:
  - type: web
    name: bond-analytics
    runtime: python
    buildCommand: |
      pip install -r requirements-api.txt
      cd frontend && npm install && npm run build
    startCommand: uvicorn api.main:app --host 0.0.0.0 --port $PORT
    envVars:
      - key: ALLOWED_USERS
        sync: false
      - key: ADMINS
        sync: false
      - key: TOKEN_KEY
        sync: false
      - key: GOOGLE_CLIENT_SECRET
        sync: false
      - key: FIREBASE_KEY_JSON
        sync: false
      - key: NEWS_API_KEY
        sync: false
      - key: COHERE_API_KEY
        sync: false
      - key: OPENROUTER_API_KEY
        sync: false
```

### GitHub → Render auto-deploy
- Push to `main` branch triggers Render build
- Same URL as current Streamlit deployment — zero downtime cutover
- During migration: Streamlit still runs on `main`; React/FastAPI developed on feature branch
- Cutover: merge feature branch → `main` → Render deploys new app automatically

---

## Environment Variables (no changes from current)

| Variable | Used by | Notes |
|---|---|---|
| `ALLOWED_USERS` | Auth | Comma-separated emails |
| `ADMINS` | Auth | Comma-separated admin emails |
| `TOKEN_KEY` | JWT | Secret key |
| `GOOGLE_CLIENT_SECRET` | OAuth | JSON string or file path |
| `FIREBASE_KEY_JSON` | Firestore | JSON string |
| `NEWS_API_KEY` | News | NewsAPI key |
| `COHERE_API_KEY` | News LLM | Cohere key |
| `OPENROUTER_API_KEY` | News LLM | OpenRouter key |
| `LOCAL_DEV` | Auth | `true` bypasses auth |

---

## Files to Create (summary)

```
api/
  main.py
  config.py
  deps.py
  routers/
    bond.py
    macro.py
    capital.py
    auth.py
    firebase.py
    news.py

frontend/src/
  pages/
    BondAnalytics.tsx      ✅ shell done
    YieldCurves.tsx
    CentralBankRates.tsx
    CapitalMarkets.tsx     (placeholder done)
    CreditSpreads.tsx
    CrossAsset.tsx
    FXCurrencies.tsx
    LeadingIndicators.tsx
    MacroDashboard.tsx
    BondCalculator.tsx
    HistoricalShocks.tsx
    CurveTradeBuilder.tsx
    FiscalScorecard.tsx
    InflationGrowth.tsx
    Heatmap.tsx
    NewsSummary.tsx
    BondPortfolio.tsx
    BondSimulator.tsx
    GridTab.tsx
    CustomTab.tsx
    Admin/
      DataSources.tsx
      Changelog.tsx
      Roadmap.tsx
  components/
    Chart.tsx              # shared Plotly.js wrapper
    Auth/
      LoginPage.tsx
      AuthGuard.tsx
  api/
    client.ts              # axios instance with JWT handling
    bond.ts
    macro.ts
    capital.ts
    news.ts
    auth.ts
    formulas.ts

render.yaml
requirements-api.txt
```

---

## Suggested Starting Point for Next Session

1. Create `api/main.py` + `api/routers/bond.py`
2. Wire `GET /api/bond/spread-grid` to real `Final.xlsx` data
3. Connect React Bond Analytics page to real API (remove mock sparklines)
4. Add Plotly.js to frontend for proper interactive charts
5. Verify full end-to-end: React → FastAPI → Final.xlsx → chart in browser
