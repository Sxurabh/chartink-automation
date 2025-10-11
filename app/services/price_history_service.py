# app/services/price_history_service.py
import yfinance as yf
import random
from typing import Tuple, Optional
from ..utils.logger import log
import time

def load_proxies():
    """Loads a list of proxies from proxy_list.txt."""
    try:
        with open('proxies.txt', 'r') as f:
            proxies = [line.strip() for line in f if line.strip()]
        if not proxies:
            log.warning("⚠️ proxy_list.txt is empty. Proceeding without proxies.")
            return []
        log.info(f"✅ Loaded {len(proxies)} proxies from proxy_list.txt.")
        return proxies
    except FileNotFoundError:
        log.warning("⚠️ proxy_list.txt not found. Proceeding without proxies.")
        return []

class PriceHistoryService:
    """
    Fetches historical stock data using a robust yfinance approach with proxy rotation.
    """
    def __init__(self):
        self.proxies = load_proxies()
        self.max_attempts = min(len(self.proxies), 5) if self.proxies else 2

    def get_last_month_ohl(self, symbol: str) -> Optional[Tuple[float, float]]:
        """
        Gets the previous month's high/low, rotating through proxies on failure.
        """
        cleaned_symbol = symbol.replace('&', '-').upper()
        ticker_symbol = f"{cleaned_symbol}.NS"
        
        # Use a copy of the proxy list for this run to avoid reusing failed proxies
        available_proxies = self.proxies[:]
        
        for attempt in range(self.max_attempts):
            proxy = None
            if available_proxies:
                proxy = random.choice(available_proxies)
                # Remove the chosen proxy so we don't reuse it on the next attempt
                available_proxies.remove(proxy)

            try:
                log.info(f"Attempt {attempt + 1}/{self.max_attempts} for {ticker_symbol} using proxy: {proxy or 'None'}")
                ticker = yf.Ticker(ticker_symbol)
                
                hist = ticker.history(
                    period="2mo", 
                    interval="1mo",
                    proxy=f"http://{proxy}" if proxy else None
                )
                
                if not hist.empty and len(hist) >= 2:
                    last_month_data = hist.iloc[-2]
                    high = round(last_month_data['High'], 2)
                    low = round(last_month_data['Low'], 2)
                    log.info(f"✅ Fetched H/L for {ticker_symbol}: High={high}, Low={low}")
                    return high, low
                else:
                    log.warning(f"⚠️ No valid historical data returned for {ticker_symbol}.")

            except Exception as e:
                log.error(f"❌ Error for {ticker_symbol} with proxy {proxy}. Reason: {e}")

            if attempt < self.max_attempts - 1:
                time.sleep(3) # Wait a few seconds before the next attempt

        log.error(f"❌ All {self.max_attempts} attempts failed for {ticker_symbol}.")
        return None