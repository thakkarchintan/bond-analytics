"""
Data loader for Global Capital Markets Dashboard.

Sources (all free, no API key):
  World Bank REST API  — equity market cap, listed companies, population, turnover
  IMF Datamapper API   — GDP (USD bn), Gross Govt Debt % GDP

Derived:
  Govt Bond Outstanding  ≈  Gross Govt Debt (% GDP)  ×  GDP (USD)
  Total Capital Market   =  Equity + Govt Bonds

Caching strategy:
  Data is saved to CACHE_FILE (committed to the repo) and loaded from disk on
  every startup — no API calls on cold start.  Use refresh_capital_markets_data()
  to pull fresh data from the APIs and overwrite the cache.
"""
from __future__ import annotations

from pathlib import Path

import requests
import pandas as pd
import streamlit as st

CACHE_FILE = Path(__file__).parent / "capital_markets_cache.parquet"

# ── Country universe ───────────────────────────────────────────────────────────

COUNTRY_META = {
    "USA": dict(wb="US",  imf="USA", name="United States",    region="Americas"),
    "CHN": dict(wb="CN",  imf="CHN", name="China",            region="Asia-Pacific"),
    "JPN": dict(wb="JP",  imf="JPN", name="Japan",            region="Asia-Pacific"),
    "IND": dict(wb="IN",  imf="IND", name="India",            region="Asia-Pacific"),
    "GBR": dict(wb="GB",  imf="GBR", name="United Kingdom",   region="Europe"),
    "FRA": dict(wb="FR",  imf="FRA", name="France",           region="Europe"),
    "DEU": dict(wb="DE",  imf="DEU", name="Germany",          region="Europe"),
    "CAN": dict(wb="CA",  imf="CAN", name="Canada",           region="Americas"),
    "BRA": dict(wb="BR",  imf="BRA", name="Brazil",           region="Americas"),
    "AUS": dict(wb="AU",  imf="AUS", name="Australia",        region="Asia-Pacific"),
}

COUNTRY_COLORS = {
    "United States":  "#60a5fa",
    "China":          "#f87171",
    "Japan":          "#34d399",
    "India":          "#f472b6",
    "United Kingdom": "#22d3ee",
    "France":         "#fbbf24",
    "Germany":        "#a78bfa",
    "Canada":         "#818cf8",
    "Brazil":         "#a3e635",
    "Australia":      "#fb923c",
}

FINANCING_MODEL = {
    "United States":  "Market-based",
    "China":          "State-led",
    "Japan":          "Government debt-heavy",
    "India":          "Mixed / developing",
    "United Kingdom": "Market-based",
    "France":         "Market + bank hybrid",
    "Germany":        "Bank-based",
    "Canada":         "Market-based",
    "Brazil":         "Government-led",
    "Australia":      "Market-based",
}

YEARS = list(range(2005, 2024))   # 2005–2023
_WB_CODES = ";".join(m["wb"] for m in COUNTRY_META.values())
_IMF_CODES = ",".join(m["imf"] for m in COUNTRY_META.values())
_WB_TO_ISO3 = {m["wb"]: iso3 for iso3, m in COUNTRY_META.items()}
_ISO3_NAME  = {iso3: m["name"] for iso3, m in COUNTRY_META.items()}


# ── Fetchers ───────────────────────────────────────────────────────────────────

def _wb_indicator(indicator: str, per_page: int = 500) -> pd.DataFrame:
    """Fetch a World Bank indicator for all 10 countries, 2005–2023."""
    url = (
        f"https://api.worldbank.org/v2/country/{_WB_CODES}"
        f"/indicator/{indicator}"
        f"?format=json&date=2005:2023&per_page={per_page}"
    )
    try:
        r = requests.get(url, timeout=20)
        r.raise_for_status()
        records = r.json()[1] or []
        rows = []
        for rec in records:
            wb2 = rec.get("countryiso3code", "")[:2]  # World Bank returns ISO3 in countryiso3code
            # Actually World Bank returns the 2-letter in country.id, ISO3 in countryiso3code
            wb2 = rec.get("country", {}).get("id", "")
            iso3 = _WB_TO_ISO3.get(wb2)
            if iso3 and rec.get("value") is not None:
                rows.append({"ISO3": iso3, "Year": int(rec["date"]), indicator: rec["value"]})
        return pd.DataFrame(rows)
    except Exception:
        return pd.DataFrame(columns=["ISO3", "Year", indicator])


