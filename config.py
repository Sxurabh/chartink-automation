# config.py

# --- Main Configuration ---
SHEET_NAME = "Trading Automation"

# --- NEW: Use a dictionary to map URLs to custom, friendly names ---
SCANNER_MAPPING = {
    "https://chartink.com/screener/5ema-monthly-for-nifty-100": "Monthly stocks for Nifty 100",
    "https://chartink.com/screener/5ema-monthly-69": "Monthly stocks from last 3 years IPO"
}

# --- Scraping Constants ---
EXPECTED_COLUMN_COUNT = 7
TABLE_HEADERS = ['Sr.', 'Stock Name', 'Symbol', 'Links', '% Chg', 'Price', 'Volume']

# --- Robustness Settings ---
RETRY_ATTEMPTS = 3
RETRY_DELAY_SECONDS = 5