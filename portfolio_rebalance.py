import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objs as go
from pandas.tseries.offsets import MonthEnd, QuarterEnd, DateOffset

def portfolio_rebalance() :
    
    st.set_page_config(layout="wide", page_title="Portfolio Rebalancer")


    @st.cache_data
    def load_data(file_path):
        df = pd.read_excel(file_path, sheet_name=0)
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        df.dropna(subset=['Date'], inplace=True)
        return df

    st.title("Portfolio Backtester — Fixed Weights + Periodic Rebalance")
    st.markdown("Upload an Excel/CSV where the **first column** is Date and each subsequent column is a product's daily price series.")

    # File upload
    # uploaded_file = st.sidebar.file_uploader("Upload Excel or CSV", type=["xlsx", "xls", "csv"])

    # uploaded_file = load_data('Final.xlsx')

    # Rebalance frequency
    rebalance_freq = st.sidebar.selectbox("Rebalance Frequency", ["Monthly", "Quarterly", "Half-Yearly", "Yearly"])

    # Risk-free rate input (annual %)
    risk_free_rate = st.sidebar.number_input("Risk-free Rate (annual %)", value=5.0, step=0.25) / 100.0

    # Date selection will be dynamic after upload

    # Helper metrics
    def calc_cagr(series):
        # series: price series indexed by date
        start_val = series.iloc[0]
        end_val = series.iloc[-1]
        years = (series.index[-1] - series.index[0]).days / 365.25
        if start_val <= 0 or years <= 0:
            return np.nan
        return (end_val / start_val) ** (1 / years) - 1


    def max_drawdown(series):
        # series: equity curve (values)
        roll_max = series.cummax()
        drawdown = series / roll_max - 1
        return drawdown.min()


    def sharpe_ratio(daily_returns, rf_annual):
        # rf_annual is in decimals
        if daily_returns.empty:
            return np.nan
        excess = daily_returns - rf_annual / 252.0
        if excess.std() == 0:
            return np.nan
        return excess.mean() / excess.std() * np.sqrt(252)


    def get_rebalance_dates(index, freq):
        # Always include the first date
        start = index[0]
        end = index[-1]
        if freq == "Monthly":
            dates = pd.date_range(start=start, end=end, freq='M')
        elif freq == "Quarterly":
            dates = pd.date_range(start=start, end=end, freq='Q')
        elif freq == "Half-Yearly":
            # Use 6 month frequency anchored to start
            dates = pd.date_range(start=start, end=end, freq='6M')
        else:
            dates = pd.date_range(start=start, end=end, freq='A')

        # make sure start is included and all dates are in index (snap to nearest available index date)
        rebalance_dates = [start]
        for d in dates:
            # find the nearest index date on or after d (prefer on or after to simulate EOD rebal)
            possible = index[index >= d]
            if not possible.empty:
                rebalance_dates.append(possible[0])
        # ensure unique and sorted
        rebalance_dates = sorted(list(pd.to_datetime(list(dict.fromkeys(rebalance_dates)))))
        # filter to be within index
        rebalance_dates = [d for d in rebalance_dates if d in index]
        return pd.DatetimeIndex(rebalance_dates)

    # Process upload
    # if uploaded_file is not None:
    #     try:
    #         if uploaded_file.name.endswith('.csv'):
    #             raw = pd.read_csv(uploaded_file)
    #         else:
    #             raw = pd.read_excel(uploaded_file)
    #     except Exception as e:
    #         st.error(f"Error reading file: {e}")
    #         st.stop()

        # Assume first column is date
    raw = load_data("Final.xlsx")   
    raw.columns = [c.strip() for c in raw.columns]
    date_col = raw.columns[0]
    df = raw.copy()
    try:
        df[date_col] = pd.to_datetime(df[date_col])
    except Exception:
        st.error("Couldn't parse the first column as dates. Ensure the first column contains valid dates.")
        st.stop()

    df.set_index(date_col, inplace=True)
    df = df.sort_index()

    # Forward fill and drop all-na columns
    df = df.ffill().dropna(how='all')

    # Allow user to pick assets
    assets = list(df.columns)
    st.sidebar.markdown("### Select assets to include")
    selected = st.sidebar.multiselect("Choose one or more products", assets, default=assets[:2])

    if not selected:
        st.warning("Choose at least one product from the sidebar.")
        st.stop()

    st.sidebar.markdown("### Set target weights (must sum to 100)")

    # Create inputs for weights
    default_weight = round(100 / len(selected), 2)
    weights = {}
    cols = st.sidebar.columns(1)
    total_weight = 0.0
    for asset in selected:
        w = st.sidebar.number_input(f"Weight % - {asset}", min_value=0.0, max_value=100.0, value=float(default_weight), step=0.5)
        weights[asset] = w
        total_weight += w

    if total_weight != 100.0:
        st.sidebar.warning(f"Weights sum to {total_weight:.2f}%. They must sum to 100%. Use the 'Normalize' button to auto-normalize.")
        if st.sidebar.button("Normalize weights to 100%"):
            # normalize
            s = sum(weights.values())
            if s == 0:
                # distribute equally
                for k in weights:
                    weights[k] = round(100.0 / len(weights), 4)
            else:
                for k in weights:
                    weights[k] = round(weights[k] / s * 100.0, 4)
            st.experimental_rerun()

    # Date range selection
    min_date = df.index.min().date()
    max_date = df.index.max().date()

    st.sidebar.markdown("---")
    start_date = st.sidebar.date_input("Start Date", value=min_date, min_value=min_date, max_value=max_date)
    end_date = st.sidebar.date_input("End Date", value=max_date, min_value=min_date, max_value=max_date)

    if pd.to_datetime(start_date) >= pd.to_datetime(end_date):
        st.error("Start date must be before end date.")
        st.stop()

    # Trim dataframe
    df = df.loc[(df.index.date >= pd.to_datetime(start_date).date()) & (df.index.date <= pd.to_datetime(end_date).date())]
    if df.empty:
        st.error("No data in chosen date range after trimming.")
        st.stop()

    # Keep only selected assets
    prices = df[selected].copy()

    # Rebalance dates
    rebalance_dates = get_rebalance_dates(prices.index, rebalance_freq)

    # Simulation
    initial_capital = st.sidebar.number_input("Initial Investment Amount", value=1000000.0, step=1000.0)

    # Prepare structures
    portfolio_values = pd.Series(index=prices.index, dtype=float)
    individual_values = pd.DataFrame(index=prices.index, columns=selected, dtype=float)

    # Start with initial allocation at first available date
    target_weights = {k: v / 100.0 for k, v in weights.items()}

    # units holdings dict
    units = {k: 0.0 for k in selected}

    # Initial buy on the first day
    first_date = prices.index[0]
    for asset in selected:
        alloc_amount = target_weights[asset] * initial_capital
        price = prices.loc[first_date, asset]
        units[asset] = alloc_amount / price if price != 0 else 0.0
        individual_values.loc[first_date, asset] = units[asset] * price
    portfolio_values.loc[first_date] = individual_values.loc[first_date].sum()

    last_rebal_date = first_date

    # Iterate through dates and rebalance on rebalance dates (except first)
    for cur_date in prices.index[1:]:
        # Carry forward individual values based on held units
        for asset in selected:
            price = prices.loc[cur_date, asset]
            individual_values.loc[cur_date, asset] = units[asset] * price

        portfolio_values.loc[cur_date] = individual_values.loc[cur_date].sum()

        # If today's a rebalance date (and not the first day), reset units to match target weights
        if cur_date in rebalance_dates and cur_date != first_date:
            total_val = portfolio_values.loc[cur_date]
            for asset in selected:
                alloc_amount = target_weights[asset] * total_val
                price = prices.loc[cur_date, asset]
                units[asset] = alloc_amount / price if price != 0 else 0.0
            last_rebal_date = cur_date

    # Fill any remaining NaNs (shouldn't be many after ffill)
    portfolio_values = portfolio_values.ffill()
    individual_values = individual_values.ffill()

    # Performance metrics
    # Individual metrics
    metrics = []
    for asset in selected:
        series = individual_values[asset]
        cagr = calc_cagr(series)
        mdd = max_drawdown(series)
        daily_ret = series.pct_change().dropna()
        sr = sharpe_ratio(daily_ret, risk_free_rate)
        metrics.append({"Asset": asset, "CAGR": cagr, "Max Drawdown": mdd, "Sharpe": sr})

    # Portfolio metrics
    port_cagr = calc_cagr(portfolio_values)
    port_mdd = max_drawdown(portfolio_values)
    port_daily_ret = portfolio_values.pct_change().dropna()
    port_sharpe = sharpe_ratio(port_daily_ret, risk_free_rate)

    # Show results
    st.subheader("Equity Curves")
    fig = go.Figure()
    # individual
    for asset in selected:
        fig.add_trace(go.Scatter(x=individual_values.index, y=individual_values[asset], mode='lines', name=f"{asset}"))
    # portfolio
    fig.add_trace(go.Scatter(x=portfolio_values.index, y=portfolio_values, mode='lines', name='Portfolio', line=dict(width=3, dash='dash')))
    fig.update_layout(title='Equity Curves (individual assets + portfolio)', xaxis_title='Date', yaxis_title='Value')
    st.plotly_chart(fig, use_container_width=True)

    # Metrics table
    metrics_df = pd.DataFrame(metrics).set_index('Asset')
    metrics_df.loc['Portfolio'] = [port_cagr, port_mdd, port_sharpe]
    metrics_df = metrics_df.rename(columns={0: 'CAGR', 1: 'Max Drawdown', 2: 'Sharpe'}) if False else metrics_df

    # Format and show
    st.subheader("Performance Metrics")
    display_df = metrics_df.copy()
    display_df['CAGR'] = display_df['CAGR'].map(lambda x: f"{x:.2%}" if pd.notnull(x) else "N/A")
    display_df['Max Drawdown'] = display_df['Max Drawdown'].map(lambda x: f"{x:.2%}" if pd.notnull(x) else "N/A")
    display_df['Sharpe'] = display_df['Sharpe'].map(lambda x: f"{x:.2f}" if pd.notnull(x) else "N/A")
    st.table(display_df)

    # Show rebalance summary
    st.subheader("Rebalance Details")
    st.write(f"Rebalance frequency: {rebalance_freq}")
    st.write(f"Rebalance dates used (sample up to 50): {list(rebalance_dates[:50])}")

    # Allow download of results
    results = pd.concat([individual_values, portfolio_values.rename('Portfolio')], axis=1)
    csv = results.to_csv(index=True)
    st.download_button("Download equity curves (CSV)", csv, file_name='equity_curves.csv', mime='text/csv')

    # else:
    #     st.info("Upload an Excel/CSV file to get started. The first column must be dates and subsequent columns prices for each product.")
