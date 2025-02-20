#from huggingface_hub import InferenceClient
import google.generativeai as genai
from logger import setup_logger
from config import config

logger = setup_logger(__name__)

""" def initial_hf_chat(): #not use
    
    client = InferenceClient(token=...)

    # Call a model (GPT-2)
    response = client.text_generation(
                            prompt="Tell me an interesting fact about space.",
                            model="gpt2",
                            max_new_tokens=1000)   

    print(response) """

def initial_gemini_chat():
    logger.info(f"Google Gemini SDK installed successfully!")

    # Get API key from environment variables
    API_KEY = config.get_secret('GEMINI_API_KEY')
    if not API_KEY:
        logger.error("GEMINI_API_KEY not found in environment variables")
        return
        
    logger.debug("API key loaded successfully")

    try:
        # Configure the API
        genai.configure(api_key=API_KEY)

        # Initialize the Gemini model
        model = genai.GenerativeModel("gemini-pro")
        chat_session = model.start_chat(history=[])

        print("💬 Gemini Chatbot - Type 'exit' to quit.\n")

        # Test a basic chat prompt
        #response = model.generate_content("Explain quantum computing in simple terms.")
        #print(response.text)

        while True:
            user_input = input("You: ")
            if user_input.lower() == "exit":
                print("Goodbye! 👋")
                break
        
            response = chat_session.send_message(user_input)
            print("Gemini:", response.text)
    finally:
        # Cleanup genai resources
        if hasattr(genai, '_client'):
            genai._client.close()
