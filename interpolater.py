import pandas as pd

def linear_interpolate_excel(file_path, output_file_path, columns_to_interpolate):
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
    # Save the updated DataFrame to a new Excel file
    df.to_excel(output_file_path, index=False)
    print(f"Updated file saved to: {output_file_path}")
            
if __name__ == "__main__":
    input_file = "Merged_Demo.xlsx"  # Path to the input Excel file
    output_file = "Interplated_Data.xlsx"  # Path to save the output Excel file
    columns = ['US2Y', 'US5Y', 'US10Y', 'US30Y', 'FGBSY', 'FGBMY', 'FGBLY', 'FGBXY', 'CAD2Y', 'CAD3Y', 'CAD5Y', 'CAD10Y', 'UK10Y', 'AUS10Y', 'FBTPY', 'FBTSY', 'FOATY']
    linear_interpolate_excel(input_file, output_file, columns)
