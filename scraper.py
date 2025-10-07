# scraper.py

import asyncio
import traceback
from typing import Dict, List, Any
from playwright.async_api import async_playwright, TimeoutError
import config

async def scrape_chartink_data(url: str) -> Dict[str, Any]:
    """
    Scrapes all visible columns and pages from a ChartInk URL with retry logic.
    """
    print(f"🚀 Starting scrape for URL: {url}...")
    
    for attempt in range(config.RETRY_ATTEMPTS):
        try:
            async with async_playwright() as p:
                browser = await p.firefox.launch()
                page = await browser.new_page()
                
                await page.goto(url, timeout=90000, wait_until='domcontentloaded')
                await page.locator('div[title="Click to run scan"]').click()
                
                scraped_rows = []
                page_num = 1
                while True:
                    await page.wait_for_selector("table tbody tr", timeout=30000)
                    
                    rows = await page.query_selector_all("table tbody tr")
                    for row in rows:
                        all_cells = await row.query_selector_all("td")
                        visible_cells = all_cells[:config.EXPECTED_COLUMN_COUNT]
                        row_data = [await cell.inner_text() for cell in visible_cells]
                        scraped_rows.append(row_data)

                    next_button = page.locator('button:has-text("Next")')
                    if await next_button.count() == 0 or await next_button.is_disabled():
                        break
                    
                    await next_button.click()
                    await page.wait_for_load_state('networkidle')
                    page_num += 1
                
                await browser.close()
                print(f"✅ Successfully scraped {len(scraped_rows)} entries from {url}")
                return {"url": url, "headers": config.TABLE_HEADERS, "data": scraped_rows}

        except TimeoutError:
            print(f"⏱️ Timeout error on attempt {attempt + 1} for {url}. The screener might have no results.")
            # If it's a timeout, it likely means no data, so we can return empty results.
            return {"url": url, "headers": config.TABLE_HEADERS, "data": []}
        except Exception as e:
            print(f"❌ Error on attempt {attempt + 1} for {url}: {e}")
            if attempt < config.RETRY_ATTEMPTS - 1:
                print(f"Retrying in {config.RETRY_DELAY_SECONDS} seconds...")
                await asyncio.sleep(config.RETRY_DELAY_SECONDS)
            else:
                print(f"❌ All {config.RETRY_ATTEMPTS} attempts failed for {url}.")
                traceback.print_exc()
                return {"url": url, "headers": config.TABLE_HEADERS, "data": []} # Return empty on final failure
    
    return {"url": url, "headers": config.TABLE_HEADERS, "data": []}