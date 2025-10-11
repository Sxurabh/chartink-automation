# app/services/sheets_service.py
import os
import gspread
from typing import List, Dict, Any
from google.oauth2.service_account import Credentials
from gspread_formatting import (
    CellFormat, Color, TextFormat, set_frozen,
    format_cell_range, NumberFormat, DataValidationRule, BooleanCondition,
    set_data_validation_for_cell_range  # <-- Correct import
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
        
        table_defs = [
            {'start': 'A', 'end': 'G', 'status': 'G'},
            {'start': 'J', 'end': 'P', 'status': 'P'}
        ]

        final_sheet_data = []
        max_rows = 0

        for i, result in enumerate(all_scraped_data):
            if i >= len(table_defs): break
            
            table_range = f"{table_defs[i]['start']}1:{table_defs[i]['end']}1000"
            try:
                existing_values = self.worksheet.get(table_range)
                if len(existing_values) > 2:
                    headers = existing_values[1]
                    records = [dict(zip(headers, row)) for row in existing_values[2:] if any(row)]
                else:
                    records = []
            except gspread.exceptions.APIError:
                records = []
            
            bought_stocks = [list(rec.values()) for rec in records if rec.get('Status','').strip().lower() == 'bought']
            bought_symbols = {stock[1] for stock in bought_stocks}
            
            new_stocks = []
            if result and result.get('data'):
                for stock in result['data']:
                    if stock[1] not in bought_symbols:
                        new_stocks.append(stock)
            
            scanner_name = result.get('scanner_name', f'Scanner {i+1}')
            table_data = [[f"Data from: {scanner_name}"], settings.table_headers, *bought_stocks, *new_stocks]
            final_sheet_data.append(table_data)
            max_rows = max(max_rows, len(table_data))

        final_grid = [[""] * 20 for _ in range(max_rows)] 
        
        for r in range(max_rows):
            if r < len(final_sheet_data[0]):
                row_data = final_sheet_data[0][r]
                final_grid[r][0:len(row_data)] = row_data
            
            if len(final_sheet_data) > 1 and r < len(final_sheet_data[1]):
                row_data = final_sheet_data[1][r]
                final_grid[r][9:9+len(row_data)] = row_data

        self.worksheet.clear()
        self.worksheet.update('A1', final_grid, value_input_option='USER_ENTERED')

        self._format_worksheet(num_tables=len(final_sheet_data))
        log.info("✅ Google Sheet updated successfully!")

    def clean_dismissed_stocks(self):
        log.info("--- Starting Manual Cleanup of 'Dismissed' Stocks ---")
        log.info("The main scheduled run automatically cleans 'Dismissed' stocks. No separate action needed.")
        pass

    def _format_worksheet(self, num_tables: int):
        log.info("🎨 Applying formatting...")
        title_format = CellFormat(backgroundColor=Color(0.2, 0.2, 0.2), textFormat=TextFormat(bold=True, foregroundColor=Color(1, 1, 1), fontSize=12))
        header_format = CellFormat(backgroundColor=Color(0.9, 0.9, 0.9), textFormat=TextFormat(bold=True))
        
        table_ranges = [
            {'title_hdr': 'A{row}:G{row}', 'nums': 'C:F', 'title_merge': 'A1:G1', 'status_col': 'G'},
            {'title_hdr': 'J{row}:P{row}', 'nums': 'L:O', 'title_merge': 'J1:P1', 'status_col': 'P'}
        ]

        set_frozen(self.worksheet, rows=2)

        status_validation_rule = DataValidationRule(
            condition=BooleanCondition('ONE_OF_LIST', ['Bought', 'Dismissed']),
            showCustomUi=True
        )

        for i in range(num_tables):
            self.worksheet.merge_cells(table_ranges[i]['title_merge'], merge_type='MERGE_ALL')
            format_cell_range(self.worksheet, table_ranges[i]['title_merge'], title_format)
            format_cell_range(self.worksheet, table_ranges[i]['title_hdr'].format(row=2), header_format)
            
            num_format = NumberFormat(type='NUMBER', pattern="#,##,##0.00")
            format_cell_range(self.worksheet, table_ranges[i]['nums'], CellFormat(numberFormat=num_format))

            # Set data validation for the status column
            status_range = f"{table_ranges[i]['status_col']}3:{table_ranges[i]['status_col']}1000"
            # 👇 This is the corrected function call
            set_data_validation_for_cell_range(self.worksheet, status_range, status_validation_rule)

        self.worksheet.columns_auto_resize(0, 20)
        log.info("✨ Formatting and status dropdowns applied successfully!")