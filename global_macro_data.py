"""
Shared data layer for the four new Global Macro pages.

Three datasets, each parquet-cached (built on first load / manual refresh):
  gmacro_annual_cache.parquet   — IMF annual: GDP, CPI, fiscal, debt, unemployment, CA
  gmacro_policy_cache.parquet   — BIS monthly: central bank policy rates
  gmacro_fx_cache.parquet       — FRED monthly: FX spot rates vs USD

Sources:
  IMF Datamapper API  — https://www.imf.org/external/datamapper/api/v1/
  BIS SDMX API        — https://data.bis.org/api/v1/
  FRED direct CSV     — https://fred.stlouisfed.org/graph/fredgraph.csv
"""
from __future__ import annotations

import warnings
from io import StringIO
from pathlib import Path

import pandas as pd
import requests
import streamlit as st

# ── Cache paths ────────────────────────────────────────────────────────────────

_HERE         = Path(__file__).parent
ANNUAL_CACHE  = _HERE / "gmacro_annual_cache.parquet"
POLICY_CACHE  = _HERE / "gmacro_policy_cache.parquet"
FX_CACHE      = _HERE / "gmacro_fx_cache.parquet"
YIELD_CACHE   = _HERE / "gmacro_yields_cache.parquet"
REER_CACHE    = _HERE / "gmacro_reer_cache.parquet"

# ── Country / CB universe ──────────────────────────────────────────────────────

# name → {imf ISO3, BIS area code, colour}
COUNTRY_META: dict[str, dict] = {
    "United States":  {"imf": "USA", "bis": "US", "color": "#60a5fa"},
    "Euro Area":      {"imf": "DEU", "bis": "XM", "color": "#a78bfa"},
    "United Kingdom": {"imf": "GBR", "bis": "GB", "color": "#22d3ee"},
    "Japan":          {"imf": "JPN", "bis": "JP", "color": "#34d399"},
    "China":          {"imf": "CHN", "bis": "CN", "color": "#f87171"},
    "India":          {"imf": "IND", "bis": "IN", "color": "#f472b6"},
    "Canada":         {"imf": "CAN", "bis": "CA", "color": "#818cf8"},
    "Australia":      {"imf": "AUS", "bis": "AU", "color": "#fb923c"},
    "Brazil":         {"imf": "BRA", "bis": "BR", "color": "#a3e635"},
    "South Korea":    {"imf": "KOR", "bis": "KR", "color": "#fbbf24"},
    "Switzerland":    {"imf": "CHE", "bis": "CH", "color": "#e879f9"},
    "Sweden":         {"imf": "SWE", "bis": "SE", "color": "#2dd4bf"},
    "Mexico":         {"imf": "MEX", "bis": "MX", "color": "#c084fc"},
    "South Africa":   {"imf": "ZAF", "bis": "ZA", "color": "#f9a8d4"},
    "Norway":         {"imf": "NOR", "bis": "NO", "color": "#67e8f9"},
    "New Zealand":    {"imf": "NZL", "bis": "NZ", "color": "#86efac"},
}

COUNTRY_COLORS: dict[str, str] = {n: m["color"] for n, m in COUNTRY_META.items()}
ALL_NAMES:      list[str]       = list(COUNTRY_META.keys())
CORE_NAMES:     list[str]       = [
    "United States", "Euro Area", "United Kingdom", "Japan",
    "China", "India", "Canada", "Australia", "Brazil", "South Korea",
]

_IMF_CODES   = ",".join(m["imf"] for m in COUNTRY_META.values())
_IMF_TO_NAME = {m["imf"]: n for n, m in COUNTRY_META.items()}
_BIS_TO_NAME = {m["bis"]: n for n, m in COUNTRY_META.items()}

