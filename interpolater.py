import pandas as pd

def linear_interpolate_excel(file_path, columns_to_interpolate):
    """
    Perform linear interpolation on specified columns in an Excel file and overwrite the original file.
    
    Parameters:
        file_path (str): Path to the input Excel file.
        columns_to_interpolate (list): List of column names to interpolate.
    """
    # Load the Excel file
    df = pd.read_excel(file_path)

    # Perform linear interpolation for specified columns
    for column in columns_to_interpolate:
        if column in df.columns:
            print(f"Performing linear interpolation for column: {column}")

            # Check for missing values
            missing_count = df[column].isna().sum()
            if missing_count > 0:
                print(f"Missing values found in column '{column}': {missing_count}")
                
                # Perform linear interpolation
                df[column] = df[column].interpolate(method='linear', limit_direction='both')

                # Round the interpolated values to three decimal places
                df[column] = df[column].round(3)

                # Check if all missing values are filled
                remaining_missing = df[column].isna().sum()
                if remaining_missing > 0:
                    print(f"Some missing values remain in column '{column}': {remaining_missing}")
                else:
                    print(f"All missing values filled in column '{column}'.")
            else:
                print(f"No missing values found in column '{column}'. Skipping...")
        else:
            print(f"Column '{column}' not found in the Excel file. Skipping...")

    # Overwrite the original file with the updated DataFrame
    df.to_excel(file_path, index=False)
    print(f"Original file updated: {file_path}")

if __name__ == "__main__":
    input_file = "Final.xlsx"  # Path to the input Excel file
    columns = ['US2Y', 'US5Y', 'US10Y', 'US30Y', 'FGBSY', 'FGBMY', 'FGBLY', 'FGBXY', 'CAD2Y', 'CAD3Y', 'CAD5Y', 'CAD10Y', 'UK10Y', 'AUS10Y', 'FBTPY', 'FBTSY', 'FOATY','AEX','CAC40','DIJA','FDAX','FSMI','FTSE','NQ','SPX','Gold (USD)']  # List of columns to interpolate
    linear_interpolate_excel(input_file, columns)