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
    SCOPES = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    gcp_creds_string = os.getenv('GCP_CREDENTIALS')
    if gcp_creds_string:
        return Credentials.from_service_account_info(json.loads(gcp_creds_string), scopes=SCOPES)
    else:
        credentials_file = 'credentials.json'
        if not os.path.exists(credentials_file): raise FileNotFoundError(f"'{credentials_file}' not found.")
        return Credentials.from_service_account_file(credentials_file, scopes=SCOPES)

def _prepare_upload_block(results: List[Dict[str, Any]], title_prefix: str):
    upload_data = []
    is_first = True
    for result in results:
        if not result.get('data'): continue
        if not is_first: upload_data.append([])
        
        scanner_name = config.SCANNER_MAPPING.get(result.get('url'), {}).get('name', 'Combined Analysis')
        upload_data.append([f"{title_prefix}{scanner_name}"])
        upload_data.append(result['headers'])
        upload_data.extend(result['data'])
        is_first = False
    return upload_data

def format_worksheet(worksheet: gspread.Worksheet):
    print("🎨 Applying visual formatting to the worksheet...")
    
    # Define Formats
    title_format_raw = gsf.cellFormat(textFormat=gsf.textFormat(bold=True, fontSize=13), backgroundColor=gsf.color(0.85, 0.85, 0.85), horizontalAlignment='CENTER')
    title_format_funda = gsf.cellFormat(textFormat=gsf.textFormat(bold=True, fontSize=13), backgroundColor=gsf.color(0.8, 0.9, 1.0), horizontalAlignment='CENTER')
    title_format_ai = gsf.cellFormat(textFormat=gsf.textFormat(bold=True, fontSize=13), backgroundColor=gsf.color(0.8, 1.0, 0.8), horizontalAlignment='CENTER')
    header_format = gsf.cellFormat(backgroundColor=gsf.color(0.95, 0.95, 0.95), textFormat=gsf.textFormat(bold=True))
    
    # --- FIX: Apply Title Formatting directly to the known cells ---
    # This is more robust than searching for text with .find()
    gsf.format_cell_ranges(worksheet, [('A1', title_format_raw), ('J1', title_format_funda), ('T1', title_format_ai)])

    # Apply Header Formatting by finding the "Sr." headers, which is more reliable
    all_header_cells = worksheet.findall("Sr.")
    header_rules = []
    for cell in all_header_cells:
        # Find the last column with content in that row to make the range dynamic
        last_col = len(worksheet.row_values(cell.row))
        range_label = f"{gspread.utils.rowcol_to_a1(cell.row, cell.col)}:{gspread.utils.rowcol_to_a1(cell.row, last_col)}"
        header_rules.append((range_label, header_format))
    if header_rules:
        gsf.format_cell_ranges(worksheet, header_rules)
    
    # Auto-Resize and Timestamp
    worksheet.columns_auto_resize(0, 7)    # Raw data columns
    worksheet.columns_auto_resize(9, 17)   # Fundamental analysis columns
    worksheet.columns_auto_resize(19, 27)  # AI analysis columns
    
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S IST')
    worksheet.update('I1', [[f"Last Updated:\n{timestamp}"]])
    worksheet.format('I1', {'textFormat': {'italic': True}, 'horizontalAlignment': 'CENTER', 'verticalAlignment': 'TOP'})
    print("✨ Formatting applied successfully.")

def update_monthly_report(raw_scraped: List, fundamental_analyzed: List, ai_analyzed: List):
    print("\n🔒 Authenticating with Google Sheets...")
    try:
        creds = get_google_credentials()
        client = gspread.authorize(creds)
        spreadsheet = client.open(config.SHEET_NAME)
        worksheet_title = datetime.now().strftime("%B-%Y")

        try:
            worksheet = spreadsheet.worksheet(worksheet_title)
            worksheet.clear()
        except gspread.exceptions.WorksheetNotFound:
            worksheet = spreadsheet.add_worksheet(title=worksheet_title, rows="1000", cols="40")

        # Upload blocks to their respective columns
        raw_block = _prepare_upload_block(raw_scraped, "Raw Scraped Data from: ")
        if raw_block: worksheet.update('A1', raw_block)
        
        funda_block = _prepare_upload_block(fundamental_analyzed, "Fundamental Analysis of: ")
        if funda_block: worksheet.update('J1', funda_block)
        
        ai_block = _prepare_upload_block(ai_analyzed, "AI-Powered Analysis of: ")
        if ai_block: worksheet.update('T1', ai_block)

        format_worksheet(worksheet)
        print("✅ Google Sheet updated with three independent analysis tables!")

    except Exception:
        print(f"❌ An error occurred while updating Google Sheet:")
        traceback.print_exc()