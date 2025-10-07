# main.py

import asyncio
import time
import config
from scraper import scrape_chartink_data
from sheets import update_google_sheet

async def main():
    """
    Main function to orchestrate concurrent scraping and sheet update.
    """
    start_time = time.time()
    print("--- Starting Monthly Stock Scan Automation ---")

    # Create a list of scraping tasks to run concurrently
    tasks = [scrape_chartink_data(url) for url in config.SCANNER_URLS]
    
    # Run all scraping tasks at the same time and wait for them to complete
    scraped_results = await asyncio.gather(*tasks)

    # Pass the collected results to the Google Sheets updater
    update_google_sheet(scraped_results)

    end_time = time.time()
    print(f"\n--- Automation Finished in {end_time - start_time:.2f} seconds ---")


if __name__ == "__main__":
    asyncio.run(main())