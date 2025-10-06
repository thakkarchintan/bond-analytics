import pandas as pd
from datetime import datetime

def safe_to_datetime(series, colname="Date"):
    bad_rows = []
    parsed = []
    for i, val in enumerate(series):
        try:
            # try parsing with day-month-year short month (03-Jan-1994)
            dt = pd.to_datetime(val, format="%d-%b-%Y")
            parsed.append(dt)
        except Exception as e:
            bad_rows.append((i, val, str(e)))
            parsed.append(pd.NaT)  # keep placeholder
    # log
    if bad_rows:
        print(f"\n⚠️ Failed parsing {len(bad_rows)} values in column {colname}:")
        for row in bad_rows[:20]:  # only show first 20
            print(row)
    return pd.Series(parsed, index=series.index)

# usage
df_market = pd.read_excel("from.xlsx")
df_instruments = pd.read_excel("test.xlsx")

df_market['Date'] = safe_to_datetime(df_market['Date'], "market.Date")
df_instruments['Date'] = safe_to_datetime(df_instruments['Date'], "instrument.Date")

merged_df = pd.merge(df_instruments, df_market, on="Date", how="left")
merged_df.rename(columns={"Price": "BTC (USD)"}, inplace=True)

merged_df['Date'] = merged_df['Date'].dt.strftime("%d-%b-%Y")
merged_df.to_excel("merged_output.xlsx", index=False)
