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
