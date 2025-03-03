import google.generativeai as genai
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

def initial_gemini_csv_categorisation():
    logger.info("Google Gemini CSV Processor Initialising!")

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
        logger.debug("Session started - sending CSV to Gemini")

        # send csv to Gemini and return a df
        file_path = os.path.join(config.output_dir, 'combined_transactions_gemTest1.csv')
        df = send_csv_to_gemini_and_return_df(chat_session, file_path)
                
        # Save to CSV file
        output_file = os.path.join(config.output_dir, "combined_transactions_categorised.csv")
        df.to_csv(output_file, index=False) 
        logger.info(f"Saved {len(df)} transactions to {output_file}")   

    finally:
        # Cleanup genai resources
        if hasattr(genai, '_client'):
            logger.debug("Closing genai client") 
            genai._client.close()

