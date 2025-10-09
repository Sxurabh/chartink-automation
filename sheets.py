# sheets.py

import os
import json
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

def format_worksheet(worksheet: gspread.Worksheet):
    print("🎨 Applying visual formatting...")
    worksheet.columns_auto_resize(0, 7)
    worksheet.columns_auto_resize(9, 20)
    print("✨ Formatting applied.")

def update_monthly_report(raw_scraped: List, ai_analyzed: List):
    """
    Updates the sheet with raw scraped data and the AI-scored analysis.
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
        except gspread.exceptions.WorksheetNotFound:
            worksheet = spreadsheet.add_worksheet(title=worksheet_title, rows="1000", cols="40")

        # Prepare and upload Raw Data
        raw_upload_data = []
        for result in raw_scraped:
            if not result.get('data'): continue
            scanner_name = config.SCANNER_MAPPING.get(result.get('url'), {}).get('name')
            raw_upload_data.append([f"Raw Data from: {scanner_name}"])
            raw_upload_data.append(result['headers'])
            raw_upload_data.extend(result['data'])
            raw_upload_data.append([])
        if raw_upload_data:
            worksheet.update('A1', raw_upload_data)
        
        # Prepare and upload AI-Scored Data
        ai_upload_data = []
        for result in ai_analyzed:
            if not result.get('data'): continue
            scanner_name = config.SCANNER_MAPPING.get(result.get('url'), {}).get('name')
            ai_upload_data.append([f"AI-Scored Analysis for: {scanner_name}"])
            ai_upload_data.append(result['headers'])
            ai_upload_data.extend(result['data'])
            ai_upload_data.append([])
        if ai_upload_data:
            worksheet.update('J1', ai_upload_data)
        else:
            worksheet.update('J1', [["No stocks were scored by the AI."]])

        format_worksheet(worksheet)
        print("✅ Google Sheet updated with raw data and AI-scored analysis!")

    except Exception as e:
        print(f"❌ An error occurred while updating Google Sheet: {e}")