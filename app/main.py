# app/main.py
import asyncio
import sys
import time
from .core.config import settings, TABLE_STRIDE, col_letter
from .services.scraper_service import run_scrapers
from .services.sheets_service import SheetsService
from .services.proxy_service import ProxyValidator
from .utils.logger import log

async def main():
    start_time = time.time()

    log.info("--- Starting Monthly Stock Scan and Update ---")

    # 0. Load and validate proxies
    proxy_start = time.time()
    proxies_raw = _load_proxies_raw()
    if proxies_raw:
        log.info(f"Loaded {len(proxies_raw)} proxies. Validating...")
        proxies = await ProxyValidator.validate_all(proxies_raw)
    else:
        proxies = []
    log.info(f"Proxy validation took {time.time() - proxy_start:.2f}s")

    # 1. Scrape data from all configured scanners (parallel)
    scrape_start = time.time()
    scraped_results = await run_scrapers(settings.scanners, proxies)
    log.info(f"Scraping all scanners took {time.time() - scrape_start:.2f}s")

    # 2. Process each scanner result to generate formulas
    process_start = time.time()
    processed_results = []
    for table_index, result in enumerate(scraped_results):
        if not (result and result.get('data')):
            processed_results.append({"scanner_name": result['scanner'].name if result else "Unknown", "data": []})
            continue

        processed_stock_data = []
        for stock_data in result['data']:
            stock_name, symbol, price, volume = stock_data

            name_col = col_letter(table_index * TABLE_STRIDE)
            symbol_col = col_letter(table_index * TABLE_STRIDE + 1)

            name_cell = f'INDIRECT("{name_col}" & ROW())'
            symbol_cell = f'INDIRECT("{symbol_col}" & ROW())'

            high_date_range = f'"high", EOMONTH(TODAY(), -2) + 1, EOMONTH(TODAY(), -1)'
            low_date_range = f'"low", EOMONTH(TODAY(), -2) + 1, EOMONTH(TODAY(), -1)'

            fetch_high = f'IFERROR(MAX(QUERY(GOOGLEFINANCE("NSE:"&{symbol_cell}, {high_date_range}), "SELECT Col2")), IFERROR(MAX(QUERY(GOOGLEFINANCE("BOM:"&{symbol_cell}, {high_date_range}), "SELECT Col2")), ""))'
            fetch_low = f'IFERROR(MIN(QUERY(GOOGLEFINANCE("NSE:"&{symbol_cell}, {low_date_range}), "SELECT Col2")), IFERROR(MIN(QUERY(GOOGLEFINANCE("BOM:"&{symbol_cell}, {low_date_range}), "SELECT Col2")), ""))'

            buy_price_formula = f'=IF(NOT(ISBLANK({name_cell})), {fetch_high}, "")'
            stop_loss_formula = f'=IF(NOT(ISBLANK({name_cell})), {fetch_low}, "")'

            processed_stock_data.append([stock_name, symbol, price, volume, buy_price_formula, stop_loss_formula, ""])

        processed_results.append({"scanner_name": result['scanner'].name, "data": processed_stock_data})
        log.info(f"Processed {len(processed_stock_data)} new stocks for '{result['scanner'].name}'.")

    log.info(f"Processing formulas took {time.time() - process_start:.2f}s")

    # 3. Update Google Sheets
    sheets_start = time.time()
    sheets_service = SheetsService()
    sheets_service.update_scanned_stocks_report(processed_results)
    log.info(f"Google Sheets update took {time.time() - sheets_start:.2f}s")

    elapsed = time.time() - start_time
    log.info(f"--- Automation Finished in {elapsed:.2f} seconds ---")

def _load_proxies_raw() -> list:
    proxies = []
    try:
        with open('proxies.txt', 'r') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                proxies.append(line)
    except FileNotFoundError:
        pass
    return proxies

if __name__ == "__main__":
    asyncio.run(main())
