# import streamlit as st
# import pandas as pd
# import plotly.graph_objects as go


# def grid_tab():
#     @st.cache_data
#     def load_data():
#         df = pd.read_excel("Final.xlsx")  # Update file path
#         df["Date"] = pd.to_datetime(df["Date"], errors="coerce")  # Ensure Date is in datetime format
#         return df.dropna(subset=["Date"])  # Drop rows where Date is NaT

#     # Dictionary: Formula Name -> Formula Logic
#     formulas = {
#     "Eurex 5-10 Spread": "FGBLY - FGBMY",
#     "Eurex 2-5 Spread": "FGBMY - FGBSY",
#     "Eurex 2-10 Spread": "FGBLY - FGBSY",
#     "Eurex 10-30 Spread": "FGBXY - FGBLY",
#     "Eurex 2-5-10 Fly": "FGBLY - 2 * FGBMY + FGBSY",
#     "Eurex 5-10-30 Fly": "FGBXY - 2 * FGBLY + FGBMY",
#     "US 5-10 Spread": "US10Y - US5Y",
#     "US 2-5 Spread": "US5Y - US2Y",
#     "US 2-10 Spread": "US10Y - US2Y",
#     "US 10-30 Spread": "US30Y - US10Y",
#     "US 2-5-10 Fly": "US10Y - 2 * US5Y + US2Y",
#     "US 5-10-30 Fly": "US30Y - 2 * US10Y + US5Y",
#     "Italian vs German 2Y": "FBTSY - FGBSY",
#     "Italian vs German 10Y": "FBTPY - FGBLY",
#     "Australian vs. Canadian 10Y": "AUS10Y - CAD10Y",
#     "French vs. German 10Y": "FOATY - FGBLY",
#     "UK vs. German 10Y": "UK10Y - FGBLY",
#     "UK vs. Australian 10Y": "UK10Y - AUS10Y",
#     "US vs. Australian 10Y": "US10Y - AUS10Y",
#     "Canadian vs. US 2-5-10 Fly": "CAD10Y - 2 * CAD5Y + CAD2Y - US10Y + 2 * US5Y - US2Y"
#     }

#     # Load Data
#     df = load_data()

#     # Sidebar: Date Range Selection
#     st.sidebar.header("📅 Filter Data by Date")

#     # Set min and max for date selection
#     min_date, max_date = df["Date"].min().date(), df["Date"].max().date()

#     start_date = st.sidebar.date_input("Start Date", min_date, min_value=min_date, max_value=max_date)
#     end_date = st.sidebar.date_input("End Date", max_date, min_value=min_date, max_value=max_date)

#     # Convert selected dates to datetime
#     start_date, end_date = pd.to_datetime(start_date), pd.to_datetime(end_date)

#     # Filter Data Based on Selected Date Range
#     df_filtered = df[(df["Date"] >= start_date) & (df["Date"] <= end_date)].reset_index(drop=True)

#     # Warn if no data is available after filtering
#     if df_filtered.empty:
#         st.warning(f"⚠️ No data available from {start_date.date()} to {end_date.date()}!")
#         st.stop()

#     # Title
#     # st.title("📊 Bond Spreads & Flies Visualization")

#     # Define Grid Layout (2 charts per row)
#     num_cols = 2
#     formula_names = list(formulas.keys())

#     for i in range(0, len(formula_names), num_cols):
#         cols = st.columns(num_cols)  # Create a row with 2 columns

#         for j, col in enumerate(cols):
#             idx = i + j
#             if idx < len(formula_names):
#                 formula_name = formula_names[idx]
#                 formula_logic = formulas[formula_name]

#                 # Compute Formula Values (Ensuring 'Date' is not included)
#                 try:
#                     df_filtered["Computed"] = df_filtered.eval(formula_logic)
#                 except Exception as e:
#                     st.error(f"Error computing {formula_name}: {e}")
#                     continue

#                 # Create Interactive Plotly Line Chart (X: Date, Y: Computed Formula)
#                 fig = go.Figure()
#                 fig.add_trace(go.Scatter(
#                     x=df_filtered['Date'],
#                     y=df_filtered['Computed'],
#                     mode='lines',
#                     name=formula_name,
#                     line=dict(color='blue')
#                 ))
#                 fig.update_layout(
#                     title=dict(text=formula_name, font=dict(color='blue')),
#                     xaxis_title='Date',
#                     yaxis_title=formula_name,
#                     height=600,
#                     width=800,
#                     xaxis=dict(showgrid=True, tickangle=-45)
#                 )

#                 # Display Graph in the respective column
#                 with col:
#                     st.plotly_chart(fig, use_container_width=True)


import streamlit as st
import pandas as pd
import plotly.graph_objects as go

def grid_tab():
    @st.cache_data
    def load_data():
        df = pd.read_excel("Final.xlsx")  # Update file path
        df["Date"] = pd.to_datetime(df["Date"], errors="coerce")  # Ensure Date is in datetime format
        return df.dropna(subset=["Date"])  # Drop rows where Date is NaT

    # Dictionary: Formula Name -> Formula Logic
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
        "Canadian vs. US 2-5-10 Fly": "CAD10Y - 2 * CAD5Y + CAD2Y - US10Y + 2 * US5Y - US2Y"
    }

    # Load Data
    df = load_data()

    # Sidebar: Date Range Selection
    min_date, max_date = df["Date"].min().date(), df["Date"].max().date()
    start_date = st.sidebar.date_input("Start Date", min_date, min_value=min_date, max_value=max_date)
    end_date = st.sidebar.date_input("End Date", max_date, min_value=min_date, max_value=max_date)

    start_date, end_date = pd.to_datetime(start_date), pd.to_datetime(end_date)
    df_filtered = df[(df["Date"] >= start_date) & (df["Date"] <= end_date)].reset_index(drop=True)

    if df_filtered.empty:
        st.warning(f"⚠️ No data available from {start_date.date()} to {end_date.date()}!")
        st.stop()

    # Sidebar: Number of Columns Selection
    num_cols = st.sidebar.slider("Select number of columns per row", min_value=1, max_value=4, value=2)

    # Define Grid Layout
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
                    x=df_filtered['Date'],
                    y=df_filtered['Computed'],
                    mode='lines',
                    name=formula_name,
                    line=dict(color='blue')
                ))
                fig.update_layout(
                    title=dict(text=formula_name, font=dict(color='blue')),
                    xaxis_title='Date',
                    yaxis_title=formula_name,
                    height=600,
                    width=800,
                    xaxis=dict(showgrid=True, tickangle=-45)
                )

                with col:
                    st.plotly_chart(fig, use_container_width=True)
