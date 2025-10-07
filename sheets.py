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

def get_google_credentials():
    """
    Gets Google credentials from GitHub Secrets (if running in Actions)
    or from a local file (if running locally).
    """
    # --- FIX: Define SCOPES inside the function ---
    SCOPES = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    
    gcp_creds_string = os.getenv('GCP_CREDENTIALS')
    if gcp_creds_string:
        print("Found GCP credentials in environment variable (GitHub Actions).")
        creds_json = json.loads(gcp_creds_string)
        return Credentials.from_service_account_info(creds_json, scopes=SCOPES)
    else:
        print("Using local 'credentials.json' file.")
        credentials_file = 'credentials.json'
        if not os.path.exists(credentials_file):
            raise FileNotFoundError(f"'{credentials_file}' not found.")
        return Credentials.from_service_account_file(credentials_file, scopes=SCOPES)

def format_worksheet(worksheet: gspread.Worksheet):
    """Applies formatting to both unfiltered and filtered sections of the worksheet."""
    print("🎨 Applying formatting to the worksheet...")
    title_format = gsf.cellFormat(textFormat=gsf.textFormat(bold=True, fontSize=12))
    header_format = gsf.cellFormat(backgroundColor=gsf.color(0.9, 0.9, 0.9), textFormat=gsf.textFormat(bold=True))
    all_formatting_rules = []
    all_title_cells = worksheet.findall("Monthly stocks")
    for cell in all_title_cells:
        all_formatting_rules.append((cell.address, title_format))
    all_header_cells = worksheet.findall("Sr.")
    for cell in all_header_cells:
        range_label = f"{gspread.utils.rowcol_to_a1(cell.row, cell.col)}:{gspread.utils.rowcol_to_a1(cell.row, cell.col + 8)}"
        all_formatting_rules.append((range_label, header_format))
    if all_formatting_rules:
        gsf.format_cell_ranges(worksheet, all_formatting_rules)
    worksheet.columns_auto_resize(0, 6)
    worksheet.columns_auto_resize(11, 20)
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S IST')
    worksheet.update('J1', [[f"Last Updated:\n{timestamp}"]])
    worksheet.format('J1', {'textFormat': {'italic': True}, 'horizontalAlignment': 'RIGHT', 'verticalAlignment': 'TOP'})
    print("✨ Formatting applied successfully.")

def _prepare_upload_block(results: List[Dict[str, Any]], title_prefix: str = "Results from Scanner: ", limit: int = None):
    """Helper function to prepare a block of data, with an optional limit."""
    upload_data = []
    is_first = True
    for result in results:
        if not result.get('data'):
            continue
        if not is_first:
            upload_data.append([])
        
        scanner_title = config.SCANNER_MAPPING.get(result['url'], result['url'])
        upload_data.append([f"{title_prefix}{scanner_title}"])
        upload_data.append(result['headers'])
        
        data_to_upload = result['data'][:limit] if limit is not None else result['data']
        upload_data.extend(data_to_upload)
        is_first = False
    return upload_data

def update_google_sheet(all_scraped_results: List[Dict[str, Any]], all_analyzed_results: List[Dict[str, Any]]):
    """
    Updates the sheet with all scraped data and the top 5 fundamentally strong stocks.
    """
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
            worksheet = spreadsheet.add_worksheet(title=worksheet_title, rows="1000", cols="30")
            print(f"✨ Created new worksheet: '{worksheet_title}'")

        unfiltered_data_block = _prepare_upload_block(all_scraped_results)
        if unfiltered_data_block:
            print(f"🔼 Uploading all {len(unfiltered_data_block)} rows of scraped data...")
            worksheet.update('A1', unfiltered_data_block, value_input_option='USER_ENTERED')
        
        top_5_block = _prepare_upload_block(all_analyzed_results, title_prefix="Top 5 Fundamental Picks: ", limit=5)
        if top_5_block:
            print(f"🔼 Uploading Top 5 fundamentally strong stocks...")
            worksheet.update('L1', top_5_block, value_input_option='USER_ENTERED')
        else:
            worksheet.update('L1', [["No stocks passed the fundamental analysis."]])

        format_worksheet(worksheet)
        
        print("✅ Google Sheet updated with full data and top 5 fundamental picks!")

    except Exception:
        print(f"❌ An error occurred while updating Google Sheet:")
        traceback.print_exc()