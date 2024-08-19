import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# Set Streamlit screen layout to wide
st.set_page_config(layout="wide", page_title="Bond Analytics")

# Path to the Excel file
file_path = 'Yields data.xlsx'

# Initialize session state
if 'custom_formula' not in st.session_state:
    st.session_state.custom_formula = ''
if 'overlay_custom_formula' not in st.session_state:
    st.session_state.overlay_custom_formula = ''

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
st.sidebar.title('Bond Analytics')

# First dropdown for selecting analysis type
analysis_type = st.sidebar.selectbox("Select Analysis Type", options=["Single", "Overlay"])

# List of instrument columns
instruments = df.columns[1:]

# Dropdown for selecting the primary instrument or custom option
selected_instrument = st.sidebar.selectbox("Select Instrument", options=["Custom"] + list(instruments))

# Text box for custom formula input when "Custom" is selected for the primary instrument
if selected_instrument == "Custom":
    st.session_state.custom_formula = st.sidebar.text_area(
        "Enter Custom Formula (e.g., 'EU 10-Year - EU 5-Year + 2')",
        value=st.session_state.custom_formula
    )

# Dropdown for selecting overlay instrument if overlay analysis is chosen
overlay_instrument = None
overlay_custom_formula = None
if analysis_type == "Overlay":
    overlay_instrument = st.sidebar.selectbox("Select Overlay Instrument", options=["Custom"] + list(instruments))
    
    # Text box for custom formula input when "Custom" is selected for the overlay instrument
    if overlay_instrument == "Custom":
        st.session_state.overlay_custom_formula = st.sidebar.text_area(
            "Enter Overlay Custom Formula (e.g., 'EU 2-Year - EU 10-Year')",
            value=st.session_state.overlay_custom_formula
        )

# Date inputs for filtering data
min_date = df['Date'].min().date()
max_date = df['Date'].max().date()
start_date = st.sidebar.date_input("Start Date", min_date, min_value=min_date, max_value=max_date)
end_date = st.sidebar.date_input("End Date", max_date, min_value=min_date, max_value=max_date)

# Submit button
submit_button = st.sidebar.button('Submit')

# Function to evaluate custom formula
def evaluate_formula(df, formula):
    try:
        # Mapping instrument names to pandas Series for safe evaluation
        instrument_series = {instrument: df[instrument] for instrument in instruments}
        # Evaluating the formula with the instrument data
        result = eval(formula, {"__builtins__": None}, instrument_series)
        return result
    except Exception as e:
        st.sidebar.error(f"Error evaluating formula: {e}")
        return None

# Fetch and plot data based on user selection
if submit_button:
    if start_date > end_date:
        st.sidebar.error('End Date must be on or after Start Date')
    else:
        # Filter the DataFrame based on the selected dates
        filtered_df = df[(df['Date'] >= pd.to_datetime(start_date)) & (df['Date'] <= pd.to_datetime(end_date))].copy()

        # Handle custom formula for primary instrument
        if selected_instrument == "Custom":
            if st.session_state.custom_formula:
                filtered_df['Primary'] = evaluate_formula(filtered_df, st.session_state.custom_formula)
                if filtered_df['Primary'] is None:
                    st.error("Error in evaluating the custom formula for the primary instrument.")
                    st.stop()
                primary_title = st.session_state.custom_formula
            else:
                st.sidebar.error("Please enter a valid custom formula for the primary instrument.")
                st.stop()
        else:
            filtered_df['Primary'] = filtered_df[selected_instrument]
            primary_title = selected_instrument

        # For Overlay, process the overlay instrument
        if analysis_type == "Overlay":
            if overlay_instrument == "Custom":
                if st.session_state.overlay_custom_formula:
                    filtered_df['Overlay'] = evaluate_formula(filtered_df, st.session_state.overlay_custom_formula)
                    if filtered_df['Overlay'] is None:
                        st.error("Error in evaluating the custom formula for the overlay instrument.")
                        st.stop()
                    overlay_title = st.session_state.overlay_custom_formula
                else:
                    st.sidebar.error("Please enter a valid custom formula for the overlay instrument.")
                    st.stop()
            else:
                if overlay_instrument in df.columns:
                    filtered_df['Overlay'] = filtered_df[overlay_instrument]
                    overlay_title = overlay_instrument
                else:
                    st.error(f"Overlay instrument '{overlay_instrument}' not found in data.")
                    st.stop()

        # Plotting with Plotly

        if analysis_type == "Single":
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=filtered_df['Date'],
                y=filtered_df['Primary'],
                mode='lines',
                name=primary_title,
                line=dict(color='blue')
            ))
            fig.update_layout(
                title=primary_title,
                xaxis_title='Date',
                yaxis_title=primary_title,
                height=800,  # Make the chart height 800
                width=1000  # Fixed width; adjust as needed
            )
            st.plotly_chart(fig, use_container_width=True)

        elif analysis_type == "Overlay":
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=filtered_df['Date'],
                y=filtered_df['Primary'],
                mode='lines',
                name=primary_title,
                line=dict(color='blue')
            ))
            fig.add_trace(go.Scatter(
                x=filtered_df['Date'],
                y=filtered_df['Overlay'],
                mode='lines',
                name=overlay_title,
                line=dict(color='red')
            ))
            fig.update_layout(
                title=f"{primary_title} vs. {overlay_title}",
                xaxis_title='Date',
                yaxis_title='Value',
                height=800,  # Make the chart height 800
                width=1000  # Fixed width; adjust as needed
            )
            st.plotly_chart(fig, use_container_width=True)
