#import logging
import config
import functions 
import ai_functions
import os
import pandas as pd 

# main function reads the transtionas data from many csv files, and builds a dataframe useing process_transactions function
def process_transactions():
    # Process transactions
    input_path = config.INPUT_DIR + "\\" # Path to input files

    # loop through files in input path and call process_transactions
    for file in os.listdir(input_path):
        if file.endswith(".csv"):
            # Process each file and append the transactions to the existing transactions_df
            if 'transactions_df' not in locals():
                transactions_df = functions.process_transactions(input_path + file)
            else:
                #transactions_df = transactions_df.append(process_transactions(input_path + file), ignore_index=True)
                transactions_df = pd.concat([transactions_df, functions.process_transactions(input_path + file)], ignore_index=True)
        
    print(transactions_df.head())
    print(transactions_df.tail())
    print(transactions_df.shape)  # (rows, columns)
    print(transactions_df.info())  # Column data types, non-null counts  

    # Save to CSV
    output_path = os.path.join(config.OUTPUT_DIR, "transactions_cleaned.csv")
    transactions_df.to_csv(output_path, index=False)

    # Save to Excel
    output_path = os.path.join(config.OUTPUT_DIR, "transactions_cleaned.xlsx")
    transactions_df.to_excel(output_path, index=False)

if __name__ == "__main__":
    
    # Set up logging
    #logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # Call the main function
    process_transactions()

    # Call the AI function
    # ai_functions.initial_chat()
