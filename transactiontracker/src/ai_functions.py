import google.generativeai as genai
import os
import pandas as pd
import yaml
import re
import json
import requests
from logger import setup_logger
from config import config
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, TextIteratorStreamer
from threading import Thread

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
        model_name = config.get('api.gemini_model')        
        logger.debug(f"Using model: {model_name}")  
        model = genai.GenerativeModel(model_name)

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

        # Initialize the Gemini model
        model_name = config.get('api.gemini_model')        
        logger.debug(f"Using model: {model_name}")  
        model = genai.GenerativeModel(model_name)
        
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

def chat_with_local_llama32():
    """
    Setting up a chat interface with the local llama32 model.
    Uses a loop to allow continuous conversation until the user exits.
    """
    logger.info("Starting chat with local Llama 3.2 model")
    
    # Define the Ollama API endpoint
    OLLAMA_ENDPOINT = "http://localhost:11434/api/generate"
    
    # Define the model
    MODEL_NAME = "llama3.2"  # Or whichever model you have pulled and want to use
    
    # System prompt to set the assistant's behavior
    SYSTEM_PROMPT = "You are a helpful, respectful and honest assistant. Always answer as helpfully as possible, while being safe. Your answers should not include any harmful, unethical, racist, sexist, toxic, dangerous, or illegal content. Please ensure that your responses are socially unbiased and positive in nature. If a question is not clear or is not factually coherent, explain why instead of answering something not correct. If you don't know the answer to a question, please don't share false information."
    
    logger.info(f"Using model: {MODEL_NAME}")
    print(f"💬 Llama 3.2 Chatbot - Type 'exit' to quit.\n")
    
    try:
        # Initialize conversation history
        conversation_history = []
        
        while True:
            # Get user input
            user_input = input("You: ")
            
            # Check if user wants to exit
            if user_input.lower() in ["exit", "quit", "bye"]:
                logger.info("User exited chat")
                print("Goodbye! 👋")
                break
            
            logger.debug(f"Sending message to Llama: {user_input}")
            
            # Prepare the conversation context
            if not conversation_history:
                # First message, include system prompt
                prompt = f"{SYSTEM_PROMPT}\n\nUser: {user_input}\nAssistant:"
            else:
                # Include conversation history
                prompt = "\n".join(conversation_history) + f"\nUser: {user_input}\nAssistant:"
            
            # Define the data payload for the POST request
            data = {
                "model": MODEL_NAME,
                "prompt": prompt,
                "stream": False,  # Set to False to get the full response at once
                "options": {
                    "temperature": 0.7,
                    "top_p": 0.95,
                    "top_k": 40
                }
            }
            
            try:
                # Send the POST request
                logger.debug("Sending request to Ollama API")
                response = requests.post(OLLAMA_ENDPOINT, json=data)
                
                # Raise an exception if the request was unsuccessful
                response.raise_for_status()
                
                # Parse the JSON response
                response_data = response.json()
                
                # Extract the actual response text
                generated_text = response_data.get("response", "No response found.")
                
                # Print the response
                print(f"Assistant: {generated_text.strip()}")
                
                # Update conversation history
                conversation_history.append(f"User: {user_input}")
                conversation_history.append(f"Assistant: {generated_text.strip()}")
                
                # Keep conversation history at a reasonable size
                if len(conversation_history) > 10:  # Keep last 5 exchanges (10 messages)
                    conversation_history = conversation_history[-10:]
                
                logger.debug(f"Received response: {generated_text[:100]}...")
                
            except requests.exceptions.RequestException as e:
                error_msg = f"Error connecting to Ollama API: {e}"
                logger.error(error_msg)
                print(f"❌ {error_msg}")
                print("Please ensure the Ollama application is running.")
                break
            except json.JSONDecodeError:
                error_msg = f"Error decoding JSON response"
                logger.error(f"{error_msg}: {response.text}")
                print(f"❌ {error_msg}")
                break
            except Exception as e:
                error_msg = f"An unexpected error occurred: {e}"
                logger.error(error_msg, exc_info=True)
                print(f"❌ {error_msg}")
                break
                
    except KeyboardInterrupt:
        logger.info("Chat interrupted by user (KeyboardInterrupt)")
        print("\nChat interrupted. Goodbye! 👋")
    except Exception as e:
        logger.error(f"Unexpected error in chat loop: {e}", exc_info=True)
        print(f"❌ An error occurred: {e}")
    finally:
        logger.info("Chat with Llama 3.2 ended")


