import pandas as pd
import streamlit as st

DATA_FILE = "Final.xlsx"


@st.cache_data
def load_data():
    df = pd.read_excel(DATA_FILE, sheet_name=0)
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    df.dropna(subset=["Date"], inplace=True)
    return df
