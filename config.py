
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()
    
openrouter_key_input = os.getenv("OPENROUTER_API_KEY")
model_size = "base"
llm_model = "gpt-4o-mini"

