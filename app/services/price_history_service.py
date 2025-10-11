# app/services/price_history_service.py
import yfinance as yf
import requests
from typing import Tuple, Optional
from ..utils.logger import log
import time

class PriceHistoryService:
    """
    Fetches historical stock data using a robust yfinance approach.
    """
    def get_last_month_ohl(self, symbol: str) -> Optional[Tuple[float, float]]:
        """
        Gets the previous full calendar month's high and low for a given stock symbol.
        It uses yf.Ticker().history() and includes an enhanced retry mechanism for CI/CD environments.
        """
        cleaned_symbol = symbol.replace('&', '-').upper()
        ticker_symbol = f"{cleaned_symbol}.NS"
        
        # Enhanced retry logic for cloud environments
        max_attempts = 4
        initial_delay_seconds = 5

        for attempt in range(max_attempts):
            try:
                # Let yfinance handle its own session management
                ticker = yf.Ticker(ticker_symbol)
                
                # Fetch the last 2 months of data on a monthly interval.
                hist = ticker.history(period="2mo", interval="1mo")
                
                if not hist.empty and len(hist) >= 2:
                    # The previous month's data is the second to last row
                    last_month_data = hist.iloc[-2]
                    high = round(last_month_data['High'], 2)
                    low = round(last_month_data['Low'], 2)
                    log.info(f"✅ [Attempt {attempt + 1}] Fetched H/L for {ticker_symbol}: High={high}, Low={low}")
                    return high, low
                elif not hist.empty:
                    log.warning(f"⚠️ [Attempt {attempt + 1}] Only one month of data returned for {ticker_symbol}.")
                else:
                    log.warning(f"⚠️ [Attempt {attempt + 1}] No historical data returned for {ticker_symbol}.")
            
            except Exception as e:
                log.error(f"❌ Error fetching data for {ticker_symbol} on attempt {attempt + 1}. Reason: {e}")

            # If it's not the last attempt, wait before retrying
            if attempt < max_attempts - 1:
                delay = initial_delay_seconds * (attempt + 1) # Increasing delay (5s, 10s, 15s)
                log.info(f"Retrying for {ticker_symbol} in {delay} seconds...")
                time.sleep(delay)

        log.error(f"❌ All {max_attempts} attempts failed for {ticker_symbol}. Could not retrieve OHLC data.")
        return None