import os
from dotenv import load_dotenv
from anthropic import Anthropic

# Load your .env file
load_dotenv()

# Configuration Constants
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
BASE_URL = "https://openrouter.ai/api" # The "Secret Sauce" for the Anthropic SDK
MODEL_NAME = "google/gemini-2.5-flash" # Fast and cheap for development

# Initialize the client once
client = Anthropic(
    base_url=BASE_URL,
    api_key=OPENROUTER_API_KEY
)