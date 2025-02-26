import google.generativeai as genai
from logger import setup_logger
from config import config

logger = setup_logger(__name__)

def initial_gemini_chat():
    logger.info("Google Gemini SDK installed successfully!")

    # Get API key from environment variables
    API_KEY = config.get_secret('GEMINI_API_KEY')
    if not API_KEY:
        logger.error("GEMINI_API_KEY not found in environment variables")
        return
        
    logger.info("API key loaded successfully")

    try:
        # Configure the API
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
