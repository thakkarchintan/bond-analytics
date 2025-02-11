import pandas as pd

def remove_weekend_data(file_path):
    """
    Remove rows corresponding to weekend dates from the Excel file and rewrite the data back to the original file.
    
    Parameters:
        file_path (str): Path to the input Excel file.
    """
    # Load the Excel file
    df = pd.read_excel(file_path)

    # Convert the 'Date' column to datetime
    df['Date'] = pd.to_datetime(df['Date'], format='%d-%b-%Y')

    # Identify weekend dates (Saturday = 5, Sunday = 6)
    df = df[~df['Date'].dt.weekday.isin([5, 6])]

    # Convert the 'Date' column back to the desired format ("dd-mmm-yyyy")
    df['Date'] = df['Date'].dt.strftime('%d-%b-%Y')

    # Save the updated DataFrame back to the original file
    df.to_excel(file_path, index=False)
    print(f"Weekend data removed and file updated: {file_path}")

# Example usage
input_file = "Final.xlsx"  # Path to the input Excel file
remove_weekend_data(input_file)