from __future__ import annotations

import pandas as pd
import streamlit as st

from data import load_data
from firebase_utils import get_instrument_metadata, save_instrument_metadata

_COUNTRIES = [
    "", "USA", "China", "Japan", "Germany", "France", "Italy",
    "United Kingdom", "India", "Canada", "Brazil",
    "Australia", "South Korea", "Mexico", "Other",
]
_ASSET_CLASSES = [
    "", "Fixed Income Bonds", "FX", "Equity Index",
    "Commodity", "Money Market", "Credit Spread", "Other",
]
_MATURITIES = [
    "", "1M", "3M", "6M", "1Y", "2Y", "3Y", "5Y",
    "7Y", "10Y", "15Y", "20Y", "30Y", "N/A",
]


def instrument_metadata_editor() -> None:
    st.markdown("#### Instrument Metadata")
    st.caption(
        "Tag each instrument with country, asset class, and maturity. "
        "Fixed Income Bonds instruments with a maturity appear in the Global Yield Curves tab."
    )

    df = load_data()
    instruments = list(df.columns[1:])  # skip the Date column

    existing = get_instrument_metadata()

    rows = [
        {
            "Instrument":   inst,
            "Country":      existing.get(inst, {}).get("country", ""),
            "Asset Class":  existing.get(inst, {}).get("asset_class", ""),
            "Maturity":     existing.get(inst, {}).get("maturity", ""),
            "Notes":        existing.get(inst, {}).get("notes", ""),
        }
        for inst in instruments
    ]
    meta_df = pd.DataFrame(rows)

    search = st.text_input(
        "filter", placeholder="Filter instruments…", label_visibility="collapsed"
    )
    display_df = (
        meta_df[meta_df["Instrument"].str.contains(search, case=False, na=False)]
        if search
        else meta_df
    )

    edited: pd.DataFrame = st.data_editor(
        display_df,
        column_config={
            "Instrument": st.column_config.TextColumn(
                "Instrument", disabled=True, width="medium"
            ),
            "Country": st.column_config.SelectboxColumn(
                "Country", options=_COUNTRIES, width="medium"
            ),
            "Asset Class": st.column_config.SelectboxColumn(
                "Asset Class", options=_ASSET_CLASSES, width="medium"
            ),
            "Maturity": st.column_config.SelectboxColumn(
                "Maturity", options=_MATURITIES, width="small"
            ),
            "Notes": st.column_config.TextColumn("Notes", width="large"),
        },
        use_container_width=True,
        hide_index=True,
        num_rows="fixed",
        key="inst_meta_editor",
    )

    col_save, col_info = st.columns([2, 5])
    with col_save:
        save_clicked = st.button("💾  Save Metadata", type="primary")

    if save_clicked:
        # Merge edited rows back into the full dict (preserves rows hidden by filter)
        full_meta: dict = dict(existing)
        for _, row in edited.iterrows():
            full_meta[row["Instrument"]] = {
                "country":     row["Country"] or "",
                "asset_class": row["Asset Class"] or "",
                "maturity":    row["Maturity"] or "",
                "notes":       row["Notes"] or "",
            }
        save_instrument_metadata(full_meta)
        st.cache_data.clear()
        with col_info:
            st.success(f"Saved {len(edited)} instrument(s).")
