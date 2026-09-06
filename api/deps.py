"""Shared FastAPI dependencies."""
from __future__ import annotations

import functools
from pathlib import Path

import pandas as pd

from api.config import FINAL_XLSX

# ── Final.xlsx loader (cached in memory after first call) ─────────────────────

@functools.lru_cache(maxsize=1)
def load_final() -> pd.DataFrame:
    df = pd.read_excel(FINAL_XLSX, sheet_name=0)
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    df.dropna(subset=["Date"], inplace=True)
    df.sort_values("Date", inplace=True)
    df.reset_index(drop=True, inplace=True)
    return df
