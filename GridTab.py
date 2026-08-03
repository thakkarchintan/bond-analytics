import streamlit as st
import plotly.graph_objects as go
from data import load_data
from firebase_utils import get_formula_list, add_formula, delete_formula


def grid_tab():
    user_email = st.session_state["user_info"].get("email", "None")
    admins = st.session_state["admins"]

    saved_formulas = None
    if user_email in admins:
        saved_formulas = get_formula_list(user_email)

    formulas = {
        "Eurex 5-10 Spread": "FGBLY - FGBMY",
        "Eurex 2-5 Spread": "FGBMY - FGBSY",
        "Eurex 2-10 Spread": "FGBLY - FGBSY",
        "Eurex 10-30 Spread": "FGBXY - FGBLY",
        "Eurex 2-5-10 Fly": "FGBLY - 2 * FGBMY + FGBSY",
        "Eurex 5-10-30 Fly": "FGBXY - 2 * FGBLY + FGBMY",
        "US 5-10 Spread": "US10Y - US5Y",
        "US 2-5 Spread": "US5Y - US2Y",
        "US 2-10 Spread": "US10Y - US2Y",
        "US 10-30 Spread": "US30Y - US10Y",
        "US 2-5-10 Fly": "US10Y - 2 * US5Y + US2Y",
        "US 5-10-30 Fly": "US30Y - 2 * US10Y + US5Y",
        "Italian vs German 2Y": "FBTSY - FGBSY",
        "Italian vs German 10Y": "FBTPY - FGBLY",
        "Australian vs. Canadian 10Y": "AUS10Y - CAD10Y",
        "French vs. German 10Y": "FOATY - FGBLY",
        "UK vs. German 10Y": "UK10Y - FGBLY",
        "UK vs. Australian 10Y": "UK10Y - AUS10Y",
        "US vs. Australian 10Y": "US10Y - AUS10Y",
        "Canadian vs. US 2-5-10 Fly": "CAD10Y - 2 * CAD5Y + CAD2Y - US10Y + 2 * US5Y - US2Y",
    }

    if saved_formulas:
        for f in saved_formulas:
            formulas[f] = f

    df = load_data()

    min_date, max_date = df["Date"].min().date(), df["Date"].max().date()
    start_date = st.sidebar.date_input("Start Date", min_date, min_value=min_date, max_value=max_date)
    end_date = st.sidebar.date_input("End Date", max_date, min_value=min_date, max_value=max_date)

    import pandas as pd
    start_date, end_date = pd.to_datetime(start_date), pd.to_datetime(end_date)
    df_filtered = df[(df["Date"] >= start_date) & (df["Date"] <= end_date)].reset_index(drop=True)

    if df_filtered.empty:
        st.warning(f"⚠️ No data available from {start_date.date()} to {end_date.date()}!")
        st.stop()

    num_cols = st.sidebar.slider("Select number of columns per row", min_value=1, max_value=4, value=2)

    if saved_formulas:
        st.sidebar.markdown(
            '<hr style="border: 1px solid #ccc; margin-top: 20px; margin-bottom: 10px;">',
            unsafe_allow_html=True,
        )
        st.sidebar.subheader("Manage Saved Formulas")
        selected_formula = st.sidebar.selectbox(
            "Select formula to delete:", saved_formulas, key="formula_dropdown"
        )
        if st.sidebar.button("Delete Formula"):
            delete_formula(user_email, selected_formula)
            st.sidebar.success(f"Deleted formula: {selected_formula}")
            st.rerun()

    formula_names = list(formulas.keys())
    for i in range(0, len(formula_names), num_cols):
        cols = st.columns(num_cols)
        for j, col in enumerate(cols):
            idx = i + j
            if idx < len(formula_names):
                formula_name = formula_names[idx]
                formula_logic = formulas[formula_name]

                try:
                    df_filtered["Computed"] = df_filtered.eval(formula_logic)
                except Exception as e:
                    st.error(f"Error computing {formula_name}: {e}")
                    continue

                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=df_filtered["Date"],
                    y=df_filtered["Computed"],
                    mode="lines",
                    name=formula_name,
                    line=dict(color="blue"),
                ))
                fig.update_layout(
                    title=dict(text=formula_name, font=dict(color="blue")),
                    xaxis_title="Date",
                    yaxis_title=formula_name,
                    height=600,
                    width=800,
                    xaxis=dict(showgrid=True, tickangle=-45),
                )

                with col:
                    st.plotly_chart(fig, use_container_width=True)
