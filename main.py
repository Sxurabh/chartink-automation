# main.py

import asyncio
import time
import config
from scraper import scrape_chartink_data
from sheets import update_monthly_report
from dotenv import load_dotenv

load_dotenv()

async def main():
    start_time = time.time()
    print("--- Starting Monthly Stock Scan ---")

    urls = list(config.SCANNER_MAPPING.keys())
    tasks = [scrape_chartink_data(url) for url in urls]
    scraped_results = await asyncio.gather(*tasks)

    update_monthly_report(scraped_results)

    end_time = time.time()
    print(f"\n--- Automation Finished in {end_time - start_time:.2f} seconds ---")

if __name__ == "__main__":
    asyncio.run(main())