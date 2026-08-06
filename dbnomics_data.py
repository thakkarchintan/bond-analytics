"""
DBnomics data layer — BIS, ECB, OECD datasets via api.db.nomics.world
No authentication required. All data cached as parquet.
"""
from __future__ import annotations

import pathlib
import time
import warnings

import pandas as pd
import requests
import streamlit as st

_HERE         = pathlib.Path(__file__).parent
_BASE         = "https://api.db.nomics.world/v22"
_HDR          = {"User-Agent": "Mozilla/5.0 (compatible; BondAnalytics/1.0)"}

# ── Cache paths ────────────────────────────────────────────────────────────────
CBPOL_CACHE   = _HERE / "dbn_cbpol_cache.parquet"
CBTA_CACHE    = _HERE / "dbn_cbta_cache.parquet"
EER_CACHE     = _HERE / "dbn_eer_cache.parquet"
ECB_YC_CACHE  = _HERE / "dbn_ecb_yc_cache.parquet"
OECD_BC_CACHE = _HERE / "dbn_oecd_bc_cache.parquet"

# ── Series definitions ─────────────────────────────────────────────────────────

CBPOL_SERIES: dict[str, str] = {
    "D.US": "United States", "D.XM": "Euro Area",   "D.GB": "United Kingdom",
    "D.JP": "Japan",         "D.AU": "Australia",    "D.CA": "Canada",
    "D.CH": "Switzerland",   "D.NO": "Norway",        "D.SE": "Sweden",
    "D.NZ": "New Zealand",   "D.KR": "South Korea",  "D.IN": "India",
    "D.BR": "Brazil",        "D.MX": "Mexico",        "D.ZA": "South Africa",
    "D.TR": "Turkey",        "D.CN": "China",         "D.ID": "Indonesia",
    "D.HK": "Hong Kong",     "D.PL": "Poland",        "D.CZ": "Czech Republic",
    "D.HU": "Hungary",       "D.RU": "Russia",        "D.TH": "Thailand",
    "D.MY": "Malaysia",
}

CBTA_SERIES: dict[str, str] = {
    "M.US": "Federal Reserve",  "M.XM": "ECB",
    "M.JP": "Bank of Japan",    "M.GB": "Bank of England",
    "M.CN": "PBoC",             "M.CH": "SNB",
    "M.CA": "Bank of Canada",   "M.AU": "RBA",
}

EER_SERIES: dict[str, str] = {
    "M.R.B.US": "USD", "M.R.B.XM": "EUR", "M.R.B.GB": "GBP",
    "M.R.B.JP": "JPY", "M.R.B.CN": "CNY", "M.R.B.AU": "AUD",
    "M.R.B.CA": "CAD", "M.R.B.CH": "CHF", "M.R.B.KR": "KRW",
    "M.R.B.IN": "INR", "M.R.B.BR": "BRL", "M.R.B.NO": "NOK",
    "M.R.B.SE": "SEK", "M.R.B.MX": "MXN",
}

ECB_YC_MATS: dict[str, float] = {
    "3M": 0.25, "6M": 0.5, "1Y": 1, "2Y": 2,
    "5Y": 5, "10Y": 10, "20Y": 20, "30Y": 30,
}

OECD_BCI_COUNTRIES = [
    "USA","GBR","JPN","DEU","FRA","ITA","CAN","AUS","KOR","ESP",
    "NLD","SWE","NOR","CHE","MEX","TUR","BRA","ZAF","CHN","IND",
    "POL","BEL","DNK","FIN","PRT","CZE","HUN","OECDE","OECD",
]
OECD_CCI_COUNTRIES = [
    "USA","GBR","JPN","DEU","FRA","ITA","AUS","KOR","ESP",
    "NLD","SWE","CHE","MEX","TUR","BRA","ZAF","CHN","IND",
    "POL","BEL","DNK","FIN","PRT","CZE","HUN","OECDE","OECD",
]
OECD_CLI_COUNTRIES = [
    "USA","GBR","JPN","DEU","FRA","ITA","CAN","AUS",
    "KOR","ESP","MEX","TUR","BRA","ZAF","CHN","IND",
]

COUNTRY_NAMES: dict[str, str] = {
    "USA":"United States","GBR":"United Kingdom","JPN":"Japan","DEU":"Germany",
    "FRA":"France","ITA":"Italy","CAN":"Canada","AUS":"Australia",
    "KOR":"South Korea","ESP":"Spain","NLD":"Netherlands","SWE":"Sweden",
    "NOR":"Norway","CHE":"Switzerland","MEX":"Mexico","TUR":"Turkey",
    "BRA":"Brazil","ZAF":"South Africa","CHN":"China","IND":"India",
    "IDN":"Indonesia","POL":"Poland","BEL":"Belgium","DNK":"Denmark",
    "FIN":"Finland","PRT":"Portugal","CZE":"Czech Republic","HUN":"Hungary",
    "OECDE":"OECD Europe","OECD":"OECD Total",
}


# ── Core fetcher ───────────────────────────────────────────────────────────────

def _dbn_series(provider: str, dataset: str, series: str,
                retries: int = 2) -> list[tuple]:
    """Fetch one DBnomics series. Returns [(period_str, value), ...] sorted."""
    url = f"{_BASE}/series/{provider}/{dataset}/{series}"
    for attempt in range(retries + 1):
        try:
            r = requests.get(url, headers=_HDR, params={"observations": 1}, timeout=30)
            if r.status_code != 200:
                return []
            doc = r.json()["series"]["docs"][0]
            pairs = []
            for p, v in zip(doc.get("period", []), doc.get("value", [])):
                if v is None:
                    continue
                try:
                    pairs.append((p, float(v)))
                except (ValueError, TypeError):
                    pass
            return sorted(pairs, key=lambda x: x[0])
        except Exception:
            if attempt < retries:
                time.sleep(1)
    return []


