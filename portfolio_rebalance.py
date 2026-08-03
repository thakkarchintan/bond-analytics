import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objs as go
from data import load_data


def portfolio_rebalance():

    def calc_cagr(series):
        start_val = series.iloc[0]
        end_val = series.iloc[-1]
        years = (series.index[-1] - series.index[0]).days / 365.25
        if start_val <= 0 or years <= 0:
            return np.nan
        return (end_val / start_val) ** (1 / years) - 1

    def max_drawdown(series):
        roll_max = series.cummax()
        drawdown = series / roll_max - 1
        return drawdown.min()

    def sharpe_ratio(daily_returns, rf_annual):
        if daily_returns.empty:
            return np.nan
        excess = daily_returns - rf_annual / 252.0
        if excess.std() == 0:
            return np.nan
        return excess.mean() / excess.std() * np.sqrt(252)

    def get_rebalance_dates(index, freq):
        start = index[0]
        end = index[-1]
        if freq == "Monthly":
            dates = pd.date_range(start=start, end=end, freq="M")
        elif freq == "Quarterly":
            dates = pd.date_range(start=start, end=end, freq="Q")
        elif freq == "Half-Yearly":
            dates = pd.date_range(start=start, end=end, freq="6M")
        else:
            dates = pd.date_range(start=start, end=end, freq="A")

        rebalance_dates = [start]
        for d in dates:
            possible = index[index >= d]
            if not possible.empty:
                rebalance_dates.append(possible[0])
        rebalance_dates = sorted(list(pd.to_datetime(list(dict.fromkeys(rebalance_dates)))))
        rebalance_dates = [d for d in rebalance_dates if d in index]
        return pd.DatetimeIndex(rebalance_dates)

    rebalance_freq = st.sidebar.selectbox(
        "Rebalance Frequency", ["Monthly", "Quarterly", "Half-Yearly", "Yearly"]
    )
    risk_free_rate = st.sidebar.number_input(
        "Risk-free Rate (annual %)", value=5.0, step=0.25
    ) / 100.0

    raw = load_data()
    raw.columns = [c.strip() for c in raw.columns]
    date_col = raw.columns[0]
    df = raw.copy()
    try:
        df[date_col] = pd.to_datetime(df[date_col])
    except Exception:
        st.error("Couldn't parse the first column as dates.")
        st.stop()

    df.set_index(date_col, inplace=True)
    df = df.sort_index()
    df = df.ffill().dropna(how="all")

    assets = list(df.columns)
    st.sidebar.markdown("### Select assets to include")
    selected = st.sidebar.multiselect(
        "Choose one or more products", assets, default=assets[:2]
    )

    if not selected:
        st.warning("Choose at least one product from the sidebar.")
        st.stop()

    st.sidebar.markdown("### Set target weights (must sum to 100)")
    default_weight = round(100 / len(selected), 2)
    weights = {}
    total_weight = 0.0
    for asset in selected:
        w = st.sidebar.number_input(
            f"Weight % - {asset}",
            min_value=0.0,
            max_value=100.0,
            value=float(default_weight),
            step=0.5,
        )
        weights[asset] = w
        total_weight += w

    if total_weight != 100.0:
        st.sidebar.warning(
            f"Weights sum to {total_weight:.2f}%. They must sum to 100%. "
            "Use the 'Normalize' button to auto-normalize."
        )
        if st.sidebar.button("Normalize weights to 100%"):
            s = sum(weights.values())
            if s == 0:
                for k in weights:
                    weights[k] = round(100.0 / len(weights), 4)
            else:
                for k in weights:
                    weights[k] = round(weights[k] / s * 100.0, 4)
            st.rerun()

    min_date = df.index.min().date()
    max_date = df.index.max().date()
    st.sidebar.markdown("---")
    start_date = st.sidebar.date_input("Start Date", value=min_date, min_value=min_date, max_value=max_date)
    end_date = st.sidebar.date_input("End Date", value=max_date, min_value=min_date, max_value=max_date)

    if pd.to_datetime(start_date) >= pd.to_datetime(end_date):
        st.error("Start date must be before end date.")
        st.stop()

    df = df.loc[
        (df.index.date >= pd.to_datetime(start_date).date())
        & (df.index.date <= pd.to_datetime(end_date).date())
    ]
    if df.empty:
        st.error("No data in chosen date range after trimming.")
        st.stop()

    prices = df[selected].copy()
    rebalance_dates = get_rebalance_dates(prices.index, rebalance_freq)

    initial_capital = st.sidebar.number_input(
        "Initial Investment Amount", value=1000000.0, step=1000.0
    )

    portfolio_values = pd.Series(index=prices.index, dtype=float)
    individual_values = pd.DataFrame(index=prices.index, columns=selected, dtype=float)
    target_weights = {k: v / 100.0 for k, v in weights.items()}
    units = {k: 0.0 for k in selected}

    first_date = prices.index[0]
    for asset in selected:
        alloc_amount = target_weights[asset] * initial_capital
        price = prices.loc[first_date, asset]
        units[asset] = alloc_amount / price if price != 0 else 0.0
        individual_values.loc[first_date, asset] = units[asset] * price
    portfolio_values.loc[first_date] = individual_values.loc[first_date].sum()

    for cur_date in prices.index[1:]:
        for asset in selected:
            price = prices.loc[cur_date, asset]
            individual_values.loc[cur_date, asset] = units[asset] * price
        portfolio_values.loc[cur_date] = individual_values.loc[cur_date].sum()
        if cur_date in rebalance_dates and cur_date != first_date:
            total_val = portfolio_values.loc[cur_date]
            for asset in selected:
                alloc_amount = target_weights[asset] * total_val
                price = prices.loc[cur_date, asset]
                units[asset] = alloc_amount / price if price != 0 else 0.0

    portfolio_values = portfolio_values.ffill()
    individual_values = individual_values.ffill()

    metrics = []
    for asset in selected:
        series = individual_values[asset]
        cagr = calc_cagr(series)
        mdd = max_drawdown(series)
        daily_ret = series.pct_change().dropna()
        sr = sharpe_ratio(daily_ret, risk_free_rate)
        metrics.append({"Asset": asset, "CAGR": cagr, "Max Drawdown": mdd, "Sharpe": sr})

    port_cagr = calc_cagr(portfolio_values)
    port_mdd = max_drawdown(portfolio_values)
    port_daily_ret = portfolio_values.pct_change().dropna()
    port_sharpe = sharpe_ratio(port_daily_ret, risk_free_rate)

    chart_values = pd.DataFrame(index=prices.index)
    for asset in selected:
        w = target_weights[asset]
        raw_series = prices[asset] / w
        chart_values[f"{asset}-Chart"] = raw_series / raw_series.iloc[0] * initial_capital
    chart_values["Portfolio"] = portfolio_values

    st.subheader("Equity Curves")
    fig = go.Figure()
    for asset in selected:
        fig.add_trace(go.Scatter(
            x=individual_values.index, y=individual_values[asset], mode="lines", name=f"{asset}"
        ))
    fig.add_trace(go.Scatter(
        x=portfolio_values.index,
        y=portfolio_values,
        mode="lines",
        name="Portfolio",
        line=dict(width=3),
    ))
    fig.add_trace(go.Scatter(
        x=chart_values.index,
        y=chart_values[selected[0] + "-Chart"],
        mode="lines",
        name="Price/Weight",
        line=dict(color="green", width=2),
    ))
    fig.update_layout(
        title="Equity Curves (individual assets + portfolio)",
        xaxis_title="Date",
        yaxis_title="Value",
    )
    st.plotly_chart(fig, use_container_width=True)

    metrics_df = pd.DataFrame(metrics).set_index("Asset")
    metrics_df.loc["Portfolio"] = [port_cagr, port_mdd, port_sharpe]

    results = pd.concat([individual_values, portfolio_values.rename("Portfolio")], axis=1)
    csv = results.to_csv(index=True)

    col1, col2, col3 = st.columns([3, 3, 2])
    with col3:
        st.download_button(
            "Download equity curves (CSV)",
            csv,
            file_name="equity_curves.csv",
            mime="text/csv",
        )

    st.subheader("Performance Metrics")
    display_df = metrics_df.copy()
    display_df["CAGR"] = display_df["CAGR"].map(lambda x: f"{x:.2%}" if pd.notnull(x) else "N/A")
    display_df["Max Drawdown"] = display_df["Max Drawdown"].map(
        lambda x: f"{x:.2%}" if pd.notnull(x) else "N/A"
    )
    display_df["Sharpe"] = display_df["Sharpe"].map(
        lambda x: f"{x:.2f}" if pd.notnull(x) else "N/A"
    )
    st.table(display_df)

    st.subheader("Rebalance Details")
    st.write(f"Rebalance frequency: {rebalance_freq}")
    rebalance_table = pd.DataFrame({
        "Rebalance Date": [d.strftime("%d-%b-%Y") for d in rebalance_dates[:50]]
    })
    st.table(rebalance_table)
