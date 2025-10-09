# app/services/scraper_service.py
import asyncio
import traceback
from typing import Dict, Any, List
from playwright.async_api import async_playwright, TimeoutError, Page, Browser
# Use relative imports
from ..core.config import ScannerConfig, settings
from ..utils.logger import log

class ScraperService:
    """
    A service class to handle web scraping operations with Playwright.
    """
    def __init__(self, browser: Browser):
        self.browser = browser

    async def scrape_single_url(self, scanner: ScannerConfig) -> Dict[str, Any]:
        """
        Scrapes all visible columns and pages from a single ChartInk URL.
        """
        log.info(f"🚀 Starting scrape for: {scanner.name} ({scanner.url})")
        
        for attempt in range(settings.retry_attempts):
            try:
                page = await self.browser.new_page()
                
                await page.goto(scanner.url, timeout=90000, wait_until='domcontentloaded')
                await page.locator('div[title="Click to run scan"]').click()
                
                scraped_rows = await self._extract_data_from_pages(page)
                
                await page.close()
                log.info(f"✅ Successfully scraped {len(scraped_rows)} entries from {scanner.name}")
                return {"scanner": scanner, "headers": settings.table_headers, "data": scraped_rows}

            except TimeoutError:
                log.warning(f"⏱️ Timeout error on attempt {attempt + 1} for {scanner.name}. The screener might have no results.")
                await page.close()
                return {"scanner": scanner, "headers": settings.table_headers, "data": []}
            except Exception as e:
                log.error(f"❌ Error on attempt {attempt + 1} for {scanner.name}: {e}")
                if attempt < settings.retry_attempts - 1:
                    log.info(f"Retrying in {settings.retry_delay_seconds} seconds...")
                    await asyncio.sleep(settings.retry_delay_seconds)
                else:
                    log.error(f"❌ All {settings.retry_attempts} attempts failed for {scanner.name}.")
                    traceback.print_exc()
                    return {"scanner": scanner, "headers": settings.table_headers, "data": []}
        
        return {"scanner": scanner, "headers": settings.table_headers, "data": []}

    async def _extract_data_from_pages(self, page: Page) -> List[List[str]]:
        """
        Extracts table data, handling pagination.
        """
        scraped_rows = []
        while True:
            await page.wait_for_selector("table tbody tr", timeout=30000)
            
            rows = await page.query_selector_all("table tbody tr")
            for row in rows:
                all_cells = await row.query_selector_all("td")
                visible_cells = all_cells[:settings.expected_column_count]
                # 👇 Slicing visible_cells[1:] to skip the first element (the "Sr." column)
                row_data = [await cell.inner_text() for cell in visible_cells[1:]]
                scraped_rows.append(row_data)

            next_button = page.locator('button:has-text("Next")')
            if await next_button.count() == 0 or await next_button.is_disabled():
                break
            
            await next_button.click()
            await page.wait_for_load_state('networkidle')
        
        return scraped_rows

async def run_scrapers(scanners: List[ScannerConfig]) -> List[Dict[str, Any]]:
    """
    Initializes Playwright, runs all scrapers concurrently, and returns results.
    """
    async with async_playwright() as p:
        browser = await p.firefox.launch()
        service = ScraperService(browser)
        
        tasks = [service.scrape_single_url(scanner) for scanner in scanners]
        results = await asyncio.gather(*tasks)
        
        await browser.close()
        return results