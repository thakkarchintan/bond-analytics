import os
import pandas as pd

def normalize_dates(df, date_column):
    """
    Normalize dates in a DataFrame to the format '%d-%b-%Y' (e.g., 16-Jan-2025).
    Logs invalid dates for debugging purposes.
    """
    try:
        # Keep track of the original dates for logging invalid entries
        original_dates = df[date_column].copy()

        # Attempt to parse dates with flexible parsing
        df[date_column] = pd.to_datetime(
            df[date_column],
            format=None,  # Automatically infer if possible
            dayfirst=True,  # Treat day as first if ambiguous
            errors='coerce'
        )

        # Identify invalid dates
        invalid_dates = original_dates[df[date_column].isna()]
        if not invalid_dates.empty:
            print(f"Invalid dates found in column '{date_column}':")
            print(invalid_dates.to_string(index=False))

        # Format valid dates as '%d-%b-%Y'
        df[date_column] = df[date_column].dt.strftime('%d-%b-%Y')

    except Exception as e:
        print(f"Error normalizing dates in '{date_column}': {e}")

    return df


def update_main_excel(main_excel_path, csv_folder, date_column="Date"):
    # Load the main Excel file
    main_df = pd.read_excel(main_excel_path)

    # Normalize dates in the main file
    print("Normalizing dates in the main Excel file...")
    main_df = normalize_dates(main_df, date_column)

    # Process each CSV file
    for csv_file in os.listdir(csv_folder):
        if csv_file.endswith(".csv"):
            csv_path = os.path.join(csv_folder, csv_file)
            column_name = os.path.splitext(csv_file)[0]

            if column_name not in main_df.columns:
                print(f"Column '{column_name}' not found in the main Excel file. Skipping...")
                continue

            print(f"Normalizing dates in {csv_path}...")
            csv_df = pd.read_csv(csv_path)

            if date_column not in csv_df.columns or 'Price' not in csv_df.columns:
                print(f"Required columns missing in {csv_path}. Skipping...")
                continue

            # Normalize dates in the CSV file
            csv_df = normalize_dates(csv_df, date_column)

            # Merge the data based on the Date column
            merged_df = pd.merge(
                main_df,
                csv_df[[date_column, 'Price']],
                on=date_column,
                how='left',
                suffixes=('', '_temp')
            )

            # Update the main DataFrame with new Price data
            if f"Price_temp" in merged_df.columns:
                merged_df[column_name] = merged_df['Price_temp'].fillna(merged_df[column_name])
                merged_df.drop(columns=['Price_temp'], inplace=True)

            main_df = merged_df

    # Save the updated main Excel file
    output_path = "updated_" + os.path.basename(main_excel_path)
    main_df.to_excel(output_path, index=False)
    print(f"Main Excel file updated successfully! Saved to {output_path}")


# Example usage
main_excel_path = "Demo.xlsx"  # Path to the main Excel file
csv_folder = "csv"  # Path to the folder containing the CSV files
update_main_excel(main_excel_path, csv_folder)
