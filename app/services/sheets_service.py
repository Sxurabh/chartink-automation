import os
import gspread
from datetime import datetime
from typing import List, Dict, Any
from google.oauth2.service_account import Credentials
from gspread_formatting import (
    CellFormat, Color, TextFormat, set_frozen,
    format_cell_range, NumberFormat
)
from ..core.config import settings, TABLE_WIDTH, TABLE_GAP, TABLE_STRIDE, col_letter
from ..utils.logger import log
from ..utils.retry import retry

class SheetsService:
    SCOPES = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]

    def __init__(self):
        self.client = self._authenticate()
        self.spreadsheet = self.client.open(settings.sheet_name)
        self.worksheet = self._get_or_create_worksheet()

    def _authenticate(self):
        log.info("Authenticating with Google Sheets...")
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

    def _get_worksheet_name(self) -> str:
        now = datetime.now()
        month_name = now.strftime("%B %Y")
        return f"{settings.worksheet_name} - {month_name}"

    def _get_or_create_worksheet(self) -> gspread.Worksheet:
        name = self._get_worksheet_name()
        try:
            return self.spreadsheet.worksheet(name)
        except gspread.exceptions.WorksheetNotFound:
            log.info(f"Worksheet '{name}' not found. Creating it.")
            worksheet = self.spreadsheet.add_worksheet(title=name, rows=1000, cols=50)
            return worksheet

    def _table_range(self, table_index, start_row, end_row=None):
        start_col = table_index * TABLE_STRIDE
        end_col = start_col + TABLE_WIDTH - 1
        start_letter = col_letter(start_col)
        end_letter = col_letter(end_col)
        if end_row is not None:
            return start_letter, end_letter, f"{start_letter}{start_row}:{end_letter}{end_row}"
        return start_letter, end_letter

    @retry(max_attempts=3, delay=2, backoff=2, exceptions=(gspread.exceptions.APIError,), logger=log)
    def _safe_get(self, range_name):
        return self.worksheet.get(range_name, value_render_option='FORMULA')

    @retry(max_attempts=3, delay=2, backoff=2, exceptions=(gspread.exceptions.APIError,), logger=log)
    def _safe_update(self, range_name, values):
        return self.worksheet.update(range_name, values, value_input_option='USER_ENTERED')

    @retry(max_attempts=3, delay=2, backoff=2, exceptions=(gspread.exceptions.APIError,), logger=log)
    def _safe_clear(self, ranges):
        return self.worksheet.batch_clear(ranges)

    def _write_titles_and_headers(self, all_scraped_data: List[Dict[str, Any]]):
        for i, result in enumerate(all_scraped_data):
            start_letter, end_letter = self._table_range(i, 1)
            scanner_name = result.get('scanner_name', f'Scanner {i+1}')
            title_range = f"{start_letter}1:{end_letter}1"
            self._safe_update(title_range, [[scanner_name]])
            header_range = f"{start_letter}2:{end_letter}2"
            self._safe_update(header_range, [settings.table_headers])

    def update_scanned_stocks_report(self, all_scraped_data: List[Dict[str, Any]]):
        log.info("--- Starting Google Sheet Update ---")

        self._write_titles_and_headers(all_scraped_data)

        for i, result in enumerate(all_scraped_data):
            start_letter, end_letter = self._table_range(i, 3)
            scanner_name = result.get('scanner_name', f'Scanner {i+1}')

            try:
                read_range = f"{start_letter}3:{end_letter}1000"
                existing_values = self._safe_get(read_range)
            except gspread.exceptions.APIError as e:
                log.error(f"Could not read from sheet for {scanner_name}: {e}")
                existing_values = []

            num_existing_rows = len(existing_values)

            existing_stocks_map = {}
            status_col = TABLE_WIDTH - 1
            for row in existing_values:
                if len(row) > 1 and row[1]:
                    symbol = row[1]
                    full_row = row + [''] * (TABLE_WIDTH - len(row))
                    status = full_row[status_col]
                    existing_stocks_map[symbol] = {'row_data': full_row, 'status': status}

            final_stock_list = []
            dismissed_count = 0
            for symbol, data in existing_stocks_map.items():
                if data['status'].strip().lower() == 'dismissed':
                    dismissed_count += 1
                    continue
                final_stock_list.append(data['row_data'])

            if dismissed_count > 0:
                log.info(f"Identified {dismissed_count} 'Dismissed' stock(s) for removal in '{scanner_name}'.")

            if result and result.get('data'):
                for new_stock in result['data']:
                    symbol = new_stock[1]
                    if symbol not in existing_stocks_map:
                        final_stock_list.append(new_stock)

            if final_stock_list:
                update_range = f"{start_letter}3:{end_letter}{len(final_stock_list) + 2}"
                self._safe_update(update_range, final_stock_list)

            num_final_rows = len(final_stock_list)
            if num_existing_rows > num_final_rows:
                clear_start_row = 3 + num_final_rows
                clear_end_row = 3 + num_existing_rows
                leftover_range = f"{start_letter}{clear_start_row}:{end_letter}{clear_end_row}"
                log.info(f"Clearing leftover data in range: {leftover_range}")
                self._safe_clear([leftover_range])

            log.info(f"Updated sheet for '{scanner_name}' with {len(final_stock_list)} stocks.")

        self._format_worksheet(num_tables=len(all_scraped_data))
        log.info("Google Sheet update finished successfully!")

    def _format_worksheet(self, num_tables: int):
        log.info("Applying formatting...")
        title_format = CellFormat(backgroundColor=Color(0.2, 0.2, 0.2), textFormat=TextFormat(bold=True, foregroundColor=Color(1, 1, 1), fontSize=12))
        header_format = CellFormat(backgroundColor=Color(0.9, 0.9, 0.9), textFormat=TextFormat(bold=True))

        set_frozen(self.worksheet, rows=2)

        for i in range(num_tables):
            start_letter, end_letter = self._table_range(i, 1)
            title_merge = f"{start_letter}1:{end_letter}1"
            header_excl_status = f"{start_letter}2:{col_letter(i * TABLE_STRIDE + TABLE_WIDTH - 2)}2"
            nums_start = col_letter(i * TABLE_STRIDE + 2)
            nums_end = col_letter(i * TABLE_STRIDE + TABLE_WIDTH - 2)

            self.worksheet.merge_cells(title_merge, merge_type='MERGE_ALL')
            format_cell_range(self.worksheet, title_merge, title_format)
            format_cell_range(self.worksheet, header_excl_status, header_format)

            num_format = NumberFormat(type='NUMBER', pattern="#,##,##0.00")
            format_cell_range(self.worksheet, f"{nums_start}:{nums_end}", CellFormat(numberFormat=num_format))

        self.worksheet.columns_auto_resize(0, max(20, num_tables * TABLE_STRIDE))
        log.info("Formatting applied successfully, status column untouched.")
