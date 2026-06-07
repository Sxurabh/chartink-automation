# app/services/scraper_service.py
import asyncio
import random
import traceback
from typing import Dict, Any, List, Optional
from playwright.async_api import async_playwright, TimeoutError, Page, Browser
from ..core.config import ScannerConfig, settings
from ..utils.logger import log

STEALTH_SCRIPT = """
Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3, 4, 5] });
Object.defineProperty(navigator, 'languages', { get: () => ['en-US', 'en'] });
"""

VIEWPORTS = [
    {'width': 1920, 'height': 1080},
    {'width': 1366, 'height': 768},
    {'width': 1536, 'height': 864},
    {'width': 1440, 'height': 900},
]

def _load_proxies() -> List[Dict[str, str]]:
    proxies = []
    try:
        with open('proxies.txt', 'r') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                if line.startswith('socks4://') or line.startswith('socks5://'):
                    proxies.append({"server": line})
                else:
                    proxies.append({"server": f"http://{line}"})
    except FileNotFoundError:
        pass
    return proxies

class ScraperService:
    def __init__(self, browser: Browser, proxies: Optional[List[Dict[str, str]]] = None):
        self.browser = browser
        self.proxies = proxies or []
        self._proxy_index = 0

    def _next_proxy(self):
        if not self.proxies:
            return None
        proxy = self.proxies[self._proxy_index % len(self.proxies)]
        self._proxy_index += 1
        random.shuffle(self.proxies)
        return proxy

    async def scrape_single_url(self, scanner: ScannerConfig) -> Dict[str, Any]:
        log.info(f"Starting scrape for: {scanner.name} ({scanner.url})")

        for attempt in range(settings.retry_attempts):
            context = None
            page = None
            try:
                context_options = {
                    'viewport': random.choice(VIEWPORTS),
                    'user_agent': (
                        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                        'AppleWebKit/537.36 (KHTML, like Gecko) '
                        'Chrome/120.0.0.0 Safari/537.36'
                    ),
                }
                if attempt > 0 and self.proxies:
                    proxy = self._next_proxy()
                    context_options['proxy'] = proxy

                context = await self.browser.new_context(**context_options)
                page = await context.new_page()
                await page.add_init_script(STEALTH_SCRIPT)

                await page.goto(scanner.url, timeout=90000, wait_until='domcontentloaded')

                scraped_rows = await self._extract_data_from_pages(page)

                await page.close()
                await context.close()
                log.info(f"Successfully scraped {len(scraped_rows)} entries from {scanner.name}")
                return {"scanner": scanner, "headers": settings.table_headers, "data": scraped_rows}

            except TimeoutError:
                log.warning(f"Timeout error on attempt {attempt + 1} for {scanner.name}. The screener might have no results.")
                if page:
                    await page.close()
                if context:
                    await context.close()
                return {"scanner": scanner, "headers": settings.table_headers, "data": []}
            except Exception as e:
                log.error(f"Error on attempt {attempt + 1} for {scanner.name}: {e}")
                if page:
                    await page.close()
                if context:
                    await context.close()
                if attempt < settings.retry_attempts - 1:
                    log.info(f"Retrying in {settings.retry_delay_seconds} seconds...")
                    await asyncio.sleep(settings.retry_delay_seconds)
                else:
                    log.error(f"All {settings.retry_attempts} attempts failed for {scanner.name}.")
                    traceback.print_exc()
                    return {"scanner": scanner, "headers": settings.table_headers, "data": []}

        return {"scanner": scanner, "headers": settings.table_headers, "data": []}

    async def _extract_data_from_pages(self, page: Page) -> List[List[str]]:
        MAX_PAGES = 20
        scraped_rows = []

        REQUIRED_FIELDS = [
            'name', 'nsecode',
            'scan-column-default-close', 'scan-column-default-volume',
        ]
        field_to_index = None
        data_table = None

        for _ in range(MAX_PAGES):
            await page.wait_for_selector("table tbody tr", timeout=30000)

            if data_table is None:
                tables = await page.query_selector_all("table")
                for table in tables:
                    headers = await table.query_selector_all("thead tr th")
                    for th in headers:
                        field = await th.get_attribute('data-field')
                        if field == 'name':
                            data_table = table
                            break
                    if data_table:
                        break

            if data_table is None:
                log.error("Could not find data table with data-field attributes.")
                break

            if field_to_index is None:
                header_cells = await data_table.query_selector_all("thead tr th")
                field_to_index = {}
                for idx, th in enumerate(header_cells):
                    field = await th.get_attribute('data-field')
                    if field:
                        field_to_index[field] = idx
                if field_to_index:
                    missing = [f for f in REQUIRED_FIELDS if f not in field_to_index]
                    if missing:
                        log.warning(f"Missing required fields in header: {missing}")

            if not field_to_index:
                log.error("Could not build column map from header row.")
                break

            rows = await data_table.query_selector_all("tbody tr")
            max_cell_index = max(field_to_index.values()) if field_to_index else 0
            for row in rows:
                cells = await row.query_selector_all("td")
                if len(cells) <= max_cell_index:
                    continue
                try:
                    row_data = [
                        await cells[field_to_index['name']].inner_text(),
                        await cells[field_to_index['nsecode']].inner_text(),
                        await cells[field_to_index['scan-column-default-close']].inner_text(),
                        await cells[field_to_index['scan-column-default-volume']].inner_text(),
                    ]
                except (IndexError, KeyError) as e:
                    continue
                scraped_rows.append(row_data)

            next_button = page.locator('button:has-text("Next")')
            if await next_button.count() == 0 or not await next_button.first.is_visible():
                break
            if await next_button.first.is_disabled():
                break

            await next_button.first.click()
            try:
                await page.wait_for_load_state('networkidle', timeout=5000)
            except TimeoutError:
                pass

        log.info(f"Extracted {len(scraped_rows)} row(s) from table.")
        return scraped_rows

async def run_scrapers(scanners: List[ScannerConfig]) -> List[Dict[str, Any]]:
    async with async_playwright() as p:
        browser = await p.firefox.launch()
        proxies = _load_proxies()
        if proxies:
            log.info(f"Loaded {len(proxies)} proxies for rotation.")
        service = ScraperService(browser, proxies)

        results = []
        for scanner in scanners:
            result = await service.scrape_single_url(scanner)
            results.append(result)

        await browser.close()
        return results