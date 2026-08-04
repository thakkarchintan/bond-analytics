import os

import streamlit as st

from CustomTab import custom_tab
from GridTab import grid_tab
from InstrumentMetadata import instrument_metadata_editor


def home_page():
    if "selected_tab" not in st.session_state:
        st.session_state.selected_tab = "Custom Formula Graphs"

    user_email = st.session_state.get("user_info", {}).get("email", "")
    admins = st.session_state.get("admins", [])
    is_admin = user_email in admins

    sections = ["Bond Spreads & Flies", "Custom Formula Graphs"]
    if is_admin:
        sections.append("Instrument Metadata")

    current = st.session_state.get("selected_tab", "Custom Formula Graphs")
    default_idx = sections.index(current) if current in sections else 0

    st.session_state.selected_tab = st.sidebar.selectbox(
        "Select Section", sections, index=default_idx
    )

    if st.session_state.selected_tab == "Bond Spreads & Flies":
        grid_tab()
    elif st.session_state.selected_tab == "Custom Formula Graphs":
        custom_tab()
    elif st.session_state.selected_tab == "Instrument Metadata":
        instrument_metadata_editor()
