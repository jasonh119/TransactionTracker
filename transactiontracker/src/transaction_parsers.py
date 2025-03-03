from abc import ABC, abstractmethod
import pandas as pd
import csv
from logger import setup_logger

class TransactionParser(ABC):
    def __init__(self):
        self.logger = setup_logger(self.__class__.__name__)

    @abstractmethod
    def parse_file(self, file_path):
        """Parse the transaction file and return a standardized DataFrame"""
        self.logger.error("parse_file method not implemented")
        raise NotImplementedError("Subclasses must implement parse_file method")

    def clean_dataframe(self, df):
        """Common cleanup operations for all parsers"""
        self.logger.debug("Cleaning DataFrame")
        # Clean whitespace
        df = df.rename(columns=lambda x: x.strip())
        df = df.apply(lambda x: x.str.strip() if x.dtype == "object" else x)
        
        # Clean up numeric columns
        for col in ['Deposit', 'Withdrawal']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col].replace('', '0'), errors='coerce')
                df[col] = df[col].fillna('')
        
        # Ensure standard column order
        standard_columns = ['Financial Institution', 'Account Name', 'Account Number', 
                          'Date', 'Transaction', 'Currency', 'Deposit', 'Withdrawal', 
                          'Running Balance']
        
        # Add missing columns with empty values
        for col in standard_columns:
            if col not in df.columns:
                df[col] = ''
                
        return df[standard_columns]

class StandardCharteredAccountParser(TransactionParser):
    def parse_file(self, file_path):
        """Parser for Standard Chartered bank format"""
        self.logger.info(f"Processing Standard Chartered file: {file_path}")
        
        # Read account info from header
        with open(file_path, "r") as file:
            lines = file.readlines()
        
        account_number = lines[3].split(",")[1].strip()
        account_number = account_number[1:]  # Remove the first character
        account_name = lines[3].split(",")[0].strip()
        
        # Read transaction data
        df = pd.read_csv(file_path, 
                        skiprows=5,
                        on_bad_lines='warn',
                        skipinitialspace=True,
                        quoting=csv.QUOTE_ALL,
                        thousands=',',
                        encoding='utf-8')
        
        # Clean up dataframe first
        df = df.rename(columns=lambda x: x.strip())  # Remove whitespace from column names
        df = df.apply(lambda x: x.str.strip() if x.dtype == "object" else x)  # Remove whitespace from values
        
        # Add account info
        df['Account Name'] = account_name
        df['Account Number'] = account_number
        df['Financial Institution'] = 'Standard Chartered'
        
        # Convert date column after cleaning
        df['Date'] = pd.to_datetime(df['Date'], format='%d/%m/%Y')
        
        # Clean up balance columns
        if 'Running Balance' in df.columns:
            df['Running Balance'] = (df['Running Balance']
                                   .str.replace(' CR', '')
                                   .str.replace(' DR', '')
                                   .str.replace(',', '')
                                   .astype(float))
        
        return self.clean_dataframe(df)