# Additional BIS central banks shown on CBR page (beyond our core 16)
BIS_CB_LABELS: dict[str, str] = {
    **{m["bis"]: n for n, m in COUNTRY_META.items()},
    "TR": "Turkey",    "DK": "Denmark",    "PL": "Poland",
    "CZ": "Czech Rep", "HU": "Hungary",    "CL": "Chile",
    "CO": "Colombia",  "ID": "Indonesia",  "IL": "Israel",
    "SA": "Saudi Arabia", "SG": "Singapore", "HK": "Hong Kong",
    "TH": "Thailand",  "PH": "Philippines","MY": "Malaysia",
    "RU": "Russia",    "AR": "Argentina",  "PE": "Peru",
}

# FRED 10Y government bond yield series (OECD via FRED, monthly %)
YIELD_SERIES: dict[str, str] = {
    "GS10":            "United States",
    "IRLTLT01DEM156N": "Euro Area",        # Germany 10Y bund as proxy
    "IRLTLT01GBM156N": "United Kingdom",
    "IRLTLT01JPM156N": "Japan",
    "IRLTLT01CAM156N": "Canada",
    "IRLTLT01AUM156N": "Australia",
    "IRLTLT01KRM156N": "South Korea",
    "IRLTLT01CHM156N": "Switzerland",
    "IRLTLT01SEM156N": "Sweden",
    "IRLTLT01NOM156N": "Norway",
    "IRLTLT01NZM156N": "New Zealand",
}

# FRED FX series → metadata
# invert=True means FRED gives USD-per-foreign; we flip to local-per-USD
FX_SERIES: dict[str, dict] = {
    "DEXJPUS": {"country": "Japan",         "ccy": "JPY", "invert": False},
    "DEXUSEU": {"country": "Euro Area",     "ccy": "EUR", "invert": True},
    "DEXUSUK": {"country": "United Kingdom","ccy": "GBP", "invert": True},
    "DEXCHUS": {"country": "China",         "ccy": "CNY", "invert": False},
    "DEXINUS": {"country": "India",         "ccy": "INR", "invert": False},
    "DEXCAUS": {"country": "Canada",        "ccy": "CAD", "invert": False},
    "DEXUSAL": {"country": "Australia",     "ccy": "AUD", "invert": True},
    "DEXBZUS": {"country": "Brazil",        "ccy": "BRL", "invert": False},
    "DEXKOUS": {"country": "South Korea",   "ccy": "KRW", "invert": False},
    "DEXSZUS": {"country": "Switzerland",   "ccy": "CHF", "invert": False},
    "DEXSDUS": {"country": "Sweden",        "ccy": "SEK", "invert": False},
    "DEXMXUS": {"country": "Mexico",        "ccy": "MXN", "invert": False},
    "DEXSFUS": {"country": "South Africa",  "ccy": "ZAR", "invert": False},
    "DEXNOUS": {"country": "Norway",        "ccy": "NOK", "invert": False},
    "DEXNZUS": {"country": "New Zealand",   "ccy": "NZD", "invert": False},
}


# ── IMF Datamapper fetchers ────────────────────────────────────────────────────

def _imf(indicator: str) -> pd.DataFrame:
    url = f"https://www.imf.org/external/datamapper/api/v1/{indicator}/{_IMF_CODES}"
    try:
        r = requests.get(url, timeout=30)
        r.raise_for_status()
        data = r.json().get("values", {}).get(indicator, {})
        rows = []
        for iso, yr_data in data.items():
            name = _IMF_TO_NAME.get(iso)
            if not name:
                continue
            for yr_str, val in yr_data.items():
                yr = int(yr_str)
                if 2000 <= yr <= 2026 and val is not None:
                    rows.append({"Country": name, "Year": yr, indicator: float(val)})
        return pd.DataFrame(rows)
    except Exception as exc:
        warnings.warn(f"IMF {indicator} failed: {exc}")
        return pd.DataFrame(columns=["Country", "Year", indicator])


