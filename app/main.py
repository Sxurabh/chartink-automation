# app/main.py
import asyncio
import time
import argparse
from .core.config import settings
from .services.scraper_service import run_scrapers
from .services.sheets_service import SheetsService
from .utils.logger import log

async def main(clean_only: bool = False):
    """
    Main asynchronous function to run the automation process.
    """
    start_time = time.time()
    sheets_service = SheetsService()

    if clean_only:
        log.info("--- Running in Cleanup-Only Mode ---")
        # This is the corrected part that ensures the cleanup function is called.
        sheets_service.clean_dismissed_stocks()
        log.info(f"--- Cleanup Finished in {time.time() - start_time:.2f} seconds ---")
        return

    log.info("--- Starting Full Stock Scan and Update ---")
    
    scraped_results = await run_scrapers(settings.scanners)

    processed_results = []
    
    for table_index, result in enumerate(scraped_results):
        if not (result and result.get('data')):
            processed_results.append({
                "scanner_name": result['scanner'].name if result else "Unknown Scanner",
                "data": []
            })
            continue

        processed_stock_data = []
        for stock_data in result['data']:
            stock_name, symbol, price, volume = stock_data
            
            name_col = 'A' if table_index == 0 else 'J'
            symbol_col = 'B' if table_index == 0 else 'K'
            
            name_cell = f'INDIRECT("{name_col}" & ROW())'
            symbol_cell = f'INDIRECT("{symbol_col}" & ROW())'
            
            high_date_range = f'"high", EOMONTH(TODAY(), -2) + 1, EOMONTH(TODAY(), -1)'
            low_date_range = f'"low", EOMONTH(TODAY(), -2) + 1, EOMONTH(TODAY(), -1)'

            fetch_high = f'IFERROR(MAX(QUERY(GOOGLEFINANCE("NSE:"&{symbol_cell}, {high_date_range}), "SELECT Col2")), IFERROR(MAX(QUERY(GOOGLEFINANCE("BOM:"&{symbol_cell}, {high_date_range}), "SELECT Col2")), ""))'
            fetch_low = f'IFERROR(MIN(QUERY(GOOGLEFINANCE("NSE:"&{symbol_cell}, {low_date_range}), "SELECT Col2")), IFERROR(MIN(QUERY(GOOGLEFINANCE("BOM:"&{symbol_cell}, {low_date_range}), "SELECT Col2")), ""))'
            
            buy_price_formula = f'=IF(NOT(ISBLANK({name_cell})), {fetch_high}, "")'
            stop_loss_formula = f'=IF(NOT(ISBLANK({name_cell})), {fetch_low}, "")'
            
            processed_stock_data.append([
                stock_name, symbol, price, volume,
                buy_price_formula, stop_loss_formula, ""
            ])
        
        processed_results.append({
            "scanner_name": result['scanner'].name,
            "data": processed_stock_data
        })
        log.info(f"Processed {len(processed_stock_data)} new stocks for '{result['scanner'].name}'.")

    sheets_service.update_scanned_stocks_report(processed_results)

    log.info(f"\n--- Automation Finished in {time.time() - start_time:.2f} seconds ---")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the ChartInk Stock Scraper.")
    parser.add_argument(
        '--clean-dismissed',
        action='store_true',
        help="Run in cleanup mode."
    )
    args = parser.parse_args()
    asyncio.run(main(clean_only=args.clean_dismissed))