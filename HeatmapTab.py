import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from data import load_data
from firebase_utils import get_instrument_metadata


@st.cache_data(ttl=300)
def _load_metadata() -> dict:
    return get_instrument_metadata()


def heatmap_tab():
    df = load_data()
    all_instruments = list(df.columns[1:])

    st.sidebar.title("Correlation Matrix")

    # ── Asset class filter ────────────────────────────────────────────────────
    meta = _load_metadata()
    inst_class = {
        inst: meta.get(inst, {}).get("asset_class", "") or "Untagged"
        for inst in all_instruments
    }
    available_classes = sorted(set(inst_class.values()))

    st.sidebar.markdown(
        '<div style="font-size:11px;color:#94a3b8;text-transform:uppercase;'
        'letter-spacing:.08em;margin:12px 0 4px;">Asset Class</div>',
        unsafe_allow_html=True,
    )
    selected_classes = st.sidebar.multiselect(
        "Asset Classes",
        options=available_classes,
        default=available_classes,
        key="hm_asset_classes",
        label_visibility="collapsed",
    )

    instruments = [i for i in all_instruments if inst_class[i] in selected_classes]

    if len(instruments) < 2:
        st.sidebar.warning("Select at least 2 instruments via the asset class filter.")

    # ── Date range ────────────────────────────────────────────────────────────
    st.sidebar.markdown(
        '<div style="font-size:11px;color:#94a3b8;text-transform:uppercase;'
        'letter-spacing:.08em;margin:12px 0 4px;">Date Range</div>',
        unsafe_allow_html=True,
    )
    min_date = df["Date"].min().date()
    max_date = df["Date"].max().date()
    start_date = st.sidebar.date_input(
        "Start Date", min_date, min_value=min_date, max_value=max_date
    )
    end_date = st.sidebar.date_input(
        "End Date", max_date, min_value=min_date, max_value=max_date
    )

    submit_button = st.sidebar.button("Submit")

    if submit_button:
        if start_date > end_date:
            st.sidebar.error("End Date must be on or after Start Date")
        else:
            try:
                if len(instruments) < 2:
                    st.warning("Select at least 2 asset classes to compute a correlation matrix.")
                    return

                filtered_df = df[
                    (df["Date"] >= pd.to_datetime(start_date))
                    & (df["Date"] <= pd.to_datetime(end_date))
                ].copy()

                numeric_cols = (
                    filtered_df[instruments]
                    .select_dtypes(include="number")
                    .columns
                )
                # Drop only the first row (always NaN after diff); let corr()
                # handle per-pair NaN so sparse columns (e.g. BTC) don't wipe the matrix
                daily_changes = filtered_df[numeric_cols].diff().iloc[1:]

                if daily_changes.empty or len(daily_changes) < 2:
                    st.warning("Not enough data in the selected date range to compute correlations.")
                else:
                    corr_matrix = daily_changes.corr()
                    fig = go.Figure(data=go.Heatmap(
                        z=corr_matrix.values,
                        x=corr_matrix.columns.tolist(),
                        y=corr_matrix.index.tolist(),
                        colorscale="RdYlGn",
                        zmin=-1,
                        zmax=1,
                        colorbar=dict(title="Correlation"),
                    ))
                    fig.update_layout(
                        title=f"Correlation Heatmap ({start_date.strftime('%d-%b-%Y')} → {end_date.strftime('%d-%b-%Y')})",
                        xaxis=dict(side="bottom", tickangle=-90),
                        height=800,
                    )
                    st.session_state["corr_fig"] = fig
            except Exception as e:
                st.error(f"Error computing correlation: {e}")

    if "corr_fig" in st.session_state:
        st.plotly_chart(st.session_state["corr_fig"], use_container_width=True)
