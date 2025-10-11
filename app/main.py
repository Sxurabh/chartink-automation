# app/main.py
import asyncio
import time
from .core.config import settings
from .services.scraper_service import run_scrapers
from .services.sheets_service import SheetsService
from .services.price_history_service import PriceHistoryService
from .utils.logger import log

async def main():
    """
    Main asynchronous function to run the automation process.
    """
    start_time = time.time()
    log.info("--- Starting Stock Scan and Signal Generation ---")

    # 1. Initialize services
    sheets_service = SheetsService()
    price_history_service = PriceHistoryService()

    # 2. Scrape data from all configured scanners
    scraped_results = await run_scrapers(settings.scanners)

    # 3. Process each scanner result to generate signals
    processed_results = []
    for result in scraped_results:
        if not (result and result.get('data')):
            continue

        processed_stock_data = []
        for stock_data in result['data']:
            stock_name, symbol, price, volume = stock_data
            
            # Fetch last month's high/low for buy price and stoploss
            ohl = price_history_service.get_last_month_ohl(symbol)
            buy_price = ohl[0] if ohl else "N/A"
            stop_loss = ohl[1] if ohl else "N/A"
            
            processed_stock_data.append([
                stock_name, symbol, price, volume,
                buy_price, stop_loss, ""  # Status is initially empty
            ])
        
        processed_results.append({
            "scanner_name": result['scanner'].name,
            "data": processed_stock_data
        })
        log.info(f"Processed {len(processed_stock_data)} stocks for '{result['scanner'].name}'.")

    # 4. Update Google Sheets with the processed data
    if not processed_results:
        log.warning("No data was scraped from any source. Skipping Google Sheet update.")
    else:
        sheets_service.update_monthly_report(processed_results)

    end_time = time.time()
    log.info(f"\n--- Automation Finished in {time.time() - start_time:.2f} seconds ---")

if __name__ == "__main__":
    asyncio.run(main())