class StandardCharteredCreditCardParser(TransactionParser):
    def parse_file(self, file_path):
        """Parser for Standard Chartered Credit Card format"""
        self.logger.info(f"Processing Standard Chartered Credit Card file: {file_path}")
        
        try:
            # Read account info from header
            with open(file_path, "r") as file:
                lines = [line.strip() for line in file.readlines() if line.strip()]  # Remove empty lines
                
            # Get account number from first line
            account_number = lines[0].split(",")[1].strip().strip("'")
            account_name = lines[0].split(",")[0].strip()
            self.logger.info(f"Account Details: {account_name}, {account_number}")
            
            # Find where transactions end (Current Balance line)
            transaction_lines = []
            for line in lines[3:]:  # Skip header lines
                if line.startswith('Current Balance'):
                    break
                if ',' in line:  # Only include lines with data
                    transaction_lines.append(line)
            
            self.logger.debug(f"Found {len(transaction_lines)} transaction lines")
            
            # Write transactions to a temporary file without empty lines
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as temp_file:
                # Write header
                temp_file.write("Date,DESCRIPTION,Foreign Currency Amount,SGD Amount\n")
                # Write transactions
                for line in transaction_lines:
                    temp_file.write(line + "\n")
                temp_path = temp_file.name
                
            # Read the clean CSV file
            df = pd.read_csv(temp_path,
                            skipinitialspace=True,
                            quoting=csv.QUOTE_ALL,
                            thousands=',',
                            encoding='utf-8')
            
            # Clean up temporary file
            import os
            os.unlink(temp_path)
            
            # Clean up dataframe
            df = df.rename(columns=lambda x: x.strip())
            df = df.apply(lambda x: x.str.strip() if x.dtype == "object" else x)
            
            # Extract foreign currency info
            foreign_currency_mask = df['Foreign Currency Amount'].notna() & (df['Foreign Currency Amount'] != '')
            df['Foreign Currency'] = None
            df['Foreign Amount'] = None
            
            if foreign_currency_mask.any():
                df.loc[foreign_currency_mask, 'Foreign Currency'] = df.loc[foreign_currency_mask, 'Foreign Currency Amount'].str.extract(r'([A-Z]{3})')[0]
                df.loc[foreign_currency_mask, 'Foreign Amount'] = df.loc[foreign_currency_mask, 'Foreign Currency Amount'].str.extract(r'([0-9,.]+)')[0].apply(
                    lambda x: float(str(x).replace(',', '')) if pd.notnull(x) else None
                )
            
            # Extract amount and type (DR/CR) from SGD Amount
            df['Amount'] = df['SGD Amount'].str.extract(r'SGD\s*([\d,.]+)\s*(DR|CR)?')[0]
            df['Type'] = df['SGD Amount'].str.extract(r'SGD\s*([\d,.]+)\s*(DR|CR)?')[1]
            
            # Convert amount to float and apply DR/CR
            df['Amount'] = pd.to_numeric(df['Amount'].str.replace(',', ''), errors='coerce')
            df.loc[df['Type'] == 'DR', 'Amount'] = -df.loc[df['Type'] == 'DR', 'Amount']
            
            # Map to standard columns
            df['Deposit'] = df.loc[df['Amount'] > 0, 'Amount']
            df['Withdrawal'] = -df.loc[df['Amount'] < 0, 'Amount']
            df['Transaction'] = df['DESCRIPTION']
            
            # Add account info
            df['Account Name'] = account_name
            df['Account Number'] = account_number
            df['Financial Institution'] = 'Standard Chartered'
            df['Currency'] = 'SGD'
            
            # Convert date
            df['Date'] = pd.to_datetime(df['Date'], format='%d/%m/%Y')
            
            # Drop temporary columns but keep foreign currency info
            df = df.drop(['DESCRIPTION', 'Foreign Currency Amount', 'SGD Amount', 'Amount', 'Type'], axis=1)
            
            # Ensure standard columns are first, followed by the foreign currency columns
            standard_df = self.clean_dataframe(df.drop(['Foreign Currency', 'Foreign Amount'], axis=1))
            
            # Add foreign currency columns back
            standard_df['Foreign Currency'] = df['Foreign Currency']
            standard_df['Foreign Amount'] = df['Foreign Amount']
            
            return standard_df
            
        except Exception as e:
            self.logger.error(f"Error parsing Standard Chartered Credit Card file: {str(e)}", exc_info=True)
            raise

def get_parser_for_file(file_path):
    """Factory function to return appropriate parser based on file characteristics"""
    file_path = file_path.lower()
    
    if not file_path.endswith('.csv'):
        raise ValueError(f"Unsupported file format: {file_path}")
        
    if "standardchartered" in file_path or "scb" in file_path or "bonussaver" in file_path or "daily" in file_path or "esaver" in file_path:
        return StandardCharteredAccountParser()
    elif "journey" in file_path:
        return StandardCharteredCreditCardParser()
    
    # Default to Standard Chartered Account parser
    return StandardCharteredAccountParser()
