# app/services/sheets_service.py
import os
import gspread
from datetime import datetime
from typing import List, Dict, Any
from google.oauth2.service_account import Credentials
# Import the correct classes
from gspread_formatting import (
    CellFormat, Color, TextFormat,
    ConditionalFormatRule, GridRange,
    get_conditional_format_rules, set_frozen,
    format_cell_range, NumberFormat,
    BooleanRule, BooleanCondition
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

    def update_monthly_report(self, scraped_data: List[Dict[str, Any]]):
        """
        Updates the Google Sheet with scraped data, placing tables side-by-side.
        """
        try:
            spreadsheet = self.client.open(settings.sheet_name)
            worksheet_title = datetime.now().strftime("%B-%Y")
            
            try:
                worksheet = spreadsheet.worksheet(worksheet_title)
                worksheet.clear()
            except gspread.exceptions.WorksheetNotFound:
                worksheet = spreadsheet.add_worksheet(title=worksheet_title, rows="1000", cols="30")

            start_cells = ['A1', 'J1']
            if not scraped_data:
                worksheet.update('A1', [["No stocks were found in any scan."]])
                return

            for i, result in enumerate(scraped_data):
                if i >= len(start_cells):
                    break
                
                if result and result.get('data'):
                    scanner = result.get('scanner')
                    table_data = [
                        [f"Raw Data from: {scanner.name}"],
                        result['headers'],
                        *result['data']
                    ]
                    worksheet.update(start_cells[i], table_data, value_input_option='USER_ENTERED')

            self._format_worksheet(worksheet, num_tables=len(scraped_data))
            log.info("✅ Google Sheet updated successfully!")

        except Exception as e:
            log.error(f"❌ An error occurred while updating Google Sheet: {e}", exc_info=True)
            raise

    def _format_worksheet(self, worksheet: gspread.Worksheet, num_tables: int):
        """
        Applies advanced formatting with the correct object structure.
        """
        try:
            log.info("🎨 Applying advanced visual formatting...")
            
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
            
            # 👇 Ranges updated from 7 columns (A-G, J-P) to 6 columns (A-F, J-O)
            table_ranges = [
                {'title_hdr': 'A{row}:F{row}', 'chg': 'D:D', 'nums': 'E:F', 'title_merge': 'A1:F1'},
                {'title_hdr': 'J{row}:O{row}', 'chg': 'M:M', 'nums': 'N:O', 'title_merge': 'J1:O1'}
            ]

            all_values = worksheet.get_all_values()
            
            header_row_num = -1
            for row_idx, row in enumerate(all_values, 1):
                # 👇 Updated check from "Sr." to "Stock Name"
                if row and "Stock Name" in row:
                    if "Stock Name" == row[0]:
                        format_cell_range(worksheet, table_ranges[0]['title_hdr'].format(row=row_idx), header_format)
                        if header_row_num == -1: header_row_num = row_idx
                    if len(row) > 8 and "Stock Name" == row[9]: # Check starts at col J (index 9)
                        format_cell_range(worksheet, table_ranges[1]['title_hdr'].format(row=row_idx), header_format)

            if header_row_num != -1:
                set_frozen(worksheet, rows=header_row_num)

            # Title Formatting
            format_cell_range(worksheet, table_ranges[0]['title_merge'], title_format)
            worksheet.merge_cells(table_ranges[0]['title_merge'])
            if num_tables > 1:
                format_cell_range(worksheet, table_ranges[1]['title_merge'], title_format)
                worksheet.merge_cells(table_ranges[1]['title_merge'])

            # --- THE FINAL AND CORRECT CONDITIONAL FORMATTING LOGIC ---
            rules = get_conditional_format_rules(worksheet)
            rules.clear()
            
            for i in range(num_tables):
                if i < len(table_ranges):
                    ranges = table_ranges[i]
                    
                    rule_positive = ConditionalFormatRule(
                        ranges=[GridRange.from_a1_range(ranges['chg'], worksheet)],
                        booleanRule=BooleanRule(
                            condition=BooleanCondition('NUMBER_GREATER', ['0']),
                            format=CellFormat(textFormat=TextFormat(foregroundColor=Color(0.18, 0.5, 0.2)))
                        )
                    )
                    rule_negative = ConditionalFormatRule(
                        ranges=[GridRange.from_a1_range(ranges['chg'], worksheet)],
                        booleanRule=BooleanRule(
                            condition=BooleanCondition('NUMBER_LESS', ['0']),
                            format=CellFormat(textFormat=TextFormat(foregroundColor=Color(0.8, 0.2, 0.2)))
                        )
                    )
                    rules.extend([rule_positive, rule_negative])

                    # Number Formatting
                    number_format_indian = NumberFormat(type='NUMBER', pattern="#,##,##0.00")
                    number_cell_format = CellFormat(numberFormat=number_format_indian)
                    format_cell_range(worksheet, ranges['nums'], number_cell_format)

            rules.save()
            worksheet.columns_auto_resize(0, 16)
            log.info("✨ Advanced formatting applied successfully!")

        except Exception as e:
            log.warning(f"⚠️ Could not apply advanced formatting due to an issue: {e}")
            log.warning("The raw data has been uploaded successfully without advanced styling.")
            worksheet.columns_auto_resize(0, 16)