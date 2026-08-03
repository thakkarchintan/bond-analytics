import streamlit as st
from GridTab import grid_tab
from CustomTab import custom_tab


def home_page():
    if "selected_tab" not in st.session_state:
        st.session_state.selected_tab = "Custom Formula Graphs"

    st.session_state.selected_tab = st.sidebar.selectbox(
        "Select Section",
        ["Bond Spreads & Flies", "Custom Formula Graphs"],
        index=1 if st.session_state.get("selected_tab") == "Custom Formula Graphs" else 0,
    )

    if st.session_state.selected_tab == "Bond Spreads & Flies":
        grid_tab()
    elif st.session_state.selected_tab == "Custom Formula Graphs":
        custom_tab()
