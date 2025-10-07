# sheets.py

import traceback
from datetime import datetime
from typing import List, Dict, Any
import gspread
from google.oauth2.service_account import Credentials
import config

# --- Constants ---
CREDENTIALS_FILE = 'credentials.json'
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

def update_google_sheet(all_results: List[Dict[str, Any]]):
    """
    Updates the Google Sheet with separated data from each scanner.
    """
    if not any(result['data'] for result in all_results):
        print("No data was scraped from any scanner. Exiting sheets update.")
        return

    print("\n🔒 Authenticating with Google Sheets...")
    try:
        creds = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=SCOPES)
        client = gspread.authorize(creds)
        spreadsheet = client.open(config.SHEET_NAME)
        worksheet_title = datetime.now().strftime("%B-%Y")

        try:
            worksheet = spreadsheet.worksheet(worksheet_title)
            worksheet.clear()
            print(f"🧹 Cleared existing worksheet: '{worksheet_title}'")
        except gspread.exceptions.WorksheetNotFound:
            worksheet = spreadsheet.add_worksheet(title=worksheet_title, rows="1000", cols="20")
            print(f"✨ Created new worksheet: '{worksheet_title}'")

        upload_data = []
        is_first_scanner = True
        for result in all_results:
            if not result['data']:
                continue

            if not is_first_scanner:
                upload_data.append([])  # Add a blank row as a separator

            upload_data.append([f"Results from Scanner: {result['url']}"])
            upload_data.append(result['headers'])
            upload_data.extend(result['data'])
            is_first_scanner = False

        if not upload_data:
            print("No data to upload after processing. Exiting.")
            return

        print(f"🔼 Uploading data to Google Sheet...")
        worksheet.update(upload_data, value_input_option='USER_ENTERED')
        
        print("✅ Google Sheet updated successfully!")

    except Exception:
        print(f"❌ An error occurred while updating Google Sheet:")
        traceback.print_exc()