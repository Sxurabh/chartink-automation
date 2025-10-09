# config.py
import os
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv(), verbose=True)

# --- Main Configuration ---
SHEET_NAME = "Trading Automation"

# --- Scanner Configuration ---
SCANNER_MAPPING = {
    "https://chartink.com/screener/5ema-monthly-for-nifty-100": {
        "name": "Monthly stocks for Nifty 100",
        "is_ipo": False,
    },
    "https://chartink.com/screener/5ema-monthly-69": {
        "name": "Monthly stocks from last 3 years IPO",
        "is_ipo": True,
    }
}

# --- Scraping & Analysis Constants ---
EXPECTED_COLUMN_COUNT = 7
TABLE_HEADERS = ['Sr.', 'Stock Name', 'Symbol', 'Links', '% Chg', 'Price', 'Volume']
RETRY_ATTEMPTS = 3
RETRY_DELAY_SECONDS = 5