import pandas as pd
from transaction_parsers import get_parser_for_file
from logger import setup_logger

logger = setup_logger(__name__)

def process_transactions(file_path):
    """Process transactions from a file using the appropriate parser"""
    
    try:
        logger.info(f"Getting parser for file: {file_path}")
        parser = get_parser_for_file(file_path)
        logger.debug(f"Using parser: {parser.__class__.__name__}")
        
        transactions_df = parser.parse_file(file_path)
        logger.info(f"Successfully parsed {len(transactions_df)} transactions")
        return transactions_df
        
    except Exception as e:
        logger.error(f"Error processing file {file_path}: {str(e)}", exc_info=True)
        return pd.DataFrame()  # Return empty DataFrame on error
