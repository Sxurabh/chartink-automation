# config.py

# --- Main Configuration ---
SHEET_NAME = "Trading Automation"

SCANNER_URLS = [
    "https://chartink.com/screener/5ema-monthly-for-nifty-100",
    "https://chartink.com/screener/5ema-monthly-69"
]

# --- Scraping Constants ---
# Number of visible columns we expect to scrape from the ChartInk table.
EXPECTED_COLUMN_COUNT = 7

# Headers that will be used in the Google Sheet.
TABLE_HEADERS = ['Sr.', 'Stock Name', 'Symbol', 'Links', '% Chg', 'Price', 'Volume']

# --- Robustness Settings ---
# Number of times to retry a failed scrape attempt for a single URL.
RETRY_ATTEMPTS = 3
# Seconds to wait between retry attempts.
RETRY_DELAY_SECONDS = 5