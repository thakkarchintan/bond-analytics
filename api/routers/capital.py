"""Capital markets data route."""
from __future__ import annotations

from pathlib import Path

import pandas as pd
from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/api", tags=["capital"])

_HERE = Path(__file__).parent.parent.parent


@router.get("/capital-markets")
def get_capital_markets() -> list[dict]:
    path = _HERE / "capital_markets_cache.parquet"
    if not path.exists():
        raise HTTPException(status_code=503, detail="Capital markets cache not found.")
    df = pd.read_parquet(path)
    for col in df.select_dtypes(include=["datetime64[ns]", "datetimetz"]).columns:
        df[col] = df[col].dt.strftime("%Y-%m-%d")
    return df.to_dict(orient="records")
