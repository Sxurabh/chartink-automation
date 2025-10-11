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

    def get_existing_stocks_for_table(self, table_index: int) -> List[List[str]]:
        table_defs = [{'start': 'A', 'end': 'G'}, {'start': 'J', 'end': 'P'}]
        if table_index >= len(table_defs): return []
        table_range = f"{table_defs[table_index]['start']}1:{table_defs[table_index]['end']}1000"
        try:
            existing_values = self.worksheet.get(table_range)
            if len(existing_values) > 2: return [row for row in existing_values[2:] if any(row)]
            else: return []
        except gspread.exceptions.APIError: return []

    def update_scanned_stocks_report(self, all_scraped_data: List[Dict[str, Any]]):
        log.info("--- Starting Google Sheet Update ---")
        table_defs = [{'start': 'A', 'end': 'G'}, {'start': 'J', 'end': 'P'}]
        final_sheet_data, max_rows = [], 0

        for i, result in enumerate(all_scraped_data):
            if i >= len(table_defs): break
            existing_stocks = self.get_existing_stocks_for_table(i)
            existing_symbols = {stock[1] for stock in existing_stocks if len(stock) > 1}
            new_stocks = []
            if result and result.get('data'):
                for stock_data in result['data']:
                    if stock_data[1] not in existing_symbols: new_stocks.append(stock_data)
            scanner_name = result.get('scanner_name', f'Scanner {i+1}')
            table_data = [[f"Data from: {scanner_name}"], settings.table_headers, *existing_stocks, *new_stocks]
            final_sheet_data.append(table_data)
            max_rows = max(max_rows, len(table_data))

        final_grid = [[""] * 20 for _ in range(max_rows)]
        for r in range(max_rows):
            if r < len(final_sheet_data[0]):
                final_grid[r][0:len(final_sheet_data[0][r])] = final_sheet_data[0][r]
            if len(final_sheet_data) > 1 and r < len(final_sheet_data[1]):
                final_grid[r][9:9+len(final_sheet_data[1][r])] = final_sheet_data[1][r]

        self.worksheet.clear()
        self.worksheet.update('A1', final_grid, value_input_option='USER_ENTERED')
        self._format_worksheet(num_tables=len(final_sheet_data))
        log.info("✅ Google Sheet updated successfully!")

    def clean_dismissed_stocks(self):
        """Reads the sheet, removes rows marked 'Dismissed', and rewrites the sheet."""
        log.info("--- Starting Cleanup of 'Dismissed' Stocks ---")
        table_defs = [{'start': 'A', 'end': 'G', 'status_col_index': 6}, {'start': 'J', 'end': 'P', 'status_col_index': 6}]
        final_sheet_data, max_rows, dismissed_count = [], 0, 0

        for i, table_def in enumerate(table_defs):
            table_range = f"{table_def['start']}1:{table_def['end']}1000"
            try: existing_values = self.worksheet.get(table_range)
            except gspread.exceptions.APIError: existing_values = []
            
            if not existing_values or len(existing_values) < 2:
                final_sheet_data.append([])
                continue

            title_row, header_row, data_rows = [existing_values[0]], [existing_values[1]], existing_values[2:]
            cleaned_data_rows = []
            for row in data_rows:
                if len(row) > table_def['status_col_index'] and row[table_def['status_col_index']].strip().lower() == 'dismissed':
                    dismissed_count += 1
                else: cleaned_data_rows.append(row)
            
            table_data = title_row + header_row + cleaned_data_rows
            final_sheet_data.append(table_data)
            max_rows = max(max_rows, len(table_data))
        
        if dismissed_count == 0:
            log.info("✅ No stocks marked as 'Dismissed'. No changes made.")
            return

        final_grid = [[""] * 20 for _ in range(max_rows)]
        for r in range(max_rows):
            if r < len(final_sheet_data[0]):
                final_grid[r][0:len(final_sheet_data[0][r])] = final_sheet_data[0][r]
            if len(final_sheet_data) > 1 and r < len(final_sheet_data[1]):
                final_grid[r][9:9+len(final_sheet_data[1][r])] = final_sheet_data[1][r]
        
        self.worksheet.clear()
        self.worksheet.update('A1', final_grid, value_input_option='USER_ENTERED')
        self._format_worksheet(num_tables=len(final_sheet_data))
        log.info(f"✅ Successfully removed {dismissed_count} 'Dismissed' stock(s).")


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
            self.worksheet.merge_cells(table_ranges[i]['title_merge'], merge_type='MERGE_ALL')
            format_cell_range(self.worksheet, table_ranges[i]['title_merge'], title_format)
            format_cell_range(self.worksheet, table_ranges[i]['title_hdr'].format(row=2), header_format)
            num_format = NumberFormat(type='NUMBER', pattern="#,##,##0.00")
            format_cell_range(self.worksheet, table_ranges[i]['nums'], CellFormat(numberFormat=num_format))
        self.worksheet.columns_auto_resize(0, 20)
        log.info("✨ Base formatting applied successfully!")