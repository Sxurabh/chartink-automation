# config.py
import os

# --- Main Configuration ---
SHEET_NAME = "Trading Automation"

# --- NEW: AI Configuration ---
# Your OpenRouter API key should be set as an environment variable
# for local testing, you can create a .env file with: OPENROUTER_API_KEY="your_key_here"
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
# Recommended free model from OpenRouter, e.g., "mistralai/mistral-7b-instruct:free"
AI_MODEL_NAME = "openai/gpt-oss-20b:free"


# --- Scanner Configuration ---
SCANNER_MAPPING = {
    "https://chartink.com/screener/5ema-monthly-for-nifty-100": {
        "name": "Monthly stocks for Nifty 100",
        "is_ipo": False
    },
    "https://chartink.com/screener/5ema-monthly-69": {
        "name": "Monthly stocks from last 3 years IPO",
        "is_ipo": True
    }
}

# --- Scraping & Analysis Constants ---
EXPECTED_COLUMN_COUNT = 7
TABLE_HEADERS = ['Sr.', 'Stock Name', 'Symbol', 'Links', '% Chg', 'Price', 'Volume']
RETRY_ATTEMPTS = 3
RETRY_DELAY_SECONDS = 5