# ── Build functions ────────────────────────────────────────────────────────────

def _build_cbpol() -> pd.DataFrame:
    rows = []
    for code, country in CBPOL_SERIES.items():
        for period, value in _dbn_series("BIS", "WS_CBPOL", code):
            rows.append({"Date": period, "Country": country, "Rate": value})
    if not rows:
        return pd.DataFrame()
    df = pd.DataFrame(rows)
    df["Date"] = pd.to_datetime(df["Date"])
    return df.sort_values(["Country", "Date"]).reset_index(drop=True)


def _build_cbta() -> pd.DataFrame:
    rows = []
    for code, cb_name in CBTA_SERIES.items():
        for period, value in _dbn_series("BIS", "WS_CBTA", code):
            rows.append({"Date": period, "CB": cb_name, "Assets_USD_bn": value})
    if not rows:
        return pd.DataFrame()
    df = pd.DataFrame(rows)
    df["Date"] = pd.to_datetime(df["Date"])
    return df.sort_values(["CB", "Date"]).reset_index(drop=True)


def _build_eer() -> pd.DataFrame:
    rows = []
    for code, ccy in EER_SERIES.items():
        for period, value in _dbn_series("BIS", "WS_EER", code):
            rows.append({"Date": period, "Currency": ccy, "EER": value})
    if not rows:
        return pd.DataFrame()
    df = pd.DataFrame(rows)
    df["Date"] = pd.to_datetime(df["Date"])
    return df.sort_values(["Currency", "Date"]).reset_index(drop=True)


def _build_ecb_yc() -> pd.DataFrame:
    rows = []
    for mat, mat_yrs in ECB_YC_MATS.items():
        code = f"B.U2.EUR.4F.G_N_A.SV_C_YM.SR_{mat}"
        for period, value in _dbn_series("ECB", "YC", code):
            rows.append({"Date": period, "Maturity": mat, "MatYrs": mat_yrs, "Rate": value})
    if not rows:
        return pd.DataFrame()
    df = pd.DataFrame(rows)
    df["Date"] = pd.to_datetime(df["Date"])
    return df.sort_values(["Date", "MatYrs"]).reset_index(drop=True)


def _build_oecd_bc() -> pd.DataFrame:
    rows = []
    for indicator, countries in [
        ("BCI", OECD_BCI_COUNTRIES),
        ("CCI", OECD_CCI_COUNTRIES),
        ("CLI", OECD_CLI_COUNTRIES),
    ]:
        suffix = f"{indicator}.AMPLITUD.LTRENDIDX.M"
        for iso in countries:
            cname = COUNTRY_NAMES.get(iso, iso)
            for period, value in _dbn_series("OECD", "DP_LIVE", f"{iso}.{suffix}"):
                rows.append({
                    "Date": period, "Country": cname, "ISO": iso,
                    "Indicator": indicator, "Value": value,
                })
    if not rows:
        return pd.DataFrame()
    df = pd.DataFrame(rows)
    df["Date"] = pd.to_datetime(df["Date"])
    return df.sort_values(["Indicator", "Country", "Date"]).reset_index(drop=True)


# ── Refresh functions ──────────────────────────────────────────────────────────

def refresh_cbpol() -> pd.DataFrame:
    df = _build_cbpol()
    if not df.empty:
        df.to_parquet(CBPOL_CACHE, index=False)
        load_cbpol.clear()
    return df


def refresh_cbta() -> pd.DataFrame:
    df = _build_cbta()
    if not df.empty:
        df.to_parquet(CBTA_CACHE, index=False)
        load_cbta.clear()
    return df


def refresh_eer() -> pd.DataFrame:
    df = _build_eer()
    if not df.empty:
        df.to_parquet(EER_CACHE, index=False)
        load_eer.clear()
    return df


def refresh_ecb_yc() -> pd.DataFrame:
    df = _build_ecb_yc()
    if not df.empty:
        df.to_parquet(ECB_YC_CACHE, index=False)
        load_ecb_yc.clear()
    return df


def refresh_oecd_bc() -> pd.DataFrame:
    df = _build_oecd_bc()
    if not df.empty:
        df.to_parquet(OECD_BC_CACHE, index=False)
        load_oecd_bc.clear()
    return df


# ── Load functions (cache-first) ───────────────────────────────────────────────

@st.cache_data(show_spinner=False)
def load_cbpol() -> pd.DataFrame:
    if CBPOL_CACHE.exists():
        return pd.read_parquet(CBPOL_CACHE)
    return refresh_cbpol()


@st.cache_data(show_spinner=False)
def load_cbta() -> pd.DataFrame:
    if CBTA_CACHE.exists():
        return pd.read_parquet(CBTA_CACHE)
    return refresh_cbta()


@st.cache_data(show_spinner=False)
def load_eer() -> pd.DataFrame:
    if EER_CACHE.exists():
        return pd.read_parquet(EER_CACHE)
    return refresh_eer()


@st.cache_data(show_spinner=False)
def load_ecb_yc() -> pd.DataFrame:
    if ECB_YC_CACHE.exists():
        return pd.read_parquet(ECB_YC_CACHE)
    return refresh_ecb_yc()


@st.cache_data(show_spinner=False)
def load_oecd_bc() -> pd.DataFrame:
    if OECD_BC_CACHE.exists():
        return pd.read_parquet(OECD_BC_CACHE)
    return refresh_oecd_bc()
