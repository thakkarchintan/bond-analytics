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

# ── Bond math helpers ─────────────────────────────────────────────────────────

def _bond_price(fv: float, coupon_pct: float, freq: int, ytm_pct: float, periods: int) -> float:
    c = (coupon_pct / 100 / freq) * fv
    r = ytm_pct / 100 / freq
    if abs(r) < 1e-12:
        return fv + c * periods
    return c * (1 - (1 + r) ** -periods) / r + fv * (1 + r) ** -periods


def _mac_duration(fv: float, coupon_pct: float, freq: int, ytm_pct: float, periods: int) -> float:
    c = (coupon_pct / 100 / freq) * fv
    r = ytm_pct / 100 / freq
    num = den = 0.0
    for t in range(1, periods + 1):
        cf = c if t < periods else c + fv
        pv = cf / (1 + r) ** t
        num += t * pv
        den += pv
    return (num / den / freq) if den else 0.0


def _convexity(fv: float, coupon_pct: float, freq: int, ytm_pct: float, periods: int) -> float:
    r = ytm_pct / 100 / freq
    c = (coupon_pct / 100 / freq) * fv
    p = _bond_price(fv, coupon_pct, freq, ytm_pct, periods)
    conv = sum(
        (c if t < periods else c + fv) * t * (t + 1) / (1 + r) ** (t + 2)
        for t in range(1, periods + 1)
    )
    return conv / (p * freq * freq) if p else 0.0

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


# ── Portfolio endpoint ────────────────────────────────────────────────────────

class BondPosition(BaseModel):
    name: str
    face_value: float = 1_000_000
    coupon_pct: float = 5.0
    freq: int = 2
    ytm_pct: float = 4.5
    maturity_years: float = 10.0
    notional: float = 1.0  # multiplier (e.g. 10 = 10 bonds)


class PortfolioRequest(BaseModel):
    positions: list[BondPosition]


@router.post("/portfolio")
def calculate_portfolio(req: PortfolioRequest) -> dict:
    if not req.positions:
        raise HTTPException(status_code=400, detail="No positions provided")

    rows = []
    total_mv = 0.0
    for pos in req.positions:
        periods = max(1, round(pos.maturity_years * pos.freq))
        price   = _bond_price(pos.face_value, pos.coupon_pct, pos.freq, pos.ytm_pct, periods)
        mac_dur = _mac_duration(pos.face_value, pos.coupon_pct, pos.freq, pos.ytm_pct, periods)
        mod_dur = mac_dur / (1 + pos.ytm_pct / 100 / pos.freq)
        convex  = _convexity(pos.face_value, pos.coupon_pct, pos.freq, pos.ytm_pct, periods)
        mv      = price * pos.notional
        dv01    = mod_dur * mv / 10_000
        rows.append({
            "name":        pos.name,
            "face_value":  pos.face_value,
            "coupon_pct":  pos.coupon_pct,
            "ytm_pct":     pos.ytm_pct,
            "maturity_yrs": pos.maturity_years,
            "clean_price": round(price, 4),
            "market_value": round(mv, 2),
            "mac_duration": round(mac_dur, 3),
            "mod_duration": round(mod_dur, 3),
            "dv01":         round(dv01, 2),
            "convexity":    round(convex, 3),
            "weight":       0.0,  # filled below
        })
        total_mv += mv

    for row in rows:
        row["weight"] = round(row["market_value"] / total_mv, 4) if total_mv else 0.0

    # Portfolio-level metrics (market-value weighted)
    port_mac_dur = sum(r["mac_duration"] * r["weight"] for r in rows)
    port_mod_dur = sum(r["mod_duration"] * r["weight"] for r in rows)
    port_dv01    = sum(r["dv01"] for r in rows)
    port_convex  = sum(r["convexity"] * r["weight"] for r in rows)

    return {
        "positions":      rows,
        "total_mv":       round(total_mv, 2),
        "portfolio_mac_duration": round(port_mac_dur, 3),
        "portfolio_mod_duration": round(port_mod_dur, 3),
        "portfolio_dv01": round(port_dv01, 2),
        "portfolio_convexity": round(port_convex, 3),
    }


