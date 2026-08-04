import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from data import load_data
from firebase_utils import get_formula_list


def heatmap_tab():
    user_email = st.session_state["user_info"].get("email", "None")
    admins = st.session_state["admins"]

    if user_email in admins:
        saved_formulas = get_formula_list(user_email)

    df = load_data()
    instruments = df.columns[1:]

    st.sidebar.title("Bond Analytics - Heatmap")

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
            filtered_df = df[
                (df["Date"] >= pd.to_datetime(start_date))
                & (df["Date"] <= pd.to_datetime(end_date))
            ].copy()

            daily_changes = filtered_df[instruments].diff().dropna()
            corr_matrix = daily_changes.corr()

            fig = go.Figure(data=go.Heatmap(
                z=corr_matrix.values,
                x=corr_matrix.columns,
                y=corr_matrix.index,
                colorscale="RdYlGn",
                zmin=-1,
                zmax=1,
                colorbar=dict(title="Correlation"),
            ))
            fig.update_layout(
                title=f"Correlation Heatmap ({start_date.strftime('%d-%b-%Y')} → {end_date.strftime('%d-%b-%Y')})",
                xaxis=dict(side="bottom", tickangle=-90),
                height=800,
                width=900,
            )
            st.session_state["corr_fig"] = fig

    if "corr_fig" in st.session_state:
        st.plotly_chart(st.session_state["corr_fig"], use_container_width=True)
