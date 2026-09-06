"""Bond data routes — Final.xlsx powered."""
from __future__ import annotations

import re
from datetime import date, datetime
from typing import Any

import numpy as np
import pandas as pd
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from api.deps import load_final

router = APIRouter(prefix="/api/bond", tags=["bond"])

# ── Preset spread grid formulas (same as GridTab.py) ─────────────────────────

PRESET_FORMULAS: dict[str, str] = {
    "Eurex 5-10 Spread":            "FGBLY - FGBMY",
    "Eurex 2-5 Spread":             "FGBMY - FGBSY",
    "Eurex 2-10 Spread":            "FGBLY - FGBSY",
    "Eurex 10-30 Spread":           "FGBXY - FGBLY",
    "Eurex 2-5-10 Fly":             "FGBLY - 2 * FGBMY + FGBSY",
    "Eurex 5-10-30 Fly":            "FGBXY - 2 * FGBLY + FGBMY",
    "US 5-10 Spread":               "US10Y - US5Y",
    "US 2-5 Spread":                "US5Y - US2Y",
    "US 2-10 Spread":               "US10Y - US2Y",
    "US 10-30 Spread":              "US30Y - US10Y",
    "US 2-5-10 Fly":                "US10Y - 2 * US5Y + US2Y",
    "US 5-10-30 Fly":               "US30Y - 2 * US10Y + US5Y",
    "Italian vs German 2Y":         "FBTSY - FGBSY",
    "Italian vs German 10Y":        "FBTPY - FGBLY",
    "Australian vs. Canadian 10Y":  "AUS10Y - CAD10Y",
    "French vs. German 10Y":        "FOATY - FGBLY",
    "UK vs. German 10Y":            "UK10Y - FGBLY",
    "UK vs. Australian 10Y":        "UK10Y - AUS10Y",
    "US vs. Australian 10Y":        "US10Y - AUS10Y",
    "Canadian vs. US 2-5-10 Fly":   "CAD10Y - 2 * CAD5Y + CAD2Y - US10Y + 2 * US5Y - US2Y",
}


def _eval_formula(df: pd.DataFrame, formula: str) -> pd.Series:
    """Evaluate a column-based formula against a DataFrame."""
    cols = df.select_dtypes(include="number").columns.tolist()
    # Build a safe namespace from numeric columns
    ns: dict[str, Any] = {c: df[c] for c in cols}
    try:
        result = eval(formula, {"__builtins__": {}}, ns)  # noqa: S307
        return pd.Series(result, index=df.index)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Formula error: {exc}") from exc


def _series_to_records(s: pd.Series, dates: pd.Series) -> list[dict]:
    return [
        {"date": d.strftime("%Y-%m-%d"), "value": round(float(v), 4)}
        for d, v in zip(dates, s)
        if pd.notna(v)
    ]


# ── Routes ─────────────────────────────────────────────────────────────────────

@router.get("/columns")
def get_columns() -> list[str]:
    df = load_final()
    return [c for c in df.columns if c != "Date"]


@router.get("/series")
def get_series(
    cols: str = Query(..., description="Comma-separated column names"),
    start: str | None = Query(None),
    end: str | None = Query(None),
) -> dict[str, list[dict]]:
    df = load_final()
    col_list = [c.strip() for c in cols.split(",")]
    missing = [c for c in col_list if c not in df.columns]
    if missing:
        raise HTTPException(status_code=404, detail=f"Unknown columns: {missing}")

    if start:
        df = df[df["Date"] >= pd.to_datetime(start)]
    if end:
        df = df[df["Date"] <= pd.to_datetime(end)]

    result: dict[str, list[dict]] = {}
    for col in col_list:
        result[col] = _series_to_records(df[col], df["Date"])
    return result


class FormulaRequest(BaseModel):
    formula: str
    start: str | None = None
    end: str | None = None


@router.post("/formula")
def evaluate_formula(req: FormulaRequest) -> list[dict]:
    df = load_final()
    if req.start:
        df = df[df["Date"] >= pd.to_datetime(req.start)]
    if req.end:
        df = df[df["Date"] <= pd.to_datetime(req.end)]
    series = _eval_formula(df, req.formula)
    return _series_to_records(series, df["Date"])


@router.get("/spread-grid")
def get_spread_grid(
    start: str | None = Query(None),
    end: str | None = Query(None),
) -> list[dict]:
    """Return all 20 preset formulas with last value, daily change, and sparkline."""
    df = load_final()
    if start:
        df = df[df["Date"] >= pd.to_datetime(start)]
    if end:
        df = df[df["Date"] <= pd.to_datetime(end)]

    result = []
    for name, formula in PRESET_FORMULAS.items():
        try:
            series = _eval_formula(df, formula).dropna()
            if series.empty:
                continue
            last_val   = float(series.iloc[-1])
            prev_val   = float(series.iloc[-2]) if len(series) > 1 else last_val
            daily_chg  = last_val - prev_val

            # Last 60 points as sparkline
            spark_vals  = series.iloc[-60:].tolist()
            spark_dates = df["Date"].iloc[series.index[-60:]].dt.strftime("%Y-%m-%d").tolist()

            result.append({
                "name":      name,
                "formula":   formula,
                "last":      round(last_val, 4),
                "change":    round(daily_chg, 4),
                "change_pct": round((daily_chg / abs(prev_val) * 100) if prev_val else 0, 2),
                "sparkline": [{"date": d, "value": round(v, 4)} for d, v in zip(spark_dates, spark_vals)],
            })
        except Exception:
            continue

    return result
