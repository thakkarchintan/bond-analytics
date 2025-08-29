import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from firebase_config import firebase_config
def heatmap_tab():
    db = None
    saved_formulas = None
    user_email = st.session_state["user_info"].get("email", "None")
    admins = st.session_state["admins"]
    
    if user_email in admins:
        db = firebase_config()

        def load_formula_list(user_id):
            """Fetch the user's saved formula list."""
            doc = db.collection("formulas").document(user_id).get()
            if doc.exists:
                return doc.to_dict().get("formula_list", [])
            return []
        
        saved_formulas = load_formula_list(user_email)
        
    # Path to the Excel file
    file_path = 'Final.xlsx'

    # Function to load the data
    @st.cache_data
    def load_data(file_path):
        df = pd.read_excel(file_path, sheet_name=0)
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        df.dropna(subset=['Date'], inplace=True)
        return df

    # Load the data
    df = load_data(file_path)
   
    # Sidebar for user inputs
    st.sidebar.title('Bond Analytics - Heatmap')

    # List of instrument columns
    instruments = df.columns[1:32]

    # Dropdown for selecting instrument
    selected_instrument = st.sidebar.selectbox("Select Instrument", options=list(instruments))

    # Date inputs
    min_date = df['Date'].min().date()
    max_date = df['Date'].max().date()
    start_date = st.sidebar.date_input("Start Date", min_date, min_value=min_date, max_value=max_date)
    end_date = st.sidebar.date_input("End Date", max_date, min_value=min_date, max_value=max_date)

    # Submit button
    submit_button = st.sidebar.button('Submit')
    
    if submit_button:
        if start_date > end_date:
            st.sidebar.error('End Date must be on or after Start Date')
    else:
        # Filter data by date
        filtered_df = df[(df['Date'] >= pd.to_datetime(start_date)) & (df['Date'] <= pd.to_datetime(end_date))].copy()

        # Compute daily change for all instruments
        daily_changes = filtered_df[instruments].diff().dropna()

        # Correlation matrix of daily changes
        corr_matrix = daily_changes.corr()

        # Build square heatmap
        fig = go.Figure(data=go.Heatmap(
            z=corr_matrix.values,
            x=corr_matrix.columns,
            y=corr_matrix.index,
            colorscale='RdYlGn',
            zmin=-1, zmax=1,  # correlation range
            colorbar=dict(title="Correlation")
        ))

        fig.update_layout(
            title=f"Correlation Heatmap ({start_date.strftime('%d-%b-%Y')} → {end_date.strftime('%d-%b-%Y')})",
            xaxis=dict(
                side="bottom",
                tickangle=-90   # makes x-axis labels vertical
            ),
            height=800,
            width=900
        )
        st.plotly_chart(fig, use_container_width=True, key="corr_heatmap")
