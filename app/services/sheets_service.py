# app/services/sheets_service.py
import os
import gspread
from typing import List, Dict, Any
from google.oauth2.service_account import Credentials
from gspread_formatting import (
    CellFormat, Color, TextFormat, set_frozen,
    format_cell_range, NumberFormat
)
from ..core.config import settings
from ..utils.logger import log

class SheetsService:
    SCOPES = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]

    def __init__(self):
        self.client = self._authenticate()
        self.spreadsheet = self.client.open(settings.sheet_name)
        self.worksheet = self._get_or_create_worksheet()

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

    def _get_or_create_worksheet(self) -> gspread.Worksheet:
        try:
            return self.spreadsheet.worksheet(settings.worksheet_name)
        except gspread.exceptions.WorksheetNotFound:
            log.info(f"Worksheet '{settings.worksheet_name}' not found. Creating it.")
            return self.spreadsheet.add_worksheet(title=settings.worksheet_name, rows="1000", cols="50")

    def update_scanned_stocks_report(self, all_scraped_data: List[Dict[str, Any]]):
        log.info("--- Starting Google Sheet Update ---")
        
        table_defs = [{'start': 'A', 'end': 'G', 'status_col_index': 6}, {'start': 'J', 'end': 'P', 'status_col_index': 6}]
        final_sheet_data = []
        max_rows = 0
        dismissed_count = 0

        for i, result in enumerate(all_scraped_data):
            if i >= len(table_defs): break
            
            table_range = f"{table_defs[i]['start']}1:{table_defs[i]['end']}1000"
            try:
                existing_values = self.worksheet.get(table_range)
            except gspread.exceptions.APIError:
                existing_values = []
            
            # 1. Clean existing stocks by removing 'Dismissed' ones
            cleaned_existing_stocks = []
            if len(existing_values) > 2:
                for row in existing_values[2:]:
                    if len(row) > table_defs[i]['status_col_index'] and row[table_defs[i]['status_col_index']].strip().lower() == 'dismissed':
                        dismissed_count += 1
                    elif any(row):
                        cleaned_existing_stocks.append(row)
            
            # 2. Filter new stocks to avoid duplicates
            existing_symbols = {stock[1] for stock in cleaned_existing_stocks if len(stock) > 1}
            new_stocks = []
            if result and result.get('data'):
                for stock_data in result['data']:
                    if stock_data[1] not in existing_symbols:
                        new_stocks.append(stock_data)
            
            # 3. Combine title, header, cleaned existing stocks, and new stocks
            scanner_name = result.get('scanner_name', f'Scanner {i+1}')
            table_data = [[f"Data from: {scanner_name}"], settings.table_headers, *cleaned_existing_stocks, *new_stocks]
            final_sheet_data.append(table_data)
            max_rows = max(max_rows, len(table_data))

        if dismissed_count > 0:
            log.info(f"Removed {dismissed_count} 'Dismissed' stock(s).")
        else:
            log.info("No 'Dismissed' stocks to remove.")

        # 4. Rebuild the entire grid and update the sheet once
        final_grid = [[""] * 20 for _ in range(max_rows)] 
        for r in range(max_rows):
            if r < len(final_sheet_data[0]):
                final_grid[r][0:len(final_sheet_data[0][r])] = final_sheet_data[0][r]
            if len(final_sheet_data) > 1 and r < len(final_sheet_data[1]):
                final_grid[r][9:9+len(final_sheet_data[1][r])] = final_sheet_data[1][r]

        self.worksheet.clear()
        self.worksheet.update('A1', final_grid, value_input_option='USER_ENTERED')
        self._format_worksheet(num_tables=len(final_sheet_data))
        
        log.info("✅ Google Sheet update finished successfully!")

    def _format_worksheet(self, num_tables: int):
        log.info("🎨 Applying formatting...")
        title_format = CellFormat(backgroundColor=Color(0.2, 0.2, 0.2), textFormat=TextFormat(bold=True, foregroundColor=Color(1, 1, 1), fontSize=12))
        header_format = CellFormat(backgroundColor=Color(0.9, 0.9, 0.9), textFormat=TextFormat(bold=True))
        
        table_ranges = [
            {'title_hdr': 'A{row}:G{row}', 'nums': 'C:F', 'title_merge': 'A1:G1'},
            {'title_hdr': 'J{row}:P{row}', 'nums': 'L:O', 'title_merge': 'J1:P1'}
        ]

        set_frozen(self.worksheet, rows=2)

        for i in range(num_tables):
            # Only apply title/header if they don't exist in the data we are about to write
            # This check is simpler now, we just do it.
            self.worksheet.merge_cells(table_ranges[i]['title_merge'], merge_type='MERGE_ALL')
            format_cell_range(self.worksheet, table_ranges[i]['title_merge'], title_format)
            format_cell_range(self.worksheet, table_ranges[i]['title_hdr'].format(row=2), header_format)
            
            num_format = NumberFormat(type='NUMBER', pattern="#,##,##0.00")
            format_cell_range(self.worksheet, table_ranges[i]['nums'], CellFormat(numberFormat=num_format))

        self.worksheet.columns_auto_resize(0, 20)
        log.info("✨ Base formatting applied successfully!")