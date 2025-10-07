# main.py

import asyncio
import time
import config
from scraper import scrape_chartink_data
from sheets import update_google_sheet
from analysis import analyze_and_rank_stocks # <-- Import the new function

async def main():
    """
    Main function to orchestrate scraping, analysis, and sheet update.
    """
    start_time = time.time()
    print("--- Starting Monthly Stock Scan Automation ---")

    tasks = [scrape_chartink_data(url) for url in config.SCANNER_MAPPING.keys()]
    scraped_results = await asyncio.gather(*tasks)

    # --- UPDATED: Call the new analysis and ranking function ---
    analyzed_results = []
    for result in scraped_results:
        if result['data']:
            ranked_result = analyze_and_rank_stocks(result)
            analyzed_results.append(ranked_result)

    # Pass both original and analyzed results to the sheet updater
    update_google_sheet(scraped_results, analyzed_results)

    end_time = time.time()
    print(f"\n--- Automation Finished in {end_time - start_time:.2f} seconds ---")

if __name__ == "__main__":
    asyncio.run(main())