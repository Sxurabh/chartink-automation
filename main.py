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

    # --- CHANGE: Get URLs from the keys of the new mapping dictionary ---
    tasks = [scrape_chartink_data(url) for url in config.SCANNER_MAPPING.keys()]
    
    scraped_results = await asyncio.gather(*tasks)

    update_google_sheet(scraped_results)

    end_time = time.time()
    print(f"\n--- Automation Finished in {end_time - start_time:.2f} seconds ---")


if __name__ == "__main__":
    asyncio.run(main())