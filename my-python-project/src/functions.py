import pandas as pd
import os
import csv
import config

def process_transactions(file_path):

    # Read CSV file, skip header rows
    print("Processing file: ", file_path)

    # df = pd.read_csv(file_path, skiprows=5)
    # Read CSV with specific parameters to handle messy data
    df = pd.read_csv(file_path, 
                     skiprows=5,
                     on_bad_lines='warn',      # Warns and skips bad lines
                     skipinitialspace=True,    # Skip extra whitespace
                     quoting=csv.QUOTE_ALL,    # Quote all fields
                     thousands=',',            # Handle thousands separator
                     encoding='utf-8')         # Specify encoding

    with open(file_path, "r") as file:
        lines = file.readlines()

    account_number = lines[3].split(",")[1].strip()
    account_number = account_number[1:]  # Remove the first character
    account_name = lines[3].split(",")[0].strip()

    # Clean up dataframe
    df = df.rename(columns=lambda x: x.strip())  # Remove whitespace from column names
    df = df.apply(lambda x: x.str.strip() if x.dtype == "object" else x)  # Remove whitespace from values
    
    # Add account details to each row
    df['Account Name'] = account_name
    df['Account Number'] = account_number
    df['Financial Institution'] = 'Standard Chartered' # TODO Move to function parameter when we have multiple banks
    
    # Convert date column
    df['Date'] = pd.to_datetime(df['Date'], format='%d/%m/%Y')
    
    # Clean up balance columns by removing 'CR' and 'DR'
    df['Running Balance'] = df['Running Balance'].str.replace(' CR', '').str.replace(' DR', '').str.replace(',', '').astype(float)

    # Clean up numeric columns
    for col in ['Deposit', 'Withdrawal']:
        df[col] = pd.to_numeric(df[col].replace('', '0'), errors='coerce')
        # Remove NaN values 
        df[col] = df[col].fillna('')
  
    # Reorder columns
    column_order = ['Financial Institution','Account Name', 'Account Number', 'Date', 'Transaction', 'Currency', 
                   'Deposit', 'Withdrawal', 'Running Balance']
    df = df[column_order]

    print("Finished processing file: ", file_path)
    return df

