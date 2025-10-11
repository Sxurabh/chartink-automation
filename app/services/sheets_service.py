# app/services/sheets_service.py
import os
import gspread
from datetime import datetime
from typing import List, Dict, Any
from google.oauth2.service_account import Credentials
from gspread_formatting import (
    CellFormat, Color, TextFormat, set_frozen,
    format_cell_range, NumberFormat
)
from ..core.config import settings
from ..utils.logger import log

class SheetsService:
    """
    A service class to handle interactions with Google Sheets.
    """
    SCOPES = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]

    def __init__(self):
        self.client = self._authenticate()

    def _authenticate(self):
        log.info("🔒 Authenticating with Google Sheets...")
        creds = None
        if settings.gcp_credentials:
            creds = Credentials.from_service_account_info(settings.gcp_credentials, scopes=self.SCOPES)
        else:
            credentials_file = 'credentials.json'
            if not os.path.exists(credentials_file):
                log.error(f"'{credentials_file}' not found and GCP_CREDENTIALS secret is not set.")
                raise FileNotFoundError(f"'{credentials_file}' not found.")
            creds = Credentials.from_service_account_file(credentials_file, scopes=self.SCOPES)
        return gspread.authorize(creds)

    def update_monthly_report(self, processed_data: List[Dict[str, Any]]):
        """
        Updates the Google Sheet with processed data, placing tables side-by-side.
        """
        try:
            spreadsheet = self.client.open(settings.sheet_name)
            worksheet_title = datetime.now().strftime("%B-%Y")
            
            try:
                worksheet = spreadsheet.worksheet(worksheet_title)
                worksheet.clear()
            except gspread.exceptions.WorksheetNotFound:
                worksheet = spreadsheet.add_worksheet(title=worksheet_title, rows="1000", cols="50")

            start_cells = ['A1', 'J1']
            if not processed_data:
                worksheet.update('A1', [["No stocks were found in any scan."]])
                return

            for i, result in enumerate(processed_data):
                if i >= len(start_cells):
                    break
                
                if result and result.get('data'):
                    scanner_name = result.get('scanner_name')
                    table_data = [
                        [f"Data from: {scanner_name}"],
                        settings.table_headers,
                        *result['data']
                    ]
                    worksheet.update(start_cells[i], table_data, value_input_option='USER_ENTERED')

            self._format_worksheet(worksheet, num_tables=len(processed_data))
            log.info("✅ Google Sheet updated successfully!")

        except Exception as e:
            log.error(f"❌ An error occurred while updating Google Sheet: {e}", exc_info=True)
            raise

    def _format_worksheet(self, worksheet: gspread.Worksheet, num_tables: int):
        """
        Applies advanced formatting to the new 7-column tables.
        """
        try:
            log.info("🎨 Applying advanced formatting...")
            
            title_format = CellFormat(
                backgroundColor=Color(0.2, 0.2, 0.2),
                textFormat=TextFormat(bold=True, foregroundColor=Color(1, 1, 1), fontSize=12),
                horizontalAlignment='CENTER'
            )
            header_format = CellFormat(
                backgroundColor=Color(0.9, 0.9, 0.9),
                textFormat=TextFormat(bold=True),
                horizontalAlignment='CENTER'
            )
            
            # Ranges for 7 columns (A-G, J-P)
            table_ranges = [
                {'title_hdr': 'A{row}:G{row}', 'nums': 'C:F', 'title_merge': 'A1:G1'},
                {'title_hdr': 'J{row}:P{row}', 'nums': 'L:O', 'title_merge': 'J1:P1'}
            ]

            all_values = worksheet.get_all_values()
            
            header_row_num = 2 # Header is now always on the second row
            set_frozen(worksheet, rows=header_row_num)

            # Title and Header Formatting
            for i in range(num_tables):
                # Title
                format_cell_range(worksheet, table_ranges[i]['title_merge'], title_format)
                worksheet.merge_cells(table_ranges[i]['title_merge'])
                # Header
                format_cell_range(worksheet, table_ranges[i]['title_hdr'].format(row=header_row_num), header_format)
                
                # Number Formatting for Price, Volume, Buying Price, Stoploss
                number_format_indian = NumberFormat(type='NUMBER', pattern="#,##,##0.00")
                number_cell_format = CellFormat(numberFormat=number_format_indian)
                format_cell_range(worksheet, table_ranges[i]['nums'], number_cell_format)

            worksheet.columns_auto_resize(0, 20)
            log.info("✨ Advanced formatting applied successfully!")

        except Exception as e:
            log.warning(f"⚠️ Could not apply advanced formatting: {e}")