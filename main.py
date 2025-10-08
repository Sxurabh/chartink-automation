# main.py

import asyncio
import time
import config
from scraper import scrape_chartink_data
from sheets import update_monthly_report
from analysis import get_fundamental_analysis, get_ai_analysis
from dotenv import load_dotenv # <-- 1. IMPORT THE LIBRARY

load_dotenv() # <-- 2. LOAD THE .env FILE

async def main():
    start_time = time.time()
    # ... rest of the file is the same
    print("--- Starting Monthly Stock Scan & Analysis ---")

    # --- Stage 1: Discovery (Scraping) ---
    urls = [url for url in config.SCANNER_MAPPING.keys()]
    tasks = [scrape_chartink_data(url) for url in urls]
    scraped_results = await asyncio.gather(*tasks)

    # --- Stage 2: Fundamental Analysis on Raw Data ---
    fundamental_analysis_results = []
    print("\n🔬 Performing Fundamental Analysis on all scraped stocks...")
    for result in scraped_results:
        funda_rows = []
        headers = result['headers'] + ["Fundamental Score", "Reasons"]
        for row in result['data']:
            symbol = row[2]
            score, reasons = get_fundamental_analysis(symbol)
            funda_rows.append(row + [score, reasons])
            print(f"  - Fundamentally analyzed {symbol}: Score {score}")
        
        funda_rows.sort(key=lambda x: x[len(headers)-2], reverse=True)
        fundamental_analysis_results.append({"url": result['url'], "headers": headers, "data": funda_rows})

    # --- Stage 3: AI Analysis on Raw Data ---
    ai_analysis_results = []
    print(f"\n🤖 Performing AI analysis on all scraped stocks...")
    for result in scraped_results:
        ai_rows = []
        headers = result['headers'] + ["AI Investment Thesis", "AI Identified Risks"]
        for row in result['data']:
            symbol = row[2]
            thesis, risks = get_ai_analysis(symbol)
            ai_rows.append(row + [thesis, risks])
            print(f"  - AI analysis complete for {symbol}")
            
        ai_analysis_results.append({"url": result['url'], "headers": headers, "data": ai_rows})
    
    # --- Stage 4: Reporting ---
    update_monthly_report(scraped_results, fundamental_analysis_results, ai_analysis_results)

    end_time = time.time()
    print(f"\n--- Automation Finished in {end_time - start_time:.2f} seconds ---")

if __name__ == "__main__":
    asyncio.run(main())