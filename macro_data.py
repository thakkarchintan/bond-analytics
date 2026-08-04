import json
import urllib.request
import warnings

import pandas as pd
import streamlit as st

_FILE = "Master_Fixed_Income_Data.xlsx"
_DAILY_FILE = "Final.xlsx"

# ── Country maps ───────────────────────────────────────────────────────────────

_WEO_COUNTRIES = {
    "United States":   "USA",
    "Japan":           "Japan",
    "Germany":         "Germany",
    "France":          "France",
    "Italy":           "Italy",
    "United Kingdom":  "United Kingdom",
    "India":           "India",
    "Canada":          "Canada",
    "Brazil":          "Brazil",
}

_GDD_COUNTRIES = {
    "United States":                 "USA",
    "China, People's Republic of":   "China",
    "Japan":                         "Japan",
    "Germany":                       "Germany",
    "France":                        "France",
    "Italy":                         "Italy",
    "United Kingdom":                "United Kingdom",
    "India":                         "India",
    "Canada":                        "Canada",
    "Brazil":                        "Brazil",
}

# OECD ISO-2 → our display name
_OECD_COUNTRY_MAP = {
    "USA": "USA",
    "GBR": "United Kingdom",
    "JPN": "Japan",
    "DEU": "Germany",
    "FRA": "France",
    "ITA": "Italy",
    "CAN": "Canada",
    "IND": "India",
    "BRA": "Brazil",
    "CHN": "China",
}

# Known 10Y columns in Final.xlsx — used when instrument metadata isn't tagged yet
_KNOWN_10Y = {
    "US10Y":   "USA",
    "UK10Y":   "United Kingdom",
    "CAD10Y":  "Canada",
    "FGBLY":   "Germany",    # German Bund long (10Y)
    "FOATY":   "France",     # French OAT (10Y)
}

_WEO_INDICATORS = {
    "NGDPD":         "GDP_USD",
    "NGDP_RPCH":     "Real_GDP_Growth",
    "PCPIPCH":       "CPI_Inflation",
    "GGXCNL_NGDP":   "Fiscal_Balance_GDP",
    "GGXONLB_NGDP":  "Primary_Balance_GDP",
    "GGXWDG_NGDP":   "_WEO_Debt_GDP",
}

ALL_COUNTRIES = ["Brazil", "Canada", "China", "France", "Germany",
                 "India", "Italy", "Japan", "United Kingdom", "USA"]
YEARS = list(range(2008, 2026))


# ── OECD fetch ─────────────────────────────────────────────────────────────────

def _fetch_oecd() -> pd.DataFrame:
    """
    Fetch MEI_FIN from OECD stats API. Returns DataFrame:
      Country, Year, TenY_Yield_OECD, ShortRate_OECD   (annual averages).
    Returns empty DataFrame on any failure so the app degrades gracefully.
    """
    url = (
        "https://stats.oecd.org/SDMX-JSON/data/MEI_FIN/IRLT.USA.M/OECD"
        "?startTime=2008-01&endTime=2025-12&contentType=json"
    )
    headers = {"Accept": "application/json", "User-Agent": "bond-analytics/1.0"}
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=30) as r:
            raw = r.read()
        d = json.loads(raw)
    except Exception as exc:
        warnings.warn(f"OECD fetch failed: {exc}")
        return pd.DataFrame()

    try:
        outer   = d["data"]["structures"][0]
        dims_s  = outer["dimensions"]["series"]
        time_vals = [v["id"] for v in outer["dimensions"]["observation"][0]["values"]]
        ds        = d["data"]["dataSets"][0]
        series    = ds["series"]
    except (KeyError, IndexError, TypeError) as exc:
        warnings.warn(f"OECD parse failed: {exc}")
        return pd.DataFrame()

    records = []
    for k, v in series.items():
        indices = [int(x) for x in k.split(":")]
        decoded = {
            dim["id"]: [vv["id"] for vv in dim["values"]][indices[i]]
            for i, dim in enumerate(dims_s)
            if i < len(indices) and indices[i] < len(dim["values"])
        }
        country_code = decoded.get("REF_AREA", "")
        measure      = decoded.get("MEASURE", "")

        if country_code not in _OECD_COUNTRY_MAP:
            continue
        if measure not in ("IRLT", "IRSTCI"):
            continue

        display = _OECD_COUNTRY_MAP[country_code]
        for t, vals in v.get("observations", {}).items():
            if not vals or vals[0] is None:
                continue
            period = time_vals[int(t)]
            try:
                year = int(str(period)[:4])
            except ValueError:
                continue
            if 2008 <= year <= 2025:
                records.append({
                    "Country": display,
                    "Year":    year,
                    "Measure": measure,
                    "Value":   float(vals[0]),
                })

    if not records:
        return pd.DataFrame()

    df = pd.DataFrame(records)
    df = df.groupby(["Country", "Year", "Measure"])["Value"].mean().reset_index()

    irlt   = (df[df["Measure"] == "IRLT"]
              .drop(columns="Measure")
              .rename(columns={"Value": "TenY_Yield_OECD"}))
    irstci = (df[df["Measure"] == "IRSTCI"]
              .drop(columns="Measure")
              .rename(columns={"Value": "ShortRate_OECD"}))

    return irlt.merge(irstci, on=["Country", "Year"], how="outer")


