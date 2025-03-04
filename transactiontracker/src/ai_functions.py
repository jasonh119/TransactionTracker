import google.generativeai as genai
import os
import pandas as pd
import yaml
import re
import json
from logger import setup_logger
from config import config

logger = setup_logger(__name__)

def initial_gemini_chat():
    logger.info("Google Gemini Chat Initialising")

    # Get API key from environment variables
    API_KEY = config.get_secret('GEMINI_API_KEY')
    if not API_KEY:
        logger.error("GEMINI_API_KEY not found in environment variables")
        return
        
    logger.info("API key loaded successfully")

    try:
        # Configure the API and Gemini
        genai.configure(api_key=API_KEY)

        # Initialize the Gemini model
        model = genai.GenerativeModel("gemini-2.0-flash")
        chat_session = model.start_chat(history=[])
        logger.debug("Chat session started successfully")
        print("💬 Gemini Chatbot - Type 'exit' to quit.\n")

        while True:
            user_input = input("You: ")
            if user_input.lower() == "exit":
                print("Goodbye! 👋")
                break
        
            logger.debug(f"Sending message: {user_input}")
            response = chat_session.send_message(content=user_input)
            print("Gemini:", response.text)
            logger.debug(f"Received message: {response.text}")   
    finally:
        # Cleanup genai resources
        if hasattr(genai, '_client'):
            logger.debug("Closing genai client") 
            genai._client.close()

        logger.info("Chat session ended successfully")      

def initial_gemini_csv_categorisation(input_file=None):
    """
    Process a CSV file of transactions using Gemini to categorize expenses.
    
    Args:
        input_file (str, optional): Path to the CSV file to process. If None, uses the combined_transactions.csv in output_dir.
    
    Returns:
        pd.DataFrame: Categorized transactions dataframe with 'Category' and 'Sub-Category' columns.
    """
    logger.info("Google Gemini CSV Categorization Initializing")

    # Get API key from environment variables
    API_KEY = config.get_secret('GEMINI_API_KEY')
    if not API_KEY:
        logger.error("GEMINI_API_KEY not found in environment variables")
        return None
        
    logger.info("API key loaded successfully")

    # TODO - Move this csv to config.yaml   
    # Determine input file path
    if input_file is None:
        input_file = os.path.join(config.output_dir, 'combined_transactions_gemTest1.csv')
    
    if not os.path.exists(input_file):
        logger.error(f"Input file not found: {input_file}")
        return None
    
    # Read the CSV file
    try:
        df = pd.read_csv(input_file)
        logger.info(f"Successfully read {len(df)} transactions from {input_file}")
        
        # Limit the number of rows to prevent response truncation
        max_rows = 50  # Adjust this number based on your needs
        if len(df) > max_rows:
            logger.warning(f"Limiting to {max_rows} transactions to prevent response truncation")
            df = df.head(max_rows)
    except Exception as e:
        logger.error(f"Error reading CSV file: {str(e)}")
        return None
    
    # Get the expense categories from config
    expense_categories = config.get('expense_categories', {})
    paynow_vendors = config.get('paynow_vendors', [])
    external_individuals = config.get('external_individuals', [])
    
    # Convert config to YAML string for the prompt
    categories_yaml = yaml.dump({
        'expense_categories': expense_categories,
        'paynow_vendors': paynow_vendors,
        'external_individuals': external_individuals
    }, default_flow_style=False)
    
    try:
        # Configure the API and Gemini
        genai.configure(api_key=API_KEY)

        # Initialize the Gemini model - using Pro for structured data tasks
        model = genai.GenerativeModel("gemini-2.0-pro-exp-02-05")
        
        # Prepare the prompt with clear instructions about JSON format
        prompt = f"""
        You are a financial transaction categorizer. I will provide you with a CSV of financial transactions and a YAML configuration of expense categories.
        
        Here is the YAML configuration for expense categories:
        ```yaml
        {categories_yaml}
        ```
        
        Your task is to:
        1. Analyze each transaction in the CSV
        2. Assign a 'Category' and 'Sub-Category' to each transaction based on the YAML configuration
        3. Pay special attention to PayNow transactions (containing "PAYNOW" in the description) and match them to vendors in the paynow_vendors list
        4. Identify transactions to individuals that should be categorized as transfers based on the external_individuals list
        
        Here is the CSV data:
        ```
        {df.to_csv(index=False)}
        ```
        
        IMPORTANT: Respond ONLY with a valid, complete JSON array. Each object in the array must have all the original columns plus 'Category' and 'Sub-Category'. 
        Do not include any explanations, markdown formatting, or code blocks in your response. Just return the raw JSON array.
        """
        
        logger.debug("Sending transaction data to Gemini for categorization")
        logger.debug(f"Prompt: {prompt}")
        
        # Set generation parameters to maximize completion
        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.1,  # Lower temperature for more deterministic output
                top_p=0.95,
                top_k=40,
                max_output_tokens=8192,  # Request maximum tokens
                response_mime_type="application/json"  # Request JSON response
            )
        )
        
        logger.debug(f"Response: {response.text}")

        # Process the response
        try:
            # Clean up the response text
            response_text = response.text.strip()
            
            # Remove any markdown code block indicators if present
            response_text = re.sub(r'```json\s*', '', response_text)
            response_text = re.sub(r'```\s*$', '', response_text)
            
            # Try to parse the JSON
            try:
                transactions_data = json.loads(response_text)
                logger.info("Successfully parsed JSON response")
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON from full response: {str(e)}")
                
                # Try to extract valid JSON from the response
                json_match = re.search(r'\[\s*\{.*\}\s*\]', response_text, re.DOTALL)
                if json_match:
                    try:
                        transactions_data = json.loads(json_match.group(0))
                        logger.info("Successfully extracted and parsed JSON from response")
                    except json.JSONDecodeError:
                        logger.error("Failed to parse extracted JSON")
                        return None
                else:
                    logger.error("Could not find valid JSON array in response")
                    return None
            
            # Convert JSON to DataFrame
            categorized_df = pd.DataFrame(transactions_data)
            logger.info(f"Successfully categorized {len(categorized_df)} transactions")
            
            # Save to CSV file
            output_file = os.path.join(config.output_dir, "categorized_transactions.csv")
            categorized_df.to_csv(output_file, index=False)
            logger.info(f"Saved categorized transactions to {output_file}")
            
            # Also save to Excel for better viewing
            output_excel = os.path.join(config.output_dir, "categorized_transactions.xlsx")
            categorized_df.to_excel(output_excel, index=False)
            logger.info(f"Saved categorized transactions to {output_excel}")
            
            return categorized_df
            
        except Exception as e:
            logger.error(f"Error processing Gemini response: {str(e)}", exc_info=True)
            return None
            
    except Exception as e:
        logger.error(f"Error during Gemini categorization: {str(e)}", exc_info=True)
        return None
        
    finally:
        # Cleanup genai resources
        if hasattr(genai, '_client'):
            logger.debug("Closing genai client") 
            genai._client.close()
            
        logger.info("Gemini CSV categorization completed")

def send_csv_to_gemini_and_return_df(chat_session, file_path):
    """Helper function to send CSV to Gemini and process the response"""
    # This function is no longer used but kept for reference
    logger.warning("send_csv_to_gemini_and_return_df is deprecated, use initial_gemini_csv_categorisation instead")
    return None
