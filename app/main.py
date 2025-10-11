# app/main.py
import asyncio
import time
import argparse
from .core.config import settings
from .services.scraper_service import run_scrapers
from .services.sheets_service import SheetsService
from .services.price_history_service import PriceHistoryService
from .utils.logger import log

async def main(clean_only: bool = False):
    """
    Main asynchronous function to run the automation process.
    """
    start_time = time.time()
    sheets_service = SheetsService()

    if clean_only:
        log.info("--- Running in Cleanup-Only Mode ---")
        sheets_service.clean_dismissed_stocks()
        log.info(f"--- Cleanup Finished in {time.time() - start_time:.2f} seconds ---")
        return

    log.info("--- Starting Full Stock Scan and Update ---")
    
    # 1. Initialize services
    price_history_service = PriceHistoryService()

    # 2. Scrape data from all configured scanners
    scraped_results = await run_scrapers(settings.scanners)

    # 3. Process each scanner result to generate signals
    processed_results = []
    for result in scraped_results:
        if not (result and result.get('data')):
            # Add an empty result to maintain table structure
            processed_results.append({
                "scanner_name": result['scanner'].name if result else "Unknown Scanner",
                "data": []
            })
            continue

        processed_stock_data = []
        for stock_data in result['data']:
            stock_name, symbol, price, volume = stock_data
            
            ohl = price_history_service.get_last_month_ohl(symbol)
            buy_price = ohl[0] if ohl else "N/A"
            stop_loss = ohl[1] if ohl else "N/A"
            
            processed_stock_data.append([
                stock_name, symbol, price, volume,
                buy_price, stop_loss, ""  # Status is initially empty
            ])
            await asyncio.sleep(0.5)
        
        processed_results.append({
            "scanner_name": result['scanner'].name,
            "data": processed_stock_data
        })
        log.info(f"Processed {len(processed_stock_data)} stocks for '{result['scanner'].name}'.")

    # 4. Update Google Sheets with the processed data
    if not processed_results:
        log.warning("No new data was scraped from any source.")
    
    sheets_service.update_scanned_stocks_report(processed_results)

    log.info(f"\n--- Automation Finished in {time.time() - start_time:.2f} seconds ---")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the ChartInk Stock Scraper.")
    parser.add_argument(
        '--clean-dismissed',
        action='store_true',
        help="Run in cleanup mode to only remove 'Dismissed' stocks from the sheet."
    )
    args = parser.parse_args()
    
    asyncio.run(main(clean_only=args.clean_dismissed))