def _build_annual() -> pd.DataFrame:
    indicators = {
        "NGDPD":        "GDP_USD_Bn",
        "NGDP_RPCH":    "RealGDP_Pct",
        "PCPIPCH":      "CPI_Pct",
        "GGXCNL_NGDP":  "FiscalBal_Pct",
        "GGXONLB_NGDP": "PrimaryBal_Pct",
        "GGXWDG_NGDP":  "DebtGDP_Pct",
        "BCA_NGDPD":    "CurrentAcct_Pct",
        "LUR":          "Unemployment_Pct",
    }
    grid = pd.DataFrame(
        [(n, y) for n in ALL_NAMES for y in range(2000, 2027)],
        columns=["Country", "Year"],
    )
    for imf_code, col in indicators.items():
        raw = _imf(imf_code)
        if not raw.empty:
            raw = raw.rename(columns={imf_code: col})
            grid = grid.merge(raw[["Country", "Year", col]], on=["Country", "Year"], how="left")
        else:
            grid[col] = float("nan")
    return grid


# ── BIS CBPOL fetcher ─────────────────────────────────────────────────────────

def _build_policy_rates() -> pd.DataFrame:
    url = (
        "https://data.bis.org/api/v1/data/BIS,WS_CBPOL_M,1.0/all"
        "?format=csv&startPeriod=2000-01&endPeriod=2025-12"
    )
    try:
        r = requests.get(url, timeout=90, headers={"Accept": "text/csv"})
        r.raise_for_status()
        df = pd.read_csv(StringIO(r.text))
        # SDMX-CSV columns: FREQ, REF_AREA, INTEREST_RATE, TIME_PERIOD, OBS_VALUE, ...
        need = {"REF_AREA", "TIME_PERIOD", "OBS_VALUE"}
        if not need.issubset(df.columns):
            warnings.warn(f"BIS CSV missing columns. Got: {df.columns.tolist()}")
            return pd.DataFrame()
        df = df[["REF_AREA", "TIME_PERIOD", "OBS_VALUE"]].copy()
        df.columns = ["BIS_Code", "Period", "Rate_Pct"]
        df["Rate_Pct"] = pd.to_numeric(df["Rate_Pct"], errors="coerce")
        df = df.dropna(subset=["Rate_Pct"])
        df["Date"] = pd.to_datetime(df["Period"].astype(str) + "-01", errors="coerce")
        df = df.dropna(subset=["Date"])
        df["Country"] = df["BIS_Code"].map(BIS_CB_LABELS).fillna(df["BIS_Code"])
        return df[["BIS_Code", "Country", "Date", "Rate_Pct"]].sort_values(["Country", "Date"])
    except Exception as exc:
        warnings.warn(f"BIS CBPOL failed: {exc}")
        return pd.DataFrame()


# ── FRED FX fetcher ───────────────────────────────────────────────────────────

_FRED_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "text/html,application/xhtml+xml,*/*",
}


def _build_fx() -> pd.DataFrame:
    frames = []
    for series_id, meta in FX_SERIES.items():
        url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}"
        try:
            r = requests.get(url, timeout=45, headers=_FRED_HEADERS)
            r.raise_for_status()
            df = pd.read_csv(StringIO(r.text), na_values=".")
            if df.shape[1] < 2:
                continue
            df.columns = ["Date", "Value"]
            df["Date"]  = pd.to_datetime(df["Date"], errors="coerce")
            df["Value"] = pd.to_numeric(df["Value"], errors="coerce")
            df = df.dropna()
            df = df[df["Date"].dt.year >= 2000]
            # Normalise: LocalPerUSD = how many local units per 1 USD
            df["LocalPerUSD"] = (1.0 / df["Value"]) if meta["invert"] else df["Value"]
            df["Country"]  = meta["country"]
            df["Currency"] = meta["ccy"]
            frames.append(df[["Date", "Country", "Currency", "LocalPerUSD"]])
        except Exception as exc:
            warnings.warn(f"FRED {series_id} failed: {exc}")
    return (
        pd.concat(frames, ignore_index=True).sort_values(["Country", "Date"])
        if frames else pd.DataFrame()
    )


# ── FRED 10Y yield fetcher ────────────────────────────────────────────────────

