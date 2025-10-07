# sheets.py

import os
import json
import traceback
from datetime import datetime
from typing import List, Dict, Any
import gspread
from google.oauth2.service_account import Credentials
import config

# --- Constants ---
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

def get_google_credentials():
    """
    Gets Google credentials from GitHub Secrets (if running in Actions)
    or from a local file (if running locally).
    """
    # Check if the GCP_CREDENTIALS environment variable exists (used by GitHub Actions)
    gcp_creds_string = os.getenv('GCP_CREDENTIALS')
    
    if gcp_creds_string:
        print("Found GCP credentials in environment variable (GitHub Actions).")
        creds_json = json.loads(gcp_creds_string)
        return Credentials.from_service_account_info(creds_json, scopes=SCOPES)
    else:
        print("Using local 'credentials.json' file.")
        credentials_file = 'credentials.json'
        if not os.path.exists(credentials_file):
            raise FileNotFoundError(f"'{credentials_file}' not found. This file is required for local execution.")
        return Credentials.from_service_account_file(credentials_file, scopes=SCOPES)

def update_google_sheet(all_results: List[Dict[str, Any]]):
    """
    Updates the Google Sheet with separated data from each scanner.
    """
    if not any(result['data'] for result in all_results):
        print("No data was scraped. Exiting sheets update.")
        return

    print("\n🔒 Authenticating with Google Sheets...")
    try:
        creds = get_google_credentials()
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
                upload_data.append([])

            upload_data.append([f"Results from Scanner: {result['url']}"])
            upload_data.append(result['headers'])
            upload_data.extend(result['data'])
            is_first_scanner = False

        if not upload_data:
            print("No data to upload after processing.")
            return

        print(f"🔼 Uploading data to Google Sheet...")
        worksheet.update(upload_data, value_input_option='USER_ENTERED')
        
        print("✅ Google Sheet updated successfully!")

    except Exception:
        print(f"❌ An error occurred while updating Google Sheet:")
        traceback.print_exc()