#Old Windows CUDA Model chat - attempt - never fully working - CUDA worked, but not call llama kept trying to find tensorflow and i couldn't get the verson compatible
"""def chat_with_llama32():
    
    Initialize and chat with the Llama 3.2-1B model using GPU acceleration.
    This function loads the model from the local checkpoint and starts an interactive chat session.
    Uses Hugging Face Transformers library for compatibility with Windows.
    
    logger.info("Llama 3.2-1B Chat Initializing")
    
    # Define the model path
    model_path = os.path.join(os.path.expanduser("~"), ".llama", "checkpoints", "Llama3.2-1B")
    
    if not os.path.exists(model_path):
        logger.error(f"Llama 3.2-1B model not found at: {model_path}")
        print(f"❌ Model not found at: {model_path}")
        return
    
    logger.info(f"Loading Llama 3.2-1B model from: {model_path}")
    print("🦙 Loading Llama 3.2-1B model... This may take a moment.")
    
    try:
        # Check if GPU is available
        device = "cuda" if torch.cuda.is_available() else "cpu"
        
        if device == "cuda":
            logger.info(f"GPU detected: {torch.cuda.get_device_name(0)}")
            print(f"🚀 Using GPU: {torch.cuda.get_device_name(0)}")
        else:
            logger.warning("No GPU detected, falling back to CPU (this will be slow)")
            print("⚠️ No GPU detected, falling back to CPU (this will be slow)")
        
        # Load the tokenizer
        tokenizer = AutoTokenizer.from_pretrained(model_path)
        
        # Load the model with GPU acceleration if available
        model = AutoModelForCausalLM.from_pretrained(
            model_path,
            torch_dtype=torch.float16 if device == "cuda" else torch.float32,
            low_cpu_mem_usage=True,
            device_map="auto"  # Automatically use GPU if available
        )
        
        logger.info("Llama 3.2-1B model loaded successfully")
        print("\n🦙 Llama 3.2-1B Chatbot - Type 'exit' to quit.\n")
        
        # Chat history for context
        chat_history = []
        
        # Chat loop
        while True:
            user_input = input("You: ")
            if user_input.lower() == "exit":
                print("Goodbye! 👋")
                break
            
            # Format the prompt with chat history
            if chat_history:
                prompt = "".join(chat_history)
                prompt += f"\nUser: {user_input}\nLlama: "
            else:
                prompt = f"User: {user_input}\nLlama: "
            
            logger.debug(f"Sending prompt: {prompt}")
            
            # Tokenize the input
            inputs = tokenizer(prompt, return_tensors="pt").to(device)
            
            # Set up streamer for real-time output
            streamer = TextIteratorStreamer(tokenizer, skip_prompt=True, skip_special_tokens=True)
            
            # Generate in a separate thread to allow streaming
            generation_kwargs = {
                "input_ids": inputs["input_ids"],
                "attention_mask": inputs["attention_mask"],
                "max_new_tokens": 1024,
                "temperature": 0.7,
                "top_p": 0.95,
                "streamer": streamer,
                "do_sample": True,
            }
            
            thread = Thread(target=model.generate, kwargs=generation_kwargs)
            thread.start()
            
            # Print the response as it's generated
            print("Llama: ", end="", flush=True)
            generated_text = ""
            for text_chunk in streamer:
                print(text_chunk, end="", flush=True)
                generated_text += text_chunk
                
                # Check for end of response
                if "\nUser:" in generated_text:
                    generated_text = generated_text.split("\nUser:")[0]
                    break
            
            print()  # New line after response
            
            logger.debug(f"Received response: {generated_text}")
            
            # Update chat history (keep it manageable to avoid context overflow)
            chat_history.append(f"User: {user_input}\nLlama: {generated_text}\n")
            
            # Limit history to last 10 exchanges to prevent context window overflow
            if len(chat_history) > 10:
                chat_history = chat_history[-10:]
                
    except Exception as e:
        logger.error(f"Error in Llama chat: {str(e)}")
        print(f"❌ Error: {str(e)}")
        
    finally:
        logger.info("Llama chat session ended")
        # Clean up resources if needed
        if 'model' in locals() and device == "cuda":
            del model
            torch.cuda.empty_cache()
            logger.debug("GPU cache cleared")
"""