def _imf_indicator(indicator: str) -> pd.DataFrame:
    """Fetch an IMF Datamapper indicator for all 10 countries, all years."""
    url = f"https://www.imf.org/external/datamapper/api/v1/{indicator}/{_IMF_CODES}"
    try:
        r = requests.get(url, timeout=20)
        r.raise_for_status()
        values = r.json().get("values", {}).get(indicator, {})
        rows = []
        for iso3, year_data in values.items():
            if iso3 not in COUNTRY_META:
                continue
            for yr_str, val in year_data.items():
                yr = int(yr_str)
                if 2005 <= yr <= 2023 and val is not None:
                    rows.append({"ISO3": iso3, "Year": yr, indicator: val})
        return pd.DataFrame(rows)
    except Exception:
        return pd.DataFrame(columns=["ISO3", "Year", indicator])


# ── Build / persist helpers ────────────────────────────────────────────────────

def _build_dataframe() -> pd.DataFrame:
    """Fetch all indicators from World Bank + IMF and return a clean DataFrame."""
    eq   = _wb_indicator("CM.MKT.LCAP.CD")
    lst  = _wb_indicator("CM.MKT.LDOM.NO")
    pop  = _wb_indicator("SP.POP.TOTL")
    trn  = _wb_indicator("CM.MKT.TRNR")
    gdp  = _imf_indicator("NGDPD")
    dbt  = _imf_indicator("GGXWDG_NGDP")

    base = pd.DataFrame(
        [(iso3, yr) for iso3 in COUNTRY_META for yr in YEARS],
        columns=["ISO3", "Year"],
    )
    for df, col in [
        (eq,  "CM.MKT.LCAP.CD"),
        (lst, "CM.MKT.LDOM.NO"),
        (pop, "SP.POP.TOTL"),
        (trn, "CM.MKT.TRNR"),
        (gdp, "NGDPD"),
        (dbt, "GGXWDG_NGDP"),
    ]:
        if not df.empty:
            base = base.merge(df[["ISO3", "Year", col]], on=["ISO3", "Year"], how="left")

    base = base.rename(columns={
        "CM.MKT.LCAP.CD": "Equity_Raw",
        "CM.MKT.LDOM.NO": "Listed_Cos",
        "SP.POP.TOTL":    "Population",
        "CM.MKT.TRNR":   "Turnover_Ratio",
        "NGDPD":          "GDP_Bn",
        "GGXWDG_NGDP":   "Debt_GDP_Pct",
    })
    base["Equity_USD"]        = base["Equity_Raw"] / 1e12
    base["GDP_USD"]           = base["GDP_Bn"] / 1e3
    base["GovtBond_USD"]      = base["Debt_GDP_Pct"] / 100 * base["GDP_USD"]
    base["Total_Cap_USD"]     = base["Equity_USD"] + base["GovtBond_USD"]
    base["Equity_GDP_Pct"]    = base["Equity_USD"] / base["GDP_USD"] * 100
    base["GovtBond_GDP_Pct"]  = base["GovtBond_USD"] / base["GDP_USD"] * 100
    base["Bond_Equity_Ratio"] = base["GovtBond_USD"] / base["Equity_USD"]
    base["Country"] = base["ISO3"].map(_ISO3_NAME)
    base["Region"]  = base["ISO3"].map({iso3: m["region"] for iso3, m in COUNTRY_META.items()})
    base = base.sort_values(["ISO3", "Year"]).reset_index(drop=True)
    cols = [
        "ISO3", "Country", "Region", "Year",
        "Equity_USD", "GDP_USD", "Debt_GDP_Pct", "GovtBond_USD", "Total_Cap_USD",
        "Equity_GDP_Pct", "GovtBond_GDP_Pct", "Bond_Equity_Ratio",
        "Listed_Cos", "Population", "Turnover_Ratio",
    ]
    return base[[c for c in cols if c in base.columns]]


def refresh_capital_markets_data() -> pd.DataFrame:
    """
    Fetch fresh data from World Bank + IMF, overwrite CACHE_FILE, clear the
    Streamlit cache so the next call to load_capital_markets_data() reads the new file.
    Returns the freshly built DataFrame.
    """
    df = _build_dataframe()
    df.to_parquet(CACHE_FILE, index=False)
    load_capital_markets_data.clear()
    return df


# ── Main loader ────────────────────────────────────────────────────────────────

@st.cache_data(show_spinner=False)
def load_capital_markets_data() -> pd.DataFrame:
    """
    Loads from the committed parquet cache (instant on cold start).
    Falls back to live API fetch only when the cache file is missing.

    Returns a long-format DataFrame:
      ISO3, Country, Year, Equity_USD, GDP_USD, Debt_GDP_Pct,
      GovtBond_USD, Total_Cap_USD, Listed_Cos, Population, Turnover_Ratio
    All USD values are in trillions.
    """
    if CACHE_FILE.exists():
        return pd.read_parquet(CACHE_FILE)
    # Cache file missing — fetch from APIs and save for next time
    df = _build_dataframe()
    df.to_parquet(CACHE_FILE, index=False)
    return df