# ── Daily → annual 10Y from Final.xlsx ────────────────────────────────────────

def _annual_10y_from_daily(metadata: dict) -> pd.DataFrame:
    """
    Reads Final.xlsx, identifies 10Y bond instruments via metadata (with
    _KNOWN_10Y as fallback), and returns annual averages per country.
    """
    # Instruments tagged in metadata as Fixed Income Bonds + 10Y maturity
    tagged_10y = {
        inst: meta["country"]
        for inst, meta in metadata.items()
        if meta.get("asset_class") == "Fixed Income Bonds"
        and meta.get("maturity") == "10Y"
        and meta.get("country")
    }

    # Merge with known fallback (tagged data takes precedence)
    inst_map = dict(_KNOWN_10Y)   # fallback
    inst_map.update(tagged_10y)   # overwrite / extend with tagged

    try:
        df = pd.read_excel(_DAILY_FILE, sheet_name=0)
        df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
        df = df.dropna(subset=["Date"])
        df["Year"] = df["Date"].dt.year
    except Exception as exc:
        warnings.warn(f"Final.xlsx read failed: {exc}")
        return pd.DataFrame()

    records = []
    for inst, country in inst_map.items():
        if inst not in df.columns:
            continue
        annual = (
            df.groupby("Year")[inst]
            .mean()
            .reset_index()
            .rename(columns={inst: "Value"})
        )
        annual["Country"] = country
        records.append(annual)

    if not records:
        return pd.DataFrame()

    combined = pd.concat(records, ignore_index=True)
    # If multiple 10Y instruments map to the same country, average them
    combined = (combined
                .groupby(["Country", "Year"])["Value"]
                .mean()
                .reset_index()
                .rename(columns={"Value": "TenY_Daily"}))
    return combined[combined["Year"].between(2008, 2025)]


# ── Main loader ────────────────────────────────────────────────────────────────

