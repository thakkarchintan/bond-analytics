import pandas as pd
import streamlit as st

_FILE = "Master_Fixed_Income_Data.xlsx"

# Mainland China missing from WEO extract; available only in GDD for Debt/GDP
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


@st.cache_data
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

    # ── Merge on full country × year grid ────────────────────────────────────
    grid = pd.MultiIndex.from_product([ALL_COUNTRIES, YEARS], names=["Country", "Year"])
    df = pd.DataFrame(index=grid).reset_index()
    df = df.merge(weo_wide, on=["Country", "Year"], how="left")
    df = df.merge(gdd_long[["Country", "Year", "Debt_GDP"]], on=["Country", "Year"], how="left")

    # Prefer GDD Debt_GDP; fall back to WEO gross debt % GDP
    if "_WEO_Debt_GDP" in df.columns:
        df["Debt_GDP"] = df["Debt_GDP"].fillna(df["_WEO_Debt_GDP"])
        df.drop(columns=["_WEO_Debt_GDP"], inplace=True)

    # Calculated column: debt stock in USD billions
    df["Govt_Debt_Outstanding"] = df["GDP_USD"] * df["Debt_GDP"] / 100

    # Placeholders for data coming later
    for col in ["Gross_Bond_Issuance", "Issuance_GDP", "TenY_Govt_Yield", "Policy_Rate"]:
        df[col] = float("nan")

    return df.sort_values(["Country", "Year"]).reset_index(drop=True)
