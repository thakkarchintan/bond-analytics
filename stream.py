# import streamlit as st
# from GridTab import grid_tab
# from CustomTab import custom_tab

# def home_page():
#     # Initialize session state for tab selection
#     if "selected_tab" not in st.session_state:
#         st.session_state.selected_tab = "Custom Formula Graphs"  # Default tab

#     # Sidebar: Tabs for different sections in a single row
#     col1, col2 = st.sidebar.columns(2)

#     # Creating buttons for tabs (Update session state on click)
#     if col1.button("Bond Spreads & Flies"):
#         st.session_state.selected_tab = "Bond Spreads & Flies"
#     if col2.button("Custom Formula Graphs"):
#         st.session_state.selected_tab = "Custom Formula Graphs"

#     # Display content based on stored selection
#     if st.session_state.selected_tab == "Bond Spreads & Flies":
#         grid_tab()
#     elif st.session_state.selected_tab == "Custom Formula Graphs":
#         custom_tab()

import streamlit as st
from GridTab import grid_tab
from CustomTab import custom_tab
from HeatmapTab import heatmap_tab

def home_page():
    # Initialize session state for tab selection
    if "selected_tab" not in st.session_state:
        st.session_state.selected_tab = "Custom Formula Graphs"  # Default tab

    st.session_state.selected_tab = st.sidebar.selectbox(
        "Select Section", 
        ["Bond Spreads & Flies", "Custom Formula Graphs"],
        index=1 if st.session_state.get("selected_tab") == "Custom Formula Graphs" else 0
    )


    # Display content based on stored selection
    if st.session_state.selected_tab == "Bond Spreads & Flies":
        grid_tab()
    elif st.session_state.selected_tab == "Custom Formula Graphs":
        custom_tab()

    