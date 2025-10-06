import os
import json
import asyncio
from datetime import datetime
import pandas as pd
from playwright.async_api import async_playwright
import gspread
from google.oauth2.service_account import Credentials

# --- CONFIGURATION ---
# Replace with your actual scanner URLs
SCANNER_URLS = [
    "https://chartink.com/screener/your-first-public-screener-url",
    "https://chartink.com/screener/your-second-public-screener-url"
]

# --- Google Sheets Configuration ---
# These will be loaded from GitHub Secrets when running in the cloud
# For local testing, ensure 'credentials.json' is in the same directory.
SHEET_NAME = os.getenv('SHEET_NAME', 'Monthly Stock Scans') 
GCP_CREDENTIALS_STRING = os.getenv('GCP_CREDENTIALS')

# Define the scope of permissions for Google API
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

async def scrape_chartink_data(url: str):
    """
    Scrapes a given ChartInk scanner URL and returns a list of stock symbols.
    """
    print(f"Scraping URL: {url}")
    symbols = []
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        try:
            await page.goto(url, timeout=60000)
            # This selector targets the rows in the results table.
            # It might need adjustment if ChartInk changes its HTML structure.
            rows = await page.query_selector_all("table#scan_results tbody tr")
            
            for row in rows:
                # Extracts text from the second cell (td) which typically contains the stock symbol.
                symbol_element = await row.query_selector("td:nth-child(2) a")
                if symbol_element:
                    symbol = await symbol_element.inner_text()
                    symbols.append(symbol.strip())
            
            print(f"Found {len(symbols)} symbols from {url}")
        except Exception as e:
            print(f"An error occurred while scraping {url}: {e}")
        finally:
            await browser.close()
    return symbols

def update_google_sheet(all_symbols: list):
    """
    Updates the Google Sheet with the list of scraped stock symbols.
    """
    if not all_symbols:
        print("No symbols found to update in Google Sheet. Exiting.")
        return

    print("Authenticating with Google Sheets...")
    try:
        if GCP_CREDENTIALS_STRING:
            # Running in GitHub Actions: Load credentials from environment variable
            creds_json = json.loads(GCP_CREDENTIALS_STRING)
            creds = Credentials.from_service_account_info(creds_json, scopes=SCOPES)
        else:
            # Running locally: Load credentials from file
            creds = Credentials.from_service_account_file('credentials.json', scopes=SCOPES)
            
        client = gspread.authorize(creds)
        
        spreadsheet = client.open(SHEET_NAME)
        
        # Get current month and year for the worksheet title (e.g., "October-2025")
        worksheet_title = datetime.now().strftime("%B-%Y")
        
        try:
            worksheet = spreadsheet.worksheet(worksheet_title)
            print(f"Found existing worksheet: '{worksheet_title}'")
            worksheet.clear() # Clear old data to replace with new scan
            print("Cleared old data.")
        except gspread.exceptions.WorksheetNotFound:
            worksheet = spreadsheet.add_worksheet(title=worksheet_title, rows="1000", cols="2")
            print(f"Created new worksheet: '{worksheet_title}'")

        # Prepare data for upload
        df = pd.DataFrame(all_symbols, columns=["Stock Symbol"])
        df['Scan Date'] = datetime.now().strftime("%Y-%m-%d")
        
        print(f"Updating sheet with {len(df)} symbols...")
        # Add headers and then the data
        worksheet.update([df.columns.values.tolist()] + df.values.tolist(), value_input_option='USER_ENTERED')
        
        print("Google Sheet updated successfully!")

    except Exception as e:
        print(f"An error occurred while updating Google Sheet: {e}")

async def main():
    """
    Main function to orchestrate the scraping and sheet update process.
    """
    all_symbols = []
    for url in SCANNER_URLS:
        symbols = await scrape_chartink_data(url)
        all_symbols.extend(symbols)
        
    # Remove duplicates by converting to a set and back to a list
    unique_symbols = sorted(list(set(all_symbols)))
    print(f"\nTotal unique symbols found: {len(unique_symbols)}")
    
    update_google_sheet(unique_symbols)

if __name__ == "__main__":
    asyncio.run(main())