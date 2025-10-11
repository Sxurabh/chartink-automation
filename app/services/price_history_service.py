# app/services/price_history_service.py
import yfinance as yf
from datetime import date
from dateutil.relativedelta import relativedelta
from typing import Tuple, Optional
from ..utils.logger import log

class PriceHistoryService:
    """
    Fetches historical stock data using a robust, multi-step yfinance approach.
    """
    def get_last_month_ohl(self, symbol: str) -> Optional[Tuple[float, float]]:
        """
        Gets the previous full month's high and low for a given stock symbol.
        It tries yf.download first, and if that fails, falls back to yf.Ticker().history().
        """
        # Clean the symbol and append .NS for NSE stocks
        cleaned_symbol = symbol.replace('&', '-').upper()
        ticker_symbol = f"{cleaned_symbol}.NS"
        
        # Define the date range for the previous complete calendar month
        end_date = date.today().replace(day=1)
        start_date = end_date - relativedelta(months=1)

        # --- Method 1: Try yf.download() first ---
        try:
            hist = yf.download(
                ticker_symbol,
                start=start_date,
                end=end_date,
                interval="1d",
                progress=False,
                threads=False
            )
            if not hist.empty:
                high = round(hist['High'].max(), 2)
                low = round(hist['Low'].min(), 2)
                log.info(f"📈 [Method 1] Fetched H/L for {ticker_symbol}: High={high}, Low={low}")
                return high, low
        except Exception as e:
            log.warning(f"⚠️ [Method 1] yf.download() failed for {ticker_symbol}. Reason: {e}. Trying fallback.")

        # --- Method 2: Fallback to yf.Ticker().history() ---
        try:
            log.info(f" mencoba [Method 2] for {ticker_symbol}...")
            ticker = yf.Ticker(ticker_symbol)
            hist = ticker.history(start=start_date, end=end_date, interval="1d")
            
            if not hist.empty:
                high = round(hist['High'].max(), 2)
                low = round(hist['Low'].min(), 2)
                log.info(f"📈 [Method 2] Successfully fetched H/L for {ticker_symbol}: High={high}, Low={low}")
                return high, low
            else:
                log.warning(f"⚠️ [Method 2] No historical data returned for {ticker_symbol} for the period.")
                return None
        except Exception as e:
            log.error(f"❌ [Method 2] Fallback also failed for {ticker_symbol}. Reason: {e}")
            return None
        
        # If both methods fail, return None after the first attempt's failure log.
        return None