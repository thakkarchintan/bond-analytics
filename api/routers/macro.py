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
