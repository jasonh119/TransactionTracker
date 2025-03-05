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
    
    return all_transactions

def categorize_transactions(transactions_df=None):
    """Use Gemini to categorize transactions"""
    logger.info("Starting transaction categorization with Gemini")
    
    if transactions_df is None:
        # If no DataFrame is provided, use a separate input file
        logger.info("No DataFrame provided, using test data csv")
        print("📊 Using test data for categorization...")
        categorized_df = ai_functions.initial_gemini_csv_categorisation()
    else:
        # If a DataFrame is provided, save it to a temporary file and process it
        logger.info(f"Processing provided DataFrame with {len(transactions_df)} transactions")
        print(f"📊 Processing {len(transactions_df)} transactions...")
        
        # Limit the number of transactions if needed
        max_rows = 50
        if len(transactions_df) > max_rows:
            print(f"⚠️ Limiting to {max_rows} transactions to prevent response truncation")
            transactions_df = transactions_df.head(max_rows)
        
        temp_file = os.path.join(config.output_dir, "temp_transactions.csv")
        transactions_df.to_csv(temp_file, index=False)
        categorized_df = ai_functions.initial_gemini_csv_categorisation(temp_file)
        
        # Clean up temporary file
        try:
            os.remove(temp_file)
        except Exception as e:
            logger.warning(f"Failed to remove temporary file: {str(e)}")
    
    return categorized_df

if __name__ == "__main__":
    logger.info("Transaction Tracker application starting")
    print("🚀 Transaction Tracker application starting...")
    
    # Process transactions
    print("📂 Processing transaction files...")
    transactions_df = process_transactions()
    
    # Ask user if they want to categorize transactions
    if not transactions_df.empty:
        user_input = input("\n🤖 Do you want to categorize transactions using Gemini AI? (y/n): ")
        if user_input.lower() == 'y':
            print("🔍 Starting transaction categorization with Gemini AI...")
            print("⏳ This may take a moment...")
            
            try:
                categorized_df = categorize_transactions(transactions_df)
                if categorized_df is not None:
                    logger.info(f"Successfully categorized {len(categorized_df)} transactions")
                    print(f"\n✅ Successfully categorized {len(categorized_df)} transactions!")
                    
                    # Display sample of categorized transactions
                    print("\n📋 Sample of categorized transactions:")
                    if 'Category' in categorized_df.columns and 'Sub-Category' in categorized_df.columns:
                        sample_cols = ['Transaction', 'Category', 'Sub-Category']
                        sample_cols = [col for col in sample_cols if col in categorized_df.columns]
                        print(categorized_df[sample_cols].head().to_string(index=False))
                    
                    output_file = os.path.join(config.output_dir, "categorized_transactions.csv")
                    print(f"\n💾 Saved categorized transactions to: {output_file}")
                else:
                    logger.warning("Transaction categorization failed")
                    print("❌ Transaction categorization failed. Check the logs for details.")
            except Exception as e:
                logger.error(f"Error during categorization: {str(e)}", exc_info=True)
                print(f"❌ Error during categorization: {str(e)}")
    
    # Ask user if they want to chat with Gemini
    user_input = input("\n💬 Do you want to chat with the Gemini AI assistant? (y/n): ")
    if user_input.lower() == 'y':
        logger.info("Starting Gemini chat")
        ai_functions.initial_gemini_chat()
    
    logger.info("Transaction Tracker application completed")
    print("\n🎉 Transaction Tracker application completed. Thank you for using the service!")
