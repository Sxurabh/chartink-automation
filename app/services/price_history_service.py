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
        It uses yf.Ticker().history() and includes a retry mechanism.
        """
        cleaned_symbol = symbol.replace('&', '-').upper()
        ticker_symbol = f"{cleaned_symbol}.NS"
        
        for attempt in range(2): # Try twice
            try:
                # Let yfinance handle its own session management
                ticker = yf.Ticker(ticker_symbol)
                
                # Fetch the last 2 months of data on a monthly interval.
                # The second to last entry will be the previous full month.
                hist = ticker.history(period="2mo", interval="1mo")
                
                # Check if we have at least two rows (current and previous month)
                if not hist.empty and len(hist) >= 2:
                    # The previous month's data is the second to last row
                    last_month_data = hist.iloc[-2]
                    high = round(last_month_data['High'], 2)
                    low = round(last_month_data['Low'], 2)
                    log.info(f"📈 Fetched H/L for {ticker_symbol}: High={high}, Low={low}")
                    return high, low
                elif not hist.empty:
                    log.warning(f"⚠️ Only one month of data returned for {ticker_symbol}. Not enough history to get the previous month.")
                else:
                    log.warning(f"⚠️ No historical data returned for {ticker_symbol} on attempt {attempt + 1}.")
            
            except Exception as e:
                log.error(f"❌ Error fetching data for {ticker_symbol} on attempt {attempt + 1}. Reason: {e}")

            if attempt == 0:
                log.info(f"Retrying for {ticker_symbol} in 2 seconds...")
                time.sleep(2) # Blocking sleep is fine here as this service is not async.

        log.error(f"❌ All attempts failed for {ticker_symbol}. Could not retrieve OHLC data.")
        return None