import os
from dotenv import load_dotenv
from anthropic import Anthropic

# Load your .env file
load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
# FIXED: Added /v1 to avoid the 404 error
BASE_URL = "https://openrouter.ai/api" # The "Secret Sauce" for the Anthropic SDK
model = "google/gemini-2.5-flash" # Fast and cheap for development


client = Anthropic(
    base_url=BASE_URL,
    api_key=OPENROUTER_API_KEY,
    default_headers={
        "HTTP-Referer": "http://localhost:3000",
        "X-Title": "Medical Research Script",
    }
)

def add_user_message(messages, message):
    messages.append({"role": "user", "content": message})

def chat(messages, system=None, temperature=1.0, tools=None):
    params = {
        "model": model,
        "max_tokens": 1024,
        "messages": messages,
        "temperature": temperature,
    }
    if tools:
        params["tools"] = tools
    if system:
        params["system"] = system

    return client.messages.create(**params)

tools = [
    {
        "name": "web_search",
        "description": "Searches for health, medical, and fitness information.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "The search query"}
            },
            "required": ["query"]
        }
    }
]

SYSTEM_INSTRUCTION = (
    "You are a medical research assistant. When using the web_search tool, "
    "always append 'site:nih.gov' to the query. Present findings objectively."
)

messages = []
add_user_message(messages, "What are the most effective exercises for building leg muscle?")

try:
    response = chat(messages, system=SYSTEM_INSTRUCTION, tools=tools)
    
    print("Assistant Response:")
    # FIXED: Loop through content to handle both Text and Tool use
    for content_block in response.content:
        if content_block.type == "text":
            print(content_block.text)
        elif content_block.type == "tool_use":
            print(f"\n[Model wants to use tool: {content_block.name}]")
            print(f"[Query: {content_block.input['query']}]")
            # In a full app, you would execute the search here and feed it back to the model.

except Exception as e:
    print(f"Error encountered: {e}")