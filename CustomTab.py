import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from data import load_data
from firebase_utils import get_formula_list, add_formula


def custom_tab():
    user_email = st.session_state["user_info"].get("email", "None")
    admins = st.session_state["admins"]

    saved_formulas = None
    if user_email in admins:
        saved_formulas = get_formula_list(user_email)

    df = load_data()

    if "custom_formula" not in st.session_state:
        st.session_state.custom_formula = ""
    if "overlay_custom_formula" not in st.session_state:
        st.session_state.overlay_custom_formula = ""

    st.sidebar.title("Bond Analytics")

    analysis_type = st.sidebar.selectbox(
        "Select Analysis Type", options=["Single", "Overlay"], key="overlayInput"
    )

    instruments = df.columns[1:]

    selected_instrument = st.sidebar.selectbox(
        "Select Instrument", options=["Custom"] + list(instruments)
    )

    if selected_instrument == "Custom":
        st.session_state.custom_formula = st.sidebar.text_area(
            "Enter Custom Formula (e.g., 'EU 10-Year - EU 5-Year + 2')",
            value=st.session_state.custom_formula,
        )

    overlay_instrument = None
    if analysis_type == "Overlay":
        overlay_instrument = st.sidebar.selectbox(
            "Select Overlay Instrument",
            options=["Custom"] + list(instruments),
            key="overlay_formula_selector",
        )
        if overlay_instrument == "Custom":
            st.session_state.overlay_custom_formula = st.sidebar.text_area(
                "Enter Overlay Custom Formula (e.g., 'EU 2-Year - EU 10-Year')",
                value=st.session_state.overlay_custom_formula,
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

    if user_email in admins:
        custom_f = st.session_state.get("custom_formula", "").strip()
        overlay_f = st.session_state.get("overlay_custom_formula", "").strip()
        saved_formulas = saved_formulas or []

        should_show_add = not saved_formulas or (
            (custom_f and custom_f not in saved_formulas)
            or (overlay_f and overlay_f not in saved_formulas)
        )

        if (custom_f or overlay_f) and should_show_add:
            if st.sidebar.button("➕ Add Formula"):
                if custom_f and custom_f not in saved_formulas:
                    add_formula(user_email, custom_f)
                    st.sidebar.success("✅ Primary formula saved.")
                if overlay_f and overlay_f not in saved_formulas:
                    add_formula(user_email, overlay_f)
                    st.sidebar.success("✅ Overlay formula saved.")

    def evaluate_formula(data, formula):
        try:
            return data.eval(formula)
        except Exception as e:
            st.sidebar.error(f"Error evaluating formula: {e}")
            return None

    if submit_button:
        if start_date > end_date:
            st.sidebar.error("End Date must be on or after Start Date")
        else:
            filtered_df = df[
                (df["Date"] >= pd.to_datetime(start_date))
                & (df["Date"] <= pd.to_datetime(end_date))
            ].copy()

            if selected_instrument == "Custom":
                if st.session_state.custom_formula:
                    filtered_df["Primary"] = evaluate_formula(
                        filtered_df, st.session_state.custom_formula
                    )
                    if filtered_df["Primary"] is None:
                        st.error("Error in evaluating the custom formula for the primary instrument.")
                        st.stop()
                    primary_title = st.session_state.custom_formula
                else:
                    st.sidebar.error("Please enter a valid custom formula for the primary instrument.")
                    st.stop()
            else:
                filtered_df["Primary"] = filtered_df[selected_instrument]
                primary_title = selected_instrument

            if analysis_type == "Overlay":
                if overlay_instrument == "Custom":
                    if st.session_state.overlay_custom_formula:
                        filtered_df["Overlay"] = evaluate_formula(
                            filtered_df, st.session_state.overlay_custom_formula
                        )
                        if filtered_df["Overlay"] is None:
                            st.error("Error in evaluating the custom formula for the overlay instrument.")
                            st.stop()
                        overlay_title = st.session_state.overlay_custom_formula
                    else:
                        st.sidebar.error("Please enter a valid custom formula for the overlay instrument.")
                        st.stop()
                else:
                    if overlay_instrument in df.columns:
                        filtered_df["Overlay"] = filtered_df[overlay_instrument]
                        overlay_title = overlay_instrument
                    else:
                        st.error(f"Overlay instrument '{overlay_instrument}' not found in data.")
                        st.stop()

            if analysis_type == "Single":
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=filtered_df["Date"],
                    y=filtered_df["Primary"],
                    mode="lines",
                    name=primary_title,
                    line=dict(color="blue"),
                ))
                fig.update_layout(
                    title=dict(text=primary_title, font=dict(color="blue")),
                    xaxis_title="Date",
                    yaxis_title=primary_title,
                    height=800,
                    width=1000,
                )
                st.plotly_chart(fig, use_container_width=True)

            elif analysis_type == "Overlay":
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=filtered_df["Date"],
                    y=filtered_df["Primary"],
                    mode="lines",
                    name=primary_title,
                    line=dict(color="blue"),
                    yaxis="y1",
                ))
                fig.add_trace(go.Scatter(
                    x=filtered_df["Date"],
                    y=filtered_df["Overlay"],
                    mode="lines",
                    name=overlay_title,
                    line=dict(color="red"),
                    yaxis="y2",
                ))
                fig.update_layout(
                    title=f"{primary_title} vs. {overlay_title}",
                    xaxis_title="Date",
                    yaxis=dict(
                        title=dict(text=primary_title, font=dict(color="blue")),
                        tickfont=dict(color="blue"),
                    ),
                    yaxis2=dict(
                        title=dict(text=overlay_title, font=dict(color="red")),
                        tickfont=dict(color="red"),
                        overlaying="y",
                        side="right",
                    ),
                    height=800,
                    width=1000,
                )
                st.plotly_chart(fig, use_container_width=True)

            if analysis_type == "Single":
                filtered_df["Daily Change"] = filtered_df["Primary"].diff()
                fig_change = go.Figure()
                fig_change.add_trace(go.Bar(
                    x=filtered_df["Date"],
                    y=filtered_df["Daily Change"],
                    name=f"Daily Change - {primary_title}",
                    marker=dict(color="blue"),
                ))
                fig_change.update_layout(
                    title=f"Daily Change - {primary_title}",
                    xaxis_title="Date",
                    yaxis_title="Daily Change",
                    height=800,
                    width=1000,
                )
                st.plotly_chart(fig_change, use_container_width=True)

            elif analysis_type == "Overlay":
                filtered_df["Primary Daily Change"] = filtered_df["Primary"].diff()
                filtered_df["Overlay Daily Change"] = filtered_df["Overlay"].diff()

                fig_primary_change = go.Figure()
                fig_primary_change.add_trace(go.Bar(
                    x=filtered_df["Date"],
                    y=filtered_df["Primary Daily Change"],
                    name=f"Daily Change - {primary_title}",
                    marker=dict(color="blue"),
                ))
                fig_primary_change.update_layout(
                    title=f"Daily Change - {primary_title}",
                    xaxis_title="Date",
                    yaxis_title="Daily Change",
                    height=800,
                    width=1000,
                )
                st.plotly_chart(fig_primary_change, use_container_width=True)

                fig_overlay_change = go.Figure()
                fig_overlay_change.add_trace(go.Bar(
                    x=filtered_df["Date"],
                    y=filtered_df["Overlay Daily Change"],
                    name=f"Daily Change - {overlay_title}",
                    marker=dict(color="red"),
                ))
                fig_overlay_change.update_layout(
                    title=f"Daily Change - {overlay_title}",
                    xaxis_title="Date",
                    yaxis_title="Daily Change",
                    height=800,
                    width=1000,
                )
                st.plotly_chart(fig_overlay_change, use_container_width=True)