def _build_teny_yields() -> pd.DataFrame:
    frames = []
    for series_id, country in YIELD_SERIES.items():
        url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}"
        try:
            r = requests.get(url, timeout=45, headers=_FRED_HEADERS)
            r.raise_for_status()
            df = pd.read_csv(StringIO(r.text), na_values=".")
            if df.shape[1] < 2:
                continue
            df.columns = ["Date", "Yield_Pct"]
            df["Date"]      = pd.to_datetime(df["Date"], errors="coerce")
            df["Yield_Pct"] = pd.to_numeric(df["Yield_Pct"], errors="coerce")
            df = df.dropna()
            df = df[df["Date"].dt.year >= 2000]
            df["Country"] = country
            frames.append(df[["Date", "Country", "Yield_Pct"]])
        except Exception as exc:
            warnings.warn(f"FRED {series_id} failed: {exc}")
    if not frames:
        return pd.DataFrame()
    return pd.concat(frames, ignore_index=True).sort_values(["Country", "Date"])


# ── BIS REER fetcher ──────────────────────────────────────────────────────────

def _build_reer() -> pd.DataFrame:
    url = (
        "https://data.bis.org/api/v1/data/BIS,WS_EER_M,1.0/all"
        "?format=csv&startPeriod=2000-01"
    )
    try:
        r = requests.get(url, timeout=120, headers={"Accept": "text/csv"})
        r.raise_for_status()
        df = pd.read_csv(StringIO(r.text))
        need = {"REF_AREA", "TIME_PERIOD", "OBS_VALUE"}
        if not need.issubset(df.columns):
            warnings.warn(f"BIS EER missing columns. Got: {df.columns.tolist()}")
            return pd.DataFrame()
        if "EER_TYPE" in df.columns:
            df = df[df["EER_TYPE"].astype(str) == "R"]
        if "EER_BASKET" in df.columns:
            df = df[df["EER_BASKET"].astype(str) == "B"]
        df = df[["REF_AREA", "TIME_PERIOD", "OBS_VALUE"]].copy()
        df.columns = ["BIS_Code", "Period", "REER"]
        df["REER"]    = pd.to_numeric(df["REER"], errors="coerce")
        df            = df.dropna(subset=["REER"])
        df["Date"]    = pd.to_datetime(df["Period"].astype(str) + "-01", errors="coerce")
        df            = df.dropna(subset=["Date"])
        df["Country"] = df["BIS_Code"].map(_BIS_TO_NAME)
        df            = df.dropna(subset=["Country"])
        return df[["Country", "Date", "REER"]].sort_values(["Country", "Date"])
    except Exception as exc:
        warnings.warn(f"BIS REER failed: {exc}")
        return pd.DataFrame()


# ── Refresh helpers ────────────────────────────────────────────────────────────

def refresh_annual() -> pd.DataFrame:
    df = _build_annual()
    if not df.empty:
        df.to_parquet(ANNUAL_CACHE, index=False)
        load_annual.clear()
    return df


def refresh_policy_rates() -> pd.DataFrame:
    df = _build_policy_rates()
    if not df.empty:
        df.to_parquet(POLICY_CACHE, index=False)
        load_policy_rates.clear()
    return df


def refresh_fx() -> pd.DataFrame:
    df = _build_fx()
    if not df.empty:
        df.to_parquet(FX_CACHE, index=False)
        load_fx.clear()
    return df


def refresh_teny_yields() -> pd.DataFrame:
    df = _build_teny_yields()
    if not df.empty:
        df.to_parquet(YIELD_CACHE, index=False)
        load_teny_yields.clear()
    return df


def refresh_reer() -> pd.DataFrame:
    df = _build_reer()
    if not df.empty:
        df.to_parquet(REER_CACHE, index=False)
        load_reer.clear()
    return df


