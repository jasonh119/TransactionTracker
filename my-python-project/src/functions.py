import pandas as pd
import os
import csv
import config
from transaction_parsers import get_parser_for_file

def process_transactions(file_path):
    """Process transactions from a file using the appropriate parser"""
    
    try:
        parser = get_parser_for_file(file_path)
        return parser.parse_file(file_path)
    except Exception as e:
        print(f"Error processing file {file_path}: {str(e)}")
        return pd.DataFrame()  # Return empty DataFrame on error
