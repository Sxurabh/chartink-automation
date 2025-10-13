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
            worksheet = self.spreadsheet.add_worksheet(title=settings.worksheet_name, rows="1000", cols="50")
            self._format_worksheet(num_tables=2)
            return worksheet

    def update_scanned_stocks_report(self, all_scraped_data: List[Dict[str, Any]]):
        log.info("--- Starting Google Sheet Update ---")
        
        table_defs = [
            {'start_col_char': 'A', 'end_col_char': 'G', 'status_col_index': 6},
            {'start_col_char': 'J', 'end_col_char': 'P', 'status_col_index': 6}
        ]

        for i, result in enumerate(all_scraped_data):
            if i >= len(table_defs):
                break
            
            table_def = table_defs[i]
            scanner_name = result.get('scanner_name', f'Scanner {i+1}')
            
            try:
                read_range = f"{table_def['start_col_char']}3:{table_def['end_col_char']}1000"
                existing_values = self.worksheet.get(read_range, value_render_option='FORMULA')
            except gspread.exceptions.APIError as e:
                log.error(f"Could not read from sheet for {scanner_name}: {e}")
                existing_values = []
            
            num_existing_rows = len(existing_values)

            # Map existing stocks by symbol, preserving their status
            existing_stocks_map = {}
            for row in existing_values:
                if len(row) > 1 and row[1]:
                    symbol = row[1]
                    # Create a full row with blank strings for missing cells
                    full_row = row + [''] * (len(settings.table_headers) - len(row))
                    status = full_row[table_def['status_col_index']]
                    existing_stocks_map[symbol] = {'row_data': full_row, 'status': status}

            # Prepare a clean list of final stocks, excluding dismissed ones
            final_stock_list = []
            dismissed_count = 0
            
            # Process existing stocks
            for symbol, data in existing_stocks_map.items():
                if data['status'].strip().lower() == 'dismissed':
                    dismissed_count += 1
                    continue
                final_stock_list.append(data['row_data'])

            if dismissed_count > 0:
                log.info(f"Identified {dismissed_count} 'Dismissed' stock(s) for removal in '{scanner_name}'.")

            # Add new stocks
            if result and result.get('data'):
                for new_stock in result['data']:
                    symbol = new_stock[1]
                    if symbol not in existing_stocks_map:
                        final_stock_list.append(new_stock)

            # --- KEY CHANGE: Overwrite and then clear leftovers ---
            # 1. Update the main data block
            if final_stock_list:
                update_range = f"{table_def['start_col_char']}3:{table_def['end_col_char']}{len(final_stock_list) + 2}"
                self.worksheet.update(update_range, final_stock_list, value_input_option='USER_ENTERED')
            
            # 2. Clear any leftover rows if the new list is shorter than the old one
            num_final_rows = len(final_stock_list)
            if num_existing_rows > num_final_rows:
                clear_start_row = 3 + num_final_rows
                clear_end_row = 3 + num_existing_rows
                leftover_range = f"{table_def['start_col_char']}{clear_start_row}:{table_def['end_col_char']}{clear_end_row}"
                log.info(f"Clearing leftover data in range: {leftover_range}")
                self.worksheet.batch_clear([leftover_range])

            log.info(f"✅ Updated sheet for '{scanner_name}' with {len(final_stock_list)} stocks.")

        # Re-apply titles, headers, and formatting (excluding status column)
        self._format_worksheet(num_tables=len(all_scraped_data))
        log.info("✅ Google Sheet update finished successfully!")

    def _format_worksheet(self, num_tables: int):
        log.info("🎨 Applying formatting...")
        title_format = CellFormat(backgroundColor=Color(0.2, 0.2, 0.2), textFormat=TextFormat(bold=True, foregroundColor=Color(1, 1, 1), fontSize=12))
        header_format = CellFormat(backgroundColor=Color(0.9, 0.9, 0.9), textFormat=TextFormat(bold=True))
        
        table_ranges = [
            # Ranges updated to EXCLUDE the status column from any formatting
            {'title_hdr': 'A{row}:F{row}', 'nums': 'C:F', 'title_merge': 'A1:G1'},
            {'title_hdr': 'J{row}:O{row}', 'nums': 'L:O', 'title_merge': 'J1:P1'}
        ]

        set_frozen(self.worksheet, rows=2)

        for i in range(num_tables):
            # Update titles and headers
            self.worksheet.merge_cells(table_ranges[i]['title_merge'], merge_type='MERGE_ALL')
            format_cell_range(self.worksheet, table_ranges[i]['title_merge'], title_format)
            format_cell_range(self.worksheet, table_ranges[i]['title_hdr'].format(row=2), header_format)
            
            # Format number columns
            num_format = NumberFormat(type='NUMBER', pattern="#,##,##0.00")
            format_cell_range(self.worksheet, table_ranges[i]['nums'], CellFormat(numberFormat=num_format))

        self.worksheet.columns_auto_resize(0, 20)
        log.info("✨ Formatting applied successfully, status column untouched.")