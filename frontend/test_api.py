import os
from dotenv import load_dotenv
from google import genai

# Load environment variables
load_dotenv()

# Debugging step
api_key = os.getenv('GEMINI_API_KEY')
print(f"GEMINI_API_KEY: {api_key}")

client = genai.Client(api_key=api_key)