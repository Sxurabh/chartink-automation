# app/main.py
import asyncio
import time
# Use relative imports within the application package
from .core.config import settings
from .services.scraper_service import run_scrapers
from .services.sheets_service import SheetsService
from .utils.logger import log

async def main():
    """
    Main asynchronous function to run the automation process.
    """
    start_time = time.time()
    log.info("--- Starting Monthly Stock Scan ---")

    # 1. Scrape data from all configured scanners
    scraped_results = await run_scrapers(settings.scanners)

    # 2. Filter out any failed or empty results
    successful_results = [res for res in scraped_results if res and res.get('data')]

    if not successful_results:
        log.warning("No data was scraped from any source. Skipping Google Sheet update.")
    else:
        # 3. Update Google Sheets with the data
        try:
            sheets_service = SheetsService()
            sheets_service.update_monthly_report(successful_results)
        except Exception as e:
            log.error(f"Failed to update Google Sheets. Error: {e}")

    end_time = time.time()
    log.info(f"\n--- Automation Finished in {end_time - start_time:.2f} seconds ---")

if __name__ == "__main__":
    asyncio.run(main())