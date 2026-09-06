"""Macro data routes — parquet-cached data."""
from __future__ import annotations

from pathlib import Path

import pandas as pd
from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/api/macro", tags=["macro"])

_HERE = Path(__file__).parent.parent.parent


def _read_parquet(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise HTTPException(status_code=503, detail=f"Cache not found: {path.name}. Run refresh first.")
    df = pd.read_parquet(path)
    # Serialise dates to strings
    for col in df.select_dtypes(include=["datetime64[ns]", "datetimetz"]).columns:
        df[col] = df[col].dt.strftime("%Y-%m-%d")
    return df


@router.get("/yields")
def get_yields() -> list[dict]:
    df = _read_parquet(_HERE / "gmacro_yields_cache.parquet")
    return df.to_dict(orient="records")


@router.get("/cb-rates")
def get_cb_rates() -> list[dict]:
    df = _read_parquet(_HERE / "gmacro_cb_rates_cache.parquet")
    return df.to_dict(orient="records")


@router.get("/fx")
def get_fx() -> list[dict]:
    df = _read_parquet(_HERE / "gmacro_fx_cache.parquet")
    return df.to_dict(orient="records")


@router.get("/credit-spreads")
def get_credit_spreads() -> list[dict]:
    df = _read_parquet(_HERE / "gmacro_spreads_cache.parquet")
    return df.to_dict(orient="records")


@router.get("/cross-asset")
def get_cross_asset() -> list[dict]:
    df = _read_parquet(_HERE / "gmacro_cross_asset_cache.parquet")
    return df.to_dict(orient="records")


@router.get("/leading")
def get_leading() -> list[dict]:
    df = _read_parquet(_HERE / "gmacro_leading_cache.parquet")
    return df.to_dict(orient="records")


@router.get("/breakeven")
def get_breakeven() -> list[dict]:
    df = _read_parquet(_HERE / "gmacro_breakeven_cache.parquet")
    return df.to_dict(orient="records")


@router.get("/inflation")
def get_inflation() -> list[dict]:
    df = _read_parquet(_HERE / "gmacro_annual_cache.parquet")
    return df.to_dict(orient="records")


@router.get("/fiscal")
def get_fiscal() -> list[dict]:
    df = _read_parquet(_HERE / "gmacro_annual_cache.parquet")
    return df.to_dict(orient="records")


@router.get("/oecd-bc")
def get_oecd_bc() -> list[dict]:
    df = _read_parquet(_HERE / "dbn_oecd_bc_cache.parquet")
    return df.to_dict(orient="records")


@router.get("/cb-balance")
def get_cb_balance() -> list[dict]:
    df = _read_parquet(_HERE / "dbn_cbta_cache.parquet")
    return df.to_dict(orient="records")


@router.get("/ecb-curve")
def get_ecb_curve() -> list[dict]:
    df = _read_parquet(_HERE / "dbn_ecb_yc_cache.parquet")
    return df.to_dict(orient="records")


@router.get("/reer")
def get_reer() -> list[dict]:
    df = _read_parquet(_HERE / "dbn_eer_cache.parquet")
    return df.to_dict(orient="records")


@router.get("/dashboard")
def get_dashboard() -> list[dict]:
    """Merged annual macro data: IMF indicators + 10Y yields + CB policy rates."""
    # Annual IMF data
    annual = _read_parquet(_HERE / "gmacro_annual_cache.parquet")

    # Annual 10Y yield averages (from monthly FRED data)
    yields_path = _HERE / "gmacro_yields_cache.parquet"
    if yields_path.exists():
        ydf = pd.read_parquet(yields_path)
        ydf["Year"] = pd.to_datetime(ydf["Date"]).dt.year
        ydf_ann = ydf.groupby(["Country", "Year"])["Yield_Pct"].mean().reset_index()
        ydf_ann = ydf_ann.rename(columns={"Yield_Pct": "TenY_Yield"})
        annual = annual.merge(ydf_ann, on=["Country", "Year"], how="left")

    # Annual CB policy rate averages (from monthly BIS data)
    cb_path = _HERE / "gmacro_cb_rates_cache.parquet"
    if cb_path.exists():
        cdf = pd.read_parquet(cb_path)
        cdf["Year"] = pd.to_datetime(cdf["Date"]).dt.year
        cdf_ann = cdf.groupby(["Country", "Year"])["Rate_Pct"].mean().reset_index()
        cdf_ann = cdf_ann.rename(columns={"Rate_Pct": "Policy_Rate"})
        annual = annual.merge(cdf_ann, on=["Country", "Year"], how="left")

    # Compute government debt outstanding (USD bn) = DebtGDP_Pct / 100 * GDP_USD_Bn
    if "DebtGDP_Pct" in annual.columns and "GDP_USD_Bn" in annual.columns:
        annual["Govt_Debt_USD_Bn"] = annual["DebtGDP_Pct"] / 100 * annual["GDP_USD_Bn"]

    # Replace NaN with None for JSON serialisation
    annual = annual.where(annual.notna(), other=None)
    return annual.to_dict(orient="records")