# ── Simulator endpoint ────────────────────────────────────────────────────────

class SimRequest(BaseModel):
    face_value: float = 1_000_000
    coupon_pct: float = 5.0
    freq: int = 2
    ytm_pct: float = 4.5
    maturity_years: float = 10.0
    horizon_years: float = 1.0
    n_paths: int = 500
    vol_pct: float = 1.0    # annual yield vol in %
    drift_pct: float = 0.0  # annual drift in %


@router.post("/simulate")
def simulate_bond(req: SimRequest) -> dict:
    import math, random

    n     = min(max(req.n_paths, 50), 2000)
    steps = max(int(req.horizon_years * 252), 1)
    dt    = req.horizon_years / steps
    sig   = req.vol_pct / 100
    mu    = req.drift_pct / 100
    periods_total = max(1, round(req.maturity_years * req.freq))

    paths_ytm: list[list[float]] = []
    final_prices: list[float] = []

    for _ in range(n):
        ytm = req.ytm_pct / 100
        path = [ytm * 100]
        for _ in range(steps):
            z = random.gauss(0, 1)
            ytm = max(0.0001, ytm * math.exp((mu - 0.5 * sig**2) * dt + sig * math.sqrt(dt) * z))
            path.append(ytm * 100)
        paths_ytm.append(path)
        # remaining maturity at horizon
        rem_mat = max(req.maturity_years - req.horizon_years, 0.5)
        rem_periods = max(1, round(rem_mat * req.freq))
        fp = _bond_price(req.face_value, req.coupon_pct, req.freq, ytm * 100, rem_periods)
        final_prices.append(fp)

    # summary stats
    init_price = _bond_price(req.face_value, req.coupon_pct, req.freq, req.ytm_pct,
                             max(1, round(req.maturity_years * req.freq)))
    sorted_prices = sorted(final_prices)
    n_p = len(sorted_prices)

    def pct(p: float) -> float:
        return sorted_prices[max(0, min(int(p / 100 * n_p), n_p - 1))]

    mean_p  = sum(final_prices) / n_p
    var_p   = sum((x - mean_p) ** 2 for x in final_prices) / n_p
    std_p   = var_p ** 0.5
    pnl     = [p - init_price for p in final_prices]
    var95   = sorted(pnl)[int(0.05 * n_p)]
    cvar95  = sum(p for p in pnl if p <= var95) / max(1, sum(1 for p in pnl if p <= var95))

    # thin paths to 50 for response size
    step_labels = [round(i * req.horizon_years / steps, 3) for i in range(steps + 1)]
    thin_step   = max(1, n // 50)
    thin_paths  = paths_ytm[::thin_step][:50]

    # histogram buckets
    lo, hi = sorted_prices[0], sorted_prices[-1]
    bucket_w = (hi - lo) / 40 if hi > lo else 1
    hist: dict[float, int] = {}
    for p in final_prices:
        b = round(lo + bucket_w * int((p - lo) / bucket_w), 2)
        hist[b] = hist.get(b, 0) + 1
    histogram = [{"price": k, "count": v} for k, v in sorted(hist.items())]

    return {
        "init_price":   round(init_price, 2),
        "mean_price":   round(mean_p, 2),
        "std_price":    round(std_p, 2),
        "p5_price":     round(pct(5), 2),
        "p25_price":    round(pct(25), 2),
        "p50_price":    round(pct(50), 2),
        "p75_price":    round(pct(75), 2),
        "p95_price":    round(pct(95), 2),
        "var95":        round(var95, 2),
        "cvar95":       round(cvar95, 2),
        "n_paths":      n,
        "horizon_years": req.horizon_years,
        "step_labels":  step_labels,
        "ytm_paths":    thin_paths,
        "histogram":    histogram,
    }
