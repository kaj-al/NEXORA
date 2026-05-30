
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()
    
openrouter_key_input = os.getenv("GROQ_API_KEY")
model_size = "base"
llm_model = "llama-3.1-8b-instant"