@st.cache_data(ttl=3600)
def load_macro_data() -> pd.DataFrame:
    # ── WEO ──────────────────────────────────────────────────────────────────
    weo_raw = pd.read_excel(_FILE, sheet_name="WEO_Raw")
    weo_raw = weo_raw[weo_raw["COUNTRY"].isin(_WEO_COUNTRIES)].copy()
    weo_raw["_ind"] = weo_raw["SERIES_CODE"].str.split(".").str[1]
    weo_needed = weo_raw[weo_raw["_ind"].isin(_WEO_INDICATORS)].copy()
    weo_needed["_col"]    = weo_needed["_ind"].map(_WEO_INDICATORS)
    weo_needed["Country"] = weo_needed["COUNTRY"].map(_WEO_COUNTRIES)

    yr_cols = [str(y) for y in YEARS if str(y) in weo_needed.columns]
    weo_long = weo_needed.melt(
        id_vars=["Country", "_col"],
        value_vars=yr_cols,
        var_name="Year",
        value_name="Value",
    )
    weo_long["Year"] = weo_long["Year"].astype(int)
    weo_wide = weo_long.pivot_table(
        index=["Country", "Year"],
        columns="_col",
        values="Value",
        aggfunc="first",
    ).reset_index()
    weo_wide.columns.name = None

    # ── GDD ──────────────────────────────────────────────────────────────────
    gdd_raw = pd.read_excel(_FILE, sheet_name="GDD_Raw")
    gdd_raw = gdd_raw[gdd_raw["COUNTRY"].isin(_GDD_COUNTRIES)].copy()
    gdd_raw["_ind"] = gdd_raw["SERIES_CODE"].str.split(".").str[1]
    gdd_debt = gdd_raw[gdd_raw["_ind"] == "FL_S13_POGDP_PT"].copy()
    gdd_debt["Country"] = gdd_debt["COUNTRY"].map(_GDD_COUNTRIES)
    gdd_yr_cols = [str(y) for y in YEARS if str(y) in gdd_debt.columns]
    gdd_long = gdd_debt.melt(
        id_vars=["Country"],
        value_vars=gdd_yr_cols,
        var_name="Year",
        value_name="Debt_GDP",
    )
    gdd_long["Year"] = gdd_long["Year"].astype(int)

    # ── Base grid ────────────────────────────────────────────────────────────
    grid = pd.MultiIndex.from_product([ALL_COUNTRIES, YEARS], names=["Country", "Year"])
    df = pd.DataFrame(index=grid).reset_index()
    df = df.merge(weo_wide, on=["Country", "Year"], how="left")
    df = df.merge(gdd_long[["Country", "Year", "Debt_GDP"]], on=["Country", "Year"], how="left")

    if "_WEO_Debt_GDP" in df.columns:
        df["Debt_GDP"] = df["Debt_GDP"].fillna(df["_WEO_Debt_GDP"])
        df.drop(columns=["_WEO_Debt_GDP"], inplace=True)

    df["Govt_Debt_Outstanding"] = df["GDP_USD"] * df["Debt_GDP"] / 100

    # ── 10Y yields — daily annual averages + OECD supplement ─────────────────
    try:
        from firebase_utils import get_instrument_metadata
        metadata = get_instrument_metadata()
    except Exception:
        metadata = {}

    daily_10y = _annual_10y_from_daily(metadata)
    oecd      = _fetch_oecd()

    if not daily_10y.empty:
        df = df.merge(daily_10y, on=["Country", "Year"], how="left")
    else:
        df["TenY_Daily"] = float("nan")

    if not oecd.empty:
        df = df.merge(oecd, on=["Country", "Year"], how="left")
    else:
        df["TenY_Yield_OECD"] = float("nan")
        df["ShortRate_OECD"]  = float("nan")

    # TenY_Govt_Yield: daily-based average preferred, OECD fills the gaps
    df["TenY_Govt_Yield"] = df["TenY_Daily"].fillna(df.get("TenY_Yield_OECD", float("nan")))

    # Policy_Rate: OECD short-term rate (3M interbank / money market proxy)
    df["Policy_Rate"] = df.get("ShortRate_OECD", float("nan"))

    # Drop intermediates
    for col in ["TenY_Daily", "TenY_Yield_OECD", "ShortRate_OECD"]:
        if col in df.columns:
            df.drop(columns=col, inplace=True)

    # Placeholders (bond issuance data still pending)
    for col in ["Gross_Bond_Issuance", "Issuance_GDP"]:
        df[col] = float("nan")

    return df.sort_values(["Country", "Year"]).reset_index(drop=True)
