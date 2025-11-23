"""
Script to list available Gemini models for the configured API key
"""
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
import google.generativeai as genai

# Load environment variables
load_dotenv()

# Get API key
api_key = os.getenv('AI_API_KEY')
if not api_key:
    print("ERROR: AI_API_KEY not found in environment variables")
    sys.exit(1)

# Configure Gemini
genai.configure(api_key=api_key)

print("Available Gemini models:\n")
print("-" * 80)

# List all available models
for model in genai.list_models():
    if 'generateContent' in model.supported_generation_methods:
        print(f"Model: {model.name}")
        print(f"  Display Name: {model.display_name}")
        print(f"  Description: {model.description}")
        print(f"  Supported methods: {', '.join(model.supported_generation_methods)}")
        print("-" * 80)
