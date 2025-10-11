# app/services/price_history_service.py
import yfinance as yf
import requests
from datetime import date
from dateutil.relativedelta import relativedelta
from typing import Tuple, Optional
from ..utils.logger import log
import time

class PriceHistoryService:
    """
    Fetches historical stock data using a robust yfinance approach with a session and retries.
    """
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36'
        })

    def get_last_month_ohl(self, symbol: str) -> Optional[Tuple[float, float]]:
        """
        Gets the previous full month's high and low for a given stock symbol.
        It uses yf.Ticker().history() with a session and includes a retry mechanism.
        """
        cleaned_symbol = symbol.replace('&', '-').upper()
        ticker_symbol = f"{cleaned_symbol}.NS"
        
        # Define the date range for the previous complete calendar month
        end_date = date.today().replace(day=1)
        start_date = end_date - relativedelta(months=1)

        for attempt in range(2): # Try twice
            try:
                ticker = yf.Ticker(ticker_symbol, session=self.session)
                hist = ticker.history(start=start_date, end=end_date, interval="1d")
                
                if not hist.empty and 'High' in hist and 'Low' in hist and not hist['High'].isnull().all() and not hist['Low'].isnull().all():
                    high = round(hist['High'].max(), 2)
                    low = round(hist['Low'].min(), 2)
                    log.info(f"📈 Fetched H/L for {ticker_symbol}: High={high}, Low={low}")
                    return high, low
                else:
                    log.warning(f"⚠️ No historical data returned for {ticker_symbol} for the period {start_date} to {end_date} on attempt {attempt + 1}.")
            
            except Exception as e:
                log.error(f"❌ Error fetching data for {ticker_symbol} on attempt {attempt + 1}. Reason: {e}")

            if attempt == 0:
                log.info(f"Retrying for {ticker_symbol} in 2 seconds...")
                time.sleep(2) # Blocking sleep is fine here, as this service is not async.

        log.error(f"❌ All attempts failed for {ticker_symbol}. Could not retrieve OHLC data.")
        return None