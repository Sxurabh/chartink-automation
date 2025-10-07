# sheets.py

import os
import json
import traceback
from datetime import datetime
from typing import List, Dict, Any
import gspread
from google.oauth2.service_account import Credentials
import gspread_formatting as gsf
import config

# --- Constants ---
SCOPES = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]

def get_google_credentials():
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

def format_worksheet(worksheet: gspread.Worksheet, data_written: List[List[Any]]):
    """
    Applies professional formatting to the worksheet after data is uploaded.
    """
    print("🎨 Applying formatting to the worksheet...")

    # Define formats
    title_format = gsf.cellFormat(
        textFormat=gsf.textFormat(bold=True, fontSize=12)
    )
    header_format = gsf.cellFormat(
        backgroundColor=gsf.color(0.9, 0.9, 0.9), # Light grey background
        textFormat=gsf.textFormat(bold=True)
    )

    # Find the rows that contain titles and headers to format them
    formatting_rules = []
    for i, row in enumerate(data_written):
        row_num = i + 1
        if not row: continue
        
        if str(row[0]).startswith("Results from Scanner"):
            formatting_rules.append((f"A{row_num}", title_format))
        elif row[0] == config.TABLE_HEADERS[0]:
            end_column = gspread.utils.rowcol_to_a1(row_num, len(row))
            formatting_rules.append((f"A{row_num}:{end_column}", header_format))

    gsf.format_cell_ranges(worksheet, formatting_rules)

    worksheet.columns_auto_resize(0, 6)
    
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S IST')
    
    # --- FIX: Wrap the single value in a list of lists ---
    worksheet.update('H1', [[f"Last Updated:\n{timestamp}"]])
    
    worksheet.format('H1', {'textFormat': {'italic': True}, 'horizontalAlignment': 'RIGHT'})
    
    print("✨ Formatting applied successfully.")


def update_google_sheet(all_results: List[Dict[str, Any]]):
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
        
        format_worksheet(worksheet, upload_data)
        
        print("✅ Google Sheet updated and formatted successfully!")

    except Exception:
        print(f"❌ An error occurred while updating Google Sheet:")
        traceback.print_exc()