def refresh_all() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Fetch all three datasets. Returns (annual, policy, fx)."""
    return refresh_annual(), refresh_policy_rates(), refresh_fx()


# ── Loaders (cache-first, fall back to API) ───────────────────────────────────

@st.cache_data(show_spinner=False)
def load_annual() -> pd.DataFrame:
    if ANNUAL_CACHE.exists():
        return pd.read_parquet(ANNUAL_CACHE)
    return refresh_annual()


@st.cache_data(show_spinner=False)
def load_policy_rates() -> pd.DataFrame:
    if POLICY_CACHE.exists():
        return pd.read_parquet(POLICY_CACHE)
    return refresh_policy_rates()


@st.cache_data(show_spinner=False)
def load_fx() -> pd.DataFrame:
    if FX_CACHE.exists():
        return pd.read_parquet(FX_CACHE)
    return refresh_fx()


@st.cache_data(show_spinner=False)
def load_teny_yields() -> pd.DataFrame:
    if YIELD_CACHE.exists():
        return pd.read_parquet(YIELD_CACHE)
    return refresh_teny_yields()


@st.cache_data(show_spinner=False)
def load_reer() -> pd.DataFrame:
    if REER_CACHE.exists():
        return pd.read_parquet(REER_CACHE)
    return refresh_reer()


# ── Additional datasets: US curve · breakeven · credit spreads · money mkts · direct CB rates ──

US_CURVE_CACHE  = _HERE / "gmacro_us_curve_cache.parquet"
BREAKEVEN_CACHE = _HERE / "gmacro_breakeven_cache.parquet"
SPREADS_CACHE   = _HERE / "gmacro_spreads_cache.parquet"
MMKT_CACHE      = _HERE / "gmacro_mmkt_cache.parquet"
CB_RATES_CACHE  = _HERE / "gmacro_cb_rates_cache.parquet"

# US Treasury constant-maturity yields (FRED, daily)
US_CURVE_SERIES: dict[str, str] = {
    "DGS1MO": "1M",  "DGS3MO": "3M",  "DGS6MO": "6M",
    "DGS1":   "1Y",  "DGS2":   "2Y",  "DGS3":   "3Y",
    "DGS5":   "5Y",  "DGS7":   "7Y",  "DGS10":  "10Y",
    "DGS20":  "20Y", "DGS30":  "30Y",
}
US_CURVE_MAT_YRS: dict[str, float] = {
    "1M": 1/12, "3M": 3/12, "6M": 6/12,
    "1Y": 1,    "2Y": 2,    "3Y": 3,
    "5Y": 5,    "7Y": 7,    "10Y": 10,
    "20Y": 20,  "30Y": 30,
}

# TIPS breakeven inflation & real yields (FRED, daily)
BREAKEVEN_SERIES: dict[str, str] = {
    "T5YIE":  "5Y Breakeven",
    "T10YIE": "10Y Breakeven",
    "T5YIFR": "5-10Y Fwd Breakeven",
    "DFII5":  "5Y Real Yield",
    "DFII10": "10Y Real Yield",
}

# ICE BofA OAS indices (FRED, daily, %)
SPREADS_SERIES: dict[str, str] = {
    "BAMLC0A0CM":   "IG",
    "BAMLC0A1CAAA": "AAA",
    "BAMLC0A2CAA":  "AA",
    "BAMLC0A3CA":   "A",
    "BAMLC0A4CBBB": "BBB",
    "BAMLH0A0HYM2": "HY",
    "BAMLH0A1HYBB": "BB",
    "BAMLH0A2HYB":  "B",
    "BAMLH0A3HYC":  "CCC",
}

# Money-market rates (FRED, daily)
MMKT_SERIES: dict[str, str] = {
    "SOFR": "SOFR",
    "DFF":  "Fed Funds (Eff.)",
}


def _fred_daily(series_id: str, col: str = "Value") -> pd.DataFrame:
    """Fetch one FRED daily/monthly series; return {Date, <col>} from 2000 onward."""
    url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}"
    try:
        r = requests.get(url, timeout=45, headers=_FRED_HEADERS)
        r.raise_for_status()
        df = pd.read_csv(StringIO(r.text), na_values=".")
        if df.shape[1] < 2:
            return pd.DataFrame()
        df.columns = ["Date", col]
        df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
        df[col]    = pd.to_numeric(df[col], errors="coerce")
        return df.dropna().loc[lambda d: d["Date"].dt.year >= 2000]
    except Exception as exc:
        warnings.warn(f"FRED {series_id} failed: {exc}")
        return pd.DataFrame()


def _build_us_curve() -> pd.DataFrame:
    frames = []
    for sid, mat in US_CURVE_SERIES.items():
        df = _fred_daily(sid, "Yield_Pct")
        if df.empty:
            continue
        df["Maturity"] = mat
        frames.append(df[["Date", "Maturity", "Yield_Pct"]])
    return (
        pd.concat(frames, ignore_index=True).sort_values(["Date", "Maturity"])
        if frames else pd.DataFrame()
    )


def _build_breakeven() -> pd.DataFrame:
    frames = []
    for sid, name in BREAKEVEN_SERIES.items():
        df = _fred_daily(sid, "Value")
        if df.empty:
            continue
        df["Series"] = name
        frames.append(df[["Date", "Series", "Value"]])
    return (
        pd.concat(frames, ignore_index=True).sort_values(["Series", "Date"])
        if frames else pd.DataFrame()
    )


def _build_spreads() -> pd.DataFrame:
    frames = []
    for sid, name in SPREADS_SERIES.items():
        df = _fred_daily(sid, "OAS_Pct")
        if df.empty:
            continue
        df["Series"] = name
        frames.append(df[["Date", "Series", "OAS_Pct"]])
    return (
        pd.concat(frames, ignore_index=True).sort_values(["Series", "Date"])
        if frames else pd.DataFrame()
    )


def _build_mmkt_rates() -> pd.DataFrame:
    frames = []
    for sid, name in MMKT_SERIES.items():
        df = _fred_daily(sid, "Rate_Pct")
        if df.empty:
            continue
        df["Series"] = name
        frames.append(df[["Date", "Series", "Rate_Pct"]])
    return (
        pd.concat(frames, ignore_index=True).sort_values(["Series", "Date"])
        if frames else pd.DataFrame()
    )


def _build_cb_rates_direct() -> pd.DataFrame:
    """Multi-source CB policy rates: FRED (US), ECB SDW, Bank of England."""
    frames = []

    # US — FRED FEDFUNDS (monthly avg of effective rate)
    df_us = _fred_daily("FEDFUNDS", "Rate_Pct")
    if not df_us.empty:
        df_us["Country"] = "United States"
        frames.append(df_us[["Country", "Date", "Rate_Pct"]])

    # ECB — deposit facility rate via ECB Statistical Data Warehouse
    try:
        ecb_url = (
            "https://data-api.ecb.europa.eu/service/data/FM/"
            "B.U2.EUR.4F.KR.DFR.LEV?format=csvdata&startPeriod=2000-01-01"
        )
        r = requests.get(ecb_url, timeout=30)
        r.raise_for_status()
        ecb = pd.read_csv(StringIO(r.text))
        if {"TIME_PERIOD", "OBS_VALUE"}.issubset(ecb.columns):
            ecb = ecb[["TIME_PERIOD", "OBS_VALUE"]].copy()
            ecb.columns = ["Date", "Rate_Pct"]
            ecb["Date"]     = pd.to_datetime(ecb["Date"], errors="coerce")
            ecb["Rate_Pct"] = pd.to_numeric(ecb["Rate_Pct"], errors="coerce")
            ecb = ecb.dropna()
            ecb["Country"] = "Euro Area"
            frames.append(ecb[["Country", "Date", "Rate_Pct"]])
    except Exception as exc:
        warnings.warn(f"ECB SDW failed: {exc}")

    # UK — Bank of England Bank Rate
    try:
        boe_url = (
            "https://www.bankofengland.co.uk/boeapps/database/fromshowcolumns.asp"
            "?CSVF=TT&UsingCodes=Y&VFD=N&SeriesCodes=IUDBEDR"
        )
        r = requests.get(boe_url, timeout=30, headers={
            "User-Agent": _FRED_HEADERS["User-Agent"],
            "Accept": "text/html,application/xhtml+xml,*/*",
        })
        r.raise_for_status()
        boe = pd.read_csv(StringIO(r.text))
        if boe.shape[1] >= 2:
            boe = boe.iloc[:, :2].copy()
            boe.columns = ["Date", "Rate_Pct"]
            boe["Date"]     = pd.to_datetime(boe["Date"], dayfirst=True, errors="coerce")
            boe["Rate_Pct"] = pd.to_numeric(boe["Rate_Pct"], errors="coerce")
            boe = boe.dropna()
            boe = boe[boe["Date"].dt.year >= 2000]
            boe["Country"] = "United Kingdom"
            frames.append(boe[["Country", "Date", "Rate_Pct"]])
    except Exception as exc:
        warnings.warn(f"BoE API failed: {exc}")

    return (
        pd.concat(frames, ignore_index=True).sort_values(["Country", "Date"])
        if frames else pd.DataFrame()
    )


# ── Refresh helpers ────────────────────────────────────────────────────────────

def refresh_us_curve() -> pd.DataFrame:
    df = _build_us_curve()
    if not df.empty:
        df.to_parquet(US_CURVE_CACHE, index=False)
        load_us_curve.clear()
    return df


def refresh_breakeven() -> pd.DataFrame:
    df = _build_breakeven()
    if not df.empty:
        df.to_parquet(BREAKEVEN_CACHE, index=False)
        load_breakeven.clear()
    return df


def refresh_spreads() -> pd.DataFrame:
    df = _build_spreads()
    if not df.empty:
        df.to_parquet(SPREADS_CACHE, index=False)
        load_spreads.clear()
    return df


def refresh_mmkt_rates() -> pd.DataFrame:
    df = _build_mmkt_rates()
    if not df.empty:
        df.to_parquet(MMKT_CACHE, index=False)
        load_mmkt_rates.clear()
    return df


def refresh_cb_rates_direct() -> pd.DataFrame:
    df = _build_cb_rates_direct()
    if not df.empty:
        df.to_parquet(CB_RATES_CACHE, index=False)
        load_cb_rates_direct.clear()
    return df


# ── Loaders (cache-first, fall back to API) ───────────────────────────────────

@st.cache_data(show_spinner=False)
def load_us_curve() -> pd.DataFrame:
    if US_CURVE_CACHE.exists():
        return pd.read_parquet(US_CURVE_CACHE)
    return refresh_us_curve()


@st.cache_data(show_spinner=False)
def load_breakeven() -> pd.DataFrame:
    if BREAKEVEN_CACHE.exists():
        return pd.read_parquet(BREAKEVEN_CACHE)
    return refresh_breakeven()


@st.cache_data(show_spinner=False)
def load_spreads() -> pd.DataFrame:
    if SPREADS_CACHE.exists():
        return pd.read_parquet(SPREADS_CACHE)
    return refresh_spreads()


@st.cache_data(show_spinner=False)
def load_mmkt_rates() -> pd.DataFrame:
    if MMKT_CACHE.exists():
        return pd.read_parquet(MMKT_CACHE)
    return refresh_mmkt_rates()


@st.cache_data(show_spinner=False)
def load_cb_rates_direct() -> pd.DataFrame:
    if CB_RATES_CACHE.exists():
        return pd.read_parquet(CB_RATES_CACHE)
    return refresh_cb_rates_direct()


# ── Cross-Asset Dashboard data ─────────────────────────────────────────────────

CROSS_ASSET_CACHE = _HERE / "gmacro_cross_asset_cache.parquet"
LEADING_CACHE     = _HERE / "gmacro_leading_cache.parquet"

CROSS_ASSET_SERIES: dict[str, str] = {
    "VIXCLS":     "VIX",
    "DCOILWTICO": "WTI Crude",
    "SP500":      "S&P 500",
}

LEADING_SERIES: dict[str, str] = {
    "ICSA":    "Initial Claims",
    "UMCSENT": "Consumer Sentiment",
    "HOUST":   "Housing Starts",
    "INDPRO":  "Industrial Production",
    "UNRATE":  "Unemployment",
    "T10Y2Y":  "2Y10Y Spread",
    "USREC":   "Recession",
}


def _build_cross_asset() -> pd.DataFrame:
    rows = []
    for sid, name in CROSS_ASSET_SERIES.items():
        try:
            df = _fred_daily(sid)
            if df.empty:
                continue
            df["Series"] = name
            rows.append(df.rename(columns={"Value": "Value"}))
        except Exception:
            pass
    if not rows:
        return pd.DataFrame()
    out = pd.concat(rows, ignore_index=True)
    out["Date"] = pd.to_datetime(out["Date"])
    return out.sort_values(["Series", "Date"]).reset_index(drop=True)


def _build_leading_indicators() -> pd.DataFrame:
    rows = []
    for sid, name in LEADING_SERIES.items():
        try:
            df = _fred_daily(sid)
            if df.empty:
                continue
            df["Series"] = name
            rows.append(df)
        except Exception:
            pass
    if not rows:
        return pd.DataFrame()
    out = pd.concat(rows, ignore_index=True)
    out["Date"] = pd.to_datetime(out["Date"])
    return out.sort_values(["Series", "Date"]).reset_index(drop=True)


def refresh_cross_asset() -> pd.DataFrame:
    df = _build_cross_asset()
    if not df.empty:
        df.to_parquet(CROSS_ASSET_CACHE, index=False)
        load_cross_asset.clear()
    return df


def refresh_leading_indicators() -> pd.DataFrame:
    df = _build_leading_indicators()
    if not df.empty:
        df.to_parquet(LEADING_CACHE, index=False)
        load_leading_indicators.clear()
    return df


@st.cache_data(show_spinner=False)
def load_cross_asset() -> pd.DataFrame:
    if CROSS_ASSET_CACHE.exists():
        return pd.read_parquet(CROSS_ASSET_CACHE)
    return refresh_cross_asset()


@st.cache_data(show_spinner=False)
def load_leading_indicators() -> pd.DataFrame:
    if LEADING_CACHE.exists():
        return pd.read_parquet(LEADING_CACHE)
    return refresh_leading_indicators()


# ── Historical credit spreads (full history, OAS suffix series) ───────────────

SPREADS_LONG_CACHE = _HERE / "gmacro_spreads_long_cache.parquet"

SPREADS_LONG_SERIES: dict[str, str] = {
    "BAMLH0A0HYM2OAS": "HY",   # US HY OAS, daily from Dec 1996
    "BAMLC0A4CBBBOAS": "BBB",  # US BBB OAS, daily from ~1997
    "BAMLH0A1HYBBOAS": "BB",   # US BB OAS, daily from ~1997
}


def _fred_all(series_id: str, col: str = "Value") -> pd.DataFrame:
    """Fetch one FRED series with full history (no year cutoff)."""
    url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}"
    try:
        r = requests.get(url, timeout=45, headers=_FRED_HEADERS)
        r.raise_for_status()
        df = pd.read_csv(StringIO(r.text), na_values=".")
        if df.shape[1] < 2:
            return pd.DataFrame()
        df.columns = ["Date", col]
        df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
        df[col]    = pd.to_numeric(df[col], errors="coerce")
        return df.dropna()
    except Exception as exc:
        warnings.warn(f"FRED {series_id} failed: {exc}")
        return pd.DataFrame()


def _build_spreads_long() -> pd.DataFrame:
    frames = []
    for sid, name in SPREADS_LONG_SERIES.items():
        df = _fred_all(sid, "OAS_Pct")
        if df.empty:
            continue
        df["Series"] = name
        frames.append(df[["Date", "Series", "OAS_Pct"]])
    return (
        pd.concat(frames, ignore_index=True).sort_values(["Series", "Date"])
        if frames else pd.DataFrame()
    )


def refresh_spreads_long() -> pd.DataFrame:
    df = _build_spreads_long()
    if not df.empty:
        df.to_parquet(SPREADS_LONG_CACHE, index=False)
        load_spreads_long.clear()
    return df


@st.cache_data(show_spinner=False)
def load_spreads_long() -> pd.DataFrame:
    if SPREADS_LONG_CACHE.exists():
        return pd.read_parquet(SPREADS_LONG_CACHE)
    return refresh_spreads_long()
