# main.py

import asyncio
import time
import config
from scraper import scrape_chartink_data
from sheets import update_monthly_report
from analysis import gather_data_for_ai, get_ai_scanned_analysis
from dotenv import load_dotenv

load_dotenv()

async def main():
    start_time = time.time()
    print("--- Starting Monthly Stock Scan & AI-Scoring ---")

    urls = [url for url in config.SCANNER_MAPPING.keys()]
    tasks = [scrape_chartink_data(url) for url in urls]
    scraped_results = await asyncio.gather(*tasks)

    # --- AI-Scoring Analysis ---
    ai_analysis_results = []
    print(f"\n🤖 Performing AI-driven scoring on all scraped stocks...")
    api_key = config.OPENROUTER_API_KEY
    if not api_key:
        print("  -> ⚠️ AI Analysis SKIPPED: OPENROUTER_API_KEY not found.")

    for result in scraped_results:
        scanner_info = config.SCANNER_MAPPING.get(result['url'], {})
        custom_prompt = scanner_info.get("ai_prompt", "Provide a generic financial analysis.")
        
        ai_scores = []
        for row in result['data']:
            symbol = row[2]
            print(f"  - Gathering data for {symbol}...")
            ticker_data = gather_data_for_ai(symbol)
            
            if "error" in ticker_data:
                print(f"    -> Skipping {symbol} due to data gathering error.")
                continue
            
            print(f"  - Sending {symbol} to AI for scoring...")
            if api_key:
                ai_score_obj = await asyncio.to_thread(get_ai_scanned_analysis, ticker_data, api_key, custom_prompt)
                ai_scores.append(ai_score_obj)
                print(f"    -> AI score received for {symbol}: Total {ai_score_obj.get('total_score', 'N/A')}")
        
        # Sort results by total score
        ai_scores.sort(key=lambda x: x.get('total_score', 0), reverse=True)
        
        # Prepare for sheet update
        if ai_scores:
            headers = list(ai_scores[0].keys())
            data_rows = [list(score.values()) for score in ai_scores]
            ai_analysis_results.append({"url": result['url'], "headers": headers, "data": data_rows})
    
    update_monthly_report(scraped_results, ai_analysis_results)

    end_time = time.time()
    print(f"\n--- Automation Finished in {end_time - start_time:.2f} seconds ---")

if __name__ == "__main__":
    asyncio.run(main())