from config import config  # Import the config instance instead of the module
import functions 
import ai_functions
import os
import pandas as pd 
from logger import setup_logger

logger = setup_logger(__name__)

def process_transactions():
    """Main function to process all transaction files"""
    logger.info("Starting transaction processing")
    
    all_transactions = pd.DataFrame()
    
    # Process each file in the input directory
    for filename in os.listdir(config.input_dir):
        file_path = os.path.join(config.input_dir, filename)
        if os.path.isfile(file_path):
            logger.info(f"Processing file: {filename}")
            try:
                transactions_df = functions.process_transactions(file_path)
                if not transactions_df.empty:
                    all_transactions = pd.concat([all_transactions, transactions_df], ignore_index=True)
                    logger.info(f"Successfully processed {len(transactions_df)} transactions from {filename}")
                else:
                    logger.warning(f"No transactions found in {filename}")
            except Exception as e:
                logger.error(f"Error processing {filename}: {str(e)}", exc_info=True)
    
    if not all_transactions.empty:
        # Save to CSV file
        output_file = os.path.join(config.output_dir, "combined_transactions.csv")
        all_transactions.to_csv(output_file, index=False)
        logger.info(f"Saved {len(all_transactions)} transactions to {output_file}")
        
        # Save to Excel file
        output_file_excel = os.path.join(config.output_dir, "combined_transactions.xlsx")
        all_transactions.to_excel(output_file_excel, index=False)
        logger.info(f"Saved {len(all_transactions)} transactions to {output_file_excel}")

        # Print out some stats
        logger.info(f"Transaction DataFrame stats: \n{all_transactions.info()}")
    else:
        logger.warning("No transactions were processed successfully")

if __name__ == "__main__":
    logger.info("Transaction Tracker application starting")
    process_transactions()
    logger.info("Transactions processed. Chat with the AI assistant")
    
    # TODO - add flag to yml file to enable/disable Gemini chat for other contributors  
    ai_functions.initial_gemini_chat()

    logger.info("Transaction Tracker application completed")
